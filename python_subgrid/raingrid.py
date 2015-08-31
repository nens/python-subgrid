# -*- coding: utf-8 -*-

from __future__ import division

import datetime
import logging
import math
import os
import tempfile
import urllib
import urlparse

from osgeo import gdal
import netCDF4
import numpy as np


logger = logging.getLogger(__name__)

POLYGON = 'POLYGON (({x1} {y1},{x2} {y1},{x2} {y2},{x1} {y2},{x1} {y1}))'

AREA_WIDE_RAIN = {
    '0': [0.0],
    '3': [0.30, 0.60, 0.90, 1.50, 2.10, 2.10, 1.50, 1.20, 1.05, 0.90,
          0.75, 0.60, 0.45, 0.30, 0.15],
    '4': [0.15, 0.30, 0.45, 0.60, 0.75, 0.90, 1.05, 1.20, 1.50, 2.10,
          2.10, 1.50, 0.90, 0.60, 0.30],
    '5': [0.30, 0.60, 1.50, 2.70, 2.70, 2.10, 1.50, 1.20, 1.05, 0.90,
          0.75, 0.60, 0.45, 0.30, 0.15],
    '6': [0.15, 0.30, 0.45, 0.60, 0.75, 0.90, 1.05, 1.20, 1.50, 2.10,
          2.70, 2.70, 1.50, 0.60, 0.30],
    '7': [0.6, 1.2, 2.1, 3.3, 3.3, 2.7, 2.1, 1.5, 1.2, 0.9, 0.6, 0.3],
    '8': [0.3, 0.6, 0.9, 1.2, 1.5, 2.1, 2.7, 3.3, 3.3, 2.1, 1.2, 0.6],
    '10': [1.8, 3.6, 6.3, 6.3, 5.7, 4.8, 3.6, 2.4, 1.2],
    }


def get_rain(bbox, width, height, datetime,
             srs='epsg:28992',
             layer='radar:5min',
             server='https://raster.lizard.net'):
        """
        Fetches rain from raster server.
        """
        x1, x2, y1, y2 = bbox

        parameters = {'sr': srs,
                      'width': width,
                      'height': height,
                      'layers': layer,
                      'compress': 'deflate',
                      'request': 'getgeotiff',
                      'time': datetime.isoformat(),
                      'geom': POLYGON.format(x1=x1, y1=y1, x2=x2, y2=y2)}

        url = '{path}?{pars}'.format(pars=urllib.urlencode(parameters),
                                     path=urlparse.urljoin(server, 'data'))
        logger.info('Loading rain data from %s...' % url)

        # receive tif into temporary file
        fileno, path = tempfile.mkstemp(suffix='.tif')
        url_file = urllib.urlopen(url)
        os.write(fileno, url_file.read())
        os.close(fileno)

        # read array and remove tempfile
        rain = gdal.Open(path).ReadAsArray()
        os.remove(path)
        return rain


