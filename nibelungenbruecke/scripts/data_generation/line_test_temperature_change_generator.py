import ufl
import numpy as np

from petsc4py.PETSc import ScalarType

from dolfinx import fem
import dolfinx as df
from nibelungenbruecke.scripts.data_generation.line_test_load_generator import LineTestLoadGenerator


class LineTestTemperatureChangeGenerator(LineTestLoadGenerator):
    ''' Generates the displacements at the sensors for a given load configuration for a line test.'''
    # TODO: This could probably be simplified by using the ForwardModel from probeye or the Problem from FenicsConcreteX
    # TODO: Delete duplicated Displacement model
    
    def __init__(self, model_path: str, sensor_positions_path: str, model_parameters: dict, output_parameters: dict = None):
        super().__init__(model_path, sensor_positions_path, model_parameters, output_parameters)

        self.temperature_coefficient = self.model_parameters["temperature_coefficient"] #For heat transfer, not used for now
        self.temperature_difference = self.model_parameters["temperature_difference"]
        self.temperature_gradient = self.model_parameters["temperature_gradient"]
        if self.model_parameters["end_temperature_difference"] != 0:
            self.temperature_gradient = self.model_parameters["end_temperature_difference"]/(self.model_parameters["road_length"]+self.model_parameters["length"])*self.model_parameters["speed"]
        self.temperature_alpha = self.model_parameters["temperature_alpha"] #Temperature coefficient for the thermal expansion
        self.reference_temperature = self.model_parameters["reference_temperature"] #Reference temperature for the thermal expansion
        self.reference_height = self.model_parameters["reference_height"] #Reference height for the thermal expansion
        self.kappa = self.temperature_alpha*(3*self.material_parameters["lambda"]+2*self.material_parameters["mu"])
        self.thickness = self.model_parameters["thickness_deck"]

    def GenerateModel(self):
        # Generate function space
        self.V = fem.VectorFunctionSpace(self.mesh, ("CG", 1))
        tmp_space = fem.FunctionSpace(self.mesh, ("CG", 1))
        # Load boundary conditions
        self.LoadBCs()

        # Distribute the temperature field
        self.temperature_difference_field = df.fem.Function(tmp_space, name="Temperature_difference")
        def temperature_differences(x):
            values = np.zeros(len(x[1]))
            for y_value, i in zip(x[1], range(len(x[1]))):
                if y_value >= -(self.thickness*1.1): #Safety margin due to irregular mesh
                    values[i] = self.temperature_difference * y_value/self.thickness
            return np.full((1, x.shape[1]), values)
        self.temperature_difference_field.interpolate(temperature_differences)

        if self.model_parameters["tension_z"] != 0.0:
            T = fem.Constant(self.mesh, ScalarType((0, 0, self.model_parameters["tension_z"])))
            ds = ufl.Measure("ds", domain=self.mesh)

        u = ufl.TrialFunction(self.V)
        v = ufl.TestFunction(self.V)

        f = fem.Constant(self.mesh, ScalarType((0, -self.load_value,0)))
        f_weight = fem.Constant(self.mesh, ScalarType(np.array([0, -self.material_parameters["rho"]*self.model_parameters["g"],0])))
        self.evaluate_load()
        W_int = ufl.inner(self.sigma(u, self.temperature_difference_field), self.epsilon(v)) * ufl.dx
        self.a = ufl.lhs(W_int) #Avoids arity error due to function space mismatch
        # self.L = ufl.dot(f, v) * self.dx_load + ufl.dot(T, v) * ds + fem.Constant(self.mesh,ScalarType(0.0))*ufl.dx
        if self.model_parameters["tension_z"] != 0.0:
            self.L = ufl.dot(f, v) * self.ds_load(1) + ufl.dot(f_weight, v) * ufl.dx + ufl.dot(T, v) * ds
        else:
            self.L = ufl.dot(f, v) * self.ds_load(1) + ufl.dot(f_weight, v) * ufl.dx 
            # self.L = ufl.dot(f, v) * self.ds_load(1)
        self.L = ufl.rhs(W_int) + self.L

    # @GeneratorModel.sensor_offloader_wrapper
    def GenerateData(self):
        # Code to generate displacement data
        super().GenerateData()
        if self.model_parameters["paraview_output"]:
            pv_file = df.io.XDMFFile(self.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+"_temperature.xdmf", "w")
            pv_file.write_mesh(self.mesh)
            pv_file.write_function(self.temperature_difference_field)
            pv_file.close()

    def sigma(self, u, temperature_difference):
        return self.material_parameters["lambda"] * ufl.nabla_div(u) * ufl.Identity(self.V.mesh.geometry.dim) + 2*self.material_parameters["mu"]*self.epsilon(u) - self.kappa*temperature_difference*ufl.Identity(self.V.mesh.geometry.dim)

    def advance_load(self, dt):
        self.temperature_difference = self.temperature_difference + self.temperature_gradient*dt
        return super().advance_load(dt)

    @staticmethod
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
            "height": 2.5,
            "length_road": 10.0,
            "width_road": 10.0,
            "dt": 1.0,
            "reference_temperature":300,
            "reference_height": -2.5,
            "temperature_difference": 0,
            "temperature_gradient": 0.01,
            "end_temperature_difference": 0,
            "temperature_alpha": 1e-5,
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