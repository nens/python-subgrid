#!/bin/bash
bin/test python_subgrid/tests/test_functional.py:TestCase.$1 $2 $3
# for debugging do:
# gdb --args python bin/test python_subgrid/tests/test_functional.py:TestCase.$1 $2 $3

