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
        self.model_to_run = self.assign_model_name()
        
        self.model_parameters_path = self.default_model_parameters_path()
        
        self.digital_twin_model = self._digital_twin_initializer()
        self._plotters = PlotterFactory.create_all_plotters(problem=None,simulation_parameters=self.simulation_parameters)

    def assign_model_name(self):
        self.model_to_run = self.simulation_parameters["model"]
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

        return self.model_to_run

    def _digital_twin_initializer(self):
        """
       Initializes the digital twin model.

       Returns:
           DigitalTwin: An instance of the DigitalTwin class initialized with the given parameters.

        """
        
        return DigitalTwin(self.model_parameters_path, self.model_to_run)

    def predict_dt(self, digital_twin, model_to_run, api_key):
        """
        Runs "prediction" method of specified digital twin object.

        Args:
            digital_twin (DigitalTwin): The digital twin model instance.
            input_value : The input data for prediction.
            model_to_run (str): Specifies which predefined model to execute.

        """
        return digital_twin.predict(model_to_run, api_key, self.simulation_parameters, self.UQ_flag_changed)

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

        path_dict = {
            '3D_model_parameter_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json',
            '2D_pilot_model_parameter_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters_2D.json',   
            }
        
        try:
            for i in path_dict.keys():
                if self.simulation_parameters["model_type"] in i:
                    path = path_dict[i]
                    return path
                    
        except:
            return path_dict[path_dict.keys()[0]]

    def compare(self, output, input_value):
        self.updated = (output == 2 * input_value)

    def set_api_key(self, key):
        self.api_key = key

    def run(self, simulation_parameters=None):
        """
        Runs the digital twin model prediction.

        """

        if simulation_parameters is not None:
            self.simulation_parameters = simulation_parameters
            self.model_to_run = self.assign_model_name()
        
        self.digital_twin_model.virtual_sensor_load(self.simulation_parameters)
        self.digital_twin_model.model_parameters_path = self.default_model_parameters_path()
        self.prediction = self.predict_dt(
            self.digital_twin_model, self.model_to_run, self.api_key)
        
        for plotter in self._plotters.values():
            plotter.set_attributes(
                problem = self.digital_twin_model.initial_model.problem,
                simulation_parameters=self.simulation_parameters, 
                default_parameters={}, api_data_frame=self.digital_twin_model.initial_model.api_dataFrame,
                all_sensors_combined=self.digital_twin_model.initial_model.all_sensor_plot_data
                )
        
    def plot(self, plot_type: str, **kwargs):
        plots_with_UQ = ["plot_all_sensors_together_with_UQ", "plot_real_vs_virtual_sensors_with_UQ", 
                         "plot_virtual_sensors_with_UQ", "plot_full_field_response", "plot_real_vs_virtual_sensors_together_with_UQ"]
        if plot_type not in self._plotters:
            #raise ValueError(f"Unknown plot type: {plot_type}")
            warnings.warn(f"Unknown plot type '{plot_type}'. Skipping plotting.")
            
        if self.simulation_parameters["uncertainty_quantification"]:
            if plot_type not in plots_with_UQ:
                #raise ValueError(f"Plot type '{plot_type}' is not supported when uncertainty quantification is enabled.")
                warnings.warn(f"Plot type '{plot_type}' is not supported when uncertainty quantification is enabled.")
                return
            
        if not self.simulation_parameters["uncertainty_quantification"]:
            if plot_type in plots_with_UQ:
                #raise ValueError(f"Plot type '{plot_type}' is not supported when uncertainty quantification is not enabled.")
                warnings.warn(f"Plot type '{plot_type}' is not supported when uncertainty quantification is not enabled.")
                return
            
        self._plotters[plot_type].plot(**kwargs)
        

