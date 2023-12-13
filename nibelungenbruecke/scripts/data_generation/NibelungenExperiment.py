from collections.abc import Callable

import dolfinx as df
import numpy as np
import pint
import ufl
from mpi4py import MPI
from petsc4py.PETSc import ScalarType

from fenicsxconcrete.boundary_conditions.bcs import BoundaryConditions
from fenicsxconcrete.boundary_conditions.boundary import line_at, point_at
from fenicsxconcrete.experimental_setup.base_experiment import Experiment
from fenicsxconcrete.util import Parameters, ureg


class NibeluengenExperiment(Experiment):
    def __init__(self, model_path, parameters: dict[str, pint.Quantity]) -> None:
    
        self.model_path = model_path
        
        default_p = Parameters()
        default_p.update(parameters)
        super().__init__(default_p)
        
        
    def setup(self):
        try:
            self.mesh, cell_tags, facet_tags = df.io.gmshio.read_from_msh(self.model_path, MPI.COMM_WORLD, 0)
            
        except Exception as e:
            raise Exception(f"An error occurred during mesh setup: {e}")

    @staticmethod
    def default_parameters() -> dict[str, pint.Quantity]:
        setup_parameters = {}
        # setup_parameters["load"] = 10000 * ureg("N/m^2")
        setup_parameters["length"] = 1 * ureg("m")
        setup_parameters["dim"] = 3 * ureg("")

        return setup_parameters

    
    def create_displacement_boundary(self, V) -> list:
        """defines displacement boundary as fixed at bottom

        Args:
            V: function space

        Returns:
            list of dirichlet boundary conditions

        """

        bc_generator = BoundaryConditions(self.mesh, V)

        
        if self.p["dim"] == 3:
            # fix line in the left
            bc_generator.add_dirichlet_bc(
                np.array([0.0, 0.0, 0.0], dtype=ScalarType),
                boundary=self.boundary_left(),
                method="geometrical",
            )
            # line with dof in x direction on the right
            bc_generator.add_dirichlet_bc(np.float64(0.0), self.boundary_right(), 1, "geometrical", 0)
            bc_generator.add_dirichlet_bc(np.float64(0.0), self.boundary_right(), 2, "geometrical", 0)

        return bc_generator.bcs 
    
    def boundary_left(self) -> Callable:
        """specifies boundary at bottom

        Returns:
            fct defining boundary

        """

        if self.p["dim"] == 3:
            return line_at([0, 0], ["x", "z"])

    def boundary_right(self) -> Callable:
        """specifies boundary at bottom

        Returns:
            fct defining boundary

        """

        if self.p["dim"] == 3:
            return line_at([self.p["length"], 0], ["x", "z"])
        

    def create_body_force(self, v: ufl.argument.Argument) -> ufl.form.Form:
        """defines body force

        Args:
            v: test function

        Returns:
            form for body force

        """

        force_vector = np.zeros(self.p["dim"])
        force_vector[-1] = -self.p["rho"] * self.p["g"]  # works for 2D and 3D

        f = df.fem.Constant(self.mesh, ScalarType(force_vector))
        L = ufl.dot(f, v) * ufl.dx

        return L