import json
import time
import pickle
import importlib
import numpy as np
import math

from datetime import datetime, timedelta
from tqdm import tqdm
from tqdm import trange
from copy import deepcopy
import dolfinx as df
import matplotlib.pyplot as plt
import pandas as pd

from fenicsxconcrete.util import ureg
#from fenicsxconcrete.finite_element_problem.thermomechanical_nibelungenbruecke_demonstrator import ThermoMechanicalNibelungenBrueckeProblem
from nibelungenbruecke.scripts.data_generation.thermomechanical_nibelungenbruecke_demonstrator import ThermoMechanicalNibelungenBrueckeProblem

from nibelungenbruecke.scripts.utilities.loaders import load_sensors
from nibelungenbruecke.scripts.utilities.offloaders import offload_sensors
from nibelungenbruecke.scripts.digital_twin_orchestrator.base_model import BaseModel
from nibelungenbruecke.scripts.data_generation.thermal_experiment import ThermalExperiment
from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request, MetadataSaver, Translator
from nibelungenbruecke.scripts.utilities.openmeteo_API import OpenMeteo


class ThermalModel(BaseModel):
    """
    A class representing a thermal model for NB simulations.
    
    """
    
    def __init__(self, model_path: str, model_parameters: dict, dt_path: str, uq_extension=None):
        """
        Initializes the ThermalModel with the given paths and parameters.
        
        Args:
            model_path (str): Path to the model geometry (mesh) file.
            model_parameters (dict): Dictionary containing material properties 
            and model-specific parameters.
            dt_path (str): Path to the digital twin parameter file (JSON format).
        """
        self.uq_extension = uq_extension
        #%%
        #super().__init__(model_path, model_parameters["thermal_model_parameters"]["model_parameters"]["problem_parameters"],)
        super().__init__(model_path, model_parameters)
        #%%
        #super().__init__(model_path, model_parameters["thermal_model_parameters"],)
        
        self.dt_path = dt_path
        
    def LoadGeometry(self):
        """
        Loads the geometry of the model for simulation.
        
        """
        pass
    
    def GenerateModel(self):
        """
        Generates the model by setting up the attributes experiment and problem with their parameters.
        
        This includes setting up experiment and problem from material parameters and related data 
        using the 'NibelungenExperiment' and `LinearElasticityNibelungenbrueckeDemonstrator`respectively.
        
        """
        self.experiment = ThermalExperiment(self.model_parameters["thermal_model_parameters"], model_path=self.model_path)
        #self.problem = ThermoMechanicalNibelungenBrueckeProblem(
        #    [self.GenerateData, self.PostAPIData, self.ParaviewProcess], self.experiment, self.experiment.parameters, pv_path=self.model_parameters["paraview_output_path"])
        
        if self.uq_extension:
            self.problem = ThermoMechanicalNibelungenBrueckeProblem(experiment=self.experiment, parameters=self.experiment.parameters, 
                                                                    pv_name=self.model_parameters["paraview_thermal_output_name"]+"_UQ", pv_path=self.model_parameters["paraview_output_path"])
        else:
            
            self.problem = ThermoMechanicalNibelungenBrueckeProblem(experiment=self.experiment, parameters=self.experiment.parameters, 
                                                                pv_name=self.model_parameters["paraview_thermal_output_name"] , pv_path=self.model_parameters["paraview_output_path"])
        
        
    def GenerateData(self, api_key, virtual_sensor_positions, which_api="MKP"):
        """
        Requests data from an API, transforms it into metadata, 
        and saves it for use with virtual sensors.

        """
        
        if which_api == "MKP":
            self.api_request = API_Request(api_key, start_time = self.model_parameters["API_request_start_time"], 
                                           end_time=self.model_parameters["API_request_end_time"], 
                                           time_step=self.model_parameters["API_request_time_step"])
            self.api_dataFrame = self.api_request.fetch_data()
            
        elif which_api == "OpenMeteo":
            start_time = self.model_parameters["API_request_start_time"][:10]
            end_time = self.model_parameters["API_request_end_time"][:10]
                                           
            OPM = OpenMeteo(start_time, end_time, time_step=self.model_parameters["API_request_time_step"])
            self.api_dataFrame = OPM.result

        metadata_saver = MetadataSaver(self.model_parameters, self.api_dataFrame)
        metadata_saver.saving_metadata()

        self.translator = Translator(self.model_parameters)
        self.translator.translator_to_sensor(self.experiment.mesh, virtual_sensor_positions)
        
        self.problem.import_sensors_from_metadata(
            self.model_parameters["MKP_meta_output_path"])
        
        
    def intial_adaptation_prep(self, data, init_cond=1):
        total_steps = len(self.api_dataFrame.loc[self.api_dataFrame.index < self.api_dataFrame.index[0] + timedelta(weeks=3)])

        self.model_parameters["thermal_model_parameters"]["model_parameters"]["initial_condition_steps"] = math.floor(total_steps*init_cond)
        self.model_parameters["thermal_model_parameters"]["model_parameters"]["burn_in_steps"] = math.ceil(total_steps*(1-init_cond))
        
        
        
    def SolveMethod(self, env_params):
        """
       Solves the model
       """
        count = 0
        data = self.api_dataFrame + 273.15      ##TODO: 'F_plus_000S_KaS-o-_Avg1' reaches to values higher than 1000??
        self.intial_adaptation_prep(data, init_cond=0.1)
        
        plot_df = data.drop(columns=[col for col in data.columns if "40TU" not in col])

        air_temperature_array = np.zeros(len(data))
        inner_temperature_array = np.zeros(len(data))
        pv_plot_flag = self.problem.p["plot_pv"]
        
        if not hasattr(self, "ic_temperature_field"):
            self.problem.p["plot_pv"] = 0
            
            initial_condition_steps = self.model_parameters["thermal_model_parameters"]["model_parameters"]["initial_condition_steps"]
            for i, (_, data_point) in enumerate(tqdm(data.iloc[:initial_condition_steps].iterrows(), total=initial_condition_steps)):

                #air_temperature_array[i] = 293  #data_point["F_plus_000TA_KaS-o-_Avg1"]
                air_temp_value = data_point.get("F_plus_000TA_KaS-o-_Avg1",
                                                data_point.get("air_temperature"))
                inner_temp_value = data_point.get("E_plus_040TI_HSS-u-_Avg", 
                                                  air_temp_value - 20)   #data_point["E_plus_040TI_HSS-u-_Avg"]
                shortwave_value = data_point.get(
                    "F_plus_000S_KaS-o-_Avg1",
                    data_point.get("shortwave_irradiation")
                    )
                
                self.problem.update_parameters({
                    "air_temperature": air_temperature_array[i],
                    "inner_temperature": inner_temperature_array[i],
                    #"shortwave_irradiation": data_point["F_plus_000S_KaS-o-_Avg1"],
                    "shortwave_irradiation": shortwave_value,
                    "calculate_shortwave_irradiation": False,
                })

                
                self.problem.solve()
        
            self.problem.fields.temperature.vector.assemble()
            self.ic_temperature_field = deepcopy(self.problem.fields.temperature.vector)
            self.problem.reset_sensors()
            self.problem.reset_fields()
        
        self.problem.u_old.vector[:] = self.ic_temperature_field
        self.problem.fields.temperature.vector[:] = self.ic_temperature_field
        
        if not hasattr(self, "burnin_temperature_field"):
            self.problem.p['plot_pv'] = 0
            burn_in_steps = self.model_parameters["thermal_model_parameters"]["model_parameters"]["burn_in_steps"]
            for i, (_, data_point) in enumerate(tqdm(data.iloc[initial_condition_steps:burn_in_steps].iterrows(), total=burn_in_steps), 
                                                start=initial_condition_steps):
                
                air_temp_value = data_point.get("F_plus_000TA_KaS-o-_Avg1",
                                                data_point.get("air_temperature"))
                inner_temp_value = data_point.get("E_plus_040TI_HSS-u-_Avg", 
                                                  air_temp_value - 20)  ##TODO: This should be something better!
                shortwave_value = data_point.get(
                    "F_plus_000S_KaS-o-_Avg1",
                    data_point.get("shortwave_irradiation"))
                
                #air_temperature_array[i] = data_point["F_plus_000TA_KaS-o-_Avg1"]
                #inner_temperature_array[i] = data_point["E_plus_040TI_HSS-u-_Avg"]
                air_temperature_array[i] = air_temp_value
                inner_temperature_array[i] = inner_temp_value
                
                
                self.problem.update_parameters({
                    "air_temperature": air_temperature_array[i],
                    #"shortwave_irradiation": data_point["F_plus_000S_KaS-o-_Avg1"],             
                    "shortwave_irradiation": shortwave_value,
                    "calculate_shortwave_irradiation": False,
                })
                
                self.problem.solve()
        
            self.problem.fields.temperature.vector.assemble()
            self.burnin_temperature_field = deepcopy(self.problem.fields.temperature.vector)
            self.problem.reset_sensors()
            self.problem.reset_fields()
        
        self.problem.u_old.vector[:] = self.burnin_temperature_field
        self.problem.fields.temperature.vector[:] = self.burnin_temperature_field
        
        start_idx = self.model_parameters["thermal_model_parameters"]["model_parameters"]["initial_condition_steps"] + self.model_parameters["thermal_model_parameters"]["model_parameters"]["burn_in_steps"]
        
        if pv_plot_flag:
            self.problem.p['plot_pv'] = 1
            
        for i, (_, data_point) in enumerate(tqdm(data.iloc[start_idx:].iterrows(), total=len(data) - start_idx)):
            
                air_temp_value = data_point.get("F_plus_000TA_KaS-o-_Avg1",
                                                data_point.get("air_temperature"))
                inner_temp_value = data_point.get("E_plus_040TI_HSS-u-_Avg", 
                                                  air_temp_value - 20)   ##TODO: This should be something better! ##FIXME:
                shortwave_value = data_point.get(
                    "F_plus_000S_KaS-o-_Avg1",
                    data_point.get("shortwave_irradiation"))
                
                air_temperature_array[start_idx+i] = air_temp_value
                inner_temperature_array[start_idx+i] = inner_temp_value
                #air_temperature_array[start_idx+i] = data_point["F_plus_000TA_KaS-o-_Avg1"]
                #inner_temperature_array[start_idx+i] = data_point["E_plus_040TI_HSS-u-_Avg"]
                    
                self.problem.update_parameters({
                    "air_temperature": air_temperature_array[start_idx+i],
                    "inner_temperature": inner_temperature_array[start_idx+i],
                    #"shortwave_irradiation": data_point["F_plus_000S_KaS-o-_Avg1"],        
                    "shortwave_irradiation": shortwave_value,
                    "calculate_shortwave_irradiation": False,
                })
                
                if data.index[start_idx+i-1] <= env_params.time[count] <= data.index[start_idx+i]:
                    param_dict = {x: env_params[x][count] for x in env_params.columns if x != "time"}
                    self.problem.update_parameters(param_dict)
                    if count < len(env_params)-1:
                        count += 1
                
                self.problem.solve()

        if len(plot_df.columns) > 0:
            first_sensor_id = plot_df.columns[0]
            temperature_value = self.problem.sensors.get(first_sensor_id, None)
            
        else:
            first_sensor_id  = "Sensor_u"
            temperature_value = self.problem.sensors.get(first_sensor_id, None)
        
        plot_df = plot_df.tail(len(temperature_value.data))
          
        #for sensor_id in plot_df.columns:
        for sensor_id in self.problem.sensors.keys():
            temperature_value = self.problem.sensors.get(sensor_id, None)
            
            if temperature_value is not None:
                temperature_value_list = [float(x) for x in temperature_value.data]
                vs_col = sensor_id+"_virtual_sensor"
                plot_df[vs_col] = temperature_value_list
                
        #self.plot_all_sensors_together(database)
        self.all_sensor_plot_data = plot_df
        return self.all_sensor_plot_data
        
        
    def plot_all_sensors_together(self, database):
        real_data = database["real_sensor_data"]
        virtual_data = database["virtual_sensor_data"]
    
        plt.figure(figsize=(12, 6))
        for sensor_id in real_data:
            # Real sensor data
            real_values = real_data[sensor_id]
    
            # Virtual sensor data (flatten lists)
            virtual_values = [v[0] if isinstance(v, list) else v for v in virtual_data[sensor_id]]
    
            # Plot real and virtual on same graph with different styles
            plt.plot(real_values, label=f"{sensor_id} - Real", linestyle='-')
            plt.plot(virtual_values, label=f"{sensor_id} - Virtual", linestyle='--')
    
        plt.title("Sensor Data: Real vs Virtual (All Sensors)")
        plt.xlabel("Timestep")
        plt.ylabel("Sensor Value")
        plt.legend(loc='best')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

 

