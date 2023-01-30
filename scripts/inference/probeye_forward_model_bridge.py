# third party imports
import numpy as np
import ufl

from typing import Optional

from petsc4py.PETSc import ScalarType

from dolfinx import fem
import dolfinx as df
from mpi4py import MPI
from utilities.boundary_condition_factory import boundary_condition_factory

# local imports (problem definition)
from probeye.definition.forward_model import ForwardModelBase
from probeye.definition.sensor import Sensor
from probeye.subroutines import len_or_one

# utilities imports
from utilities.probeye_utilities import *
from utilities.checks import assert_path_exists
from utilities.general_utilities import modify_key


class BridgeModel(ForwardModelBase):
    ''' Bridge forward model class to be used in inference procedures to obtain 
    parameters of the Nibelungenbrücke given a set of displacements'''

    def __init__(self, name: str, *args, **kwargs):
        self.forward_model_parameters = kwargs["forward_model_parameters"]
        super().__init__(name, *args, **kwargs)
        self.model_parameters = kwargs["forward_model_parameters"]["model_parameters"]
        self.material_parameters = kwargs["forward_model_parameters"]["model_parameters"]["material_parameters"]
        
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
        self.f = fem.Constant(self.mesh, ScalarType((0, -self.material_parameters["rho"]*self.material_parameters["g"],0)))
        self.a = ufl.inner(self.sigma(u), self.epsilon(v)) * ufl.dx
        self.L = ufl.dot(self.f, v) * ufl.dx + ufl.dot(self.T, v) * ds
        self.problem = fem.petsc.LinearProblem(self.a, self.L, bcs=self.bcs, petsc_options={"ksp_type": "preonly", "pc_type": "lu"})

    def Solve(self):
        self.displacement = self.problem.solve()


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