import ufl

from petsc4py.PETSc import ScalarType

from dolfinx import fem
import dolfinx as df
from mpi4py import MPI
from data_generation.generator_model_base_class import GeneratorModel
from utilities.boundary_condition_factory import boundary_condition_factory

class Displacement3DGenerator(GeneratorModel):
    ''' Generates the displacements at the sensors for a given load configuration.'''
    
    def __init__(self, model_path: str, sensor_positions_path: str, model_parameters: dict, output_parameters: dict):
        super().__init__(model_path, sensor_positions_path, model_parameters, output_parameters)

        self.material_parameters = model_parameters["material_parameters"]


    def GenerateModel(self):
        # Code to generate the displacement model
        
        # self.mesh = df.mesh.create_box(comm=MPI.COMM_WORLD,
        #                     points=((0.0, 0.0, 0.0), (-8.0, -8.0, 100.0)), n=(16, 16, 100),
        #                     cell_type=df.mesh.CellType.hexahedron)

        # Generate function space
        self.V = fem.VectorFunctionSpace(self.mesh, ("CG", 1))

        # Load boundary conditions
        self.LoadBCs()

        T = fem.Constant(self.mesh, ScalarType((0, 0, self.model_parameters["tension_z"])))
        ds = ufl.Measure("ds", domain=self.mesh)

        u = ufl.TrialFunction(self.V)
        v = ufl.TestFunction(self.V)
        f = fem.Constant(self.mesh, ScalarType((0, -self.material_parameters["rho"]*self.material_parameters["g"],0)))
        self.a = ufl.inner(self.sigma(u), self.epsilon(v)) * ufl.dx
        self.L = ufl.dot(f, v) * ufl.dx + ufl.dot(T, v) * ds

    @GeneratorModel.sensor_offloader_wrapper
    def GenerateData(self):
        # Code to generate displacement data

        # Solve the problem
        problem = fem.petsc.LinearProblem(self.a, self.L, bcs=self.bcs, petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
        self.displacement = problem.solve()
       
        # The wrapper takes care of the offloading

        # Paraview output
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.mesh.comm, self.model_parameters["paraview_output_path"]+"/"+self.model_parameters["model_name"]+".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.mesh)
                xdmf.write_function(self.displacement)


    def LoadBCs(self):

        bcs = []
        for bc_model in self.model_parameters["boundary_conditions"]:
            bc = boundary_condition_factory(self.mesh,bc_model["model"],self.V, bc_model)
            bcs.append(bc)

        self.bcs = bcs

    def epsilon(self, u):
        return ufl.sym(ufl.grad(u)) # Equivalent to 0.5*(ufl.nabla_grad(u) + ufl.nabla_grad(u).T)

    def sigma(self, u):
        return self.material_parameters["lambda"] * ufl.nabla_div(u) * ufl.Identity(len(u)) + 2*self.material_parameters["mu"]*self.epsilon(u)

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
