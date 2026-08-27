import dolfinx as df
import numpy as np
import pint
import ufl
from mpi4py import MPI
from petsc4py.PETSc import ScalarType

from fenicsxconcrete.experimental_setup.base_experiment import Experiment
from fenicsxconcrete.util import Parameters, ureg

class ThermalExperiment(Experiment):
    """Sets up a thermal experiment geometry from msh file or box."""

    def __init__(self, parameters: dict[str, pint.Quantity] | None = None, model_path=None):
        """
        Initializes the ThermalExperiment object.

        Args:
            parameters: Dictionary containing the required parameters for the experiment set-up.
        """
        #%%
        ##TODO: 
            
        if model_path:
            parameters["model_parameters"]["problem_parameters"]["mesh_path"] = model_path
        
        self.params = ThermalExperiment.unitize_parameters(parameters["model_parameters"]["problem_parameters"],
            ThermalExperiment.pint_default_units()
        )
        ##TODO:
        
        super().__init__(self.params)

        #%%
    def setup(self) -> None:
        """
        Defines the mesh for 2D or 3D.

        Raises:
            ValueError: If dimension (self.p["dim"]) is not 2 or 3, or geometry is not implemented.
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
            self.mesh, self.cell_tags, self.facet_tags = df.io.gmshio.read_from_msh(
                self.p["mesh_path"], MPI.COMM_WORLD, 0, self.p["dim"]
            )
            
        else:
            raise ValueError(f'wrong geometry: {self.p["geometry"]} is not implemented for problem setup')
    
    @staticmethod
    def default_parameters() -> dict[str, pint.Quantity]:
        """sets up a working set of parameter values as example

        Returns:
            dictionary with a working set of the required parameter

        """
        setup_parameters = {}
        setup_parameters["geometry"] = "gmsh" * ureg("")
        setup_parameters["length"] = 1 * ureg("m")
        setup_parameters["height"] = 0.3 * ureg("m")
        setup_parameters["width"] = 0.3 * ureg("m")  # only relevant for 3D case
        setup_parameters["dim"] = 3 * ureg("")
        setup_parameters["num_elements_length"] = 10 * ureg("")
        setup_parameters["num_elements_height"] = 3 * ureg("")
        setup_parameters["num_elements_width"] = 3 * ureg("")  # only relevant for 3D case
        
        return setup_parameters

    
    
    @staticmethod
    def pint_default_units() -> dict[str, pint.Unit]:
        return {
            # Temperatures
            'air_temperature': ureg.kelvin,
            'inner_temperature': ureg.kelvin,
            'initial_temperature': ureg.kelvin,
    
            # Material properties
            'heat_capacity': ureg.joule / (ureg.kilogram * ureg.kelvin),
            'density': ureg.kilogram / ureg.meter**3,
            'conductivity': ureg.watt / (ureg.meter * ureg.kelvin),
            'diffusivity': ureg.meter**2 / ureg.second,
    
            # Time
            'dt': ureg.second,
    
            # Geometry / location
            'length': ureg.meter,
            'height': ureg.meter,
            'width': ureg.meter,
            'sensor_location_u': ureg.meter,
            'sensor_location_s': ureg.meter,
            'sensor_location_n': ureg.meter,
            'sensor_location_o': ureg.meter,
            'characteristic_length': ureg.meter,
    
            # Air properties
            'wind_speed': ureg.meter / ureg.second,
            'air_viscosity': ureg.pascal * ureg.second,
            'air_prandtl_number': ureg.dimensionless,
            'air_thermal_conductivity': ureg.watt / (ureg.meter * ureg.kelvin),
    
            # Radiation
            'shortwave_irradiation': ureg.watt / ureg.meter**2,
            'shortwave_radiation_constant': ureg.dimensionless,
            'longwave_radiation_constant': ureg.dimensionless,
            'emissivity': ureg.dimensionless,
            'albedo': ureg.dimensionless,
    
            # Convection
            'convection_coefficient': ureg.watt / (ureg.meter**2 * ureg.kelvin),
            'natural_convection_coefficient': ureg.watt / (ureg.meter**2 * ureg.kelvin),
            'wind_forced_convection_parameter_constant': ureg.dimensionless,
            'wind_forced_convection_parameter_constant_top': ureg.dimensionless,
            'wind_forced_convection_parameter_constant_bottom': ureg.dimensionless,
    
            # Simulation control / numerical
            'theta': ureg.dimensionless,
            'initial_condition_steps': ureg.dimensionless,
            'burn_in_steps': ureg.dimensionless,
            'dim': ureg.dimensionless,
            'num_elements_length': ureg.dimensionless,
            'num_elements_height': ureg.dimensionless,
            'num_elements_width': ureg.dimensionless,
    
            # Tags and flags
            'top_tag': ureg.dimensionless,
            'bottom_tag': ureg.dimensionless,
            'end_tag': ureg.dimensionless,
            'convection': ureg.dimensionless,
            'wind_forced_convection': ureg.dimensionless,
            'shortwave_radiation': ureg.dimensionless,
            'longwave_radiation': ureg.dimensionless,
            'calculate_shortwave_irradiation': ureg.dimensionless,
            'plot_pv': ureg.dimensionless,
        }
    
    @staticmethod
    def unitize_parameters(data: dict, unit_map: dict[str, pint.Unit]) -> dict:
        """
        Recursively converts numeric and boolean values in a nested dictionary into pint.Quantity,
        using provided unit mappings or dimensionless as fallback.
    
        Args:
            data (dict): Dictionary of parameters to convert.
            unit_map (dict): Dictionary mapping keys to pint units.
    
        Returns:
            dict: Same structure as input, with quantities applied.
        """
        converted = {}
    
        for key, value in data.items():
            # Handle nested dictionaries
            if isinstance(value, dict):
                converted[key] = ThermalExperiment.unitize_parameters(value, unit_map)
            
            # Convert booleans to 1/0 with dimensionless unit
            elif isinstance(value, bool):
                converted[key] = int(value) * ureg.dimensionless
                
            # Apply unit for numbers (float/int)
            elif isinstance(value, (int, float)):
                unit = unit_map.get(key, ureg.dimensionless)
                converted[key] = value * unit
    

    
            # Leave everything else untouched (e.g. str, list, None)
            else:
                converted[key] = value * ureg.dimensionless
    
        return converted

    
    def create_temperature_boundary(self, V) -> list:
        """
        Defines temperature boundary as fixed at bottom.

        Args:
            V: Function space.

        Returns:
            list: List of Dirichlet boundary conditions.
        """
        temperature_bcs = []
        max_x = max(vertex[0] for vertex in self.mesh.geometry.x)
        def clamped_boundary(x):
            return np.logical_or(np.isclose(x[0], 0), np.isclose(x[0], max_x))
        temperature_bcs.append(
            df.fem.dirichletbc(
                np.array(np.float64(293.0), dtype=ScalarType),
                df.fem.locate_dofs_geometrical(V, clamped_boundary),
                V,
            )
        )
        return temperature_bcs

    def create_displacement_boundary(self, V) -> list:
        """
        Placeholder for displacement boundary creation.

        Args:
            V: Function space.

        Returns:
            None
        """
        pass

    def create_body_force(self, v: ufl.argument.Argument) -> ufl.form.Form:
        """
        Placeholder for body force creation.

        Args:
            v: Test function.

        Returns:
            None
        """
        pass