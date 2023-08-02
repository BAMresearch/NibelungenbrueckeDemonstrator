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


def boundary_side(side_coord, coord):
    return lambda x: np.isclose(x[coord], side_coord)

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
