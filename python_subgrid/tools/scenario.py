"""
Read scenario files

*.json
"""
import datetime
import iso8601
import json
import logging
import os
import random
import string

from python_subgrid.raingrid import RainGrid
from python_subgrid.raingrid import AreaWideRainGrid


logger = logging.getLogger(__name__)


def random_string(length):
    return ''.join(
        random.choice(string.ascii_lowercase)
        for _ in range(length))


class Event(object):
    expected_fields = set([
        'sim_time_start',  # time start in seconds
        'sim_time_end',   # can be None
        ])

    def __init__(self, *args, **kwargs):
        # every key in kwargs must be present in expected fields
        for k in kwargs.keys():
            assert(k in self.expected_fields)

        self.sim_time_start = float(kwargs['sim_time_start'])
        if kwargs['sim_time_end'] == 'None' or kwargs['sim_time_end'] is None:
            self.sim_time_end = None
        else:
            self.sim_time_end = float(kwargs['sim_time_end'])


class RadarGrid(Event):
    expected_fields = set([
        'sim_time_start',  # time start in seconds
        'sim_time_end',  # can be None
        'radar_dt',  # radar datetime at sim_time_start
        'sync',  # not used
        'multiplier',  # not used
        'type',  # not used
        ])

    def __init__(self, *args, **kwargs):
        super(RadarGrid, self).__init__(*args, **kwargs)
        self.radar_dt = iso8601.parse_date(kwargs['radar_dt'])
        self.memcdf_name = 'precipitation_%s.nc' % random_string(8)
        self.rain_grid_dt = None  # current radar datetime

    def init(self, subgrid, radar_url_template):
        self.subgrid = subgrid
        self.radar_url_template = radar_url_template
        self.rain_grid = RainGrid(
            subgrid, url_template=radar_url_template,
            memcdf_name=self.memcdf_name,
            size_x=500, size_y=500, initial_value=0.0)
        self.rain_grid_dt = self.radar_dt

    def update(self, sim_time):
        """Update grid and apply. Return whether the grid has changed"""
        self.rain_grid_dt = (
            self.radar_dt + datetime.timedelta(
                seconds=int(float(sim_time)) -
                int(float(self.sim_time_start))))
        changed = self.rain_grid.update(dt=self.rain_grid_dt, multiplier=1000)
        return changed

    def delete_memcdf(self):
        if os.path.exists(self.memcdf_name):
            os.remove(self.memcdf_name)

    def __str__(self):
        return 'rain grid %s (%r-%r)' % (
            self.radar_dt.strftime('%Y-%m-%d'),
            self.sim_time_start, self.sim_time_end)


class AreaWideGrid(Event):
    expected_fields = set([
        'sim_time_start',  # time start in seconds
        'sim_time_end',  # can be None
        'rain_definition',  # which "ontwerpbui"?
        'type',  # not used
        ])

    def __init__(self, *args, **kwargs):
        super(AreaWideGrid, self).__init__(*args, **kwargs)
        self.rain_definition = kwargs['rain_definition']
        self.memcdf_name = 'area_wide_%s.nc' % random_string(8)

    def init(self, subgrid):
        self.subgrid = subgrid
        self.rain_grid = AreaWideRainGrid(
            subgrid,
            memcdf_name=self.memcdf_name)

    def update(self, sim_time):
        """Update grid and apply. Return whether the grid has changed"""
        lookup_time = int(sim_time - self.sim_time_start)
        changed = self.rain_grid.update(
            rain_definition=self.rain_definition,
            time_seconds=lookup_time)
        return changed

    def delete_memcdf(self):
        if os.path.exists(self.memcdf_name):
            os.remove(self.memcdf_name)

    def __str__(self):
        return 'area wide rain grid %s (%r-%r)' % (
            self.rain_definition, self.sim_time_start, self.sim_time_end)


