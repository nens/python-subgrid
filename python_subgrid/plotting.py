import numpy as np
import logging

def make_quad_grid(subgrid):
    """
    Create a quad grid based on the grid information
    It is a masked array with fill value of -1.
    Append a transparent color at the end of a color vector.
    """
    # Create lookup index
    grid = {}
    for var in {'nodn', 'nodm', 'nodk', 'dxp', 'dx', 'nmax', 'mmax', 'imaxk', 'jmaxk', 'imax', 'jmax'}:
        grid[var] = subgrid.get_nd(var)

    m = (grid['nodm']-1)*grid['imaxk'][grid['nodk']-1]
    n = (grid['nodn']-1)*grid['jmaxk'][grid['nodk']-1]
    size = grid['imaxk'][grid['nodk']-1]


    quad_grid_shape = (grid['jmax'], grid['imax'])
    quad_grid = np.ma.empty(quad_grid_shape, dtype='int32')
    quad_grid.mask = True
    quad_grid.fill_value = -1
    for i, (m_i, n_i, size_i) in enumerate(zip(m,n,size)):
        quad_grid[n_i:(n_i+ size_i), m_i:(m_i+size_i)] = i
    return quad_grid


def colors(var, cmap='Blues', vmin=None, vmax=None, **args):
    """return colors for variable var, with an appended transparent pixel"""

    try:
        import matplotlib.colors
        import matplotlib.cm
    except ImportError:
        # just reraise
        logging.exception("Can't find matplotlib. Needed for colors function.")
        raise

    if vmin is None:
        vmin = var.min()
    if vmax is None:
        vmax = var.max()
    # Create a normalisation function
    N = matplotlib.colors.Normalize(vmin, vmax)
    # and lookup the colormap
    C = matplotlib.cm.cmap_d[cmap]
    # Apply both
    colors = C(N(var), **args)
    # append a transparent
    colors = np.r_[colors, np.array([0,0,0,0])[np.newaxis,:]]
    return colors



