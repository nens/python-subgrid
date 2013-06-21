"""
This module provides functions for running verification checks on small 
models and to create reports about them.

"""
from __future__ import print_function
import argparse
import logging
import os

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


def run_simulation(mdu_filepath, report):
    original_dir = os.getcwd()
    os.chdir(os.path.dirname(mdu_filepath))
    logger.info("Running %s" % mdu_filepath)
    cmd = '/opt/3di/bin/subgridf90 ' + os.path.basename(mdu_filepath)
    exit_code, output = system(cmd)
    if exit_code:
        logger.error("Loading failed")
        report.record_not_loadable(mdu_filepath, output)
    else:
        logger.info("Successfully loaded")
        report.record_loadable(mdu_filepath, output)

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
    
