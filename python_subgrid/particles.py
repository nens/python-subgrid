"""
Particle system.

This module can be used to compute particle updates.
It supports the subgrid netCDF as input for the grid.
"""

# py3 compatible
from __future__ import (
    division,
    absolute_import,
    print_function,
    unicode_literals
)

import logging

import numpy as np
import pandas
import scipy.interpolate

logger = logging.getLogger(__name__)

import rtree

# tvtk is part of mayavi
from tvtk.api import tvtk

# TODO: cleanup delta_t, work with timedelta/datetime


class ParticleSystem(object):
    """A VTK based particle system"""
    def __init__(self, dataset, delta_t=900):
        """Initalize the particle system with a netCDF dataset"""
        # store a reference to the dataset
        self.dataset = dataset
        # By default do an update for 15minutes
        self.delta_t = delta_t
        # id administration of particles
        self.source_ids = np.array([], dtype='int64')
        self.current_id = 0
        # current timestep
        self.current_i = 0
        self.grid = self.make_grid()
        self.particles = self.make_particles()
        self.tracer = self.make_tracer()

    def make_particles(self):
        """just an empty polydata, with an empty set of indices"""
        particles = tvtk.PolyData()
        return particles

    def make_tracer(self):
        """create a data object to store particles"""
        grid = self.grid
        # Connect the grid
        cell2pointgrid = tvtk.CellDataToPointData()
        cell2pointgrid.input = grid
        cell2pointgrid.update()

        # Create a stream tracer
        tracer = tvtk.StreamTracer()
        # Set the points in the streamer
        tracer.source = self.particles
        # Set the corner velocities
        tracer.input = cell2pointgrid.output

        maximum_propagation = 5000 # max propagation
        maximum_number_of_steps = 200 # max number of steps
        tracer.maximum_propagation = maximum_propagation # 1km max propagation
        tracer.integration_step_unit = 1
        tracer.minimum_integration_step = maximum_propagation/maximum_number_of_steps
        tracer.maximum_integration_step = 10*(maximum_propagation/maximum_number_of_steps)
        tracer.maximum_number_of_steps = maximum_number_of_steps
        tracer.maximum_error = 0.1
        tracer.integrator_type = 'runge_kutta45'
        return tracer

    def make_grid(self):
        """return an unstructured grid, based on contours (x_contour, y_contour)
        with possible scalar and vector values"""

        # Get the contours
        x_contour = self.dataset.variables['FlowElemContour_x']
        y_contour = self.dataset.variables['FlowElemContour_y']

        ncells = x_contour.shape[0]
        # We're using an unstructured grid
        grid = tvtk.UnstructuredGrid()
        ncells = x_contour.shape[0]
        X = x_contour[:]
        Y = y_contour[:]
        Z = np.zeros_like(X)
        pts = np.c_[X.ravel(), Y.ravel(), Z.ravel() ]

        # quads all the way down
        cell_array = tvtk.CellArray()
        cell_types = np.array([tvtk.Quad().cell_type for i in range(ncells)])
        # generate a vector that consists of [number of nodes node# node# node #, etc]
        cell_idx = np.array([
            [4] + [i*4 + j for j in range(4) ]
            for i in range(ncells)
        ]).ravel()
        cell_offsets = np.array([i*5 for i in range(ncells)])
        cell_array.set_cells(ncells, cell_idx)

        # fill in the properties
        grid.points = pts
        grid.set_cells(cell_types, cell_offsets, cell_array)
        grid.build_links()
        return grid

    def update_particles(self, pts):
        """set the particle points and ids"""
        if self.particles.points is None:
            self.particles.points = pts
        else:
            self.particles.points.from_array(pts)
        ids = np.arange(self.current_id, self.current_id + pts.shape[0])
        # update the current id
        self.current_id += pts.shape[0]
        self.source_ids = ids
        self.particles.modified()


    def reseed(self, pts):
        """update the streamtracer with points from pts"""
        extra_ids = np.arange(self.current_id, self.current_id+pts.shape[0])
        self.current_id += pts.shape[0]

        # get current list of particles
        df = self.get_particles()
        # lookup position at t_stop
        t_next = self.dataset.variables['time'][self.current_i + 1]
        current_df = df[df['t'] == t_next]
        logger.info("got %s particles at t_stop", (len(current_df), ))
        current_df = current_df[np.in1d(current_df['reason'], (3,4,5))]
        logger.info("got %s particles still alive", (len(current_df), ))

        current_pts = np.array(current_df[['x', 'y', 'z']], dtype='float64')
        current_ids = np.array(current_df['particle'], dtype="int64")
        logger.info("%s particles used from previous run (%s)" % (current_pts.shape, current_pts.dtype))


        # add the extra points to the points that were alive
        new_pts = np.r_[current_pts, pts]
        new_ids = np.array(list(current_ids) + list(extra_ids))

        # set the points to the tracer
        logger.info("Setting particles to %s points %s", new_pts.shape, new_pts.dtype)
        if self.particles.points is None:
            self.particles.points = new_pts
        else:
            self.particles.points.from_array(new_pts)
        # update administration
        self.source_ids = new_ids

        self.particles.modified()
    def update_grid(self, i=0):
        """set the scalar and vector values to timestep i"""
        grid = self.grid
        dataset = self.dataset
        s1 = dataset.variables['s1'][i]
        grid.cell_data.scalars = s1
        grid.cell_data.scalars.name = 's1'
        ucx = dataset.variables['ucx'][i]
        ucy = dataset.variables['ucy'][i]
        vectors = np.c_[ucx, ucy, np.zeros_like(ucx)]
        grid.cell_data.vectors = vectors
        grid.cell_data.vectors.name = 'vector'
        self.current_i = i
        grid.modified()

    def get_points(self):
        """convert a streamtracer to a point dataframe"""
        tracer = self.tracer
        pd = tracer.output.point_data
        data = {}
        for i in range(pd.number_of_arrays):
            name = pd.get_array_name(i)
            arr = pd.get_array(i).to_array()
            if len(arr.shape)>1:
                for j in range(arr.shape[1]):
                    data['%s_%d' % (name, j)  ] = arr[:,j]
            else:
                data[name] = arr
        df = pandas.DataFrame(data)
        df['point_idx'] = df.index
        return df


    def get_lines(self):
        """get the streamlines of the tracer"""
        line_ids = self.get_ids()

        start = 0
        tracer = self.tracer
        if tracer.output.lines.number_of_cells == 0:
            df = pandas.DataFrame(columns=['p', 'line', 'point_idx', 'reason', 'line_idx', 'x', 'y', 'z', 'n'])
            return df
        lines = tracer.output.lines.data.to_array()
        points = tracer.output.points.to_array()
        reason = tracer.output.cell_data.get_array(0).to_array()
        rows = []
        for i in range(tracer.output.lines.number_of_cells):
            """loop over al lines"""
            n = lines[start]
            idx = lines[(start+1):(start+n+1)]
            line = points[idx]
            assert len(idx) == line.shape[0], "%s : %s" % (len(idx), line.shape[0])
            for j, (idx_i, x_i, y_i, z_i) in enumerate(zip(idx, line[:,0], line[:,1], line[:,2])):
                rows.append(dict(p=line_ids[i], line=i, point_idx=idx_i, reason=reason[i], line_idx=j, x=x_i, y=y_i, z=z_i, n=n))
            start += (n + 1)
        df = pandas.DataFrame(data=rows)
        return df


    def df2particles(self, df_points, df_lines):
        """combine the points and lines to generate position as function of time"""
        times = self.dataset.variables['time'][:]
        # Lookup the  relative stop time
        t_stop = times[self.current_i + 1] - times[self.current_i]
        columns = ['line', 'line_idx', 'n', 'point_idx', 'x', 'y', 'z', 'IntegrationTime', 'reason', 'p']
        if df_points.empty or df_lines.empty:
            df = pandas.DataFrame(columns=['t', 'x', 'y', 'z', 'particle', 'reason'])
            return df
        df = df_lines.merge(df_points, right_on='point_idx', left_on='point_idx')
        df = df[columns]
        rows = []
        for particle_i, group in df.groupby('p'):
            if particle_i<0:
                continue
            reason = group['reason'].irow(0)
            arr  = np.array(group[['x', 'y', 'z']])
            x = np.array(group['IntegrationTime'])

            # extrapolate
            if x[-1] < t_stop:
                x = np.append(x, [t_stop])
                arr = np.append(arr, arr[-1][np.newaxis,:], axis=0)
            # create an interpolation function
            f = scipy.interpolate.interp1d(x, arr, axis=0, bounds_error=True)
            t = np.linspace(0, t_stop, num=16)
            # apply interpolation function
            x, y, z = np.atleast_2d(f(t).T)
            # Generate rows for the dataframe
            for t_i, x_i, y_i, z_i in zip(t, x, y, z):
                # TODO hack in time properly
                row = dict(t=t_i + times[self.current_i], x=x_i, y=y_i, z=z_i, particle=particle_i, reason=reason)
                rows.append(row)
        df2 = pandas.DataFrame(rows)
        return df2

    def get_particles(self):
        """extract the particles from a streamtracer"""
        df_points = self.get_points()
        df_lines = self.get_lines()
        df = self.df2particles(df_points, df_lines)
        return df



    def get_ids(self):
        """indices of particles in the line list"""
        tracer = self.tracer

        if tracer.output.lines.number_of_cells == 0:
            # no lines, no indices
            logger.info('No output lines found')
            return np.array([], dtype='int64')

        # create an rtree for fast lookup
        # ids should be as long as number of points in particles
        assert len(self.source_ids) == self.particles.number_of_points, "%s should be %s" % (len(self.source_ids),  self.particles.number_of_points)

        # ids of the source points
        tree = rtree.Rtree()
        for i, (x_i, y_i, _) in zip(self.source_ids, self.particles.points.to_array()):
            tree.add(i, (x_i, y_i))

        lines = tracer.output.lines.data.to_array()
        points = tracer.output.points.to_array()
        rows = []
        start = 0
        for i in range(tracer.output.lines.number_of_cells):
            """loop over al lines"""
            n = lines[start]
            idx = lines[start+1]
            coord = points[idx]
            start += (n + 1)
            rows.append(coord)
        # assert start == st.output.number_of_connectivity_entries, "%s : %s" % (start, st.output.number_of_connectivity_entries)
        lines = np.array(rows)

        # lookup all locations of the particles in the ids
        idxs = []
        for line_i in lines:
            idx = tree.nearest(tuple(line_i[:2])).next()
            idxs.append(idx)
        return np.array(idxs)

    def get_alive(self, t=None):
        """create an index that determines if particles are still alive at time t"""
        if t is None:
            t = self.delta_t
        if self.tracer.output.cell_data.number_of_arrays == 0:
            return np.array([], dtype='bool')

        arr = self.tracer.output.cell_data.get_array(0).to_array()
        alive = np.in1d(arr, np.array([3,4,5]))
        return alive
