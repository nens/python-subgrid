import netCDF4
import numpy as np
from tvtk.api import  tvtk
import mayavi.sources.vtk_data_source
import mayavi.mlab
import matplotlib.cm
import matplotlib.colors
import osgeo.osr
import datetime
import pandas
import scipy.interpolate
import requests
import io
import collections
import python_subgrid.particles
import logging
import pyprind
import ipdb
import matplotlib.pyplot as plt

def num2deg(xtile, ytile, zoom):
    """convert x,y zoom number to a lat/long"""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
    lat_deg = np.degrees(lat_rad)
    return (lon_deg, lat_deg)


def seed_alcatraz(system):
    n_current = len(system.get_ids())
    n_new = 50
    x_src = np.random.uniform(alcatraz['x_utm'], alcatraz['x_utm']+100, size=n_new)
    y_src = np.random.uniform(alcatraz['y_utm'], alcatraz['y_utm']+100, size=n_new)
    system.reseed(pts=np.c_[x_src, y_src, np.zeros_like(x_src)])

def seed_domain(system, n_total=2000):
    n_current = len(system.get_ids())
    if n_current < n_total:
        n_new = n_total - n_current
    else:
        n_new = 0
    x_src = np.random.uniform(ll_utm[0], ur_utm[0], size=n_new)
    y_src = np.random.uniform(ll_utm[1], ur_utm[1], size=n_new)
    system.reseed(pts=np.c_[x_src, y_src, np.zeros_like(x_src)])


logging.basicConfig()
logging.root.setLevel(logging.WARNING)

# generate the spatial reference systems and the transformations
utm_srs = osgeo.osr.SpatialReference()
utm_srs.ImportFromEPSGA(26910)
osm_srs = osgeo.osr.SpatialReference()
osm_srs.ImportFromEPSGA(3857)
wgs_srs = osgeo.osr.SpatialReference()
wgs_srs.ImportFromEPSGA(4326)
utm2wgs = osgeo.osr.CoordinateTransformation(utm_srs, wgs_srs)
utm2osm = osgeo.osr.CoordinateTransformation(utm_srs, osm_srs)
wgs2utm = osgeo.osr.CoordinateTransformation(wgs_srs, utm_srs)
wgs2osm = osgeo.osr.CoordinateTransformation(wgs_srs, osm_srs)

# define the location of the Alcatraz escape location
alcatraz = {}
alcatraz['lon'] = -122.4239052
alcatraz['lat'] = 37.8279125
alcatraz['x_osm'], alcatraz['y_osm'], _ = wgs2osm.TransformPoint(alcatraz['lon'], alcatraz['lat'])
alcatraz['x_utm'], alcatraz['y_utm'], _ = wgs2utm.TransformPoint(alcatraz['lon'], alcatraz['lat'])

# we're using this area
ll, ur = num2deg(1308, 3167, 13), num2deg(1314, 3163, 13)
# lookup bounding box in different coordinate systems
ll_osm = wgs2osm.TransformPoint(ll[0], ll[1])
ur_osm = wgs2osm.TransformPoint(ur[0], ur[1])

ll_utm = wgs2utm.TransformPoint(ll[0], ll[1])
ur_utm = wgs2utm.TransformPoint(ur[0], ur[1])

ll, ur, ll_osm, ur_osm, ll_utm, ur_utm
# we'll use the version with a sepia color (for contrast with the blue lines)
img = plt.imread('sfo_13_1308_1314_3163_3167-sepia.png')


ds = netCDF4.Dataset('/home/fedor/Downloads/subgrid_map_15min.nc')
times = netCDF4.num2date(ds.variables['time'][:], ds.variables['time'].units)
system = python_subgrid.particles.ParticleSystem(ds)




dfs = []
selection = times[250:340]
prbar = pyprind.ProgBar(selection.shape[0],
                        width=100, track_time=True)   # 1) initialization with number of iterations

swimmers = [datetime.datetime(1962, 6, 11, 22, 0),
            datetime.datetime(1962, 6, 11, 23, 0),
            datetime.datetime(1962, 6, 12, 0, 0),
            datetime.datetime(1962, 6, 12, 1, 0),
            datetime.datetime(1962, 6, 12, 2, 0),
            datetime.datetime(1962, 6, 12, 3, 0),
            datetime.datetime(1962, 6, 12, 4, 0)]
for i, t in enumerate(selection):
    prbar.update()
    if t in swimmers:
        seed_alcatraz(system)
    else:
        seed_domain(system)
    system.update_grid(i=i)
    system.tracer.update()
    df = system.get_particles()
    dfs.append(df)
df = pandas.concat(dfs)
df.drop_duplicates(cols=['particle', 't'], inplace=True)
df.sort(columns=['particle', 't'], inplace=True)
df.to_hdf('parts2.h5', 'particles')
