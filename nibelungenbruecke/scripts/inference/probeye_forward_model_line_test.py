# third party imports
import numpy as np
import ufl

from petsc4py import PETSc

from dolfinx import fem, mesh
import dolfinx as df
from mpi4py import MPI
from copy import deepcopy
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

        self.dt = self.model_parameters["dt"]
        
        # Initialize the load
        self.initial_position = self.model_parameters["initial_position"] #Initial position of the front left wheel of the vehicle
        self.current_position = deepcopy(self.initial_position) #Current position of the front left wheel of the vehicle
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
        self.model_parameters = self.forward_model_parameters["model_parameters"]
        self.material_parameters = self.forward_model_parameters["model_parameters"]["material_parameters"]
        self.calculate_lame_constants()

        # Update possible changes in variables
        self.lambda_.value = float(self.material_parameters["lambda"])
        self.mu.value = float( self.material_parameters["mu"])
        self.T.value = PETSc.ScalarType((0, 0, self.forward_model_parameters["model_parameters"]["tension_z"]))
        self.f_weight.value = PETSc.ScalarType((0, -self.forward_model_parameters["model_parameters"]["material_parameters"]["rho"]*self.forward_model_parameters["model_parameters"]["material_parameters"]["g"],0))

        # Update bilinear operator
        self.A = fem.petsc.assemble_matrix(self.bilinear_form, bcs=self.bcs)
        self.A.assemble()
        self.solver.setOperators(self.A)

        # Solve the problem
        self.Solve()

        return self.response_dict

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
        
        self.T = fem.Constant(self.mesh, PETSc.ScalarType((0, 0, self.model_parameters["tension_z"])))
        self.ds = ufl.Measure("ds", domain=self.mesh)

        # Define solution field
        self.uh = fem.Function(self.V)
        self.uh.name = "Displacement"

        # Define variational problem
        self.u = ufl.TrialFunction(self.V)
        self.v = ufl.TestFunction(self.V)
        self.f = fem.Constant(self.mesh, PETSc.ScalarType((0, -self.load_value,0)))
        self.f_weight = fem.Constant(self.mesh, PETSc.ScalarType((0, -self.material_parameters["rho"]*self.material_parameters["g"],0)))
        a = ufl.inner(self.sigma(self.u), self.epsilon(self.v)) * ufl.dx
        self.evaluate_load()

        # Define bilinear and linear forms
        self.bilinear_form = fem.form(a)
        linear_form = fem.form(self.L)
        self.A = fem.petsc.assemble_matrix(self.bilinear_form, bcs=self.bcs)
        self.A.assemble()
        self.b = fem.petsc.create_vector(linear_form)

        # Pre-compute the linear forms for improved efficiency
        self.list_linear_forms = []
        self.current_position = deepcopy(self.initial_position) #Current position of the front left wheel of the vehicle
        self.historic_position = [self.current_position[2]] #Historic X position of the front left wheel of the vehicle
        converged = False
        i=0
        while not converged:
            if i>0:
                self.evaluate_load()
            linear_form = fem.form(self.L)
            self.list_linear_forms.append(linear_form)
            converged = self.advance_load(self.dt)
            i+=1

        # Define solver
        self.solver = PETSc.KSP().create(self.mesh.comm)
        self.solver.setOperators(self.A)
        self.solver.setType(PETSc.KSP.Type.PREONLY)
        self.solver.getPC().setType(PETSc.PC.Type.LU)

        # Evaluate sensor locations
        for os in self.output_sensors:
            where =  np.transpose(os.coords)
            self.points_on_proc, self.cells = self.evaluate_sensor_locations(where)
            
    def Solve(self):
        # self.displacement = self.problem.solve()
        i=0
        
        self.response_dict = {}

        for linear_form in self.list_linear_forms:

            # Update the right hand side reusing the initial vector
            with self.b.localForm() as loc_b:
                loc_b.set(0)
            # fem.petsc.assemble_vector(self.b, fem.form(self.L))
            fem.petsc.assemble_vector(self.b, linear_form)
            
            # Apply Dirichlet boundary conditions to the vector
            fem.petsc.apply_lifting(self.b, [self.bilinear_form], [self.bcs])
            self.b.ghostUpdate(addv=PETSc.InsertMode.ADD_VALUES, mode=PETSc.ScatterMode.REVERSE)
            fem.petsc.set_bc(self.b, self.bcs)

            # Solve linear problem
            self.solver.solve(self.b, self.uh.vector)
            self.uh.x.scatter_forward()
       
            # Sensor measurement (should be adapted with the wrapper)
            for os, point_on_proc, cells_point in zip(self.output_sensors, self.points_on_proc, self.cells):
                if i==0:
                    self.response_dict[os.name] = []
                self.response_dict[os.name].append(self.extrapolate_to_point(point_on_proc, cells_point)[1])
            i+=1
        print("Stop")

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
        self.update_L()

    def update_L(self):
        if self.model_parameters["tension_z"] != 0.0:
            self.L = ufl.dot(self.f, self.v) * self.ds_load(1) + ufl.dot(self.f_weight, self.v) * ufl.dx + ufl.dot(self.T, self.v) * self.ds
        else:
            self.L = ufl.dot(self.f, self.v) * self.ds_load(1) + ufl.dot(self.f_weight, self.v) * ufl.dx 

    def evaluate_sensor_locations(self, where):
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
        return points_on_proc, cells
    
    def extrapolate_to_point(self, point_on_proc, cells):
        
        return self.uh.eval(np.squeeze(point_on_proc), cells)

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