#%%
    def PostAPIData(self):
        """
        Saving data of virtual sensor' after the model solve
        """
        
        self.translator.save_to_MKP(self.api_dataFrame)
        self.translator.save_virtual_sensor(self.problem)        
        
    def ParaviewFirstRun(self):
        """
        Handles the first run of Paraview data output.
        
        This method is useful for initializing the Paraview output for the 
        first time, setting up the model visualization,
        and preparing the mesh for further data writing in later iterations.
        """
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, self.model_parameters["paraview_output_path"]
                                +"/"+self.model_parameters["model_name"]+".xdmf", "w") as xdmf:
                xdmf.write_mesh(self.problem.mesh)
                #xdmf.write_function(self.problem.fields.displacement, self.problem.time)     
                
    def ParaviewProcess(self):
        """
        Processes the Paraview data during each timestep.
        It writes the displacement fields to the Paraview XDMF file.
        """
        
        if self.model_parameters["paraview_output"]:
            with df.io.XDMFFile(self.problem.mesh.comm, 
                                self.model_parameters["paraview_output_path"]+
                                "/"+self.model_parameters["model_name"]+".xdmf", "a") as xdmf:
                # xdmf.write_mesh(self.problem.mesh)
                xdmf.write_function(self.problem.fields.displacement, 
                                    self.problem.time)


    
