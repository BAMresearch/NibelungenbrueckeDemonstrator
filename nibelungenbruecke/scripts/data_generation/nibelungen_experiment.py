from collections.abc import Callable
from copy import deepcopy

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

from dolfinx import fem, mesh

class NibelungenExperiment(Experiment):
    def __init__(self, model_path, model_parameters: dict[str, pint.Quantity]) -> None:
        
        self.model_parameters = model_parameters
        self.material_parameters = self.model_parameters["material_parameters"]
        
        self.calculate_lame_constants()
        
        ##TODO: Modifications
        self.model_path = model_path
        
        default_p = Parameters()
        #default_p.update(self._experience_default_parameters())
        default_p.update(self._experience_default_parameters())
        

        for key, value in self.material_parameters.items():
            if key in default_p:
                default_p[key] = value * default_p[key].units

        super().__init__(default_p)
        
        self.dt = model_parameters["dt"]
        
        # Initialize the load
        self.initial_position = self.model_parameters[
            "initial_position"
        ]  # Initial position of the front left wheel of the vehicle
        self.current_position = deepcopy(
            self.initial_position
        )  # Current position of the front left wheel of the vehicle
        self.historic_position = [
            self.current_position[2]
        ]  # Historic X position of the front left wheel of the vehicle
        self.speed = self.model_parameters["speed"]  # Speed of the vehicle
        self.length_vehicle = self.model_parameters["length"]  # Length of the vehicle
        self.width_vehicle = self.model_parameters["width"]  # Width of the vehicle
        self.load_value = (
            self.model_parameters["mass"] * self.model_parameters["g"] / (self.length_vehicle * self.width_vehicle)
        )  # Load of the vehicle per surface unit
        self.length_road = self.model_parameters["length_road"]  # Length of the road
        self.width_road = self.model_parameters["width_road"]  # Width of the road
        
        self.converged = False

        assert (
            self.length_vehicle < self.length_road
        ), "The length of the vehicle is bigger than the length of the road"
        assert self.width_vehicle < self.width_road, "The width of the vehicle is bigger than the width of the road"
        assert (
            self.initial_position[0] > -self.width_road / 2
        ), "The initial position of the vehicle is outside the road width (left)"
        assert (
            self.initial_position[0] + self.width_vehicle < self.width_road / 2
        ), "The initial position of the vehicle is outside the road width (right)"

        
    def setup(self):
        """
        try:
            ##TODO: self.mesh, cell_tags, facet_tags = df.io.gmshio.read_from_msh(self.model_path, MPI.COMM_WORLD, 0)
            self.mesh, cell_tags, facet_tags = df.io.gmshio.read_from_msh(self.model_path, MPI.COMM_WORLD, 0)
            pass
        except Exception as e:
            raise Exception(f"An error occurred during mesh setup: {e}")
        """
        """defines the mesh for 2D or 3D

        Raises:
            ValueError: if dimension (self.p["dim"]) is not 2 or 3
        """
        if self.p["geometry"] == "box":
            if self.p["dim"] == 2:
                self.mesh = df.mesh.create_rectangle(
                    comm=MPI.COMM_WORLD,
                    points=[(0.0, 0.0), (self.p["length"], self.p["height"])],
                    n=(self.p["num_elements_length"], self.p["num_elements_height"]),
                    cell_type=df.mesh.CellType.quadrilateral,
                )
            elif self.p["dim"] == 3:
                self.mesh = df.mesh.create_box(
                    comm=MPI.COMM_WORLD,
                    points=[
                        (0.0, 0.0, 0.0),
                        (self.p["length"], self.p["width"], self.p["height"]),
                    ],
                    n=[
                        self.p["num_elements_length"],
                        self.p["num_elements_width"],
                        self.p["num_elements_height"],
                    ],
                    cell_type=df.mesh.CellType.hexahedron,
                )
            else:
                raise ValueError(f'wrong dimension: {self.p["dim"]} is not implemented for problem setup')
        elif self.p["geometry"] == "gmsh":
            try:
                import gmsh
                gmsh.initialize()
                gmsh.open(self.model_path)

                self.mesh, self.cell_tags, self.facet_tags = df.io.gmshio.model_to_mesh(
                    gmsh.model, MPI.COMM_WORLD, 0, self.p["dim"]
                )
                
                gmsh.finalize()

            except Exception as e:
                print("Failed to read gmsh mesh from:", self.model_path)
                print("Error:", e)
                gmsh.finalize()  # Ensure finalization even if exception occurs
                raise



            # DEBUG MESH TAGS
            # with df.io.XDMFFile(self.mesh.comm, "ft.xdmf", "w") as xdmf:
            #     xdmf.write_mesh(self.mesh)
            #     xdmf.write_meshtags(self.facet_tags)
        else:
            raise ValueError(f'wrong geometry: {self.p["geometry"]} is not implemented for problem setup')


    @staticmethod
    def default_parameters() -> dict[str, pint.Quantity]:
        """sets up a working set of parameter values as example

        Returns:
            dictionary with a working set of the required parameter

        """
        setup_parameters = {}
        setup_parameters["load"] = 1000 * ureg("N/m^2")
        #setup_parameters["height"] = 0.3 * ureg("m")    #TODO:
        #setup_parameters["length"] = 70 * ureg("m")
        #setup_parameters["dim"] = 3 * ureg("")
        #setup_parameters["width"] = 0.3 * ureg("m")  # only relevant for 3D case
        #setup_parameters["num_elements_length"] = 10 * ureg("")
        #setup_parameters["num_elements_height"] = 3 * ureg("")
        # only relevant for 3D case
        #setup_parameters["num_elements_width"] = 3 * ureg("")

        # Thermal model parameters
        #setup_parameters["geometry"] = "box" * ureg("")
        setup_parameters["geometry"] = "gmsh" * ureg("")
        setup_parameters["length"] = 100 * ureg("m")
        setup_parameters["height"] = 15 * ureg("m")
        setup_parameters["width"] = 2 * ureg("m")  # only relevant for 3D case
        setup_parameters["dim"] = 3 * ureg("")
        setup_parameters["num_elements_length"] = 20 * ureg("")
        setup_parameters["num_elements_height"] = 5 * ureg("")
        setup_parameters["num_elements_width"] = 5 * ureg("")  # only relevant for 3D case

        return setup_parameters
    
    @staticmethod
    def _get_default_parameters():
        """Get the default parameters for the line test load generator."""
        default_parameters = {
            "model_name": "displacements",
            "paraview_output": False,
            "paraview_output_path": "output/paraview",
            "material_parameters": {"rho": 1.0, "mu": 1, "lambda": 1.25},
            "tension_z": 0.0,
            "mass": 1000,
            "g": 9.81,
            "initial_position": [0.0, 0.0, 0.0],
            "speed": 1.0,
            "length": 1.0,
            "width": 1.0,
            "length_road": 90.0,
            "width_road": 10.0,
            "dt": 50.0,     ##TODO:
            "boundary_conditions": [{"model": "clamped_boundary", "side_coord": 0.0, "coord": 0}],
        }

        return default_parameters
    
                    
    @staticmethod
    def _experience_default_parameters():
        """
        Get default material parameters.

        Returns:
            dict: Default material parameters.
        """
        default_parameters = {
            "rho":7750 * ureg("kg/m^3"),
            "E":210e9 * ureg("N/m^2"),
            "nu":0.28 * ureg("")
        }
        return default_parameters
    

    
    def create_displacement_boundary(self, V) -> list:
        """defines displacement boundary as fixed at bottom

        Args:
            V: function space

        Returns:
            list of dirichlet boundary conditions

        """

        bc_generator = BoundaryConditions(self.mesh, V)

        if self.p["dim"] == 2:
            # fix line in the left
            bc_generator.add_dirichlet_bc(
                np.array([0.0, 0.0], dtype=ScalarType),
                boundary=self.boundary_left(),
                method="geometrical",
            )
            # line with dof in x direction on the right
            bc_generator.add_dirichlet_bc(np.float64(0.0), self.boundary_right(), 1, "geometrical", 0)

        elif self.p["dim"] == 3:
            # fix line in the left
            bc_generator.add_dirichlet_bc(
                np.array([0.0, 0.0, 0.0], dtype=ScalarType),
                boundary=self.boundary_left(),
                method="geometrical",
            )
            
            # fix line in the left
            bc_generator.add_dirichlet_bc(
                np.array([0.0, 0.0, 0.0], dtype=ScalarType),
                boundary=self.boundary_right(),
                method="geometrical",
            )
            
            # line with dof in x direction on the right
            #bc_generator.add_dirichlet_bc(np.float64(0.0), self.boundary_right(), 1, "geometrical", 0)
            #bc_generator.add_dirichlet_bc(np.float64(0.0), self.boundary_right(), 2, "geometrical", 0)
            
        return bc_generator.bcs
    
    def create_temperature_boundary(self, V) -> list:
        """defines temperature boundary as fixed at bottom

        Args:
            V: function space

        Returns:
            list of dirichlet boundary conditions

        """

        # fenics will individually call this function for every node and will note the true or false value.
        temperature_bcs = []
        max_x = max(vertex[0] for vertex in self.mesh.geometry.x)
        def clamped_boundary(x):
            return np.logical_or(np.isclose(x[0], 0),np.isclose(x[0], max_x))


        temperature_bcs.append(
            df.fem.dirichletbc(
                np.array(np.float64(293.0), dtype=ScalarType),
                df.fem.locate_dofs_geometrical(V, clamped_boundary),
                V,
            )
        )

        return temperature_bcs
    
    def boundary_left(self) -> Callable:
        """specifies boundary at bottom

        Returns:
            fct defining boundary

        """

        if self.p["dim"] == 2:
            return point_at([0, 0])
        elif self.p["dim"] == 3:
            return line_at([0, 0], ["y", "z"])

    def boundary_right(self) -> Callable:
        """specifies boundary at bottom

        Returns:
            fct defining boundary

        """

        if self.p["dim"] == 2:
            return point_at([0, self.length_road])
        elif self.p["dim"] == 3:
            return line_at([0, self.length_road], ["y", "z"])
        

    def create_body_force(self, v: ufl.argument.Argument) -> ufl.form.Form:
        """defines body force

        Args:
            v: test function

        Returns:
            form for body force

        """

        force_vector = np.zeros(self.p["dim"])
        force_vector[1] = -self.p["rho"] * self.p["g"]  # works for 2D and 3D

        f = df.fem.Constant(self.mesh, ScalarType(force_vector))
        L = ufl.dot(f, v) * ufl.dx

        return L

    def boundary_force_field(self):
    
        f = fem.Constant(self.mesh, ScalarType((0, -self.load_value, 0)))
        return f
 
    def create_force_boundary(self, v: ufl.argument.Argument) -> ufl.form.Form: ## TODO: Delete v!?
        """moving load

        Args:
            v: test function

        Returns:
            form for force boundary

        """
        
        i = 0
        if not self.converged:
            self.evaluate_load()
                
            self.converged = self.advance_load(self.dt)
            i += 1
            
        return self.ds_load
   
    def calculate_lame_constants(self):
        """Calculate the Lame constants for the line test load generator."""
        E_modulus = self.material_parameters["E"]
        nu = self.material_parameters["nu"]
        self.material_parameters["lambda"] = (E_modulus * nu) / ((1 + nu) * (1 - 2 * nu))
        self.material_parameters["mu"] = E_modulus / (2 * (1 + nu))
        
        
    def advance_load(self, dt):
        """Advance the load for the line test load generator."""
        self.current_position[2] += self.speed * dt
        self.historic_position.append(self.current_position[2])
        self.evaluate_load()

        return self.current_position[2] > self.length_road + self.length_vehicle

    def evaluate_load(self):
        """Evaluate the load for the line test load generator."""

        # Apply local load (surface force) in subdomain
        load_subdomain = LoadSubDomain(
            corner=self.current_position, length=self.length_vehicle, width=self.width_vehicle
        )
        subdomain = mesh.locate_entities(self.mesh, self.mesh.topology.dim - 1, marker=load_subdomain.inside)
        subdomain_values = np.full_like(subdomain, 1)
        facet_tags = mesh.meshtags(self.mesh, self.mesh.topology.dim - 1, subdomain, subdomain_values)
        self.ds_load = ufl.Measure("ds", domain=self.mesh, subdomain_data=facet_tags)


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
                    np.logical_and(x[0] > self.corner[0], x[0] < self.corner[0] + self.width), x[2] < self.corner[2]
                ),
                x[2] > self.corner[2] - self.length,
            ),
            np.isclose(x[1], self.corner[1]),
        )




