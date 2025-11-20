#!/usr/bin/python
# Python 2/3 compatibility - reviewed and fixed 2025-11-20
# All syntax in this file is compatible with both Python 2.7 and Python 3.x

############################################################
#
# Common commandline main implementation for platform
# testing.
#
############################################################
import argparse

def main(platform):

    ap = argparse.ArgumentParser(description="ONL Platform tool.")

    ap.add_argument("--info", action='store_true')
    ap.add_argument("--env", action='store_true')

    ops = ap.parse_args()

    if ops.info:
        print(platform)

    if ops.env:
        print(platform.get_environment())

