import ufl
import numpy as np

from petsc4py.PETSc import ScalarType

from dolfinx import fem, mesh
import dolfinx as df
from mpi4py import MPI
from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel
from nibelungenbruecke.scripts.utilities.boundary_condition_factory import boundary_condition_factory
from nibelungenbruecke.scripts.utilities.loaders import load_sensors
from nibelungenbruecke.scripts.utilities.offloaders import offload_sensors

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
        self.initial_position = self.model_parameters["initial_position"] #Initial position of the front left wheel of the vehicle
        self.current_position = self.initial_position #Current position of the front left wheel of the vehicle
        self.historic_position = [self.current_position[2]] #Historic X position of the front left wheel of the vehicle
        self.speed = self.model_parameters["speed"] #Speed of the vehicle
        self.length_vehicle = self.model_parameters["length"] #Length of the vehicle
        self.width_vehicle = self.model_parameters["width"] #Width of the vehicle
        self.load_value = self.model_parameters["mass"]*self.model_parameters["g"]/(self.length_vehicle*self.width_vehicle) #Load of the vehicle per surface unit
        self.length_road = self.model_parameters["lenght_road"] #Length of the road
        self.width_road = self.model_parameters["width_road"] #Width of the road

        assert self.length_vehicle < self.length_road, "The length of the vehicle is bigger than the length of the road"
        assert self.width_vehicle < self.width_road, "The width of the vehicle is bigger than the width of the road"
        assert self.initial_position[0] > -self.width_road/2, "The initial position of the vehicle is outside the road width (left)"
        assert self.initial_position[0] + self.width_vehicle < self.width_road/2, "The initial position of the vehicle is outside the road width (right)"


    def GenerateModel(self):
        # Generate function space
        self.V = fem.VectorFunctionSpace(self.mesh, ("CG", 1))

        # Load boundary conditions
        self.LoadBCs()

        if self.model_parameters["tension_z"] != 0.0:
            T = fem.Constant(self.mesh, ScalarType((0, 0, self.model_parameters["tension_z"])))
            ds = ufl.Measure("ds", domain=self.mesh)

        u = ufl.TrialFunction(self.V)
        v = ufl.TestFunction(self.V)

        f = fem.Constant(self.mesh, ScalarType((0, -self.load_value,0)))
        f_weight = fem.Constant(self.mesh, ScalarType(np.array([0, -self.material_parameters["rho"]*self.model_parameters["g"],0])))
        self.evaluate_load()
        self.a = ufl.inner(self.sigma(u), self.epsilon(v)) * ufl.dx
        # self.L = ufl.dot(f, v) * self.dx_load + ufl.dot(T, v) * ds + fem.Constant(self.mesh,ScalarType(0.0))*ufl.dx
        if self.model_parameters["tension_z"] != 0.0:
            self.L = ufl.dot(f, v) * self.ds_load(1) + ufl.dot(f_weight, v) * ufl.dx + ufl.dot(T, v) * ds
        else:
            self.L = ufl.dot(f, v) * self.ds_load(1) + ufl.dot(f_weight, v) * ufl.dx 

    # @GeneratorModel.sensor_offloader_wrapper
    def GenerateData(self):
        # Code to generate displacement data

        if self.model_parameters["paraview_output"]:
            pv_file = df.io.XDMFFile(self.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+".xdmf", "w")

        # Solve the problem
        sensors = load_sensors(self.sensor_positions)
        i=0
        converged = False
        while not converged:
            self.GenerateModel()
            problem = fem.petsc.LinearProblem(self.a, self.L, bcs=self.bcs, petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
            self.displacement = problem.solve()
            self.displacement.name = "Displacement"
       
            # Sensor measurement (should be adapted with the wrapper)
            for sensor in sensors:
                sensor.measure(self)

            # Paraview output
            if self.model_parameters["paraview_output"]:
                if i ==0:
                    pv_file.write_mesh(self.mesh)
                pv_file.write_function(self.displacement,i*self.dt)
                L_vector = fem.assemble_vector(fem.form(self.L))
                L_function = fem.Function(self.V, x=L_vector, name="Load")
                pv_file.write_function(L_function,i*self.dt)
                pv_file.close()
                # Store the value at the sensors

            converged = self.advance_load(self.dt)
            i+=1
        
        offload_sensors(sensors, self.output_parameters["output_path"]+"/"+self.model_parameters["model_name"], self.output_parameters["output_format"])

        print(f"Number of iterations: {i}")

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
        self.current_position[2] += self.speed*dt
        self.historic_position.append(self.current_position[2])
        self.evaluate_load()

        return self.current_position[2] > self.length_road+self.length_vehicle

    def evaluate_load(self):
        ''' Evaluate the load'''

        # Apply local load (surface force) in subdomain
        load_subdomain = LoadSubDomain(corner=self.current_position, length=self.length_vehicle, width=self.width_vehicle)
        subdomain = mesh.locate_entities(self.mesh, self.mesh.topology.dim-1, marker= load_subdomain.inside)
        subdomain_values = np.full_like(subdomain, 1)
        facet_tags = mesh.meshtags(self.mesh, self.mesh.topology.dim-1, subdomain, subdomain_values)
        self.ds_load = ufl.Measure('ds', domain = self.mesh, subdomain_data = facet_tags)

    def _get_default_parameters():
        default_parameters = {
            "model_name":"displacements",
            "paraview_output": False,
            "paraview_output_path": "output/paraview",
            "material_parameters":{
                "rho": 1.0,
                "mu": 1,
                "lambda": 1.25
            },
            "tension_z": 0.0,
            "mass": 1000,
            "g": 9.81,
            "initial_position": [0.0,0.0,0.0],
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
    
# Define subdomain where the load should be applied
class LoadSubDomain:
    def __init__(self, corner, length, width):
        self.corner = corner
        self.length = length
        self.width = width

    def inside(self, x):
        return np.logical_and(
            np.logical_and(
                np.logical_and(
                    np.logical_and(
                        x[0] > self.corner[0],
                        x[0] < self.corner[0] + self.width
                    ), x[2] < self.corner[2]
                ), x[2] > self.corner[2] - self.length
            ), np.isclose(x[1], self.corner[1]))