import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pyvista as pv
import os
import pandas as pd

from nibelungenbruecke.scripts.digital_twin_orchestrator.digital_twin import DigitalTwin
from nibelungenbruecke.scripts.utilities.mesh_point_detector import query_point

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

        self.default_parameters = self.default_parameters()
        self.model_parameters_path = self.default_parameters['model_parameter_path']
        
        self.digital_twin_model = self._digital_twin_initializer()
        self.plot_virtual_sensors = {}
        self.plot_model_typ = ""
        self.UQ_flag = False
        
    
    def assign_model_name(self):
        self.model_to_run = self.simulation_parameters["model"]
        
        if self.simulation_parameters["uncertainty_quantification"]:
           self.UQ_flag = True
        else:
            self.UQ_flag = False
    
        return self.model_to_run
            
        
    def _digital_twin_initializer(self):
        """
       Initializes the digital twin model.
       
       Returns:
           DigitalTwin: An instance of the DigitalTwin class initialized with the given parameters.
       
        """
        return DigitalTwin(self.model_parameters_path, self.model_to_run)
        
    def predict_dt(self, digital_twin, model_to_run, api_key):   ##TODO: Input parameters to be deleted!!
        """
        Runs "prediction" method of specified digital twin object.
        
        Args:
            digital_twin (DigitalTwin): The digital twin model instance.
            input_value : The input data for prediction.
            model_to_run (str): Specifies which predefined model to execute.
        
        """
        return digital_twin.predict(model_to_run, api_key, self.simulation_parameters, self.UQ_flag)
    
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
    

    def default_parameters(self):

        return {
            'model_parameter_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json',
            'thermal_h5py_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_thermal.h5',
            'thermal_xmdf_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_thermal.xmdf',
            'displacement_h5py_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_displacement.h5',
            'displacement_xmdf_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_displacement.xmdf',
                }
    

    def compare(self, output, input_value):
        self.updated = (output == 2 * input_value)
        
    def set_api_key(self, key):
        self.api_key = key

    def load(self, simulation_parameters):
        """
        Validates simulation parameters by checking if virtual sensor positions lie within the mesh domain.

        Args:
            simulation_parameters (dict): The simulation parameters including virtual sensor positions.

        Raises:
            ValueError: If any virtual sensor lies outside the mesh domain.
        """
        
        model = simulation_parameters.get('model')
        if model == 'TransientThermal_1':       # TODO: Should be same model probably!
            path = self.default_parameters['thermal_h5py_path']
        elif model == 'displacement_1':
            path = self.default_parameters['displacement_h5py_path']
        else:
            raise ValueError(f"Unsupported model type: {model}")

        with h5py.File(path, 'r') as f:
            geometry = f['/Mesh/mesh/geometry'][:]

        for sensor in simulation_parameters.get('virtual_sensor_positions', []):
            coords = np.array([sensor['x'], sensor['y'], sensor['z']])

            distances = np.linalg.norm(geometry - coords, axis=1)
            min_dist = np.min(distances)


            threshold = 1.29  ##TODO: Maximum element size is 1.283 m. Outer virtual sensors that are below that treshold considered in the domain!!

            if min_dist > threshold:
                raise ValueError(
                    f"Virtual sensor '{sensor['name']}' at {coords.tolist()} "
                    f"is outside the mesh domain (nearest node distance: {min_dist:.6f} m)."
                )

        print("All virtual sensors are within the mesh domain.\n")
       

    def run(self, simulation_parameters=None):
        """
        Runs the digital twin model prediction.
        
        TODO:
        - Implement conditional execution based on prediction type.
        - Support more flexible input types.
        
        Args:
            input_value : The input data for prediction.
            model_to_run (str): Specifies which predefined model to execute.
        
        """

        if simulation_parameters is not None:
            self.simulation_parameters = simulation_parameters
            self.model_to_run = self.assign_model_name()
          
        self.prediction = self.predict_dt(self.digital_twin_model, self.model_to_run, self.api_key)
        
        if not self.prediction:
            pass
        
        else:
            self.plot_virtual_sensors = self.extract_virtual_sensor_data()
        

    def extract_virtual_sensor_data(self):
        output_file = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/sensor_timeseries.json"

        sensors = self.digital_twin_model.initial_model.problem.sensors
        self.sensor_data_json = {}

        for sensor_name, sensor in sensors.items():
            times = sensor.time
            data = sensor.data

            if len(times) != len(data):
                print(f"Skipping sensor '{sensor_name}' due to mismatched time and data lengths.")
                continue

            paired_data = [
                {"time": t, "value": float(d[0]) if isinstance(d, np.ndarray) else float(d)}
                for t, d in zip(times, data)
            ]
            self.sensor_data_json[sensor_name] = paired_data

        with open(output_file, "w") as f:
            json.dump(self.sensor_data_json, f, indent=2)

        return self.sensor_data_json

    def plot_virtual_sensor_data(self):
        
        sensors = self.digital_twin_model.initial_model.problem.sensors

        for sensor_name, sensor in sensors.items():
            if "Sensor_" in sensor_name:
                times = sensor.time
                data = sensor.data
    
                if len(times) != len(data):
                    print(f"Skipping sensor '{sensor_name}' due to mismatched time and data lengths.")
                    continue
    
                # Flatten data points
                values = [float(d[0]) if isinstance(d, np.ndarray) else float(d) for d in data]
    
                # Plot
                plt.figure(figsize=(10, 4))
                plt.plot(times, values, linestyle='-', color='tab:blue')
                plt.title(f"Sensor: {sensor_name}")
                plt.xlabel("Time (s)")
                plt.ylabel("Sensor Value")
                plt.grid(True)
                plt.tight_layout()
                plt.show()
            
    ##TODO: 
        
    def plot_full_field_response(self, full_field=True):
        # '''
        # currently returns the simulation result paths
        # '''
        # if full_field:
            
        #     model_type = self.simulation_parameters["model"]

        #     # Set file paths based on model type
        #     if "Displacement" in model_type:
        #         path_h5 = self.default_parameters["displacement_h5py_path"]
        #         field_name = "displacement"
        #         timestep = "600"  # Can be dynamic or user-defined
        #     elif "Thermal" in model_type:
        #         path_h5 = self.default_parameters["thermal_h5py_path"]
        #         field_name = "temperature"
        #         timestep = "748200"  # Can be dynamic or user-defined
        #     else:
        #         raise ValueError("Unsupported model type.")
        
        #     # Open HDF5 file and extract mesh
        #     with h5py.File(path_h5, "r") as h5:
        #         points = h5["/Mesh/mesh/geometry"][:]       # (N, 3)
        #         cells = h5["/Mesh/mesh/topology"][:]        # (M, 4)
        #         n_cells = cells.shape[0]
        #         cell_data = np.hstack([np.full((n_cells, 1), 4), cells]).flatten()
        #         grid = pv.UnstructuredGrid(cell_data, np.full(n_cells, pv.CellType.TETRA), points)
        
        #         # Load field
        #         field_path = f"/Function/{field_name}/{timestep}"
        #         if field_path not in h5:
        #             raise KeyError(f"{field_name.capitalize()} data at timestep {timestep} not found.")
        
        #         field_data = h5[field_path][:]
        
        #         # Determine scalar or vector field
        #         if field_data.shape[1] == 1:
        #             # Scalar field (e.g., temperature)
        #             grid.point_data[field_name] = field_data.ravel()
        #             plotter = pv.Plotter()
        #             plotter.add_mesh(grid, scalars=field_name, cmap="plasma", show_edges=False)
        #             plotter.add_scalar_bar(title=field_name.capitalize())
        #         elif field_data.shape[1] == 3:
        #             # Vector field (e.g., displacement)
        #             grid.point_data[field_name] = field_data
        #             warped = grid.warp_by_vector(field_name, factor=1.0)
        #             plotter = pv.Plotter()
        #             plotter.add_mesh(warped, show_edges=True)
        #         else:
        #             raise ValueError(f"Unsupported data shape for {field_name}: {field_data.shape}")
        
        #         plotter.show()
                

            model = self.simulation_parameters.get('model')
            
            if 'TransientThermal' in model:
                h5py_path = self.default_parameters['thermal_h5py_path']
                xmdf_path = self.default_parameters['thermal_xmdf_path']
                
                print(f"Path to full-field results:")
                print(f"TransientThermal-> h5py_path: {h5py_path}")
                print(f"TransientThermal -> xmdf_path: {xmdf_path}")
                
            elif 'displacement' in model:
                h5py_path = self.default_parameters['displacement_h5py_path']
                xmdf_path = self.default_parameters['displacement_xmdf_path']
                
                print(f"Path to full-field results:")
                print(f"Displacement-> h5py_path: {h5py_path}")
                print(f"Displacement -> xmdf_path: {xmdf_path}")


    def plot_real_sensor_vs_virtual_sensor(self):
        json_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/sensor_timeseries.json"

        # Try to load JSON data if not already in memory
        if not self.sensor_data_json:
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    self.sensor_data_json = json.load(f)
            else:
                print("No sensor data found. Please run export_sensor_data_to_json() first.")
                return
    
        # Add 273.15 to convert °C to K
        df = self.digital_twin_model.initial_model.api_dataFrame + 273.15
    
        # Get datetime range of measured data
        measured_start = df.index[0]
        measured_end = df.index[-1]
    
        # Mapping from df sensor names → sensor_data_json keys
        sensor_mapping = {
            "E_plus_040TU_HS--o-_Avg1": "Sensor_o",
            "E_plus_040TU_HSN-m-_Avg1": "Sensor_n",
            "E_plus_040TU_HSS-m-_Avg1": "Sensor_s",
            "E_plus_040TU_HS--u-_Avg1": "Sensor_u",  # Intentional reuse
        }
    
        for df_sensor_name, json_sensor_key in sensor_mapping.items():
            if json_sensor_key not in self.sensor_data_json:
                print(f"Sensor '{json_sensor_key}' not found in sensor_data_json.")
                continue
            if df_sensor_name not in df.columns:
                print(f"Sensor '{df_sensor_name}' not found in measured DataFrame.")
                continue
    
            # --- Measured data
            measured_times = df.index
            measured_values = df[df_sensor_name].values
    
            # --- Model data
            model_data = self.sensor_data_json[json_sensor_key]
            model_times_sec = np.array([entry["time"] for entry in model_data])
            model_values = np.array([entry["value"] for entry in model_data])
    
            if len(model_times_sec) < 2:
                print(f"Not enough model data for sensor '{json_sensor_key}' to interpolate.")
                continue
    
            # Normalize model time [0, 1]
            model_times_norm = (model_times_sec - model_times_sec[0]) / (model_times_sec[-1] - model_times_sec[0])
    
            # Rescale to datetime
            measured_range_seconds = (measured_end - measured_start).total_seconds()
            model_times_dt = [measured_start + pd.to_timedelta(t * measured_range_seconds, unit='s') for t in model_times_norm]
    
            # Interpolation
            model_seconds = [(t - measured_start).total_seconds() for t in model_times_dt]
            measured_seconds = [(t - measured_start).total_seconds() for t in measured_times]
            interp_model_values = np.interp(measured_seconds, model_seconds, model_values)
    
            # --- Plotting
            plt.figure(figsize=(10, 4))
            plt.plot(measured_times, measured_values, label=f"Measurement ({df_sensor_name})", alpha=0.8)
            plt.plot(measured_times, interp_model_values, label=f"Model ({json_sensor_key})", linestyle='--', markersize=3)
            plt.title(f"Sensor Comparison: {df_sensor_name} vs {json_sensor_key}")
            plt.xlabel("Time")
            plt.ylabel("Sensor Value (K)")
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()
            
            
        
            
                    
                
       #%%

