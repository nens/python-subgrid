import os
import sys
from python_subgrid.wrapper import SubgridWrapper


def main():
    mdu_path = os.path.abspath(sys.argv[1])
    with SubgridWrapper(mdu=mdu_path, set_logger=False) as subgrid:
        subgrid.initmodel()
        tend = subgrid.get_nd('tend')
        time = subgrid.get_nd('t1')
        subgrid.update(-1)                  # Maar EEN tijdstap om te initialiseren
        while(time<tend):
            subgrid.update(-1)
    print '*'*30
    print 'SIMULATION ENDED !!!!! '
    print '*'*30
