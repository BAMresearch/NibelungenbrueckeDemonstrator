
from pathlib import Path

from mpi4py import MPI
from petsc4py.PETSc import ScalarType  # type: ignore

import numpy as np

import ufl
from dolfinx import fem, io, mesh, plot
from dolfinx.fem.petsc import LinearProblem


msh = mesh.create_rectangle(
    comm=MPI.COMM_WORLD,
    points=((0.0, 0.0), (2.0, 1.0)),
    n=(32, 16),
    cell_type=mesh.CellType.triangle,
)
V = fem.FunctionSpace(msh, ("Lagrange", 1))

facets = mesh.locate_entities_boundary(
    msh,
    dim=(msh.topology.dim - 1),
    marker=lambda x: np.isclose(x[0], 0.0) | np.isclose(x[0], 2.0),
)

dofs = fem.locate_dofs_topological(V=V, entity_dim=1, entities=facets)


bc = fem.dirichletbc(value=ScalarType(0), dofs=dofs, V=V)

dt = fem.Constant(msh, ScalarType(0.01))

t = 0.0
T_end = 1.0

# +
u = ufl.TrialFunction(V)
v = ufl.TestFunction(V)
u_n = fem.Function(V)

x = ufl.SpatialCoordinate(msh)
f = 10 * ufl.exp(-((x[0] - 0.5) ** 2 + (x[1] - 0.5) ** 2) / 0.02)
g = ufl.sin(5 * x[0])
a = (u * v / dt + ufl.inner(ufl.grad(u), ufl.grad(v))) * ufl.dx
L = (u_n * v / dt + f * v) * ufl.dx + g * v * ufl.ds
# -

problem = LinearProblem(
    a,
    L,
    bcs=[bc],
    #petsc_options_prefix="demo_poisson_",
    petsc_options={"ksp_type": "preonly", "pc_type": "lu", "ksp_error_if_not_converged": True},
)

u_n.interpolate(lambda x: np.zeros(x.shape[1]))

with io.XDMFFile(msh.comm, "heat.xdmf", "w") as file:
    file.write_mesh(msh)
    while t < T_end:
        t += float(dt.value)
        uh = problem.solve()
        file.write_function(uh, t)
        u_n.x.array[:] = uh.x.array

assert isinstance(uh, fem.Function)
# -

# The solution can be written to a {py:class}`XDMFFile
# <dolfinx.io.XDMFFile>` file visualization with [ParaView](https://www.paraview.org/)
# or [VisIt](https://visit-dav.github.io/visit-website/):

# +
out_folder = Path("out_poisson")
out_folder.mkdir(parents=True, exist_ok=True)
with io.XDMFFile(msh.comm, out_folder / "poisson.xdmf", "w") as file:
    file.write_mesh(msh)
    file.write_function(uh)
# -

# and displayed using [pyvista](https://docs.pyvista.org/).

# +
try:
    import pyvista

    cells, types, x = plot.create_vtk_mesh(V)
    grid = pyvista.UnstructuredGrid(cells, types, x)
    grid.point_data["u"] = uh.x.array.real
    grid.set_active_scalars("u")
    plotter = pyvista.Plotter()
    plotter.add_mesh(grid, show_edges=True)
    warped = grid.warp_by_scalar()
    plotter.add_mesh(warped)
    if pyvista.OFF_SCREEN:
        plotter.screenshot(out_folder / "uh_poisson.png")
    else:
        plotter.show()
except ModuleNotFoundError:
    print("'pyvista' is required to visualise the solution.")
    print("To install pyvista with pip: 'python3 -m pip install pyvista'.")
# -