import dolfinx as df
import numpy as np
import pint
import ufl
from petsc4py.PETSc import ScalarType
from dolfinx.fem.forms import form as _create_form

from fenicsxconcrete.experimental_setup import CantileverBeam, Experiment
from fenicsxconcrete.finite_element_problem.base_material import MaterialProblem, QuadratureFields, SolutionFields
from fenicsxconcrete.util import Parameters, ureg


class LinearElasticityNibelungenbrueckeDemonstrator(MaterialProblem):
    """Material definition for linear elasticity"""

    def __init__(
        self,
        callbacks: None,
        experiment: Experiment,
        parameters: dict[str, pint.Quantity],
        pv_name: str = "pv_output_full",
        pv_path: str = None,
    ) -> None:
        """defines default parameters, for the rest, see base class"""

        # # adding default material parameter, will be overridden by outside input
        # default_p = Parameters()
        # default_p["stress_state"] = "plane_strain" * ureg("")  # default stress state in 2D, optional "plane_stress"
        #
        # # updating parameters, overriding defaults
        # default_p.update(parameters)
#%%
        self.callbacks = callbacks
        super().__init__(experiment, parameters, pv_name, pv_path)
        
#%%
    def setup(self) -> None:
        # compute different set of elastic moduli

        self.lambda_ = df.fem.Constant(
            self.mesh,
            self.p["E"] * self.p["nu"] / ((1 + self.p["nu"]) * (1 - 2 * self.p["nu"])),
        )
        self.mu = df.fem.Constant(self.mesh, self.p["E"] / (2 * (1 + self.p["nu"])))
        if self.p["dim"] == 2 and self.p["stress_state"].lower() == "plane_stress":
            self.lambda_ = df.fem.Constant(
                self.mesh, 2.0 * self.mu.value * self.lambda_.value / (self.lambda_.value + 2 * self.mu.value)
            )

        # define function space ets.
        self.V = df.fem.VectorFunctionSpace(self.mesh, ("Lagrange", self.p["degree"]))  # 2 for quadratic elements
        self.V_scalar = df.fem.FunctionSpace(self.mesh, ("Lagrange", self.p["degree"]))

        # Define variational problem
        self.u_trial = ufl.TrialFunction(self.V)
        self.v = ufl.TestFunction(self.V)

        self.fields = SolutionFields(displacement=df.fem.Function(self.V, name="displacement"))
        self.q_fields = QuadratureFields(
            measure=ufl.dx,
            plot_space_type=("DG", self.p["degree"] - 1),
            stress=self.sigma(self.fields.displacement),
            strain=self.epsilon(self.fields.displacement),
        )

        self.a = ufl.inner(self.sigma(self.u_trial), self.epsilon(self.v)) * ufl.dx

    def dynamic_solve(self, form_compiler_options={}, jit_options={}):
        """
       Solves the dynamically moving load system using the specified form compiler options and JIT options.
       
       In each iteration, the vehicle (moving load) moves forward by a predefined step size, and the system is solved 
        for that increment. The following steps are performed at each increment:
        - External forces and body forces are applied.
        - Boundary conditions are enforced.
        - The system is solved.
        - Callbacks are triggered for data extraction and post-processing.
        
        The solution continues until the convergence condition is met.
        
        """
        i = 0   # Iteration counter for the load increments
               
        # Initialize the L field (e.g., zero displacement field)
        zero_field = df.fem.Constant(self.mesh, ScalarType(np.zeros(self.p["dim"])))
        
        # boundary conditions only after function space
        bcs = self.experiment.create_displacement_boundary(self.V)

        # Begin the iteration process to solve the system at each load increment (vehicle step)
        while not self.experiment.converged:
                
            # Execute callbacks after the first iteration
            #if i == 1:
                #self.callbacks[0]() # Execute the first callback
            
            # Apply external moving load (boundary forces) at each step of the vehicle's movement
            moving_load = self.experiment.boundary_force_field()     # Moving load due to vehicle step
            ds_load = self.experiment.create_force_boundary(self.v)
            external_force = ufl.dot(moving_load, self.v) * ds_load(1)
            
            # Initialize the weak form (L) for the first iteration
            self.L = ufl.dot(zero_field, self.v) * ufl.dx
            if external_force:
                self.L = self.L + external_force
            
            # Apply body forces to the system
            body_force = self.experiment.create_body_force(self.v)
            if body_force:
                self.L = self.L + body_force
                
            # Set up the linear problem on the first iteration
            if i == 0:
                self.weak_form_problem = df.fem.petsc.LinearProblem(
                    self.a,
                    self.L,
                    bcs=bcs,
                    u=self.fields.displacement,
                    petsc_options={"ksp_type": "preonly", "pc_type": "lu"},
                )
            
            elif i > 0:
                # Update the linear problem for subsequent iterations
                self._L = _create_form(self.L, form_compiler_options=form_compiler_options, jit_options=jit_options)
                self.weak_form_problem._L = self._L  
            
            # Solve the system for the current increment
            self.solve()
            
            # Execute remaining callbacks after solving the system
            self.callbacks[1]()
                
            self.callbacks[2]()
                
            i += 1
            
        
            
    @staticmethod
    def parameter_description() -> dict[str, str]:
        """static method returning a description dictionary for required parameters

        Returns:
            description dictionary

        """
        description = {
            "g": "gravity",
            "dt": "time step",
            "rho": "density of fresh concrete",
            "E": "Young's Modulus",
            "nu": "Poissons Ratio",
            "stress_state": "for 2D plain stress or plane strain",
            "degree": "Polynomial degree for the FEM model",
            "dt": "time step",
        }

        return description

    @staticmethod
    def default_parameters() -> tuple[Experiment, dict[str, pint.Quantity]]:
        """returns a dictionary with required parameters and a set of working values as example"""
        # default setup for this material
        #experiment = CantileverBeam(CantileverBeam.default_parameters())
        experiment = ""

        model_parameters = {}
        model_parameters["g"] = 9.81 * ureg("m/s^2")
        #model_parameters["dt"] = 30.0 * ureg("s")

        model_parameters["stress_state"] = "plane_strain" * ureg("")
        model_parameters["degree"] = 2 * ureg("")  # polynomial degree
        model_parameters["dt"] = 60.0 * ureg("s")

        return experiment, model_parameters
    
    
    # Stress computation for linear elastic problem
    def epsilon(self, u: ufl.argument.Argument) -> ufl.tensoralgebra.Sym:
        return ufl.tensoralgebra.Sym(ufl.grad(u))

    def sigma(self, u: ufl.argument.Argument) -> ufl.core.expr.Expr:
        return self.lambda_ * ufl.nabla_div(u) * ufl.Identity(self.p["dim"]) + 2 * self.mu * self.epsilon(u)

    def solve(self) -> None:
        self.update_time()
        self.logger.info(f"solving t={self.time}")
        self.weak_form_problem.solve()

        # TODO Defined as abstractmethod. Should it depend on sensor instead of material?
        self.compute_residuals()

        # get sensor data
        for sensor_name in self.sensors:
            
            if self.sensors[sensor_name].__class__.__name__ == "DisplacementSensor":
                # go through all sensors and measure
                self.sensors[sensor_name].measure(self)
            else:
                pass

    def compute_residuals(self) -> None:
        self.residual = ufl.action(self.a, self.fields.displacement) - self.L

    # paraview output
    # TODO move this to sensor definition!?!?!
    def pv_plot(self) -> None:
        # Displacement Plot

        with df.io.XDMFFile(self.mesh.comm, self.pv_output_file, "a") as f:
            f.write_function(self.fields.displacement, self.time)
            