if __name__ == "__main__":
    
    simulation_parameters = {       ##Throw an error checking UQ!!
        'simulation_name': 'TestSimulation',
        'model': 'TransientThermal_1',
        'start_time': '2023-08-11T08:00:00Z',
        'end_time': '2023-08-11T08:10:00Z',
        'time_step': '10min',
        'virtual_sensor_positions': [
        {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
        {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'},
        {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor3'},
        {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor4'}
    ],
        'plot_pv': False,
        'full_field_results': False, # Set to True if you want full field results, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': False, # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
    }


    orchestrator =  Orchestrator(simulation_parameters)
    #key = input("\nEnter the code to connect API: ").strip()
    #
    key = ""
    orchestrator.set_api_key(key)
    orchestrator.run(simulation_parameters)
    
    orchestrator.plot_virtual_sensor_data()
    
        
    orchestrator.plot_real_sensor_vs_virtual_sensor()

    ## 
    
    ##
    
    simulation_parameters = {       ##Throw an error checking UQ!!
        'simulation_name': 'TestSimulation',
        'model': 'TransientThermal_1',
        'start_time': '2023-08-11T08:00:00Z',
        'end_time': '2023-08-11T08:10:00Z',
        'time_step': '10min',
        'virtual_sensor_positions': [
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor1'},
            {'x': 1.0, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'}
            # Note: the real sensor positions are added automatically by the interface, so you don't need to specify them here.
        ],
        'plot_pv': False,
        'full_field_results': False, # Set to True if you want full field results, the simulation will take longer and the results will be larger.
        'uncertainty_quantification': True, # Set to True if you want uncertainty quantification, the simulation will take longer and the results will be larger.
    }


    #orchestrator =  Orchestrator(simulation_parameters)
    #key = input("\nEnter the code to connect API: ").strip()
    #orchestrator.set_api_key(key)
    orchestrator.run(simulation_parameters)
    
    orchestrator.plot_virtual_sensor_data()

    ## 

    virtual_sensor_positions = [
        {'x': 1.78, 'y': 0.0, 'z': 26.91, 'name': 'Sensor1'},
        {'x': -1.83, 'y': 0.0, 'z': 0.0, 'name': 'Sensor2'}
        # Note: the real sensor positions are added automatcally by the interface, so you don't need to specify them here.
    ]

    orchestrator.simulation_parameters["virtual_sensor_positions"] = virtual_sensor_positions


    orchestrator.plot_virtual_sensor_data()
    
        
    orchestrator.plot_real_sensor_vs_virtual_sensor()

    

    #orchestrator.run(simulation_parameters)