# -*- coding: utf-8 -*-
"""
Findings:
- dps transpose questionable? Does it matter?
- Range endpoint is exclusive.
- Coordinates are now topleft coordinates instead of centers
- Fetched data is of correct date and location
- Spline sum is approximately same as neasest neighbour sum:
    ('spline: ', 445.52081027555687)
    ('nearest:', 452.0166)
- Data is interpolated and stored with smallest y-coordinate first

Changes:
- Fix aranges
- Remove interpolation alltogether
- Data straight from raster-server as in-memory geotiff, see extract tool.

Remaining questions:
- Okay to interpolate exactly on dxp and dyp grid?
- Okay to treat x0p and y0p as centers of cells?
- Okay to return upside-down grid?
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from datetime import datetime as Datetime
import argparse
import logging
import sys

from osgeo import gdal

from python_subgrid.raingrid import RainGrid

logger = logging.getLogger(__name__)


class Subgrid(dict):
    def __init__(self, path):
        dataset = gdal.Open(path)
        self.dps = -dataset.ReadAsArray()
        p, a, b, q, c, d = dataset.GetGeoTransform()
        self.x0p = p
        self.dxp = a
        self.y0p = q
        self.dyp = d
        self.jmax, self.imax = self.dps.shape

    def get_nd(self, key):
        return getattr(self, key)


def sandbox():
    subgrid = Subgrid('kockengen.tif')
    url_template = ('http://opendap.nationaleregenradar.nl'
                    '/thredds/dodsC/radar/TF0005_A/'
                    '{year}/{month}/01/RAD_TF0005_A_{year}{month}01000000.h5')
    rain_grid = RainGrid(subgrid=subgrid, url_template=url_template)

    rain_grid.update(Datetime(2014, 7, 28, 10))
    logger.debug('done.')


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    return parser


def main():
    """ Call command with args from parser. """
    kwargs = vars(get_parser().parse_args())

    logging.basicConfig(stream=sys.stderr,
                        level=logging.DEBUG,
                        format='%(message)s')

    try:
        sandbox(**kwargs)
        return 0
    except:
        logger.exception('An exception has occurred.')
        return 1


if __name__ == '__main__':
    exit(main())
