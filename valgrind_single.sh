#!/bin/bash
valgrind --track-origins=yes --gen-suppressions=all --suppressions=extra.supp --suppressions=valgrind-python.supp  python bin/test python_subgrid/tests/test_functional.py:TestCase.$1 $2 $3

