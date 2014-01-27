
Fortran functions and variables
===============================


Wrapped Fortran subgrid library functions
-----------------------------------------


.. function:: update(PyCPointerType)

    Returns PyCSimpleType


.. function:: startup()

    Returns PyCSimpleType


.. function:: shutdown()

    Returns PyCSimpleType


.. function:: loadmodel(PyCSimpleType)

    Returns PyCSimpleType


.. function:: initmodel()

    Returns PyCSimpleType


.. function:: finalizemodel()

    Returns PyCSimpleType


.. function:: changebathy(PyCPointerType, PyCPointerType, PyCPointerType, PyCPointerType, PyCPointerType)

    Returns PyCSimpleType


.. function:: floodfilling(PyCPointerType, PyCPointerType, PyCPointerType, PyCPointerType)

    Returns PyCSimpleType


.. function:: discharge(PyCPointerType, PyCPointerType, PyCSimpleType, PyCPointerType, PyCPointerType)

    Returns PyCSimpleType


.. function:: discard_manhole(PyCPointerType, PyCPointerType)

    Returns PyCSimpleType


.. function:: discard_structure(PyCSimpleType)

    Returns PyCSimpleType


.. function:: dropinstantrain(PyCPointerType, PyCPointerType, PyCPointerType, PyCPointerType)

    Returns PyCSimpleType


.. function:: getwaterlevel(PyCPointerType, PyCPointerType, PyCPointerType)

    Returns PyCSimpleType


.. function:: subgrid_info()

    Returns NoneType


.. function:: subscribe_dataset(PyCSimpleType)

    Returns PyCSimpleType


.. function:: save_tables(PyCSimpleType)

    Returns NoneType


.. function:: save_grid(PyCSimpleType)

    Returns NoneType


Directly accessible Fortran variables
-------------------------------------

These variables can be called from the wrapper's ``get_nd`` function.


.. attribute:: FlowElemContour_x

    List of x points forming flow element


.. attribute:: FlowElemContour_y

    List of y points forming flow element


.. attribute:: FlowElem_xcc

    Cell center x coordinate (pressure point) for all quadtree cells (i.e. nodes).


.. attribute:: FlowElem_ycc

    Cell center y coordinate (pressure point) for all quadtree cells (i.e. nodes).


.. attribute:: FlowLink

    Flow links/lines between coarse grid cells: line(L,1) = nod1, line(L,2) = nod2


.. attribute:: FlowLink_xu

    Velocity x coordinate for 1d, 2d, including boundaries


.. attribute:: FlowLink_yu

    Velocity y coordinate for 1d, 2d, including boundaries


.. attribute:: LandUse

    percentage of a crop per node


.. attribute:: MaxInterception

    max thickness of interception layer on fine base grid


.. attribute:: ade

    advection


.. attribute:: adi

    advection


.. attribute:: cropType

    crop factors on fine grid


.. attribute:: culverts

    Culvert


.. attribute:: dps

    bathymetry pixel values on fine base grid


.. attribute:: ds1d

    gridsize in 1d channels


.. attribute:: dsnop

    Dummy missing value for bathymetry pixels, single precision.


.. attribute:: dt

    delta t


.. attribute:: dtmax

    maximum delta t


.. attribute:: dtmin

    minumum delta t


.. attribute:: dx

    gridsize for all coarse quadtree levels 1:kmax


.. attribute:: dxp

    pixel dimensions


.. attribute:: dyp

    pixel dimensions


.. attribute:: imax

    number of pixels in x directions


.. attribute:: imaxk

    number of pixels in a quad tree cell of refinement k (1:kmax)


.. attribute:: infiltrationRate

    infiltration rate values on fine base grid


.. attribute:: ip

    subgrid pixel numbers in coarse grid cells, see subroutine couplegrids(). E.g., ip(1:kmax,1:mmax(k),0:3).


.. attribute:: jmax

    number of pixels in y directions