#%%
    def solve(self, api_key, orchestrator_simulation_parameters, env_params):
        """
        Reloading, model generating and solving model.
        """
        self.LoadGeometry()
        self.GenerateModel()
        self.GenerateData(api_key, orchestrator_simulation_parameters["virtual_sensor_positions"], 
                          which_api=orchestrator_simulation_parameters["data_source"])
        self.SolveMethod(env_params)
            
      

    def export_output(self, path: str):
        ##TODO: hard-coded path!!
        json_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/" + path + ".json"
        try:
            with open(json_path, 'r') as file:
                output_data = json.load(file)
                
        except FileNotFoundError:
            output_data = {}
            
        output_data.setdefault('real_sensor_output', []).append(self.sensor_out)
        output_data.setdefault('virtual_sensor_output', []).append(self.vs_sensor_out)

        local_time = time.localtime()
        output_data.setdefault('time', []).append(time.strftime("%y-%m-%d %H:%M:%S", local_time))

        with open(self.dt_path, 'r') as f:
            dt_params = json.load(f)
        output_data.setdefault('Input_parameter', []).append(dt_params[0]["parameters"]["E"])

        with open(json_path, 'w') as file:
            json.dump(output_data, file)
            
        return json_path
    
    def fields_assignment(self, data):
        if data == None:
            pass
        
        else:
            for i in data.keys():
                if i == "displacement":
                    self.problem.fields.displacement = data[i]
                elif i == "temperature":
                    self.problem.fields.temperature = data[i]
        
    def fields_data_storer(self, path):
        data_to_store = {}

        for i in dir(self.problem.fields):
            if not i.startswith("_"):
                k = getattr(self.problem.fields, i)
                if k:
                    data_to_store[i] = k.x.array[:]
        try:
            pkl_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/" + path
            with open(f"{pkl_path}_params.pkl", "wb") as f:
                pickle.dump(data_to_store, f)
                
        except Exception as e:
            print(f"An error occurred while saving the model: {e}")
            


