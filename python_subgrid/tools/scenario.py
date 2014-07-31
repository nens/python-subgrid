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

    def from_file(cls, filename):
        grid = cls()
        with open(filename, 'r') as json_data:
            data = json.load(json_data)
            logger.info(data)
        return grid

    def add(self, *args, **kwargs):
        # self._events.append({
        #     })
        logger.info(args)
        logger.info(kwargs)


class RadarGrids(Event):
    # def add(self, sim_time_start, radar_dt, sim_time_end=None):
    #     self._events.append({
    #         'sim_time_start': sim_time_start,
    #         'sim_time_end': sim_time_end,
    #         'radar_dt': radar_dt  # datetime of radar at sim_time_start
    #         })
    pass


class Scenario(object):
    """
    Holder for all scenario events
    """
    def __init__(self, path=None):
        if path is not None:
            # self.area_wide_rain_grids = AreaWideRainGrids.from_file(
            #     os.path.join(path, 'area_wide_rain_grids.json'))

            self.radar_grids = RadarGrids.from_file(
                os.path.join(path, 'radar_grids.json'))
        else:
            self.radar_grids = RadarGrids()