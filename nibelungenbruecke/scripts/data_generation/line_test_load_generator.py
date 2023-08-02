import ufl
import numpy as np

from petsc4py.PETSc import ScalarType

from dolfinx import fem, mesh
import dolfinx as df
from mpi4py import MPI
from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel
from nibelungenbruecke.scripts.utilities.boundary_condition_factory import boundary_condition_factory
from nibelungenbruecke.scripts.utilities.boundary_conditions import point_at

class LineTestLoadGenerator(GeneratorModel):
    ''' Generates the displacements at the sensors for a given load configuration for a line test.'''
    # TODO: This could probably be simplified by using the ForwardModel from probeye or the Problem from FenicsConcreteX
    # TODO: Delete duplicated Displacement model
    
    def __init__(self, model_path: str, sensor_positions_path: str, model_parameters: dict, output_parameters: dict = None):
        super().__init__(model_path, sensor_positions_path, model_parameters, output_parameters)

        self.material_parameters = model_parameters["material_parameters"]
        self.calculate_lame_constants()

        self.dt = model_parameters["dt"]
        
        # Initialize the load
        self.load_value = self.model_parameters["mass"]*self.model_parameters["g"] #Load of the vehicle
        self.initial_position = [0,0,self.model_parameters["initial_position"]] #Initial position of the front left wheel of the vehicle
        self.current_position = self.initial_position #Current position of the front left wheel of the vehicle
        self.historic_position = [self.current_position[0]] #Historic X position of the front left wheel of the vehicle
        self.speed = self.model_parameters["speed"] #Speed of the vehicle
        self.length_vehicle = self.model_parameters["length"] #Length of the vehicle
        self.width_vehicle = self.model_parameters["width"] #Width of the vehicle
        self.length_road = self.model_parameters["lenght_road"] #Length of the road
        self.width_road = self.model_parameters["width_road"] #Width of the road

        assert self.length_vehicle < self.length_road, "The length of the vehicle is bigger than the length of the road"
        assert self.width_vehicle < self.width_road, "The width of the vehicle is bigger than the width of the road"
        assert self.initial_position[2] > self.width_road/2, "The initial position of the vehicle is outside the road width (left)"
        assert self.initial_position[2] + self.width_vehicle < self.width_road/2, "The initial position of the vehicle is outside the road width (right)"


    def GenerateModel(self):
        # Generate function space
        self.V = fem.VectorFunctionSpace(self.mesh, ("CG", 1))

        # Load boundary conditions
        self.LoadBCs()

        T = fem.Constant(self.mesh, ScalarType((0, 0, self.model_parameters["tension_z"])))
        ds = ufl.Measure("ds", domain=self.mesh)

        u = ufl.TrialFunction(self.V)
        v = ufl.TestFunction(self.V)

        self.f_field=fem.Function(self.V)
        self.evaluate_load()
        self.a = ufl.inner(self.sigma(u), self.epsilon(v)) * ufl.dx
        self.L = ufl.dot(self.f_field, v) * ufl.dx + ufl.dot(T, v) * ds

    @GeneratorModel.sensor_offloader_wrapper
    def GenerateData(self):
        # Code to generate displacement data

        # Solve the problem
        problem = fem.petsc.LinearProblem(self.a, self.L, bcs=self.bcs, petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
        while self.advance_load(self.dt):
            self.displacement = problem.solve()
       
        # The wrapper takes care of the offloading

        # Paraview output
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.mesh)
                xdmf.write_function(self.displacement)

    def LoadBCs(self):

        bcs = []
        for bc_name, bc_model in self.model_parameters["boundary_conditions"].items():
            bc = boundary_condition_factory(self.mesh,bc_model["model"],self.V, bc_model)
            bcs.append(bc)

        self.bcs = bcs

    def epsilon(self, u):
        return ufl.sym(ufl.grad(u)) # Equivalent to 0.5*(ufl.nabla_grad(u) + ufl.nabla_grad(u).T)

    def sigma(self, u):
        return self.material_parameters["lambda"] * ufl.nabla_div(u) * ufl.Identity(len(u)) + 2*self.material_parameters["mu"]*self.epsilon(u)

    def calculate_lame_constants(self):
        E_modulus  = self.material_parameters["E"]
        nu = self.material_parameters["nu"]
        self.material_parameters["lambda"] = (E_modulus*nu)/((1+nu)*(1-2*nu))
        self.material_parameters["mu"] = E_modulus/(2*(1+nu))

    def advance_load(self, dt):
        ''' Advance the load'''
        self.current_position[0] += self.speed*dt
        self.historic_position.append(self.current_position[0])
        self.evaluate_load()

        if self.current_position[0] > self.length_road+self.length_vehicle:
            return False
        else:
            return True    

    def evaluate_load(self):
        ''' Evaluate the load'''

        fdim = self.mesh.topology.dim - 1

        if self.current_position[0] < self.length_road:
            front_left_facets = mesh.locate_entities_boundary(self.mesh, fdim, point_at(self.current_position))
            self.f_field.x.array[front_left_facets] += np.array([0,-self.load_value/4.00, 0.0], dtype=ScalarType)
            front_right_facets = mesh.locate_entities_boundary(self.mesh, fdim, point_at([self.current_position[0],self.current_position[1],self.current_position[2]+self.width_vehicle]))
            self.f_field.x.array[front_right_facets] += np.array([0,-self.load_value/4.00, 0.0], dtype=ScalarType)
        
        if self.current_position[0] < self.length_vehicle:
            back_left_facets = mesh.locate_entities_boundary(self.mesh, fdim, point_at([self.current_position[0],self.current_position[1],self.current_position[2]]))
            self.f_field.x.array[back_left_facets] += np.array([0,-self.load_value/4.00, 0.0], dtype=ScalarType)
            back_right_facets = mesh.locate_entities_boundary(self.mesh, fdim, point_at([self.current_position[0]-self.length_vehicle,self.current_position[1],self.current_position[2]+self.width_vehicle]))
            self.f_field.x.array[back_right_facets] += np.array([0,-self.load_value/4.00, 0.0], dtype=ScalarType)

    def _get_default_parameters():
        default_parameters = {
            "model_name":"displacements",
            "paraview_output": False,
            "paraview_output_path": "output/paraview",
            "material_parameters":{
                "rho": 1.0,
                "g": 100,
                "mu": 1,
                "lambda": 1.25
            },
            "tension_z": 0.0,
            "mass": 1000,
            "g": 9.81,
            "initial_position": 0.0,
            "speed": 1.0,
            "length": 1.0,
            "width": 1.0,
            "lenght_road": 10.0,
            "width_road": 10.0,
            "dt": 1.0,
            "boundary_conditions": [{
                "model":"clamped_boundary",
                "side_coord": 0.0,
                "coord": 0
            }]
        }

        return default_parameters