"""
This module provides functions for running verification checks on small 
models and to create reports about them.

"""
from __future__ import print_function
import argparse
import csv
import logging
import os

from netCDF4 import Dataset
import numpy as np
from jinja2 import Environment, PackageLoader

from python_subgrid.wrapper import SubgridWrapper
from python_subgrid.utils import system

jinja_env = Environment(loader=PackageLoader('python_subgrid', 'templates'))
logger = logging.getLogger(__name__)


class Report(object):

    def __init__(self):
        self.not_loadable = []
        self.loadable = []

    def record_not_loadable(self, mdu_file, output):
        self.not_loadable.append([mdu_file, output])

    def record_loadable(self, mdu_file, output):
        self.loadable.append([mdu_file, output])

    def write_template(self, template_name, outfile=None, title=None):
        if outfile is None:
            outfile = template_name
        template = jinja_env.get_template(template_name)
        open(outfile, 'w').write(template.render(view=self, title=title))
        logger.debug("Wrote %s", outfile)

    def export_reports(self):
        self.write_template('index.html',
                            title='Overview')
        self.write_template('not_loadable.html',
                            title='Not loadable MDUs')
        self.write_template('loadable.html',
                            title='Loadable MDUs')


def check_his(instructions, report=None):
    netcdf_filename = 'subgrid_his.nc'
    with Dataset(netcdf_filename) as dataset:
        for instruction in instructions:
            # Brute force for now.
            parameter_name = instruction['param']
            if not parameter_name in dataset.variables:
                logger.error("Parameter '%s' not found in %s",
                             parameter_name,
                             dataset.variables.keys())
                continue
            parameter_values = dataset.variables[parameter_name][:]
            desired_time = instruction['time']
            if desired_time == 'SUM':
                logger.debug("Summing all values")
                found = parameter_values.sum()
            else:
                desired_time = float(desired_time)
                logger.debug("Looking up value for time %s", desired_time)
                # TODO: less brute force, if possible.
                time_values = list(dataset.variables['time'][:])
                try:
                    desired_index = time_values.index(desired_time)
                except ValueError:
                    logger.exception("Time %s not found in %s",
                                     desired_time,
                                     time_values)
                    continue
                found = parameter_values[desired_index][0]

            desired = instruction['ref']
            logger.info("Found value %s for parameter %s; desired=%s", 
                        found,
                        parameter_name,
                        desired)
                        

def run_simulation(mdu_filepath, report):
    original_dir = os.getcwd()
    os.chdir(os.path.dirname(mdu_filepath))
    logger.debug("Loading %s...", mdu_filepath)
    cmd = '/opt/3di/bin/subgridf90 ' + os.path.basename(mdu_filepath)
    # ^^^ TODO: hardcoded.
    exit_code, output = system(cmd)
    if exit_code:
        logger.error("Loading failed: %s", mdu_filepath)
        report.record_not_loadable(mdu_filepath, output)
    else:
        logger.info("Successfully loaded: %s", mdu_filepath)
        report.record_loadable(mdu_filepath, output)
        csv_filenames = [f for f in os.listdir('.') if f.endswith('.csv')]
        for csv_filename in csv_filenames:
            logger.info("Reading instructions from %s", csv_filename)
            with open(csv_filename) as csv_file:
                instructions = list(csv.DictReader(csv_file, delimiter=';'))
                if 'his' in csv_filename:
                    check_his(instructions, report=report)
                else:
                    logger.warn("TODO: Handle this one")
    os.chdir(original_dir)


def mdu_filepaths(basedir):
    """Iterator that yields full paths to .mdu files."""
    basedir = os.path.abspath(basedir)
    for dirpath, dirnames, filenames in os.walk(basedir):
        mdu_filenames = [f for f in filenames if f.endswith('.mdu')]
        for mdu_filename in mdu_filenames:
            yield os.path.join(dirpath, mdu_filename)


def main():
    parser = argparse.ArgumentParser(
        description='Run verification tests on the "unit test" models.')
    parser.add_argument('directory',
                        nargs='?',
                        default='.',
                        help='directory with the tests')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    report = Report()
    for mdu_filepath in mdu_filepaths(args.directory):
        run_simulation(mdu_filepath, report)
    report.export_reports()
    
