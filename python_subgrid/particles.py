"""
Particle module that seeds particles in an unstructured or quadtree grid.
"""

import logging

import numpy as np
import pandas
import scipy.interpolate
# enum34
import enum
# mayavi
from tvtk.api import tvtk, write_data
# for spatial matching
import rtree

# Use a logger named to the module
logger = logging.getLogger(__name__)


# Reason for termination
class Reason(enum.Enum):
    OUT_OF_DOMAIN = 1
    NOT_INITIALIZED = 2
    UNEXPECTED_VALUE = 3
    OUT_OF_TIME = 4
    OUT_OF_STEPS = 5
    STAGNATION = 6
    # this is extra for living partciles
    DEAD = 11


class ParticleSystem(object):
    """A VTK based particle system with custom particle behaviour"""
    def __init__(self, ds):

        # store a reference to the dataset
        self.ds = ds
        # id administration of particles
        # Needed because VTK does not store particle identification
        self.source_ids = np.array([], dtype='int64')
        # next id to be used for a particle
        self.current_id = 0
        # current timestep
        self.current_i = 0
        # computational grid
        self.grid = self.make_grid()
        # Current locations of the particles
        self.particles = self.make_particles()
        # Streamtracer for current timestep
        self.tracer = self.make_tracer()
        # Custom velocities and behaviour per partcil
        self.velocities = {}
        self.behaviour = {}

    def make_particles(self):
        """just an empty polydata, with an empty set of indices"""
        pd = tvtk.PolyData()
        return pd

    def make_tracer(self):
        """create a data object to store particles"""
        grid = self.grid
        # This drops unlinked polygons
        # Clean the polydata
        # If you do this for quadtrees you'll lose half of the particles
        # The better way would be to setup an AMR, but that only
        # works from >vtk6
        clean = tvtk.CleanPolyData()
        clean.input = grid
        # gives a topological sound grid
        clean.update()
        # We need to convert to point data for interpolation of velocities.
        # This assumes vectors are cell centered
        cell2pointgrid = tvtk.CellDataToPointData()
        cell2pointgrid.input = clean.output
        cell2pointgrid.update()

        # Create a stream tracer
        # We want to use the particle class that also can interpolate over time
        # But it is not working as expected so we'll use the streamtracer
        # This gives the same results if the velocity field is stationary
        # If the velocity field is not stationary you have to reduce
        # your timestep
        st = tvtk.StreamTracer()

        # We attach 2 data source
        # Set the points in the streamer
        st.source = self.particles
        # Set the corner velocities
        st.input = cell2pointgrid.output

        # You can compute up to 2km per timestep (8km/hr for )
        l = 2000  # max propagation
        n = 200  # max number of steps

        st.maximum_propagation = l
        # In m
        st.integration_step_unit = 1
        # Minimum 10m per step
        st.minimum_integration_step = (l/n)
        # Maximum 100m per step
        st.maximum_integration_step = 10*(l/n)
        # Maximum 200 steps
        st.maximum_number_of_steps = n
        # Maximum error 1cm
        st.maximum_error = 1e-2
        # We use a path integration. You could argue that you need a
        # particle tracking algorithm that matches the numerical grid
        # (in our case edge velocities
        # and integration over a cell instead of over a line)
        st.integrator_type = 'runge_kutta45'
        return st

    def make_grid(self):
        """return an unstructured grid, based on contours (xc, yc) with possible
        scalar and vector values"""

        # Get the contours
        xc = self.ds.variables['FlowElemContour_x']
        yc = self.ds.variables['FlowElemContour_y']

        ncells = xc.shape[0]
        # We're using an unstructured grid
        grid = tvtk.PolyData()
        ncells = xc.shape[0]
        X = xc[:]
        Y = yc[:]
        Z = np.zeros_like(X)
        pts = np.c_[X.ravel(), Y.ravel(), Z.ravel()]

        # quads all the way down
        # quads with different resolutions actually don't work so well
        cell_array = tvtk.CellArray()
        # For unstructured grids you need to count the number of edges per cell
        cell_idx = np.array([[4] + [i*4 + j for j in range(4)]
                             for i in range(ncells)]).ravel()
        cell_array.set_cells(ncells, cell_idx)

        # fill in the properties
        grid.points = pts
        grid.polys = cell_array
        return grid

    def update_particles(self, pts):
        """set the particle points and generate ids"""
        # If we don't have particles yet add them
        if self.particles.points is None:
            self.particles.points = pts
        else:
            # or set them
            self.particles.points.from_array(pts)
        # generate new id's
        ids = np.arange(self.current_id, self.current_id + pts.shape[0])
        # update the current id
        self.current_id += pts.shape[0]
        self.source_ids = ids
        self.particles.modified()

    def reseed(self, pts, velocity=None, behaviour=None):
        """
        update the streamtracer with points from pts
        velocity is a tuple of u,v
        behaviour is a function that returns a new txyz, given the txyz
        """

        extra_ids = np.arange(self.current_id, self.current_id+pts.shape[0])
        self.current_id += pts.shape[0]

        # get current list of particles
        df = self.get_particles()
        # lookup position at t_stop
        current_df = df[df['t'] == self.current_i * 900 + 900]
        logger.info("got %s particles at t_stop", (len(current_df), ))
        current_df = current_df[np.in1d(current_df['reason'], (3, 4, 5))]
        logger.info("got %s particles still alive", (len(current_df), ))

        current_pts = np.array(current_df[['x', 'y', 'z']], dtype='float64')
        current_ids = np.array(current_df['particle'], dtype="int64")
        logger.info("%s particles used from previous run (%s)",
                    current_pts.shape, current_pts.dtype)

        # add the extra points to the points that were alive
        new_pts = np.r_[current_pts, pts]
        new_ids = np.array(list(current_ids) + list(extra_ids))

        # set the points to the tracer
        logger.info("Setting particles to %s points %s",
                    new_pts.shape, new_pts.dtype)
        if self.particles.points is None:
            self.particles.points = new_pts
        else:
            self.particles.points.from_array(new_pts)
        # update administration
        self.source_ids = new_ids

        self.particles.modified()

        # keep track of the velocity per particle
        if velocity is not None:
            for id_i in extra_ids:
                self.velocities[id_i] = velocity
        if behaviour is not None:
            for id_i in extra_ids:
                self.behaviour[id_i] = behaviour

    def update_grid(self, i=0):
        grid = self.grid
        ds = self.ds
        s1 = ds.variables['s1'][i]
        grid.cell_data.scalars = s1
        grid.cell_data.scalars.name = 's1'
        ucx = ds.variables['ucx'][i]
        ucy = ds.variables['ucy'][i]
        vectors = np.c_[ucx, ucy, np.zeros_like(ucx)]
        grid.cell_data.vectors = vectors
        grid.cell_data.vectors.name = 'vector'
        self.current_i = i
        grid.modified()

    def save_grid(self):
        write_data(self.grid, 'grid.vtk')

    def get_points(self):
        """convert a streamtracer to a point dataframe"""
        st = self.tracer
        pd = st.output.point_data
        data = {}
        for i in range(pd.number_of_arrays):
            name = pd.get_array_name(i)
            arr = pd.get_array(i).to_array()
            if len(arr.shape) > 1:
                for j in range(arr.shape[1]):
                    data['%s_%d' % (name, j)] = arr[:, j]
            else:
                data[name] = arr
        df = pandas.DataFrame(data)
        df['point_idx'] = df.index
        return df

    def get_lines(self):
        """convert the streamlines to a data frame"""
        line_ids = self.get_ids()

        start = 0
        st = self.tracer
        if st.output.lines.number_of_cells == 0:
            df = pandas.DataFrame(columns=['p', 'line', 'point_idx', 'reason',
                                           'line_idx', 'x', 'y', 'z', 'n'])
            return df
        lines = st.output.lines.data.to_array()
        points = st.output.points.to_array()
        reason = st.output.cell_data.get_array(0).to_array()
        rows = []
        for i in range(st.output.lines.number_of_cells):
            """loop over al lines"""
            n = lines[start]
            idx = lines[(start+1):(start+n+1)]
            line = points[idx]
            assert len(idx) == line.shape[0], "%s : %s" % (
                len(idx), line.shape[0])
            for j, (idx_i, x_i, y_i, z_i) in enumerate(zip(
                    idx, line[:, 0], line[:, 1], line[:, 2])):
                rows.append(dict(p=line_ids[i], line=i, point_idx=idx_i,
                                 reason=reason[i], line_idx=j, x=x_i,
                                 y=y_i, z=z_i, n=n))
            start += (n + 1)
        df = pandas.DataFrame(data=rows)
        return df

    def df2particles(self, df_points, df_lines, t_stop):
        """merge points, lines and cut off at a stop time"""
        columns = ['line', 'line_idx', 'n', 'point_idx', 'x', 'y', 'z',
                   'IntegrationTime', 'reason', 'p']
        if df_points.empty or df_lines.empty:
            columns = ['t', 'x', 'y', 'z', 'particle', 'reason']
            df = pandas.DataFrame(columns=columns)
            return df
        # Combine the lines and points
        df = df_lines.merge(df_points,
                            right_on='point_idx',
                            left_on='point_idx')
        df = df[columns]
        rows = []
        # For each particle
        for particle_i, group in df.groupby('p'):
            # Not sure when this happens
            if particle_i < 0:
                continue
            # Get the reason at t=0
            reason = group['reason'].irow(0)
            # Lookup the coordinates
            arr = np.array(group[['x', 'y', 'z']])
            x = np.array(group['IntegrationTime'])

            # extrapolate if we don't reach t_stop
            if x[-1] < t_stop:
                x = np.append(x, [t_stop])
                arr = np.append(arr, arr[-1][np.newaxis, :], axis=0)
            # interpolate in the current timestep (for reduced output size)
            f = scipy.interpolate.interp1d(x, arr, axis=0, bounds_error=True)
            # we only need 16 points
            t = np.linspace(0, t_stop, num=16)
            # return the recomputed times
            # interpolated over position as function of integrationtime
            x, y, z = np.atleast_2d(f(t).T)

            # add velocity if given
            velocity = self.velocities.get(particle_i, (0, 0))
            x += t * velocity[0]
            y += t * velocity[1]

            # add behaviour if given
            txyz = np.c_[t, x, y, z]
            # change the particle using a behaviour function
            # TODO: add reason and deaths
            behaviour = self.behaviour.get(particle_i, lambda txyz: txyz)
            txyz = behaviour(txyz)

            # create a new data frame
            for t_i, x_i, y_i, z_i in txyz:
                # TODO hack in time properly
                # 900 -> always 15min, also check resolution and tracer
                # settings
                row = dict(t=t_i + self.current_i * 900, x=x_i, y=y_i, z=z_i,
                           particle=particle_i, reason=reason)
                rows.append(row)
        df2 = pandas.DataFrame(rows)
        return df2

    def get_particles(self, t_stop=900):
        """extract the particles from a streamtracer"""
        df_points = self.get_points()
        df_lines = self.get_lines()
        # Combine, interpolate, behave and return
        df = self.df2particles(df_points, df_lines, t_stop=t_stop)
        return df

    def get_ids(self):
        """indices of particles in the line list"""
        st = self.tracer

        if self.tracer.output.lines.number_of_cells == 0:
            # no lines, no indices
            logger.info('No output lines found')
            return np.array([], dtype='int64')

        # create an rtree for fast lookup
        # ids should be as long as number of points in particles
        msg = "%s should be %s" % (len(self.source_ids),
                                   self.particles.number_of_points)
        assert len(self.source_ids) == self.particles.number_of_points, msg

        # ids of the source points
        tree = rtree.Rtree()
        for i, (x_i, y_i, _) in zip(self.source_ids,
                                    self.particles.points.to_array()):
            tree.add(i, (x_i, y_i))

        # lookup lines and points
        lines = st.output.lines.data.to_array()
        points = st.output.points.to_array()
        rows = []
        start = 0
        for i in range(st.output.lines.number_of_cells):
            # loop over al lines
            n = lines[start]
            idx = lines[start+1]
            coord = points[idx]
            start += (n + 1)
            rows.append(coord)
        lines = np.array(rows)

        # lookup all locations of the particles in the ids
        idxs = []
        for line_i in lines:
            # find the particle that is closest, max of 10 locations
            for idx in tree.nearest(tuple(line_i[:2]), num_results=10):
                if idx in idxs:
                    # if we already found this, keep looking
                    continue
                else:
                    # found one
                    break
            else:
                # oops, we can't find a single particle here that
                # we haven't used already
                idx = iter(tree.nearest(tuple(line_i[:2]))).next()
                msg = 'Could not find particle for %s, reusing %s'
                logging.warn(msg, line_i, idx)
            # add it to the list
            idxs.append(idx)
        return np.array(idxs)

    def get_alive(self, t=900):
        """create an index that determines if particles are still alive at
        time t
        """
        if self.tracer.output.cell_data.number_of_arrays == 0:
            return np.array([], dtype='bool')
        arr = self.tracer.output.cell_data.get_array(0).to_array()
        alive = np.in1d(arr, np.array([3, 4, 5]))
        return alive
