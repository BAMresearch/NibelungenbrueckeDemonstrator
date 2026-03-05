import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pyvista as pv
import os
import pandas as pd
import xml.etree.ElementTree as ET
import meshio
import dolfinx as df
from mpi4py import MPI
from petsc4py.PETSc import ScalarType
import warnings

from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin
from nibelungenbruecke.scripts.utilities.mesh_point_detector import query_point
from nibelungenbruecke.scripts.plotters.factory import *
from nibelungenbruecke.scripts.plotters.sensor_strategy import TemperatureStrategy, DisplacementStrategy

class Orchestrator:
    """
   Manages the workflow of the digital twin, transitioning from a linear, step-by-step approach 
   to a more dynamic, feedback-based system.

   This class initializes and orchestrates a digital twin model, enabling predictions and comparisons 
   based on input values.

   Attributes:
       model_parameters_path (str): Path to the model parameters dictionary.
       model_to_run (str): Specifies which predefined model to execute.
       updated (bool): Indicates whether the model has been updated based on comparisons.
       digital_twin_model (DigitalTwin): The initialized digital twin model instance.

    """

    def __init__(self, simulation_parameters):
        """
        Initializes the Orchestrator.

        Args:
            model_parameters_path (str): Path to the model parameters dictionary.
            model_to_run (str): Specifies which predefined model to execute. Defaults to "Displacement_1".

        """

        self.simulation_parameters = simulation_parameters
        self.model_to_run, _ = self.assign_model_name()
        
        self.model_parameters_path = self.default_model_parameters_path()
        
        self.digital_twin_model = self._digital_twin_initializer()
        # Build plotter sets for all supported sensor-type strategies.
        # Temperature plotters use bare keys (e.g. "plot_virtual_sensors");
        # displacement plotters use suffixed keys (e.g. "plot_virtual_sensors_displacement").
        self._plotters = PlotterFactory.create_all_plotters_for_strategies(
            problem=None,
            simulation_parameters=self.simulation_parameters,
            strategies=[TemperatureStrategy(), DisplacementStrategy()],
        )

    def assign_model_name(self):
        model_to_run = self.simulation_parameters["model"]
        self.UQ_flag_changed = False

        current_UQ_flag = bool(self.simulation_parameters.get(
            "uncertainty_quantification", False))

        if not hasattr(self, "UQ_flag"):
            self.UQ_flag = current_UQ_flag
            self.previous_UQ_flag = None

        else:
            self.previous_UQ_flag = self.UQ_flag
            self.UQ_flag = current_UQ_flag

        if self.previous_UQ_flag != self.UQ_flag:
            self.UQ_flag_changed = True
            
        
        if hasattr(self, "geo_dim"):
            previous_geo_dim = self.geo_dim
            current_geo_dim = self.simulation_parameters["model_info"]["type"]
            
            if previous_geo_dim == current_geo_dim:
                dimension_change = False
                
            else:
                dimension_change = True
                self.geo_dim = self.simulation_parameters["model_info"]["type"]
                
        else:
            self.geo_dim = self.simulation_parameters["model_info"]["type"]
            dimension_change = True
            
            
        return model_to_run, dimension_change

    def _digital_twin_initializer(self):
        """
       Initializes the digital twin model.

       Returns:
           DigitalTwin: An instance of the DigitalTwin class initialized with the given parameters.

        """
        
        return DigitalTwin(self.model_parameters_path, self.model_to_run)

    def predict_dt(self, digital_twin, model_to_run, api_key, dimension_change_flag=None):
        """
        Runs "prediction" method of specified digital twin object.

        Args:
            digital_twin (DigitalTwin): The digital twin model instance.
            input_value : The input data for prediction.
            model_to_run (str): Specifies which predefined model to execute.

        """
        return digital_twin.predict(model_to_run, api_key, self.simulation_parameters, self.UQ_flag_changed, dimension_change_flag=dimension_change_flag)

    def predict_last_week(self, digital_twin, inputs):
        """
        Generates predictions for a series of inputs from the series of inputs of same data.

        Args:
            digital_twin (DigitalTwin): The digital twin model instance.
            inputs (list|dict): A list of input values for prediction.

        Returns:
            list: A list of predictions.
        """
        predictions = []
        for input_value in inputs:
            prediction = digital_twin.predict(input_value)
            if prediction is not None:
                predictions.append(prediction)
        return predictions

    def default_model_parameters_path(self):
        ##TODO: should hardcoded paths be removed/moved?
        ##TODO: Need for different JSONs for different cross sections?(Span, Pilot)
        path_dict = {
            '3D_model_parameter_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json',
            '2D_model_parameter_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters_2D.json',
            }
        
        try:
            for i in path_dict.keys():
                if self.simulation_parameters["model_info"]["type"] in i:
                    path = path_dict[i]
                    return path
                    
        except:
            return path_dict[path_dict.keys()[0]]

    def compare(self, output, input_value):
        self.updated = (output == 2 * input_value)

    def set_api_key(self, key):
        self.api_key = key

    def get_paraview_paths(self):
        """Return absolute paths for the XDMF/H5 output and the VTU conversion targets.

        The method should be called *after* :meth:`run` so that the model
        parameters have been fully populated.

        Returns
        -------
        dict with keys:
            ``h5_file``   – absolute path to the HDF5 companion file.
            ``xdmf_file`` – absolute path to the XDMF time-series file.
            ``vtu_dir``   – directory where converted VTU files should be written.
            ``pvd_file``  – path for the output PVD collection file.
        """
        model_params = self.digital_twin_model.initial_model.model_parameters
        pv_path = os.path.abspath(model_params["paraview_output_path"])
        pv_name = model_params["paraview_thermal_output_name"]
        return {
            "h5_file":   os.path.join(pv_path, pv_name + ".h5"),
            "xdmf_file": os.path.join(pv_path, pv_name + ".xdmf"),
            "vtu_dir":   os.path.join(pv_path, "vtu_series"),
            "pvd_file":  os.path.join(pv_path, "pv_output.pvd"),
        }

    def run(self, simulation_parameters=None):
        """
        Runs the digital twin model prediction.

        """
        dimension_change_flag = None
        if simulation_parameters is not None:
            self.simulation_parameters = simulation_parameters
            self.model_to_run, dimension_change_flag = self.assign_model_name()
            

            if dimension_change_flag:
                self.model_parameters_path = self.default_model_parameters_path()
                self.digital_twin_model.model_parameters_path = self.digital_twin_model.model_parameters_path
                self.digital_twin_model.orchestrator_parameters = self.digital_twin_model._extract_model_parameters(self.model_parameters_path)
                self.digital_twin_model._set_model(self.simulation_parameters)
                #self.digital_twin_model._set_model(self.simulation_parameters)
                            
        self.digital_twin_model.virtual_sensor_load(self.simulation_parameters)
        self.digital_twin_model.model_parameters_path = self.default_model_parameters_path()
        self.prediction = self.predict_dt(
            self.digital_twin_model, self.model_to_run, self.api_key, dimension_change_flag=dimension_change_flag)
        
        for plotter in self._plotters.values():
            plotter.set_attributes(
                problem=self.digital_twin_model.initial_model.problem,
                simulation_parameters=self.simulation_parameters,
                default_parameters={},
                api_data_frame=self.digital_twin_model.initial_model.api_dataFrame,
                all_sensors_combined=self.digital_twin_model.initial_model.all_sensor_plot_data,
                virtual_sensor_noise=self.digital_twin_model.noise_on_sensors,
            )
        
    def plot(self, plot_type: str, **kwargs):
        
        #database = self.digital_twin_model._request_environmental_parameters(self.simulation_parameters["start_time"], self.simulation_parameters["end_time"])
        
        # Base UQ keys; displacement variants follow the same _with_UQ naming convention
        # with the additional _displacement suffix, so we strip any strategy suffix
        # before checking the UQ constraint.
        _base_uq_keys = {
            "plot_all_sensors_together_with_UQ",
            "plot_real_vs_virtual_sensors_with_UQ",
            "plot_virtual_sensors_with_UQ",
            "plot_real_vs_virtual_sensors_together_with_UQ",
        }
        # Derive UQ status from the bare plot type name (strip known strategy suffixes).
        _known_suffixes = ("_displacement",)  # extend as new strategies are added
        _bare_plot_type = plot_type
        for _sfx in _known_suffixes:
            if _bare_plot_type.endswith(_sfx):
                _bare_plot_type = _bare_plot_type[: -len(_sfx)]
                break
        is_uq_plot = _bare_plot_type in _base_uq_keys

        if plot_type not in self._plotters:
            print(f"Unknown plot method '{plot_type}'. Skipping plotting.")
            return

        if self.simulation_parameters["uncertainty_quantification"] and plot_type != "plot_full_field_response":
            if not is_uq_plot:
                print(f"Plot method '{plot_type}' is not supported when uncertainty quantification is enabled.")
                return

        if not self.simulation_parameters["uncertainty_quantification"] and plot_type != "plot_full_field_response":
            if is_uq_plot:
                print(f"Plot method '{plot_type}' is not supported when uncertainty quantification is not enabled.")
                return

        self._plotters[plot_type].plot(**kwargs)
        