if __name__ == "__main__":

    # %%
    # orchestration initialization and Transient Thermal model without UQ - 2D
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '2D_TransientThermal_1',
        'model_type': '2D',
        'start_time': '2024-04-11T08:00:00Z',
        'end_time': '2024-05-14T16:10:00Z',
        'time_step': '200min',
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
    key = input("\nEnter the code to connect API: ").strip()

    # key = ""
    orchestrator.set_api_key(key)
    orchestrator.run()

    orchestrator.plot("plot_real_vs_virtual_sensors_together")
    orchestrator.plot("plot_all_sensors_together")
    orchestrator.plot("plot_virtual_sensors")
    orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
    orchestrator.plot("plot_real_vs_virtual_sensors")
    orchestrator.plot("plot_full_field_response")       ##TODO: to be modified!!
    
    
    # %%
    # Transient Thermal model with UQ - 2D
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '2D_TransientThermal_1',
        'model_type': '2D',
        'start_time': '2023-08-11T08:00:00Z',
        'end_time': '2023-09-11T16:10:00Z',
        'time_step': '200min',
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
    # orchestration initialization and Transient Thermal model with UQ - 3D
    simulation_parameters = {
        'simulation_name': 'TestSimulation',
        'model': '3D_TransientThermal_1',
        'model_type': '3D',
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
        'model_type': '3D',
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
# =============================================================================
# 
#     # %%
#     # orchestration initialization and Transient Thermal model without UQ
#     # simulation_parameters = {
#     #     'simulation_name': 'TestSimulation',
#     #     'model': 'TransientThermal_1',
#     #     'model_type': '3D',
#     #     'start_time': '2023-08-11T08:00:00Z',
#     #     'end_time': '2023-08-11T16:10:00Z',
#     #     'time_step': '1min',
#     #     'virtual_sensor_positions': [
#     #         {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
#     #         {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
#     #         {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
#     #         {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'},
#     #         {'x': -73, 'y': 10.0, 'z': 230.0, 'name': 'Sensor5'},
#     #         {'x': -4.5, 'y': 10.0, 'z': 0.0, 'name': 'Sensor6'},
# 
#     #     ],
#     #     'plot_pv': True,
#     #     # Set to True if you want full field results, the simulation will take longer and the results will be larger
#     #     'full_field_results': True,
#     #     # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
#     #     'uncertainty_quantification': False,
#     # }
# 
#     # orchestrator = Orchestrator(simulation_parameters)
#     # key = input("\nEnter the code to connect API: ").strip()
# 
#     # # key = ""
#     # orchestrator.set_api_key(key)
#     # orchestrator.run()
# 
#     # orchestrator.plot("plot_all_sensors_together")
#     # orchestrator.plot("plot_virtual_sensors")
#     # orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
#     # orchestrator.plot("plot_real_vs_virtual_sensors")
#     # orchestrator.plot("plot_full_field_response")
# 
#     # %%
#     # Transient thermal UQ with different time interval and sensor positions
# 
#     simulation_parameters = {  # Throw an error checking UQ!!
#         'simulation_name': 'TestSimulation',
#         'model': 'TransientThermal_1',
#         'model_type': '3D',
#         'start_time': '2024-08-11T08:00:00Z',
#         'end_time': '2024-09-13T02:10:00Z',
#         'time_step': '200min',
#         'virtual_sensor_positions': [
#             {'x': -2, 'y': 0.0, 'z': 42.01, 'name': 'Sensor1'},
#             {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
#             {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
#             {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'}
#         ],
#         'plot_pv': False,
#         # Set to True if you want full field results, the simulation will take longer and the results will be larger
#         'full_field_results': True,
#         # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
#         'uncertainty_quantification': True,
#     }
# 
#     orchestrator.run(simulation_parameters)
#     orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
#     orchestrator.plot("plot_all_sensors_together_with_UQ")
#     orchestrator.plot("plot_virtual_sensors_with_UQ")
#     orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
#     orchestrator.plot("plot_real_vs_virtual_sensors")
#     orchestrator.plot("plot_full_field_response")
# 
#     # %%
# 
# # Transient thermal without UQ different time interval and sensor positions
# 
#     simulation_parameters = {  # Throw an error checking UQ!!
#         'simulation_name': 'TestSimulation',
#         'model': 'TransientThermal_1',
#         'model_type': '3D',
#         'start_time': '2024-08-11T08:00:00Z',
#         'end_time': '2024-08-25T02:10:00Z',
#         'time_step': '10min',
#         'virtual_sensor_positions': [
#             {'x': -2, 'y': 0.0, 'z': 42.01, 'name': 'Sensor1'},
#             {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
#             {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
#             {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'}
#         ],
#         'plot_pv': False,
#         # Set to True if you want full field results, the simulation will take longer and the results will be larger
#         'full_field_results': False,
#         # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
#         'uncertainty_quantification': True,
#     }
# 
#     orchestrator.run(simulation_parameters)
#     
#     orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
#     orchestrator.plot("plot_all_sensors_together_with_UQ")      ##TODO: ("plot_all_sensors_together")
#     orchestrator.plot("plot_virtual_sensors_with_UQ")
#     orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
#     orchestrator.plot("plot_full_field_response")
# 
# 
#     # %%
# 
# # Transient thermal without UQ different time interval and sensor positions
# 
#     simulation_parameters = {  # Throw an error checking UQ!!
#         'simulation_name': 'TestSimulation',
#         'model': 'TransientThermal_1',
#         'model_type': '3D',
#         'start_time': '2024-08-11T08:00:00Z',
#         'end_time': '2024-09-13T02:10:00Z',
#         'time_step': '450min',
#         'virtual_sensor_positions': [
#             {'x': -2, 'y': 0.0, 'z': 42.01, 'name': 'Sensor1'},
#             {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
#             {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
#             {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'}
#         ],
#         'plot_pv': False,
#         # Set to True if you want full field results, the simulation will take longer and the results will be larger
#         'full_field_results': False,
#         # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
#         'uncertainty_quantification': True,
#     }
# 
#     orchestrator.run(simulation_parameters)
#     
#     orchestrator.plot("plot_real_vs_virtual_sensors_together_with_UQ")
#     orchestrator.plot("plot_all_sensors_together_with_UQ")
#     orchestrator.plot("plot_virtual_sensors_with_UQ")
#     orchestrator.plot("plot_real_vs_virtual_sensors_with_UQ")
#     orchestrator.plot("plot_full_field_response")
# 
#     
# =============================================================================
