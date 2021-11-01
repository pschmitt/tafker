#!/usr/bin/env python3
# coding: utf-8

import sys

from tafker.tafker import main

if __name__ == "__main__":
    RC = main()
    sys.exit(RC if isinstance(RC, int) else 9)