#%%
    
if __name__ == "__main__": 
    
    #model_path = '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh'
    model_path = '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh_3d.msh'
    
    model_parameters = {'model_name': 'displacements',
     'df_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_df_output.csv',
     'meta_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_meta_output.json',
     'MKP_meta_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_meta_output.json',
     'MKP_translated_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_translated.json',
     'virtual_sensor_added_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json',
     "secret_path" : "",
     "API_request_start_time": "2023-08-11T08:00:00Z",
     "API_request_end_time": "2023-09-11T08:01:00Z",
     "API_request_time_step": "10min",
     "cache_path": "",
     'paraview_output': True,
     "paraview_output_name": "Nibelungenbrücke_thermal",
     "paraview_output_path": "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview",
     #'material_parameters': {'E': 40000000000000.0, 'nu': 0.2, 'rho': 2350},
     'material_parameters': {},
     "secret_path" : "/home/msoenmez/Desktop/API_request_password",
     'thermal_model_parameters': {
        "name": "Nibelungenbrücke thermal",
        "experiments": ["TestSeries_1"],
        "input_sensors_path": "./input/sensors/sensors_temperature_probeye_input.json",
        "output_sensors_path": "./input/sensors/sensors_temperature_probeye_output.json",
        "problem_parameters": ["sigma_u", "sigma_n", "sigma_s", "sigma_o"], 
        "parameter_key_paths": [[],[],[],[]],
        "model_type": "embedded_for_noise",
        "model_parameters": {
            "model_name": "temperature",
            "initial_condition_steps": 100,
            "burn_in_steps": 300,
            "experiment_parameters":{ 
                "dim": 2  
            },
            "problem_parameters": {
                "air_temperature": 293.0,
                "inner_temperature": 293.0,
                "initial_temperature": 293.0,
                "heat_capacity": 870.0,
                "dt": 600.0,
                "theta": 1.0,
                "density": 2400.0,
                "conductivity": 2.5,
                "diffusivity": 1.0E-6,
                "sensor_location_u": -4.3,
                "sensor_location_s": -2.2,
                "sensor_location_n": -3.56,
                "sensor_location_o": -0.17,
                "convection": True,
                "natural_convection_coefficient": 10.0,
                "wind_forced_convection": False,
                "wind_forced_convection_parameter_constant": 1.0,
                "wind_speed": 5.0,
                "shortwave_radiation": True,
                "shortwave_radiation_constant": 1.0,
                "shortwave_irradiation": 0.0,
                "calculate_shortwave_irradiation": False,
                "top_tag": 9,
                "bottom_tag": 8,
                "end_tag": 7,
                "plot_pv": False
            },
            "sensor_metadata": "./input/sensors/sensors_temperature.json"
        }}
    }
    dt_path = '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json'
    
    
    dm = ThermalModel(model_path, model_parameters, dt_path)
    api_key = ""
    dm.solve(api_key)
