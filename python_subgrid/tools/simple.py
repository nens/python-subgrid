import os
import sys

from python_subgrid.wrapper import SubgridWrapper


def main():
    mdu_path = os.path.abspath(sys.argv[1])
    with SubgridWrapper(mdu=mdu_path, set_logger=False) as subgrid:
        tend = subgrid.get_nd('tend')
        time = subgrid.get_nd('t1')
        while(time < tend):
            subgrid.update(-1)
            time = subgrid.get_nd('t1')