class RainGrid(object):
    """
    Manage a rain grid.

    Only works on the Netherlands.
    """
    def __init__(self, subgrid, url_template=None,
                 memcdf_name='precipitation.nc',
                 size_x=None, size_y=None, initial_value=0.0):
        """subgrid is used to initialize the rain grid.

        url_template is needed in function update: it fetches data from an
        opendap server
        """
        if not url_template:
            logger.warning('No url_template given.')
        if size_x:
            logger.warning('Ignoring deprecated keyword argument: size_x')
        if size_y:
            logger.warning('Ignoring deprecated keyword argument: size_y')

        self.dt_current = None
        self.memcdf_name = memcdf_name
        self.diskless = False

        # Read pixels in model to inspect bathymetry width, height and bbox
        width = subgrid.get_nd('imax') + 1
        height = subgrid.get_nd('jmax') + 1

        x1 = subgrid.get_nd('x0p')
        y2 = subgrid.get_nd('y0p')

        dx = subgrid.get_nd('dxp')
        dy = -subgrid.get_nd('dyp')

        x2 = x1 + width * dx
        y1 = y2 - height * dy

        self.bbox = x1, x2, y1, y2

        # determine width and height for a smaller grid with same aspect

        area = 512 * 512
        aspect = width / height

        width = int(math.sqrt(area * aspect))
        height = int(area / width)

        dx = (x2 - x1) / width
        dy = (y2 - y1) / height

        self.width = width
        self.height = height

        # TODO: replace precipitation.nc with a unique name
        # TODO: add diskless=True, requires netcdf version >= 4.2.x
        # For now use netcdf classic, issue with netcdf redefinition in hdf5
        # format
        logger.info('Creating a %i x %i rain grid.', width, height)
        memcdf = netCDF4.Dataset(self.memcdf_name,
                                 mode="w",
                                 diskless=self.diskless,
                                 format='NETCDF3_64BIT')

        memcdf.createDimension("nx", width)
        memcdf.createDimension("ny", height)

        # Put coordinates and values in the netcdf
        var = memcdf.createVariable(
            "x", datatype="double", dimensions=("nx",))
        var[:] = np.linspace(x1 + dx / 2, x2 - dx / 2, width)
        var.standard_name = 'projected_x_coordinate'
        var.units = 'm'

        var = memcdf.createVariable(
            "y", datatype="double", dimensions=("ny", ))
        var[:] = np.linspace(y1 + dy / 2, y2 - dy / 2, height)
        var.standard_name = 'projected_y_coordinate'
        var.units = 'm'

        rainfall_var = memcdf.createVariable(
            "rainfall", datatype="double", dimensions=("ny", "nx"),
            fill_value=-9999)

        rainfall_var.standard_name = 'precipitation'
        rainfall_var.coordinates = 'y x'
        rainfall_var.units = 'm/min'
        memcdf.close()

        self.fill(initial_value)

    def fill(self, value=0.0):
        """Fill rainfall variable"""
        memcdf = netCDF4.Dataset(
            self.memcdf_name, mode="r+", diskless=self.diskless)
        rainfall_var = memcdf.variables["rainfall"]
        rainfall_var[:, :] = value
        memcdf.sync()
        memcdf.close()

    def update(self, dt, multiplier=1.0):
        """Update the grid with rain at given datetime

        Return True if grid has changed"""
        # Quantize on 5 minutes
        minutes = dt.minute // 5 * 5
        dt_request = datetime.datetime(dt.year, dt.month, dt.day, dt.hour,
                                       minutes, 0)
        if dt_request == self.dt_current:
            # Nothing to do
            return False

        rain = get_rain(bbox=self.bbox,
                        width=self.width,
                        height=self.height,
                        datetime=dt_request)[::-1]

        memcdf = netCDF4.Dataset(self.memcdf_name,
                                 mode="a",
                                 diskless=self.diskless)
        rainfall_var = memcdf.variables["rainfall"]
        rain /= 5     # to mm/min
        rain /= 1000  # to m/min
        rain *= multiplier

        rainfall_var[:] = rain
        memcdf.sync()
        memcdf.close()

        logger.info('Rainfall maximum: %f', rain.max())

        self.dt_current = dt_request
        return True


class AreaWideRainGrid(RainGrid):
    def __init__(self, subgrid, url_template='dummy',
                 memcdf_name='area_wide.nc', *args, **kwargs):

        self.current_value = None
        self.current_rain_definition = None
        self.memcdf_name = memcdf_name
        super(AreaWideRainGrid, self).__init__(
            subgrid,
            url_template=url_template,
            memcdf_name=self.memcdf_name, *args, **kwargs)

    # It has the handy fill method, init with subgrid only
    def update(self, rain_definition, time_seconds):
        idx = int(time_seconds) // 300
        if idx < len(AREA_WIDE_RAIN[rain_definition]) and idx >= 0:
            new_value = AREA_WIDE_RAIN[rain_definition][idx]
            self.cumulative = sum(AREA_WIDE_RAIN[rain_definition][:idx])
        else:
            new_value = 0.0
            if idx > 0:
                self.cumulative = sum(AREA_WIDE_RAIN[rain_definition])
            else:
                self.cumulative = 0

        value_changed = new_value != self.current_value
        definition_changed = rain_definition != self.current_rain_definition
        if value_changed or definition_changed:
            logger.debug('New intensity area wide rain: time %ds new value %f',
                         time_seconds, new_value)
            # convert mm/300s to mm/min????
            self.fill(new_value / 300 * 60)
            self.current_value = new_value
            self.current_rain_definition = rain_definition
            return True
        return False


class RainGridContainer(RainGrid):
    """Container for rain grids"""
    def __init__(self, subgrid, url_template='dummy', *args, **kwargs):
        self.grid_names = set([])
        self.memcdf_name = 'container_grid.nc'
        super(RainGridContainer, self).__init__(
            subgrid, url_template,
            memcdf_name=self.memcdf_name, *args, **kwargs)

    def register(self, name):
        self.grid_names.add(name)

    def unregister(self, name):
        self.grid_names.remove(name)

    def update(self):
        """Recalculate sum of grids"""
        memcdf = netCDF4.Dataset(self.memcdf_name, mode="a", diskless=False)
        rainfall_var = memcdf.variables["rainfall"]

        if not self.grid_names:
            rainfall_var[:, :] = 0
        first = True
        for grid_name in self.grid_names:
            _memcdf = netCDF4.Dataset(grid_name, mode="r+", diskless=False)
            if first:
                rainfall_var[:, :] = _memcdf.variables["rainfall"][:, :]
                first = False
            else:
                rainfall_var[:, :] += _memcdf.variables["rainfall"][:, :]
            _memcdf.close()
        memcdf.sync()
        memcdf.close()

    def delete_memcdf(self):
        if os.path.exists(self.memcdf_name):
            os.remove(self.memcdf_name)