.. attribute:: jmaxk

    number of pixels in a quad tree cell of refinement k (1:kmax)


.. attribute:: jp

    subgrid pixel numbers in coarse grid cells, see subroutine couplegrids(). E.g., ip(1:kmax,1:mmax(k),0:3).


.. attribute:: kf

    administration of wet or dry velocity points (wet=1, dry=0)


.. attribute:: ks

    administration of wet or dry quarter cells (wet=1, dry=0)


.. attribute:: lg

    Quadtree refinement level for each pixel (kmax=coarsest, 1=finest)


.. attribute:: lh

    Quadtree node number to which each pixel belongs.


.. attribute:: link_branchid

    Original link number


.. attribute:: link_chainage

    Distance along the branch


.. attribute:: link_idx

    Index in the u vector


.. attribute:: link_type

    Type of link


.. attribute:: lu1dmx

    number of u points per channel (for embedded: nr of 2D cell interfaces crossed by 1D channel)


.. attribute:: mbndry

    coordinates of East boundaries


.. attribute:: mmax

    quadtree grid administration


.. attribute:: nFlowElem1d

    total number of nodal points in 1d without boundary points


.. attribute:: nFlowElem1dBounds

    number of  1d boundary points


.. attribute:: nFlowElem2d

    number of 2d nodes


.. attribute:: nFlowElem2dBounds

    number of nodal points  2d boundary points


.. attribute:: nbndry

    coordinates of North boundaries


.. attribute:: nmax

    quadtree grid administration


.. attribute:: nod_type

    Type of node


.. attribute:: nodk

    inverse indirect adressing of coarse grid cells: nod = ls(k)$mn(m,n) --> k = nodk(nod)


.. attribute:: nodm

    inverse indirect adressing of coarse grid cells: nod = ls(k)$mn(m,n) --> m = nodm(nod)


.. attribute:: nodn

    inverse indirect adressing of coarse grid cells: nod = ls(k)$mn(m,n) --> n = nodn(nod)


.. attribute:: orifices

    Orifice


.. attribute:: pumps

    Pump


.. attribute:: q

    discharge on full grid on current timestep


.. attribute:: qh1

    discharge on half grid on current timestep


.. attribute:: qh2

    discharge on half grid on next timestep


.. attribute:: qrain

    rainfall


.. attribute:: rain

    rainfall


.. attribute:: rootLength

    root lengths on fine grid


.. attribute:: s0

    waterlevel at previous timestep


.. attribute:: s1

    waterlevel at current timestep


.. attribute:: s2

    waterlevel at next timestep


.. attribute:: sg

    ground water level measured from "ground level" upwards (time dependent)


.. attribute:: si

    thickness of interception layer per node


.. attribute:: si0

    thickness of interception layer per node at previous timestep


.. attribute:: soilType

    soil types on fine grid


.. attribute:: su

    volume surface in coarse grid cell on current


.. attribute:: su0

    volume surface in coarse grid cell in previous timestep


.. attribute:: t0

    time at previous timestep


.. attribute:: t1

    time at current timestep


.. attribute:: tend

    stop time of simulation


.. attribute:: tstart

    start time of simulation


.. attribute:: u0

    velocity at previous timestep


.. attribute:: u1

    velocity at current timestep


.. attribute:: u2

    velocity at next timestep


.. attribute:: vol0

    volume in coarse grid cell on previous timestep


.. attribute:: vol1

    volume in coarse grid cell on current timestep


.. attribute:: vol2

    volume in coarse grid cell on previous timestep + (incoming discharges - outgoing discharges) * dt


.. attribute:: weirs

    Weir


.. attribute:: wkt

    Projection information in Well Known Text fo4096


.. attribute:: x0p

    origin of pixel grid


.. attribute:: x1p

    origin of pixel grid


.. attribute:: y0p

    origin of pixel grid


.. attribute:: y1p

    origin of pixel grid