#%%

if __name__ == "__main__":
    
    model_path = '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh'
    
    model_parameters = {'model_name': 'displacements',
     'df_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_df_output.csv',
     'meta_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_meta_output.json',
     'MKP_meta_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_meta_output.json',
     'MKP_translated_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_translated.json',
     'virtual_sensor_added_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json',
     'cache_path': '',
     'paraview_output': True,
     'paraview_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview',
     'material_parameters': {'E': 40000000000000.0, 'nu': 0.2, 'rho': 2350},
     'tension_z': 0.0,
     'mass': 50000.0,
     'g': 9.81,
     'initial_position': [0.0, 0.0, 0.0],
     'speed': 1.0,
     'length': 7.5,
     'width': 2.5,
     'height': 6.5,
     'length_road': 95.0,
     'width_road': 14.0,
     'thickness_deck': 0.2,
     'dt': 75.0,
     'reference_temperature': 300,
     'temperature_coefficient': 1e-05,
     'temperature_alpha': 1e-05,
     'temperature_difference': 5.0,
     'reference_height': -2.5,
     'boundary_conditions': {'bc1': {'model': 'clamped_edge',
       'side_coord_1': 0.0,
       'coord_1': 2,
       'side_coord_2': 0.0,
       'coord_2': 1},
      'bc2': {'model': 'clamped_edge',
       'side_coord_1': 95.185,
       'coord_1': 2,
       'side_coord_2': 0.0,
       'coord_2': 1}}} 
    
    nb = NibelungenExperiment(model_path, model_parameters)