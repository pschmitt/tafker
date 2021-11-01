#!/usr/bin/env python3
# coding: utf-8

import sys

from tafker.tafker import main

if __name__ == "__main__":
    rc = main()
    sys.exit(rc if isinstance(rc, int) else 9)
