# third party imports
import numpy as np
import ufl

from petsc4py.PETSc import ScalarType

from dolfinx import fem, mesh
import dolfinx as df
from mpi4py import MPI
from nibelungenbruecke.scripts.utilities.boundary_condition_factory import boundary_condition_factory

# local imports (problem definition)
from probeye.definition.forward_model import ForwardModelBase

# utilities imports
from nibelungenbruecke.scripts.utilities.probeye_utilities import *
from nibelungenbruecke.scripts.utilities.checks import assert_path_exists
from nibelungenbruecke.scripts.utilities.general_utilities import modify_key


class BridgeModel(ForwardModelBase):
    ''' Bridge forward model class to be used in inference procedures to obtain 
    parameters of the Nibelungenbrücke given a set of line test measurements'''

    def __init__(self, name: str, *args, **kwargs):
        self.forward_model_parameters = kwargs["forward_model_parameters"]
        super().__init__(name, *args, **kwargs)
        self.model_parameters = kwargs["forward_model_parameters"]["model_parameters"]
        self.material_parameters = kwargs["forward_model_parameters"]["model_parameters"]["material_parameters"]
        self.calculate_lame_constants()
        
    def interface(self):
        self.parameters = self.forward_model_parameters["problem_parameters"]
        if self.forward_model_parameters["parameter_key_paths"] is None:
            self.parameter_key_paths = [[]*len(self.parameters)]
        else:
            self.parameter_key_paths = self.forward_model_parameters["parameter_key_paths"]
        self.input_sensors = load_probeye_sensors(self.forward_model_parameters["input_sensors_path"])
        self.output_sensors = load_probeye_sensors(self.forward_model_parameters["output_sensors_path"])

    def response(self, inp: dict) -> dict:

        # Update model parameters
        for key, key_path in zip(self.parameters, self.parameter_key_paths):
            modify_key(self.forward_model_parameters["model_parameters"], key, inp[key], path=key_path)
        self.calculate_lame_constants()

        # Update possible changes in variables
        self.lambda_.value = float(self.material_parameters["lambda"])
        self.mu.value = float( self.material_parameters["mu"])
        self.T.value = ScalarType((0, 0, self.forward_model_parameters["model_parameters"]["tension_z"]))
        self.f.value = ScalarType((0, -self.forward_model_parameters["model_parameters"]["material_parameters"]["rho"]*self.forward_model_parameters["model_parameters"]["material_parameters"]["g"],0))

        self.Solve()

        response = {}
        for os in self.output_sensors:
            response[os.name] = self.extrapolate_to_point(np.transpose(os.coords))
        return response

    def LoadGeometry(self, model_path):
        ''' Load the meshed geometry from a .msh file'''
        assert_path_exists(model_path)
        
        # Translate mesh from gmsh to dolfinx
        self.mesh, cell_tags, facet_tags = df.io.gmshio.read_from_msh(model_path, MPI.COMM_WORLD, 0)

    def GenerateModel(self):
        # Code to generate the displacement model

        # Generate function space
        self.V = fem.VectorFunctionSpace(self.mesh, ("CG", 1))

        # Load boundary conditions
        self.LoadBCs()

        # Load Lamé constants
        self.lambda_ = fem.Constant(self.mesh, np.float64(self.material_parameters["lambda"]))
        self.mu = fem.Constant(self.mesh, np.float64(self.material_parameters["mu"]))
        
        self.T = fem.Constant(self.mesh, ScalarType((0, 0, self.model_parameters["tension_z"])))
        ds = ufl.Measure("ds", domain=self.mesh)

        u = ufl.TrialFunction(self.V)
        v = ufl.TestFunction(self.V)
        f = fem.Constant(self.mesh, ScalarType((0, -self.load_value,0)))
        self.f_weigth = fem.Constant(self.mesh, ScalarType((0, -self.material_parameters["rho"]*self.material_parameters["g"],0)))
        self.evaluate_load()
        self.a = ufl.inner(self.sigma(u), self.epsilon(v)) * ufl.dx
        if self.model_parameters["tension_z"] != 0.0:
            self.L = ufl.dot(f, v) * self.ds_load(1) + ufl.dot(self.f_weight, v) * ufl.dx + ufl.dot(self.T, v) * ds
        else:
            self.L = ufl.dot(f, v) * self.ds_load(1) + ufl.dot(self.f_weight, v) * ufl.dx 
        self.problem = fem.petsc.LinearProblem(self.a, self.L, bcs=self.bcs, petsc_options={"ksp_type": "preonly", "pc_type": "lu"})

    def Solve(self):
        self.displacement = self.problem.solve()
        i=0
        converged = False
        while not converged:
            self.GenerateModel()
            problem = fem.petsc.LinearProblem(self.a, self.L, bcs=self.bcs, petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
            self.displacement = problem.solve()
            self.displacement.name = "Displacement"
       
            # Sensor measurement (should be adapted with the wrapper)
            for sensor in self.output_sensors:
                sensor.measure(self, i*self.dt)

            converged = self.advance_load(self.dt)
            i+=1
        

    def LoadBCs(self):

        bcs = []
        for bc_model_name, bc_model_params in self.model_parameters["boundary_conditions"].items():
            bc = boundary_condition_factory(self.mesh,bc_model_params["model"],self.V, bc_model_params)
            bcs.append(bc)

        self.bcs = bcs

    def epsilon(self, u):
        return ufl.sym(ufl.grad(u)) # Equivalent to 0.5*(ufl.nabla_grad(u) + ufl.nabla_grad(u).T)

    def sigma(self, u):
        return self.lambda_ * ufl.nabla_div(u) * ufl.Identity(len(u)) + 2*self.mu*self.epsilon(u)

    def calculate_lame_constants(self):
        E_modulus  = self.material_parameters["E"]
        nu = self.material_parameters["nu"]
        self.material_parameters["lambda"] = (E_modulus*nu)/((1+nu)*(1-2*nu))
        self.material_parameters["mu"] = E_modulus/(2*(1+nu))

    def advance_load(self, dt):
        ''' Advance the load'''
        self.current_position[2] += self.speed*dt
        self.historic_position.append(self.current_position[2])
        # self.evaluate_load()

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
                "g": 100,
                "mu": 1,
                "lambda": 1.25
            },
            "tension_z": 0.0,
            "boundary_conditions": [{
                "model":"clamped_boundary",
                "side_coord": 0.0,
                "coord": 0
            }]
        }

        return default_parameters

    def extrapolate_to_point(self, where):
        # get displacements
        bb_tree = df.geometry.BoundingBoxTree(self.mesh, self.mesh.topology.dim)
        cells = []
        points_on_proc = []

        # Find cells whose bounding-box collide with the the points
        cell_candidates = df.geometry.compute_collisions(bb_tree, where)

        # Choose one of the cells that contains the point
        colliding_cells = df.geometry.compute_colliding_cells(self.mesh, cell_candidates, where)
        for i, point in enumerate(where):
            if len(colliding_cells)>0:
                points_on_proc.append(point)
                cells.append(colliding_cells.array[0])
        points_on_proc = np.array(points_on_proc, dtype=np.float64)
        return self.displacement.eval(np.squeeze(points_on_proc), cells)
    
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