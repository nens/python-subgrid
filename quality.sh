#!/bin/sh
bin/pep8 python_subgrid  | perl -ple 's/: [WE](\d+)/: [W$1]/' > pep8.txt
bin/pyflakes python_subgrid | perl -ple 's/:\ /: [E] /' >> pep8.txt
cat pep8.txt
