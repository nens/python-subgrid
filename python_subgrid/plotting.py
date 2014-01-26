import numpy as np
import matplotlib.colors
import matplotlib.cm


def make_quad_grid(subgrid):
    """
    Create a quad grid based on the grid information
    It is a masked array with fill value of -1.
    Append a transparent color at the end of a color vector.

    >>> quad_grid = make_quad_grid(subgrid)
    >>> colors = matplotlib.cm.Set2(waterlevel)
    >>> colors = np.r_[colors, np.array([0,0,0,0])[np.newaxis,:]]
    >>> plt.imshow(colors[quad_grid.filled()])
    """
    # Create lookup index
    grid = {}
    for var in {'nodn', 'nodm', 'nodk', 'dxp', 'dx', 'nmax', 'mmax'}:
        grid[var] = subgrid.get_nd(var)
    m = (grid['nodm']-1)*grid['dx'][grid['nodk']-1]/grid['dxp']
    n = (grid['nodn']-1)*grid['dx'][grid['nodk']-1]/grid['dxp']
    size = np.round(grid['dx'][grid['nodk']-1]/grid['dxp']).astype('int32')
    # Compute the maximum size which could contain quad_cells
    size_n = int(((grid['nmax']*grid['dx'])/grid['dxp'])[0])
    quad_grid_shape = (size_n, size_n)
    # Grid containing the integers for value lookup
    quad_grid = np.ma.empty(quad_grid_shape, dtype='int32')
    quad_grid.mask = True

    quad_grid.fill_value = -1
    for i, (m_i, n_i, size_i) in enumerate(zip(m,n,size)):
        quad_grid[n_i:(n_i+ size_i), m_i:(m_i+size_i)] = i
    return quad_grid


def colors(var, cmap='Blues', vmin=None, vmax=None):
    """return colors for variable var, with an appended transparent pixel"""
    if vmin is None:
        vmin = var.min()
    if vmax is None:
        vmax = var.max()
    # Create a normalisation function
    N = matplotlib.colors.Normalize(vmin, vmax)
    # and lookup the colormap
    C = matplotlib.cm.cmap_d[cmap]
    # Apply both
    colors = C(N(var))
    # append a transparent
    colors = np.r_[colors, np.array([0,0,0,0])[np.newaxis,:]]
    return colors