class EventContainer(object):
    """
    Container for events aka scenario
    """
    area_wide_rain_grids_filename = 'area_wide_rain_grids.json'
    radar_grids_filename = 'radar_grids.json'

    def __init__(self, path=None):
        self._events = []
        if path is not None:
            self.from_path(path)

    def events(self, event_object=None, sim_time=None,
               start_within=None, ends_within=None):
        """
        return event(s) for given sim_time, or return all events

        option: start_within: typically the timestep size or delta time,
          sim_time_start should be with within this time from sim_sime
        """
        if sim_time is not None:
            result = []
            for e in self._events:

                if event_object is not None:
                    if not isinstance(e, event_object):
                        continue
                if start_within is not None:
                    if (e.sim_time_start >= sim_time and
                        e.sim_time_start < sim_time + start_within):

                        result.append(e)
                    continue
                if ends_within is not None:
                    if (e.sim_time_end is not None and
                        e.sim_time_end <= sim_time and
                        e.sim_time_end > sim_time - ends_within):

                        result.append(e)
                    continue

                # normal
                if ((e.sim_time_start <= sim_time) and
                    (e.sim_time_end is None or
                     e.sim_time_end > sim_time)):

                    result.append(e)

            return result
        else:
            return self._events

    def from_file(self, event_object, filename):
        with open(filename, 'r') as json_data:
            data = json.load(json_data)
            for event in data:
                self.add(event_object, **event)

    def from_path(self, path):
        """Load all files from given path"""
        fn = os.path.join(path, self.radar_grids_filename)
        if os.path.exists(fn):
            logger.info('Reading radar grids [%s]...' % fn)
            self.from_file(RadarGrid, fn)

        fn = os.path.join(path, self.area_wide_rain_grids_filename)
        if os.path.exists(fn):
            logger.info('Reading area wide rain grids [%s]...' % fn)
            self.from_file(AreaWideGrid, fn)

    def add(self, event_object, **kwargs):
        self._events.append(event_object(**kwargs))

    def summary(self):
        result = []
        count = {'area_wide_grid': 0, 'radar_grid': 0}
        for e in self._events:
            if isinstance(e, AreaWideGrid):
                count['area_wide_grid'] += 1
            elif isinstance(e, RadarGrid):
                count['radar_grid'] += 1
        result.append('Area Wide Grids : %d' % count['area_wide_grid'])
        result.append('Radar Grids     : %d' % count['radar_grid'])
        for e in self._events:
            result.append('  event         : %s' % str(e))
        return result

def apply_events(subgrid, scenario, rain_grid_container):
    """Apply events that will occur during the current timestep."""
    t1 = subgrid.get_nd('t1')
    t0 = subgrid.get_nd('t0')
    dt = subgrid.get_nd('dt')

    sim_time = float(t1)
    previous_t = float(t0)
    radar_url_template = 'http://opendap.nationaleregenradar.nl/thredds/dodsC/radar/TF0005_A/{year}/{month}/01/RAD_TF0005_A_{year}{month}01000000.h5'
    radar_grid_changed = False
    # starting scenario events
    events_init = scenario.events(
        sim_time=sim_time, start_within=sim_time - previous_t)
    for event in events_init:
        logger.info('Init event: %s' % str(event))
        if isinstance(event, RadarGrid):
            event.init(subgrid, radar_url_template)
            rain_grid_container.register(event.memcdf_name)
        elif isinstance(event, AreaWideGrid):
            event.init(subgrid)
            rain_grid_container.register(event.memcdf_name)

    # finished scenario events
    events_finish = scenario.events(
        sim_time=sim_time, ends_within=dt)
    for event in events_finish:
        logger.info('Finish event: %s' % str(event))
        if isinstance(event, RadarGrid):
            rain_grid_container.unregister(event.memcdf_name)
            radar_grid_changed = True
        elif isinstance(event, AreaWideGrid):
            rain_grid_container.unregister(event.memcdf_name)
            radar_grid_changed = True

    # active scenario events
    events = scenario.events(sim_time=sim_time)
    for event in events:
        # logger.info('Update event: %s' % str(event))
        if isinstance(event, RadarGrid):
            changed = event.update(sim_time)
            if changed:
                radar_grid_changed = True
        if isinstance(event, AreaWideGrid):
            changed = event.update(sim_time)
            if changed:
                radar_grid_changed = True
    if radar_grid_changed:
        # update container
        rain_grid_container.update()


def clean_events(scenario, rain_grid_container):
    """Clean up events and corresponding files."""
    logger.info('Cleaning up...')
    for event in scenario.events():
        if isinstance(event, RadarGrid):
            logger.info('deleting temp file %s...',
                        event.memcdf_name)
            event.delete_memcdf()
        elif isinstance(event, AreaWideGrid):
            logger.info('deleting temp file %s...',
                        event.memcdf_name)
            event.delete_memcdf()
            logger.info('deleting temp file %s...',
                        rain_grid_container.memcdf_name)
            rain_grid_container.delete_memcdf()
