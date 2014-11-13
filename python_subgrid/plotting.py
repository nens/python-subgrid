import logging
import json

from shapely.geometry import shape
import numpy as np
import skimage.draw

logging.basicConfig()
logging.root.setLevel(logging.DEBUG)
# ^^^ What is this doing at the top level? Everything that imports this gets
# that setting. TODO


def make_quad_grid(subgrid):
    """
    Create a quad grid based on the grid information
    It is a masked array with fill value of -1.
    Append a transparent color at the end of a color vector.
    """
    # Create lookup index
    grid = {}
    for var in {'nodn', 'nodm', 'nodk', 'dxp', 'dx', 'nmax',
                'mmax', 'imaxk', 'jmaxk', 'imax', 'jmax',
                'nod_type'}:
        grid[var] = subgrid.get_nd(var)

    grid['nodm'] = grid['nodm'][grid['nod_type'][1:] == 1]
    grid['nodn'] = grid['nodn'][grid['nod_type'][1:] == 1]
    grid['nodk'] = grid['nodk'][grid['nod_type'][1:] == 1]

    m = (grid['nodm']-1)*grid['imaxk'][grid['nodk']-1]
    n = (grid['nodn']-1)*grid['jmaxk'][grid['nodk']-1]
    size = grid['imaxk'][grid['nodk']-1]

    quad_grid_shape = (grid['jmax'], grid['imax'])
    quad_grid = np.ma.empty(quad_grid_shape, dtype='int32')
    quad_grid.mask = True
    quad_grid.fill_value = -1
    for i, (m_i, n_i, size_i) in enumerate(zip(m, n, size)):
        quad_grid[n_i:(n_i + size_i), m_i:(m_i+size_i)] = i
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
    colors = np.r_[colors, np.array([0, 0, 0, 0])[np.newaxis, :]]
    return colors


def draw_shape_on_raster(geojson, raster, value, extent=None):
    """
    draw the polygon geojson on the raster with value=value, inline
    """
    logging.debug(
        "drawing in %s using value %s and geometry %s within extent %s",
        raster, value, geojson, extent)
    geom = shape(json.loads(geojson))
    # and back to numpy vectors
    if geom.type == 'Polygon':
        coords = np.array(geom.exterior.coords)
        x, y = coords.T
        if extent is not None:
            x0, y0, x1, y1 = extent
            # rescale to pixel coordinates, assuming unrotated grid
            x = raster.shape[1] * (x - min(x0, x1)) / abs(x1 - x0)
            y = raster.shape[0] * (y - min(y0, y1)) / abs(y1 - y0)
        rr, cc = skimage.draw.polygon(x=x, y=y, shape=raster.shape)
        logging.debug("drawing in %s, %s", rr, cc)
    else:
        raise ValueError("Can only draw polygon exteriors")
    raster[rr, cc] = value
    return rr, cc
