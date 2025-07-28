import dolfinx as df
import numpy as np
import pint
import ufl
from petsc4py.PETSc import ScalarType
from dolfinx.fem.forms import form as _create_form
import pandas as pd
import pvlib
import math

from fenicsxconcrete.experimental_setup import CantileverBeam, Experiment
from fenicsxconcrete.finite_element_problem.base_material import MaterialProblem, QuadratureFields, SolutionFields
from fenicsxconcrete.util import Parameters, ureg

from fenicsxconcrete.sensor_definition.temperature_sensor import TemperatureSensor
from fenicsxconcrete.sensor_definition.displacement_sensor import DisplacementSensor


class ThermoMechanicalNibelungenBrueckeProblem(MaterialProblem):
    """Transientthermal problem definition"""

    def __init__(
        self,
        #callbacks: None,
        experiment: Experiment,
        parameters: dict[str, pint.Quantity],
        pv_name: str = "pv_output_full",
        pv_path: str = None,
    ) -> None:
        """Initializes the TransientThermal problem.

        Args:
            experiment (Experiment): The experimental setup.
            parameters (dict[str, pint.Quantity]): The parameters for the problem.
            pv_name (str, optional): The name of the PV output. Defaults to "pv_output_full".
            pv_path (str, optional): The path to the PV data. Defaults to None.
        """
        #self.callbacks = callbacks
        super().__init__(experiment, parameters, pv_name, pv_path)
        if self.p["shortwave_radiation"]:
            self.initialize_incidence_data()
        
    def setup(self) -> None:
        """Sets up the TransientThermal problem."""

        self.time = 0.0
        self.V = df.fem.FunctionSpace(
            self.mesh, ("CG", self.p["degree"])
        )  # 2 for quadratic elements

        # Define variational problem
        self.u = ufl.TrialFunction(self.V)
        self.u_old = df.fem.Function(self.V)
        # Initialize u_old with p["initial_temperature"]
        self.initial_temperature = df.fem.Constant(self.mesh, np.float64(self.p["initial_temperature"]))     
        #with self.u_old.vector.localForm() as loc:
        #    loc.set(self.initial_temperature)
        
        self.v = ufl.TestFunction(self.V)
        self.theta = df.fem.Constant(self.mesh, np.float64(self.p["theta"]))
        self.idt = df.fem.Constant(self.mesh, np.float64(1.0 / self.p["dt"]))

        self.fields = SolutionFields(
            temperature=df.fem.Function(self.V, name="temperature")
        )
        self.q_fields = QuadratureFields(
            measure=ufl.dx,
            plot_space_type=("CG", self.p["degree"] - 1),
            #temperature=self.fields.temperature,
        )
        self.q_fields.temperature = self.fields.temperature,

        self.cp = df.fem.Constant(self.mesh, np.float64(self.p["heat_capacity"]))
        self.conductivity = df.fem.Constant(
            self.mesh, np.float64(self.p["conductivity"])
        )
        

        # TODO: The boundary conditions probably should be defined at the experiment level
        # Identify top surface for radiation
        min_y = min(vertex[1] for vertex in self.mesh.geometry.x)
        max_y = max(vertex[1] for vertex in self.mesh.geometry.x)
        max_x = max(vertex[0] for vertex in self.mesh.geometry.x)

        def top(x):
            return np.isclose(x[1], 0.0)

        def bottom(x):
            return np.isclose(x[1], max_y)
        
        def right(x):
            return np.isclose(x[0], max_x)
        
        def left(x):
            return np.isclose(x[0], 0.0)

        # Identify exposed surfaces for convection
        def exposed(x):
            return np.logical_and(
                np.logical_not(np.isclose(x[0], 0.0)),
                np.logical_not(np.isclose(x[0], max_x)),
            )

        # def adiabatic(x):
        #     return np.logical_and(np.isclose(x[0], 0.0), np.isclose(x[0], max_x))

        def adiabatic(x):
            return left(x)
        
        def convection(x):
            return np.logical_or(np.logical_or(top(x), bottom(x)), right(x))
        
        facet_indices, facet_markers = [], []
        fdim = self.mesh.topology.dim - 1
        if self.p["geometry"] == "gmsh":
            self.ds_experiment = ufl.Measure(
                "ds", domain=self.mesh, subdomain_data=self.experiment.facet_tags
            )
        else:
            facets_top = df.mesh.locate_entities(self.mesh, fdim, top)
            facets_bottom = df.mesh.locate_entities(self.mesh, fdim, convection)
            # facets_bottom = df.mesh.locate_entities(self.mesh, fdim, bottom)
            facet_indices.append(facets_top)
            facet_indices.append(facets_bottom)
            facet_markers.append(np.full_like(facets_top, 1))
            facet_markers.append(np.full_like(facets_bottom, 2))
            facets_adiabatic = df.mesh.locate_entities(self.mesh, fdim, adiabatic)
            facet_indices.append(facets_adiabatic)
            facet_markers.append(np.full_like(facets_adiabatic, 3))

            facet_indices = np.hstack(facet_indices).astype(np.int32)
            facet_markers = np.hstack(facet_markers).astype(np.int32)
            sorted_facets = np.argsort(facet_indices)
            facet_tags = df.mesh.meshtags(
                self.mesh,
                fdim,
                facet_indices[sorted_facets],
                facet_markers[sorted_facets],
            )

            self.ds = ufl.Measure("ds", domain=self.mesh, subdomain_data=facet_tags)
        # THIS PART MUST BE CHANGED FROM SCRATCH, problaly defined at experiment level somehow

        with self.fields.temperature.vector.localForm() as loc:
            loc.set(self.initial_temperature)

        F = (
            self.p["density"]
            * self.cp
            * self.idt
            * ufl.inner(self.u - self.u_old, self.v)
            * ufl.dx
            + self.conductivity
            * ufl.inner(
                ufl.grad(self.theta * self.u + (1 - self.theta) * self.u_old),
                ufl.grad(self.v),
            )
            * ufl.dx
        )
        if self.p["geometry"] == "gmsh":
            if self.p["shortwave_radiation"]:
                F -= self.calculate_shortwave_radiation_heat(
                    self.v, measure=self.ds_experiment(self.p["top_tag"])
                )
            if self.p["convection"]:
                F -= self.calculate_convection_heat(
                    self.u,
                    self.u_old,
                    self.v,
                    measure=(
                        self.ds_experiment(self.p["top_tag"])
                        + self.ds_experiment(self.p["bottom_tag"])
                        + self.ds_experiment(self.p["external_tag"])
                    ),
                )
            if self.p["wind_forced_convection"]:
                # F -= self.calculate_wind_convection_heat(
                #     self.u,
                #     self.u_old,
                #     self.v,
                #     measure=(
                #         self.ds_experiment(self.p["bottom_tag"])
                #     ),
                # )
                # if not self.p["convection"]:
                #     F -= self.calculate_convection_heat(
                #         self.u,
                #         self.u_old,
                #         self.v,
                #         measure=(self.ds_experiment(self.p["external_tag"])),
                #     )
                # F -= self.calculate_wind_convection_heat(
                #     self.u,
                #     self.u_old,
                #     self.v,
                #     measure=(self.ds_experiment(self.p["top_tag"])),
                # )

                # Q = df.fem.FunctionSpace(self.mesh, ("DG", 0))
                self.wind_constant_function = df.fem.Function(self.V)
                fdim = self.mesh.topology.dim - 1
                top_facets = self.experiment.facet_tags.find(self.p["top_tag"])
                self.top_dofs = df.fem.locate_dofs_topological(self.V, fdim, top_facets)
                bottom_facets = self.experiment.facet_tags.find(self.p["bottom_tag"])
                self.bottom_dofs = df.fem.locate_dofs_topological(self.V, fdim, bottom_facets)
                hole_facets = self.experiment.facet_tags.find(self.p["hole_tag"])
                self.hole_dofs = df.fem.locate_dofs_topological(self.V, fdim, hole_facets)
                # top_geometry_entities = df.cpp.mesh.entities_to_geometry(self.mesh, fdim, self.experiment.facet_tags.find(self.p["top_tag"]), False)
                # bottom_geometry_entities = df.cpp.mesh.entities_to_geometry(self.mesh, fdim, self.experiment.facet_tags.find(self.p["bottom_tag"]), False)
                self.wind_constant_function.x.array[self.top_dofs] = self.p["wind_forced_convection_parameter_constant_top"]
                self.wind_constant_function.x.array[self.bottom_dofs] = self.p["wind_forced_convection_parameter_constant_bottom"]

                F -= self.calculate_wind_convection_heat(
                    self.u,
                    self.u_old,
                    self.v,
                    measure=(
                        self.ds_experiment(self.p["top_tag"])
                        + self.ds_experiment(self.p["bottom_tag"])
                        + self.ds_experiment(self.p["external_tag"])
                        # self.ds_experiment(self.p["hole_tag"])
                    ),
                )
                F -= self.calculate_convection_heat_hole(
                    self.u,
                    self.u_old,
                    self.v,
                    measure=(
                        self.ds_experiment(self.p["hole_tag"])
                    ),
                )
                # F_1 = self.calculate_wind_convection_heat_top(
                #     self.u,
                #     self.u_old,
                #     self.v,
                #     measure=(
                #         self.ds_experiment(self.p["top_tag"])
                #     ),
                # )
                # F_2 = self.calculate_wind_convection_heat_bottom(
                #     self.u,
                #     self.u_old,
                #     self.v,
                #     measure=(
                #         self.ds_experiment(self.p["bottom_tag"])
                #         + self.ds_experiment(self.p["external_tag"])
                #     ),
                # )
                # F = F - F_1 - F_2
            if self.p["longwave_radiation"]:  # Not available for a linear solver
                F -= self.calculate_longwave_radiation_heat(
                    self.u,
                    self.v,
                    measure=(
                        self.ds_experiment(self.p["top_tag"])
                        + self.ds_experiment(self.p["bottom_tag"])
                    ),
                )
            # Add adiabatic boundary condition
            # F -= self.add_adiabatic_boundary(
            #     self.v, measure=self.ds_experiment(self.p["end_tag"])
            # )
            # F -= self.add_adiabatic_boundary(
            #     self.v, measure=self.ds_experiment(self.p["hole_tag"])
            # )
        else:
            if self.p["shortwave_radiation"]:
                F -= self.calculate_shortwave_radiation_heat(self.v, measure=self.ds(1))
            if self.p["convection"]:
                F -= self.calculate_convection_heat(
                    self.u, self.u_old, self.v, measure=(self.ds(2) + self.ds(1))
                )
            if self.p["wind_forced_convection"]:
                F -= self.calculate_wind_convection_heat(
                    self.u, self.u_old, self.v, measure=(self.ds(2) + self.ds(1))
                )
            if self.p["longwave_radiation"]:  # Not available for a linear solver
                F -= self.calculate_longwave_radiation_heat(
                    self.u, self.v, measure=(self.ds(2) + self.ds(1))
                )
            # Add adiabatic boundary condition
            F -= self.add_adiabatic_boundary(self.v, measure=self.ds(3))

        self.F = F
        self.a = ufl.lhs(self.F)
        self.L = ufl.rhs(self.F)

        # Add dirichlet boundary condition
        bcs = [] 
        # bottom_dofs = df.fem.locate_dofs_geometrical(self.V, convection)
        # dirichlet_bc = df.fem.dirichletbc(value=ScalarType(1273.15), dofs=bottom_dofs, V=self.V)
        # bcs.append(dirichlet_bc)
        self.problem = df.fem.petsc.LinearProblem(
            self.a,
            self.L,
            bcs=bcs,
            u=self.fields.temperature,
            petsc_options={"ksp_type": "preonly", "pc_type": "lu"},
        )

    @staticmethod
    def parameter_description() -> dict[str, str]:
        """Returns a description dictionary for required parameters.

        Returns:
            dict[str, str]: The description dictionary.
        """
        description = {
            "g": "gravity",
            "dt": "time step",
            "density": "density of fresh concrete",
            "E": "Young's Modulus",
            "nu": "Poissons Ratio",
            "stress_state": "for 2D plain stress or plane strain",
            "degree": "Polynomial degree for the FEM model",
            "dt": "time step",
        }

        return description

    @classmethod
    def default_parameters(cls) -> tuple[Experiment, dict[str, pint.Quantity]]:
        """Returns a dictionary with required parameters and a set of working values as example.

        Returns:
            tuple[Experiment, dict[str, pint.Quantity]]: The default parameters.
        """
        # default setup for this material
        #experiment = CantileverBeam(CantileverBeam.default_parameters())
        experiment = ""

        model_parameters = {}
        model_parameters["g"] = 9.81 * ureg("m/s^2")
        model_parameters["dt"] = 1.0 * ureg("day")
        model_parameters["theta"] = 0 * ureg("")  # 0 for forward Euler, 0.5 for Crank-Nicolson, 1.0 for backward Euler
        model_parameters["initial_temperature"] = 282.0 * ureg("K")

        model_parameters["top_tag"] = 9 * ureg("")
        model_parameters["bottom_tag"] = 8 * ureg("")
        model_parameters["end_tag"] = 7 * ureg("")
        model_parameters["external_tag"] = 100 * ureg("")
        model_parameters["hole_tag"] = 2 * ureg("")

        model_parameters["conductivity"] = 1.5 * ureg("W/(m*K)")
        model_parameters["density"] = 2400.0 * ureg("kg/m^3")
        model_parameters["E"] = 210e9 * ureg("N/m^2")
        model_parameters["nu"] = 0.28 * ureg("")

        model_parameters["stress_state"] = "plane_strain" * ureg("")
        model_parameters["degree"] = 2 * ureg("")  # polynomial degree

        model_parameters["air_temperature"] = 293.0 * ureg("K")
        model_parameters["inner_temperature"] = 293.0 * ureg("K")
        model_parameters["latitude"] = 52.5 * ureg("deg")
        model_parameters["longitude"] = 13.4 * ureg("deg")
        model_parameters["name"] = "Berlin" * ureg("")
        model_parameters["altitude"] = 34.0 * ureg("m")
        model_parameters["time_zone"] = "'Etc/GMT-1'" * ureg("")
        model_parameters["timestamp"] = "2015-01-01 13:00:00+00:00" * ureg("")
        #model_parameters["convection"] = False
        model_parameters["convection"] = ureg.Quantity(0, "dimensionless") 
        model_parameters["convection_coefficient"] = 0.0 * ureg("W/(m^2*K)")
        #model_parameters["wind_forced_convection"] = True
        model_parameters["wind_forced_convection"] = ureg.Quantity(0, "dimensionless") 
        model_parameters["wind_forced_convection_parameter_constant"] = 1.0 * ureg("")
        model_parameters["wind_forced_convection_parameter_constant_top"] = 1.0 * ureg("")
        model_parameters["wind_forced_convection_parameter_constant_bottom"] = 1.0 * ureg("")
        model_parameters["wind_speed"] = 0.0 * ureg("m/s")
        model_parameters["characteristic_length"] = 1.0 * ureg("m")
        model_parameters["air_viscosity"] = 1.81e-5 * ureg("Pa*s")
        model_parameters["air_prandtl_number"] = 0.71 * ureg("")
        model_parameters["air_thermal_conductivity"] = 0.025 * ureg("W/(m*K)")
        #model_parameters["shortwave_radiation"] = False
        model_parameters["shortwave_radiation"] = ureg.Quantity(0, "dimensionless") 
        #model_parameters["calculate_shortwave_irradiation"] = True
        model_parameters["calculate_shortwave_irradiation"] = ureg.Quantity(0, "dimensionless") 
        model_parameters["shortwave_radiation_constant"] = 0.0 * ureg("")       ##TODO: 1.0 -> 0.1
        model_parameters["albedo"] = 0.275 * ureg("")
        model_parameters["shortwave_irradiation"] = 0.0 * ureg("W/m^2")
        #model_parameters["longwave_radiation"] = False
        model_parameters["longwave_radiation"] = ureg.Quantity(0, "dimensionless") 
        model_parameters["longwave_radiation_constant"] = 0.0 * ureg("")
        model_parameters["emissivity"] = 0.9 * ureg("")

        #model_parameters["plot_pv"] = False
        model_parameters["plot_pv"] = ureg.Quantity(0, "dimensionless") 
        
        model_parameters.update(cls.update_default_parameters())

        return experiment, model_parameters  
    
    ## TODO: Testing params!!
    @staticmethod
    def update_default_parameters():
        update_params = {
            "air_temperature": 1273.15 * ureg("K"),
            "initial_temperature": 273.15 * ureg("K"),
            "heat_capacity": 460.0 * ureg("J/(kg*K)"),
            "dt": 1.0 * ureg("s"),
            "theta": 1.0 * ureg(""),
            "density": 7850.0 * ureg("kg/m**3"),
            "conductivity": 52 * ureg("W/(m*K)"),
            #"convection": False,
            "convection": ureg.Quantity(1, "dimensionless"),
            "convection_coefficient": 10.0 * ureg("kg/K/s**3"),
            #"wind_forced_convection": False,
            #"wind_forced_convection": ureg.Quantity(1, "dimensionless") ,
            # "wind_forced_convection_parameter_constant_top": 1.0 * ureg(""),
            # "wind_forced_convection_parameter_constant_bottom": 1.0 * ureg(""),
            "wind_forced_convection_parameter_constant": 1.0 * ureg(""),
            "wind_speed": 5.0 * ureg("m/s"),
            #"shortwave_radiation": False,
            #"shortwave_radiation": ureg.Quantity(1, "dimensionless"),
            "shortwave_radiation_constant": 1.0  * ureg(""),
            "shortwave_irradiation": 0.0 * ureg("W/m**2"),
            #"calculate_shortwave_irradiation": False,
            "calculate_shortwave_irradiation": ureg.Quantity(1, "dimensionless"),
            #"longwave_radiation": False,
            #"longwave_radiation": ureg.Quantity(1, "dimensionless"),
            "longwave_radiation_constant": 1.0  * ureg(""),
            "timestamp": "2015-06-02 13:00:00+00:00" * ureg(""),
            "top_tag": 9 * ureg(""),
            "bottom_tag": 8 * ureg(""),
            "end_tag": 7 * ureg(""),
            "external_tag": 100 * ureg(""),
            "hole_tag": 2 * ureg(""),
            #"geometry": "box" * ureg(""),
            #"plot_pv": True,
            "plot_pv": ureg.Quantity(1, "dimensionless"),
        }
        
        return update_params

    def calculate_convection_heat(
        self,
        u: ufl.argument.Argument,
        u_old: ufl.argument.Argument,
        v: ufl.argument.Argument,
        measure: ufl.Measure,
    ) -> float:
        self.convection_coefficient = df.fem.Constant(
            self.mesh, np.float64(self.p["convection_coefficient"])
        )
        if "air_temperature" not in self.__dict__:
            self.air_temperature = df.fem.Function(self.V)
        self.air_temperature.x.array[:] = np.float64(self.p["air_temperature"])
        try:
            self.air_temperature.x.array[self.hole_dofs] = np.float64(self.p["inner_temperature"])
        except AttributeError:
            pass

        return (
            self.convection_coefficient
            # * self.p["dt"]
            * ufl.inner(
                self.air_temperature - (self.theta * u + (1 - self.theta) * u_old), v
            )
            * measure
        )
    def calculate_convection_heat_hole(
        self,
        u: ufl.argument.Argument,
        u_old: ufl.argument.Argument,
        v: ufl.argument.Argument,
        measure: ufl.Measure,
    ) -> float:
        self.convection_coefficient = df.fem.Constant(
            self.mesh, np.float64(self.p["convection_coefficient"])
        )
        if "air_temperature" not in self.__dict__:
            self.air_temperature = df.fem.Function(self.V)
        self.air_temperature.x.array[:] = np.float64(self.p["air_temperature"])
        self.air_temperature.x.array[self.hole_dofs] = np.float64(self.p["inner_temperature"])

        return (
            self.convection_coefficient
            # * self.p["dt"]
            * ufl.inner(
                self.air_temperature - (self.theta * u + (1 - self.theta) * u_old), v
            )
            * measure
        )

    def calculate_h_wind(self) -> float:
        reynolds = (
            self.p["wind_speed"]
            * self.p["characteristic_length"]
            / self.p["air_viscosity"]
        )
        nusselt = 0.037 * reynolds ** (4 / 5) * self.p["air_prandtl_number"] ** (1 / 3)
        h_wind = (
            nusselt
            * self.p["air_thermal_conductivity"]
            / self.p["characteristic_length"]
        )

        return h_wind

    def calculate_wind_convection_heat(
        self,
        u: ufl.argument.Argument,
        u_old: ufl.argument.Argument,
        v: ufl.argument.Argument,
        measure: ufl.Measure,
    ) -> float:
        h_wind = self.calculate_h_wind()

        self.wind_forced_convection_parameter_constant = df.fem.Constant(
            self.mesh, np.float64(self.p["wind_forced_convection_parameter_constant"])
        )
        
        
        
        # self.air_temperature = df.fem.Constant(
        #     self.mesh, np.float64(self.p["air_temperature"])
        # )
        if "air_temperature" not in self.__dict__:
            self.air_temperature = df.fem.Function(self.V)
        self.air_temperature.x.array[:] = np.float64(self.p["air_temperature"])
        self.air_temperature.x.array[self.hole_dofs] = np.float64(self.p["inner_temperature"])
        if "h_wind" not in self.__dict__:
            self.h_wind = df.fem.Constant(self.mesh, np.float64(h_wind))
        else:
            self.h_wind.value = np.float64(h_wind)

        return (
            self.wind_forced_convection_parameter_constant
            # self.wind_constant_function
            * self.h_wind
            # * self.p["dt"]
            * ufl.inner(
                self.air_temperature - (self.theta * u + (1 - self.theta) * u_old), v
            )
            * measure
        )
    
    def initialize_incidence_data(self):
        weather_tmy = pvlib.iotools.get_pvgis_tmy(
            math.degrees(self.p["latitude"]), math.degrees(self.p["longitude"])
        )[0]
        self.weather_tmy = weather_tmy.groupby(
            [weather_tmy.index.month, weather_tmy.index.day, weather_tmy.index.hour]
        ).mean()
        self.weather_tmy.index.name = "utc_time"

    def calculate_total_irradiance_pvlib(self) -> pd.DataFrame:
        if "weather_tmy" not in self.__dict__:
            self.initialize_incidence_data()

        system = {"surface_azimuth": 180, "surface_tilt": self.p["latitude"]}
        given_date_time = pd.to_datetime(self.p["timestamp"], utc=True)

        # Find the row with the nearest timestamp
        # Create a list of tuples representing the absolute difference
        absolute_differences = [
            (
                index[0] - given_date_time.month,
                index[1] - given_date_time.day,
                index[2] - given_date_time.hour,
            )
            for index in self.weather_tmy.index
        ]

        # Calculate the absolute values for each tuple
        absolute_differences_abs = [
            abs(diff[0]) + abs(diff[1]) + abs(diff[2]) for diff in absolute_differences
        ]

        # Find the index of the closest row
        closest_row_index = pd.Series(absolute_differences_abs).idxmin()

        # Retrieve the closest row from the grouped DataFrame
        weather = self.weather_tmy.iloc[closest_row_index]
        solpos = pvlib.solarposition.get_solarposition(
            time=given_date_time,
            latitude=self.p["latitude"],
            longitude=self.p["longitude"],
            altitude=self.p["altitude"],
            temperature=weather["temp_air"],
            pressure=pvlib.atmosphere.alt2pres(self.p["altitude"]),
        )
        dni_extra = pvlib.irradiance.get_extra_radiation(given_date_time)
        total_irradiance_df = pvlib.irradiance.get_total_irradiance(
            system["surface_tilt"],
            system["surface_azimuth"],
            solpos["apparent_zenith"],
            solpos["azimuth"],
            weather["dni"],
            weather["ghi"],
            weather["dhi"],
            dni_extra=dni_extra,
            model="haydavies",
            albedo=self.p["albedo"],
        )
        return total_irradiance_df

    def calculate_shortwave_radiation_heat(
        self, v: ufl.argument.Argument, measure: ufl.Measure
    ) -> float:
        self.shortwave_radiation_constant = df.fem.Constant(
            self.mesh, np.float64(self.p["shortwave_radiation_constant"])
        )
        try:
            self.shortwave_irradiation = self.shortwave_irradiation_new
        except AttributeError:
            self.shortwave_irradiation = df.fem.Constant(self.mesh, np.float64(0.0))

        if self.p["calculate_shortwave_irradiation"]:
            total_irradiance_df = self.calculate_total_irradiance_pvlib()
            self.shortwave_irradiation_new = df.fem.Constant(
                self.mesh, np.float64(total_irradiance_df["poa_global"].values[0])
            )
        else:
            self.shortwave_irradiation_new = df.fem.Constant(
                self.mesh,
                np.float64(self.p["albedo"] * self.p["shortwave_irradiation"]),
            )
        return (
            self.shortwave_radiation_constant
            # * self.p["dt"]
            * ufl.inner(
                self.theta * self.shortwave_irradiation
                + (1 - self.theta) * self.shortwave_irradiation_new,
                v,
            )
            * measure
        )

    def calculate_longwave_radiation_heat(
        self, u: ufl.argument.Argument, v: ufl.argument.Argument, measure: ufl.Measure
    ) -> float:
        # boltzman_constant = 5.67e-8 * ureg("W/(m^2*K^4)")
        # return self.p["longwave_radiation_constant"] *self.p["emissivity"]*boltzman_constant.magnitude* (self.p["air_temperature"]**4-u**4) * v *measure
        raise NotImplementedError(
            "Longwave radiation is not available for a linear solver."
        )

    def add_adiabatic_boundary(
        self, v: ufl.argument.Argument, measure: ufl.Measure
    ) -> float:
        return 0.0 * v * measure

    def solve(self) -> None:
        self.update_time()
        self.logger.info(f"solving t={self.time}")

        self.problem.solve()

        self.u_old.vector[:] = self.fields.temperature.vector

        # TODO Defined as abstractmethod. Should it depend on sensor instead of material?
        self.compute_residuals()

        # get sensor data
        for sensor_name, sensor_type in self.sensors.items():
            # go through all sensors and measure
            if isinstance(sensor_type, TemperatureSensor):
                sensor_type.measure(self)

        if self.p["plot_pv"]:
            self.pv_plot()

    def update_time(self) -> None:
        self.time += self.p["dt"]
        self.idt.value = np.float64(1.0 / self.p["dt"])

    def update_parameters(self, parameters: dict[str, pint.Quantity]) -> None:
        # self.parameters.update(parameters)
        # self.p = self.parameters.to_magnitude()
        self.p.update(parameters)
        self.experiment.p = self.p
        self.cp.value = np.float64(self.p["heat_capacity"])
        if "diffusivity" in self.p.keys():
            self.conductivity.value = np.float64(self.p["heat_capacity"]*self.p["diffusivity"]*self.p["density"])
        self.initial_temperature.value = np.float64(self.p["initial_temperature"])
        if "sensor_location_u" in self.p.keys():
            self.sensors["Sensor_u"].where[1] = self.p["sensor_location_u"]
        if "sensor_location_o" in self.p.keys():
            self.sensors["Sensor_o"].where[1] = self.p["sensor_location_o"]
        if "sensor_location_n" in self.p.keys():
            self.sensors["Sensor_n"].where[0] = self.p["sensor_location_n"]
        if "sensor_location_s" in self.p.keys():
            self.sensors["Sensor_s"].where[0] = self.p["sensor_location_s"]
        if self.p["convection"]:
            self.convection_coefficient.value = np.float64(
                self.p["convection_coefficient"]
            )
            if "air_temperature" not in self.__dict__:
                self.air_temperature = df.fem.Function(self.V)
            self.air_temperature.x.array[:] = np.float64(self.p["air_temperature"])
            try:
                self.air_temperature.x.array[self.hole_dofs] = np.float64(self.p["inner_temperature"])
            except AttributeError:
                pass
        if self.p["wind_forced_convection"]:
            self.wind_forced_convection_parameter_constant.value = np.float64(
                self.p["wind_forced_convection_parameter_constant"]
            )
            # self.wind_constant_function.x.array[self.top_dofs] = self.p["wind_forced_convection_parameter_constant_top"]
            # self.wind_constant_function.x.array[self.bottom_dofs] = self.p["wind_forced_convection_parameter_constant_bottom"]
            # self.air_temperature.value = np.float64(self.p["air_temperature"])
            if "air_temperature" not in self.__dict__:
                self.air_temperature = df.fem.Function(self.V)
            self.air_temperature.x.array[:] = np.float64(self.p["air_temperature"])
            self.air_temperature.x.array[self.hole_dofs] = np.float64(self.p["inner_temperature"])
            self.h_wind.value = np.float64(self.calculate_h_wind())
            # self.h_wind.value = np.float64(10.0)
            # self.h_wind_top.value = np.float64(self.calculate_h_wind())
            # self.h_wind_bottom.value = np.float64(self.calculate_h_wind())

        if self.p["shortwave_radiation"]:
            self.shortwave_radiation_constant.value = np.float64(
                self.p["shortwave_radiation_constant"]
            )
            if self.p["calculate_shortwave_irradiation"]:
                self.shortwave_irradiation.value = np.float64(
                    self.calculate_total_irradiance_pvlib()["poa_global"].values[0]
                )
            else:
                self.shortwave_irradiation.value = np.float64(
                    self.p["albedo"] * self.p["shortwave_irradiation"]
                )

    def reset_fields(self) -> None:

        with self.fields.temperature.vector.localForm() as loc:
            loc.set(self.initial_temperature)

        self.u_old.vector[:] = self.fields.temperature.vector
        self.time = 0.0

    def reset_sensors(self) -> None:

        for sensor in self.sensors.values():
            sensor.data = []
        
    def compute_residuals(self) -> None:
        self.residual = ufl.action(self.a, self.fields.temperature) - self.L

    # paraview output
    # TODO move this to sensor definition!?!?!
    def pv_plot(self) -> None:

            with df.io.XDMFFile(self.mesh.comm, self.pv_output_file, "a") as f:
                f.write_function(self.fields.temperature, self.time)

    def assign_full_field_values(self, field_name: str, values: list[list[float]], burn:int) -> None:
        """
        Assign full field vector values to function for all timesteps.

        Args:
            field_name (str): The name of the field.
            values (list[list[float]]): List of list of nodal values for each timestep.
        """

        # Create the function field
        field = df.fem.Function(self.V, name=field_name)

        # Assign values to the function field for each timestep and plot to Paraview
        for i, timestep_values in enumerate(values):
            field.vector[:] = timestep_values
            with df.io.XDMFFile(self.mesh.comm, self.pv_output_file, "a") as f:
                f.write_function(field, (i+burn+2) * self.p["dt"])

    def update_and_solve(
        self,
        **kwargs
    ) -> float:
        
        self.update_parameters(kwargs)
        self.solve()

        # return np.array(self.sensors["Sensor_1"].data)[-1]-273.15
    
    @staticmethod
    def wrapper_salib(X, func=update_and_solve):
        """
        Wrapper function for SALib analysis. Evaluates the given function for each row in the input array X.

        Parameters:
        -----------
        X : numpy.ndarray
            Input array of shape (N, D) where N is the number of samples and D is the number of parameters.
        func : callable
            Function to be evaluated for each row in X. The function should take D arguments.

        Returns:
        --------
        numpy.ndarray
            Array of shape (N,) containing the results of evaluating func for each row in X.
        """
        N, D = X.shape
        results = np.empty(N)
        for i in range(N):
            temp_const, wind_const, zenith_constant, azimuth_constant, elevation_constant = X[i, :]
            results[i] = func(temp_const, wind_const, zenith_constant, azimuth_constant, elevation_constant)

        return results