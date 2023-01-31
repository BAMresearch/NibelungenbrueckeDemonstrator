import numpy as np
from dolfinx import mesh, fem

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