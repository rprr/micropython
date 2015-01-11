from __future__ import print_function

import argparse
import re
import sys

# codepoint2name is different in Python 2 to Python 3
import platform
if platform.python_version_tuple()[0] == '2':
    from htmlentitydefs import codepoint2name
elif platform.python_version_tuple()[0] == '3':
    from html.entities import codepoint2name
codepoint2name[ord('-')] = 'hyphen';

# add some custom names to map characters that aren't in HTML
codepoint2name[ord(' ')] = 'space'
codepoint2name[ord('\'')] = 'squot'
codepoint2name[ord(',')] = 'comma'
codepoint2name[ord('.')] = 'dot'
codepoint2name[ord(':')] = 'colon'
codepoint2name[ord('/')] = 'slash'
codepoint2name[ord('%')] = 'percent'
codepoint2name[ord('#')] = 'hash'
codepoint2name[ord('(')] = 'paren_open'
codepoint2name[ord(')')] = 'paren_close'
codepoint2name[ord('[')] = 'bracket_open'
codepoint2name[ord(']')] = 'bracket_close'
codepoint2name[ord('{')] = 'brace_open'
codepoint2name[ord('}')] = 'brace_close'
codepoint2name[ord('*')] = 'star'
codepoint2name[ord('!')] = 'bang'

# this must match the equivalent function in qstr.c
def compute_hash(qstr):
    hash = 5381
    for char in qstr:
        hash = (hash * 33) ^ ord(char)
    # Make sure that valid hash is never zero, zero means "hash not computed"
    return (hash & 0xffff) or 1

def do_work(infiles):
    # read the qstrs in from the input files
    qcfgs = {}
    qstrs = {}
    for infile in infiles:
        with open(infile, 'rt') as f:
            for line in f:
                line = line.strip()

                # is this a config line?
                match = re.match(r'^QCFG\((.+), (.+)\)', line)
                if match:
                    value = match.group(2)
                    if value[0] == '(' and value[-1] == ')':
                        # strip parenthesis from config value
                        value = value[1:-1]
                    qcfgs[match.group(1)] = value
                    continue

                # is this a QSTR line?
                match = re.match(r'^Q\((.*)\)$', line)
                if not match:
                    continue

                # get the qstr value
                qstr = match.group(1)
                ident = re.sub(r'[^A-Za-z0-9_]', lambda s: "_" + codepoint2name[ord(s.group(0))] + "_", qstr)

                # don't add duplicates
                if ident in qstrs:
                    continue

                # add the qstr to the list, with order number to retain original order in file
                qstrs[ident] = (len(qstrs), ident, qstr)

    # process the qstrs, printing out the generated C header file
    print('// This file was automatically generated by makeqstrdata.py')
    print('')
    # add NULL qstr with no hash or data
    print('QDEF(MP_QSTR_NULL, (const byte*)"\\x00\\x00\\x00\\x00" "")')
    for order, ident, qstr in sorted(qstrs.values(), key=lambda x: x[0]):
        qhash = compute_hash(qstr)
        qlen = len(qstr)
        qdata = qstr.replace('"', '\\"')
        print('QDEF(MP_QSTR_%s, (const byte*)"\\x%02x\\x%02x\\x%02x\\x%02x" "%s")' % (ident, qhash & 0xff, (qhash >> 8) & 0xff, qlen & 0xff, (qlen >> 8) & 0xff, qdata))

    return True

def main():
    arg_parser = argparse.ArgumentParser(description='Process raw qstr file and output qstr data with length, hash and data bytes')
    arg_parser.add_argument('files', nargs='+', help='input file(s)')
    args = arg_parser.parse_args()

    result = do_work(args.files)
    if not result:
        print('exiting with error code', file=sys.stderr)
        exit(1)

if __name__ == "__main__":
    main()
