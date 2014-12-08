import logging
import datetime
import functools

# enum34
import enum

import pandas
import netCDF4
import numpy as np
import osgeo.osr
import matplotlib.pyplot as plt
import dateutil.rrule

import pyprind
import python_subgrid.particles


# Reason for termination
class Reason(enum.Enum):
    # VTK termination reasons
    OUT_OF_DOMAIN = 1
    NOT_INITIALIZED = 2
    UNEXPECTED_VALUE = 3
    OUT_OF_TIME = 4
    OUT_OF_STEPS = 5
    STAGNATION = 6
    # this is extra for living particles
    DEATH = 11
    ESCAPE = 12


def behaviour(txyz, velocity, targets, survivaltime=60*60*5, i0=0):
    """swim with velocity to a target in the target list"""
    # determine target at t0
    x, y = txyz[0, 1], txyz[0, 2]
    dt = txyz[-1, 0] - txyz[0, 0]

    distance = np.sqrt((targets['x_utm'] - x)**2 + (targets['y_utm'] - y)**2)
    name = distance.argmin()
    target = targets.ix[name]

    # Default reason
    reason = Reason.OUT_OF_TIME.value

    # Make sure we don't overshoot
    if distance.ix[name]/dt <= velocity:
        velocity = min(distance.ix[name]/dt, velocity)
        reason = Reason.ESCAPE.value

    angle = np.arctan2(target['y_utm'] - y, target['x_utm'] - x)
    dx = np.cos(angle) * velocity
    dy = np.sin(angle) * velocity
    # add the velocity to the path
    txyz[:, 1] += dx * txyz[:, 0]
    txyz[:, 2] += dy * txyz[:, 0]

    if (txyz[-1, 0] - (i0 * 900)) > survivaltime:
        reason = Reason.DEATH.value
    return txyz, reason


def num2deg(xtile, ytile, zoom):
    """convert x,y zoom number to a lat/long"""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
    lat_deg = np.degrees(lat_rad)
    return (lon_deg, lat_deg)


def seed_alcatraz(system, velocity=None, behaviour=None):
    """toss in some swimmers"""
    n_new = 50
    x_src = np.random.uniform(locations.ix['alcatraz']['x_utm'], locations.ix['alcatraz']['x_utm']+100,
                              size=n_new)
    y_src = np.random.uniform(locations.ix['alcatraz']['y_utm'], locations.ix['alcatraz']['y_utm']+100,
                              size=n_new)
    system.reseed(
        pts=np.c_[x_src, y_src, np.zeros_like(x_src)],
        velocity=velocity,
        behaviour=behaviour
    )


def seed_domain(system, n_total=2000):
    n_current = len(system.get_ids())
    if n_current < n_total:
        n_new = n_total - n_current
    else:
        n_new = 0
    x_src = np.random.uniform(ll_utm[0], ur_utm[0], size=n_new)
    y_src = np.random.uniform(ll_utm[1], ur_utm[1], size=n_new)
    system.reseed(pts=np.c_[x_src, y_src, np.zeros_like(x_src)])


if __name__ == "__main__":
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
    locations = []
    locations.append(dict(name='alcatraz', lon=-122.4239052, lat=37.8279125))
    locations.append(dict(name='point_blunt', lat=37.852489, lon=-122.419121))
    locations.append(dict(name='golden_gate', lat=37.831936, lon=-122.472733))
    locations.append(dict(name='fishermans_warf', lat=37.810781, lon=-122.412790))
    locations = pandas.DataFrame(locations)

    xyz = wgs2osm.TransformPoints(
        list(np.c_[locations['lon'], locations['lat']])
    )
    locations['x_osm'] = [xyz_i[0] for xyz_i in xyz]
    locations['y_osm'] = [xyz_i[1] for xyz_i in xyz]

    xyz = wgs2utm.TransformPoints(
        np.c_[locations['lon'], locations['lat']]
    )
    locations['x_utm'] = [xyz_i[0] for xyz_i in xyz]
    locations['y_utm'] = [xyz_i[1] for xyz_i in xyz]
    locations = locations.set_index('name')


    # we're using this area
    ll, ur = num2deg(1308, 3167, 13), num2deg(1314, 3163, 13)
    # lookup bounding box in different coordinate systems
    ll_osm = wgs2osm.TransformPoint(ll[0], ll[1])
    ur_osm = wgs2osm.TransformPoint(ur[0], ur[1])

    ll_utm = wgs2utm.TransformPoint(ll[0], ll[1])
    ur_utm = wgs2utm.TransformPoint(ur[0], ur[1])

    ll, ur, ll_osm, ur_osm, ll_utm, ur_utm

    # Model input
    filename = '/Users/baart_f/models/sfo/sfo-3di/subgrid_map_15min.nc'
    ds = netCDF4.Dataset(filename)
    times = netCDF4.num2date(ds.variables['time'][:],
                             ds.variables['time'].units)
    system = python_subgrid.particles.ParticleSystem(ds)

    dfs = []
    selection = times[250:340]
    # 1) initialization with number of iterations
    prbar = pyprind.ProgBar(selection.shape[0],
                            width=100, track_time=True)

    rrule = dateutil.rrule.rrule(
        dateutil.rrule.HOURLY,
        dtstart=datetime.datetime(1962, 6, 11, 19, 0)
    )
    swimmers = rrule.between(
        datetime.datetime(1962, 6, 11, 19, 0),
        datetime.datetime(1962, 6, 12, 4, 0),
        inc=True
    )
    targets = locations[locations.index != 'alcatraz']

    behaviour = functools.partial(behaviour, velocity=0.25, targets=targets)
    for i, t in enumerate(selection):
        prbar.update()
        if t in swimmers:
            behaviour = functools.partial(behaviour, i0=i)
            seed_alcatraz(system, behaviour=behaviour)
        else:
            seed_domain(system)
        system.update_grid(i=i)
        system.tracer.update()
        df = system.get_particles()
        dfs.append(df)
    df = pandas.concat(dfs)
    df.drop_duplicates(cols=['particle', 't'], inplace=True)
    df.sort(columns=['particle', 't'], inplace=True)
    df.to_hdf('parts6.h5', 'particles')
