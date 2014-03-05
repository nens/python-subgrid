import numpy as np
import netCDF4
import datetime
import logging
import scipy.interpolate


logger = logging.getLogger(__name__)


class RainGrid(object):
    """
    Manage a rain grid.

    Only works on the Netherlands.
    """
    def __init__(
        self, subgrid, url_template='', memcdf_name='precipitation.nc', 
        size_x=500, size_y=500, initial_value=0.0):

        """
        subgrid is used to initialize the rain grid.

        url_template is needed in function update: it fetches data from an opendap server
        """
        if not url_template:
            logger.warning('No url_template given.')
        self.url_template = url_template
        self.size_x = size_x
        self.size_y = size_y
        self.dt_current = None
        self.memcdf_name = memcdf_name
        self.diskless = False

        # Read pixels in model to create grid for rain
        pixels = {}
        pixels['dps'] = subgrid.get_nd('dps')[1:-1,1:-1].T # contains ghost cells? # why transposed
        pixels['dps'] = np.ma.masked_array(-pixels['dps'], mask=pixels['dps']==pixels['dps'].min())
        pixels['x0p'] = subgrid.get_nd('x0p')
        pixels['dxp'] = subgrid.get_nd('dxp')
        pixels['y0p'] = subgrid.get_nd('y0p')
        pixels['dyp'] = subgrid.get_nd('dyp')
        pixels['imax'] = subgrid.get_nd('imax')
        pixels['jmax'] = subgrid.get_nd('jmax')
        pixels['x'] = np.arange(pixels['x0p'], pixels['x0p'] + pixels['imax']*pixels['dxp'], pixels['dxp'])
        pixels['y'] = np.arange(pixels['y0p'], pixels['y0p'] + pixels['jmax']*pixels['dyp'], pixels['dyp'])
        #logger.info(pixels)

        # Create a new grid for our rain
        self.interp = {}
        self.interp['x'] = np.linspace(pixels['x'].min(), pixels['x'].max(), num=self.size_x)
        self.interp['y'] = np.linspace(pixels['y'].min(), pixels['y'].max(), num=self.size_y)
        self.interp['X'], self.interp['Y'] = np.meshgrid(self.interp['x'], self.interp['y'])

        # TODO: replace precipitation.nc with a unique name
        # TODO: add diskless=True, requires netcdf version >= 4.2.x
        # For now use netcdf classic, issue with netcdf redefinition in hdf5 format
        memcdf = netCDF4.Dataset(self.memcdf_name, mode="w", diskless=self.diskless, format='NETCDF3_64BIT')

        memcdf.createDimension("nx", self.interp['x'].shape[0])
        logger.info('interp x shape %r' % self.interp['x'].shape[0])
        memcdf.createDimension("ny", self.interp['y'].shape[0])
        logger.info('interp y shape %r' % self.interp['y'].shape[0])

        # Put coordinates and values in the netcdf
        var = memcdf.createVariable("x", datatype="double", dimensions=("nx",))
        var[:] = self.interp['x']
        var.standard_name = 'projected_x_coordinate'
        var.units = 'm'

        var = memcdf.createVariable("y", datatype="double", dimensions=("ny", ))
        var[:] = self.interp['y']
        var.standard_name = 'projected_y_coordinate'
        var.units = 'm'

        rainfall_var = memcdf.createVariable(
            "rainfall", datatype="double", dimensions=("ny", "nx"), fill_value=-9999)
        #logger.info('interp X shape')
        #logger.info(self.interp['X'].shape)

        rainfall_var.standard_name = 'precipitation'
        rainfall_var.coordinates = 'y x'
        rainfall_var.units = 'm/min'
        #memcdf.sync()
        memcdf.close()

        self.fill(initial_value)

        #self.memcdf.close()

    def fill(self, value=0.0):
        """Fill rainfall variable"""
        memcdf = netCDF4.Dataset(self.memcdf_name, mode="r+", diskless=self.diskless)
        #print(memcdf.variables.keys())
        rainfall_var = memcdf.variables["rainfall"]
        rainfall_var[:,:] = value #interp['Z']*(1/5.0)*(1/1000.0) #  mm/5min * 5min/min * m/mm -> m/min 
        memcdf.sync()
        memcdf.close()

    def update(self, dt, multiplier=1.0):
        """Update the (interpolated) grid with given datetime"""
        if not self.url_template:
            logger.error('No url_template given, cannot use opendap server.')
            return

        # Quantize on 5 minutes
        minutes = dt.minute / 5 * 5
        dt_request = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, minutes, 0)
        if dt_request == self.dt_current:
            # Nothing to do
            return

        url = self.url_template.format(year=dt.year, month='%02d' % dt.month)
        logger.info('Reading rain data from %s...' % url)
        # url = 'http://opendap.nationaleregenradar.nl/thredds/dodsC/radar/TF0005_A/2013/10/01/RAD_TF0005_A_20131001000000.h5'
        ds = netCDF4.Dataset(url)

        rain = {}
        rain['time'] = netCDF4.num2date(ds.variables['time'][:], ds.variables['time'].units)
        rain['x'] = ds.variables['east'][:]
        rain['y'] = ds.variables['north'][:]
        rain['P'] = ds.variables['precipitation']

        # Pick the index of the requested datetime.
        time_idx = np.where(rain['time'] == dt_request)[0]
        rain['p'] = rain['P'][:,:,time_idx] # x, y expected by some routines

        # Interpolate rain data rain -> interp
        logger.info('Interpolating rain data...')
        F = scipy.interpolate.RectBivariateSpline(
            rain['x'].ravel(), 
            rain['y'][::-1], 
            # reverse y axis and swap x,y
            np.swapaxes(rain['p'][::-1,:].filled(0), 0,1)
        )

        # Evaluate the interpolation function on the new grid
        self.interp['z'] = F.ev(self.interp['X'].ravel(), self.interp['Y'].ravel())

        self.interp['Z'] = self.interp['z'].reshape(self.interp['X'].shape)

        logger.info('Updating memcdf...')

        ds.close()

        memcdf = netCDF4.Dataset(self.memcdf_name, mode="a", diskless=self.diskless)
        rainfall_var = memcdf.variables["rainfall"]
        rainfall_var[:,:] = self.interp['Z']*(1/5.0)*(1/1000.0)*multiplier #  mm/5min * 5min/min * m/mm -> m/min 
        memcdf.sync()
        memcdf.close()

        logger.info('Rainfall sum: %f' % np.sum(self.interp['Z']*(1/5.0)*(1/1000.0)*multiplier))


        self.dt_current = dt_request