#def inner_outer_temp(inner_temp, outer):
#    
        

if __name__ == "__main__":
    
    API_password_path = "../../../../Old/API_request_password"


    with open(API_password_path, "r") as f:
        key = f.read().strip()
    
    
    # %%
    # orchestration initialization and Transient Thermal model without UQ - 2D
    # simulation_parameters = {
    #     'simulation_name': 'TestSimulation',
    #     'model': '2D_TransientThermal_1',
    #     'model_info': {
    #         'type': '2D', 
    #         'path': 'Span'
    #         },
    #     'start_time': '2024-04-11T08:00:00Z',
    #     'end_time': '2024-05-14T16:10:00Z',
    #     'time_step': '750min',
    #     'virtual_sensor_positions': [
    #         {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
    #         {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
    #         {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
    #         {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
    #         {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
    #         {'x': -1.25, 'y': -0.2, 'z': 0.0, 'name': 'Sensor6'},
    #     ],
    #     'plot_pv': True,
    #     # Set to True if you want full field results, the simulation will take longer and the results will be larger
    #     'full_field_results': True,
    #     # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
    #     'uncertainty_quantification': False,
    # }

    # orchestrator = Orchestrator(simulation_parameters)
    # #key = input("\nEnter the code to connect API: ").strip()

    # # key = ""
    # orchestrator.set_api_key(key)
    # orchestrator.run()

    # orchestrator.plot("plot_real_vs_virtual_sensors_together")
    # orchestrator.plot("plot_all_sensors_together")
    # orchestrator.plot("plot_virtual_sensors")
    # orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    # orchestrator.plot("plot_real_vs_virtual_sensors")
    # orchestrator.plot("plot_full_field_response")       ##TODO: to be modified!!
    
    # # %%
    # # Transient Thermal model with UQ - 2D
    # simulation_parameters = {
    #     'simulation_name': 'TestSimulation',
    #     'model': '2D_TransientThermal_1',        
    #     'model_info': {
    #                 'type': '2D', 
    #                 'path': 'Span'
    #                 },
    #     'start_time': '2023-08-11T08:00:00Z',
    #     'end_time': '2023-09-11T16:10:00Z',
    #     'time_step': '700min',
    #     'virtual_sensor_positions': [
    #         {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
    #         {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
    #         {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
    #         {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
    #         {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
    #         {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

    #     ],
    #     'plot_pv': False,
    #     # Set to True if you want full field results, the simulation will take longer and the results will be larger
    #     'full_field_results': True,
    #     # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
    #     'uncertainty_quantification': True,
    # }

    # orchestrator.run(simulation_parameters)

    # orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    # orchestrator.plot("plot_all_sensors_together_with_UQ")
    # orchestrator.plot("plot_virtual_sensors_with_UQ")
    # orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    # orchestrator.plot("plot_full_field_response")


    #%%
    # # %%
    # orchestration initialization and Transient Thermal model without UQ - 2D

    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '2D_TransientThermal_1',
        'model_info': {
            'type': '2D', 
            'path': 'Pilot'
            },
        'data_source': 'OpenMeteo', # or 'MKP'
        'start_time': '2024-04-11T08:00:00Z',
        'end_time': '2024-05-14T16:10:00Z',
        'time_step': '20min',
        'virtual_sensor_positions': [
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1', 'bias': 0.02},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2', 'bias': 0.01},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
            {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
            {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

        ],
        'plot_pv': True,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': True,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': False,
    }

    orchestrator = Orchestrator(simulation_parameters)
    #key = input("\nEnter the code to connect API: ").strip()

    # key = ""
    orchestrator.set_api_key(key)  
    orchestrator.run()

    orchestrator.plot("plot_real_vs_virtual_sensors_together")
    orchestrator.plot("plot_all_sensors_together")
    orchestrator.plot("plot_virtual_sensors")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors")
    orchestrator.plot("plot_full_field_response")       ##TODO: to be modified!!
    
    #%%
    # # %%
    # orchestration initialization and Transient Thermal model without UQ - 2D
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '2D_TransientThermal_1',
        'model_info': {
            'type': '2D', 
            'path': 'Pilot'
            },
        'data_source': 'MKP', # or 'OpenMeteo'
        'start_time': '2024-04-11T08:00:00Z',
        'end_time': '2024-05-14T16:10:00Z',
        'time_step': '750min',
        'virtual_sensor_positions': [
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1', 'bias': 0.02},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2', 'bias': 0.01},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
            {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
            {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

        ],
        'plot_pv': True,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': True,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': False,
    }

    orchestrator = Orchestrator(simulation_parameters)
    #key = input("\nEnter the code to connect API: ").strip()

    # key = ""
    orchestrator.set_api_key(key)
    orchestrator.run()

    orchestrator.plot("plot_real_vs_virtual_sensors_together")
    orchestrator.plot("plot_all_sensors_together")
    orchestrator.plot("plot_virtual_sensors")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors")
    orchestrator.plot("plot_full_field_response")  

    # %%
    # Transient Thermal model with UQ - 2D
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '2D_TransientThermal_1',        
        'model_info': {
                    'type': '2D', 
                    'path': 'Pilot'
                    },
        'data_source': 'MKP', # or 'OpenMeteo'
        'start_time': '2023-08-11T08:00:00Z',
        'end_time': '2023-09-11T16:10:00Z',
        'time_step': '400min',
        'virtual_sensor_positions': [
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
            {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
            {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

        ],
        'plot_pv': False,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': True,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': True,
    }

    orchestrator.run(simulation_parameters)

    orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    orchestrator.plot("plot_all_sensors_together_with_UQ")
    orchestrator.plot("plot_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_full_field_response")

    
    # %%
    # Transient Thermal model with UQ - 2D
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '2D_TransientThermal_1',        
        'model_info': {
                    'type': '2D', 
                    'path': 'Pilot'
                    },
        'data_source': 'OpenMeteo', # or 'MKP'
        'start_time': '2023-08-11T08:00:00Z',
        'end_time': '2023-09-11T16:10:00Z',
        'time_step': '400min',
        'virtual_sensor_positions': [
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
            {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
            {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

        ],
        'plot_pv': False,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': True,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': True,
    }

    orchestrator.run(simulation_parameters)

    orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    orchestrator.plot("plot_all_sensors_together_with_UQ")
    orchestrator.plot("plot_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_full_field_response")


    # %%
    # orchestration initialization and Transient Thermal model with UQ - s
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '3D_TransientThermal_1',
        'model_info': {
                    'type': '3D', 
                    'path': ''
                    },
        'data_source': 'OpenMeteo', # or 'MKP'
        'start_time': '2023-08-11T08:00:00Z',
        'end_time': '2023-09-13T08:10:00Z',
        'time_step': '250min',
        'virtual_sensor_positions': [
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
            {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
            {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

        ],
        'plot_pv': False,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': True,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': True,
    }
    
    orchestrator.run(simulation_parameters)

    orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    orchestrator.plot("plot_all_sensors_together_with_UQ")
    orchestrator.plot("plot_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_full_field_response")

    # %%
    # orchestration initialization and Transient Thermal model without UQ - 3D
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '3D_TransientThermal_1',
        'model_info': {
                    'type': '3D', 
                    'path': ''
                    },
        'data_source': 'OpenMeteo', # or 'MKP'
        'start_time': '2023-08-11T08:00:00Z',
        'end_time': '2023-09-13T08:10:00Z',
        'time_step': '250min',
        'virtual_sensor_positions': [
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
            {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
            {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

        ],
        'plot_pv': True,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': True,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': False,
    }

    orchestrator.run(simulation_parameters)

    orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    orchestrator.plot("plot_all_sensors_together_with_UQ")
    orchestrator.plot("plot_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_full_field_response")
    
    #%%
    # %%
    # orchestration initialization and Transient Thermal model without UQ - 2D
    # Span
    # simulation_parameters = {
    #     'simulation_name': 'TestSimulation',
    #     'model': '2D_TransientThermal_1',
    #     'model_info': {
    #         'type': '2D', 
    #         'path': 'Span'
    #         },
    #     'start_time': '2024-04-11T08:00:00Z',
    #     'end_time': '2024-05-14T16:10:00Z',
    #     'time_step': '600min',
    #     'virtual_sensor_positions': [
    #         {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
    #         {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
    #         {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
    #         {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
    #         {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
    #         {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

    #     ],
    #     'plot_pv': True,
    #     # Set to True if you want full field results, the simulation will take longer and the results will be larger
    #     'full_field_results': True,
    #     # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
    #     'uncertainty_quantification': False,
    # }

    # orchestrator = Orchestrator(simulation_parameters)
    # key = input("\nEnter the code to connect API: ").strip()

    # # key = ""
    # orchestrator.set_api_key(key)
    # orchestrator.run()

    # orchestrator.plot("plot_real_vs_virtual_sensors_together")
    # orchestrator.plot("plot_all_sensors_together")
    # orchestrator.plot("plot_virtual_sensors")
    # orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    # orchestrator.plot("plot_real_vs_virtual_sensors")
    # orchestrator.plot("plot_full_field_response")       ##TODO: to be modified!!
    
    
    # # # %%
    # # # Transient Thermal model with UQ - 2D
    # simulation_parameters = {
    #     'simulation_name': 'TestSimulation',
    #     'model': '2D_TransientThermal_1',        
    #     'model_info': {
    #                 'type': '2D', 
    #                 'path': 'Span'
    #                 },
    #     'start_time': '2023-08-11T08:00:00Z',
    #     'end_time': '2023-09-11T16:10:00Z',
    #     'time_step': '700min',
    #     'virtual_sensor_positions': [
    #         {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
    #         {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
    #         {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
    #         {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
    #         {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
    #         {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

    #     ],
    #     'plot_pv': False,
    #     # Set to True if you want full field results, the simulation will take longer and the results will be larger
    #     'full_field_results': True,
    #     # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
    #     'uncertainty_quantification': True,
    # }

    # orchestrator.run(simulation_parameters)

    # orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    # orchestrator.plot("plot_all_sensors_together_with_UQ")
    # orchestrator.plot("plot_virtual_sensors_with_UQ")
    # orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    # orchestrator.plot("plot_full_field_response")

    # %%
    # orchestration initialization and Transient Thermal model without UQ
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '3D_TransientThermal_1',
        'model_info': {
                    'type': '3D', 
                    'path': ''
                    },
        'data_source': 'MKP', # or 'MKP'
        'start_time': '2023-08-11T08:00:00Z',
        'end_time': '2023-08-11T16:10:00Z',
        'time_step': '1min',
        'virtual_sensor_positions': [
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
            {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
            {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},

        ],
        'plot_pv': True,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': True,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': False,
    }

    orchestrator = Orchestrator(simulation_parameters)
    #key = input("\nEnter the code to connect API: ").strip()

    # key = ""
    orchestrator.set_api_key(key)
    orchestrator.run()

    orchestrator.plot("plot_all_sensors_together")
    orchestrator.plot("plot_virtual_sensors")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors")
    orchestrator.plot("plot_full_field_response")

    # %%
    # Transient thermal UQ with different time interval and sensor positions

    simulation_parameters = {  # Throw an error checking UQ!!
        'simulation_name': 'TestSimulation',
        'model': '3D_TransientThermal_1',
        'model_info': {
                    'type': '3D', 
                    'path': ''
                    },
        'data_source': 'MKP', # or 'MKP'
        'start_time': '2024-08-11T08:00:00Z',
        'end_time': '2024-09-13T02:10:00Z',
        'time_step': '200min',
        'virtual_sensor_positions': [
            {'x': -2, 'y': 0.0, 'z': 42.01, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'}
        ],
        'plot_pv': False,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': True,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': True,
    }

    orchestrator.run(simulation_parameters)
    orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    orchestrator.plot("plot_all_sensors_together_with_UQ")
    orchestrator.plot("plot_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors")
    orchestrator.plot("plot_full_field_response")

    # %%

# Transient thermal without UQ different time interval and sensor positions

    simulation_parameters = {  # Throw an error checking UQ!!
        'simulation_name': 'TestSimulation',
        'model': '3D_TransientThermal_1',
        'model_info': {
                    'type': '3D', 
                    'path': ''
                    },
        'data_source': 'MKP', # or 'MKP'
        'start_time': '2024-08-11T08:00:00Z',
        'end_time': '2024-08-25T02:10:00Z',
        'time_step': '10min',
        'virtual_sensor_positions': [
            {'x': -2, 'y': 0.0, 'z': 42.01, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'}
        ],
        'plot_pv': False,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': False,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': True,
    }

    orchestrator.run(simulation_parameters)
    
    orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    orchestrator.plot("plot_all_sensors_together_with_UQ")      ##TODO: ("plot_all_sensors_together")
    orchestrator.plot("plot_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_full_field_response")


    # %%

# Transient thermal without UQ different time interval and sensor positions

    simulation_parameters = {  # Throw an error checking UQ!!
        'simulation_name': 'TestSimulation',
        'model': '3D_TransientThermal_1',
        'model_info': {
                    'type': '3D', 
                    'path': ''
                    },
        'data_source': 'MKP', # or 'MKP'
        'start_time': '2024-08-11T08:00:00Z',
        'end_time': '2024-09-13T02:10:00Z',
        'time_step': '450min',
        'virtual_sensor_positions': [
            {'x': -2, 'y': 0.0, 'z': 42.01, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
            {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
            {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'}
        ],
        'plot_pv': False,
        # Set to True if you want full field results, the simulation will take longer and the results will be larger
        'full_field_results': False,
        # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': True,
    }

    orchestrator.run(simulation_parameters)
    
    orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
    orchestrator.plot("plot_all_sensors_together_with_UQ")
    orchestrator.plot("plot_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_full_field_response")