import numpy as np
from dolfinx import mesh, fem
from collections.abc import Callable

from petsc4py.PETSc import ScalarType

def clamped_boundary(domain, V, parameters):

    fdim = domain.topology.dim - 1
    boundary_facets = mesh.locate_entities_boundary(domain, fdim, boundary_side(parameters["side_coord"],parameters["coord"]))

    u_D = np.array([0,0,0], dtype=ScalarType)
    bc = fem.dirichletbc(u_D, fem.locate_dofs_topological(V, fdim, boundary_facets), V)
    return bc

def pinned_boundary(domain, V, parameters):

    fdim = domain.topology.dim - 1
    boundary_facets = mesh.locate_entities_boundary(domain, fdim, boundary_side(parameters["side_coord"],parameters["coord"]))
    facet_dofs = fem.locate_dofs_topological(V, fdim, boundary_facets)
    if 0 in parameters["pinned_coords"]:
        dofs_x = V.sub(0).dofmap.list.array[facet_dofs]
    else:
        dofs_x = None
    if 1 in parameters["pinned_coords"]:
        dofs_y = V.sub(1).dofmap.list.array[facet_dofs]
    else:
        dofs_y = None
    if 2 in parameters["pinned_coords"]:
        dofs_z = V.sub(2).dofmap.list.array[facet_dofs]
    else:
        dofs_z = None
    bc_dofs = np.hstack([dofs_x, dofs_y, dofs_z])
    bc_dofs = bc_dofs[bc_dofs != np.array(None)]
    bc_dofs = bc_dofs.astype(np.int32)
    u_D = fem.Function(V)
    with u_D.vector.localForm() as u_local:
        u_local.set(0.0)
    bc = fem.dirichletbc(u_D, bc_dofs)
    return bc

def clamped_edge(domain, V, parameters):

    fdim = domain.topology.dim - 2
    boundary_facets = mesh.locate_entities_boundary(domain, fdim, boundary_edge(parameters["side_coord_1"],parameters["coord_1"],parameters["side_coord_2"],parameters["coord_2"]))

    u_D = np.array([0,0,0], dtype=ScalarType)
    bc = fem.dirichletbc(u_D, fem.locate_dofs_topological(V, fdim, boundary_facets), V)
    return bc

def boundary_side(side_coord, coord):
    return lambda x: np.isclose(x[coord], side_coord)

def boundary_edge(side_coord_1, coord_1, side_coord_2, coord_2):
    return lambda x: np.logical_and(np.isclose(x[coord_1], side_coord_1), np.isclose(x[coord_2], side_coord_2))

def boundary_full(x):
    return x

def boundary_empty(x):
    return None

def point_at(coord) -> Callable:
    """Defines a point. Copied from FEniCSXConcrete.

    Args:
        coord: points coordinates

    Returns:
        function defining the boundary
    """
    p = to_floats(coord)

    def boundary(x):
        return np.logical_and(
            np.logical_and(np.isclose(x[0], p[0]), np.isclose(x[1], p[1])),
            np.isclose(x[2], p[2]),
        )

    return boundary

def to_floats(x) -> list[float]:
    """Converts `x` to a 3d coordinate. Copied from FEniCSXConcrete.

    Args:
        x: point coordinates at least 1D

    Returns:
        point described as list with x,y,z value
    """

    floats = []
    try:
        for v in x:
            floats.append(float(v))
        while len(floats) < 3:
            floats.append(0.0)
    except TypeError:
        floats = [float(x), 0.0, 0.0]

    return floats
