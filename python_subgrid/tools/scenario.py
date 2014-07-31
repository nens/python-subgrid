"""
Read scenario files

*.json
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

# class AreaWideRainGrids(object):
#     def __init__(self):
#         self._events = []

#     def add(self, sim_time_start, rain_definition, sim_time_end=None):
#         self._events.append({
#             'sim_time_start': sim_time_start,
#             'sim_time_end': sim_time_end,
#             'rain_definition': rain_definition
#             })

#     def events(self, sim_time=None):
#         """
#         return event(s) for given sim_time, or return all events
#         """
#         if sim_time is not None:
#             result = []
#             for e in self._events:
#                 if (e['sim_time_start'] <= sim_time and 
#                     (e['sim_time_end'] is None or 
#                      e['sim_time_end'] > sim_time)):
#                 result.append(e)
#             return result
#         else:
#             return self._events

#     def from_file(cls, filename):
#         grid = cls()
#         # TODO: try to read file
#         return grid


class Event(object):
    expected_fields = set()

    def __init__(self):
        self._events = []

    def events(self, sim_time=None):
        """
        return event(s) for given sim_time, or return all events
        """
        if sim_time is not None:
            result = []
            for e in self._events:
                if (e['sim_time_start'] <= sim_time and 
                    (e['sim_time_end'] is None or 
                     e['sim_time_end'] > sim_time)):

                    result.append(e)
            return result
        else:
            return self._events

    def from_file(self, filename):
        with open(filename, 'r') as json_data:
            data = json.load(json_data)
            for event in data:
                self.add(**event)

    def add(self, **kwargs):
        if self.expected_fields:
            # every key in kwargs must be present in expected fields
            for k in kwargs.keys():
                assert(k in self.expected_fields)
        self._events.append(kwargs)


class RadarGrids(Event):
    expected_fields = set([
        'sim_time_start',  # time start in seconds
        'sim_time_end',  # can be None
        'radar_dt',  # radar datetime at sim_time_start
        'sync',   # not used
        'multiplier',  # not used
        'type',  # not used
        ])


class Scenario(object):
    """
    Holder for all scenario events
    """
    area_wide_rain_grids_filename = 'area_wide_rain_grids.json'
    radar_grids_filename = 'radar_grids.json'

    def __init__(self, path=None):
        self.radar_grids = RadarGrids()
        if path is not None:
            # self.area_wide_rain_grids = AreaWideRainGrids.from_file(
            #     os.path.join(path, 'area_wide_rain_grids.json'))

            fn = os.path.join(path, self.radar_grids_filename)
            if os.path.exists(fn):
                logger.info('Reading %s...' % fn)
                self.radar_grids.from_file(fn)
        
