import chaospy
import numpy as np
from tqdm import tqdm
from tqdm import trange
from copy import deepcopy
import dolfinx as df
import matplotlib.pyplot as plt
from nibelungenbruecke.scripts.digital_twin_orchestrator.thermal_model import ThermalModel

class ThermalModelUQ(ThermalModel):
    """
    A class representing a thermal model for NB simulations with UQ using PCE.
    """

    def __init__(self, model_path: str, model_parameters: dict, dt_path: str,
                 uq_params: dict = None):
        """
        Initializes the ThermalModelUQ with the given paths, parameters, and UQ settings.
        Args:
            model_path (str): Path to the model geometry (mesh) file.
            model_parameters (dict): Dictionary containing material properties and model-specific parameters.
            dt_path (str): Path to the digital twin parameter file (JSON format).
            uq_params (dict): Dictionary with UQ settings (keys: 'order', 'distribution', 'param_names').
        """
        super().__init__(model_path, model_parameters, dt_path, uq_extension=True)
        self.uq_params = uq_params or {
            "order": 2,
            "distribution": {"air_temperature": ("normal", 293.15, 2.0)},  # mean, std
            "param_names": ["air_temperature"]
        }
        self.bias_model_parameters = model_parameters["bias_model_parameters"]

        self.forward_model_parameters = model_parameters["thermal_model_parameters"]
        self.parameters = self.forward_model_parameters["problem_parameters"]
        self.parameters_minus_bias = self.parameters.copy()
        for bias_parameters in self.bias_model_parameters["parameters"]:
            self.parameters_minus_bias.remove(bias_parameters["bias_name"])

        if self.forward_model_parameters["parameter_key_paths"] is None:
            self.parameter_key_paths = [[] for _ in range(len(self.parameters))]
        else:
            self.parameter_key_paths = self.forward_model_parameters["parameter_key_paths"]
        # Assumes load_probeye_sensors is imported/available in this scope
        self.output_sensor_names = ["bridge_temperature_u", "bridge_temperature_o", "bridge_temperature_n", "bridge_temperature_s"]
        
    def extend_output_sensors(self):
        
        self.output_sensor_names = ["bridge_temperature_u", "bridge_temperature_o", "bridge_temperature_n", "bridge_temperature_s"]
        self.output_sensor_names.extend([i for i in self.problem.sensors.keys()])
        

    def SolveMethod(self, env_params):
        """
        Solves the model for each quadrature node in the PCE expansion and computes statistics.
        """

        self.input_sensor_names = ['air_temperature', 'inner_temperature', 'shortwave_irradiation', 'wind_speed']
        self.extend_output_sensors()
        
        b_dist_list = []

        # Prepare input dictionary with bias model parameters and sensor data
        inp = {}
        data = self.api_dataFrame
        self.intial_adaptation_prep(data, init_cond=0.2)
        #data = plot_df.drop(columns=[col for col in plot_df.columns if "40TU" not in col])

        # Add bias model parameters (mean and std/bias for each parameter)
        for param_dict in self.bias_model_parameters["parameters"]:
            inp[param_dict["variable_name"]] = param_dict.get("mean", 0.0)
            inp[param_dict["bias_name"]] = param_dict.get("std", 0.1)

        # Prepare arrays for sensor data
        air_temperature_array = np.zeros(len(data))
        inner_temperature_array = np.zeros(len(data))
        shortwave_irradiation_array = np.zeros(len(data))
        wind_speed_array = np.zeros(len(data))

        for i, (_, data_point) in enumerate(tqdm(data.iterrows(), total=len(data))):
            #air_temperature_array[i] = data_point["F_plus_000TA_KaS-o-_Avg1"]
            #inner_temperature_array[i] = data_point["E_plus_040TI_HSS-u-_Avg"]
            #shortwave_irradiation_array[i] = data_point["F_plus_000S_KaS-o-_Avg1"]

            air_temp_value = data_point.get("F_plus_000TA_KaS-o-_Avg1",
                                            data_point.get("air_temperature"))

            inner_temp_value = data_point.get("E_plus_040TI_HSS-u-_Avg",
                                              air_temp_value - 20)
            #inner_temp_value = air_temp_value - 20  ##TODO: This should be something better!
            shortwave_value = data_point.get(
                "F_plus_000S_KaS-o-_Avg1",
                data_point.get("shortwave_irradiation"))
            wind_speed_value = data_point.get("wind_speed", self.problem.p["wind_speed"])

            air_temperature_array[i] = air_temp_value
            inner_temperature_array[i] = inner_temp_value
            shortwave_irradiation_array[i] = shortwave_value
            wind_speed_array[i] = wind_speed_value

        inp["air_temperature"] = air_temperature_array
        inp["inner_temperature"] = inner_temperature_array
        inp["shortwave_irradiation"] = shortwave_irradiation_array
        inp["wind_speed"] = wind_speed_array
        inp["calculate_shortwave_irradiation"] = False

        # Run surrogate
        # FIXME: The embedding formulation should be flexible from the input parameters
        for param_dict in self.bias_model_parameters["parameters"]:
            #if param_dict["variable_name"]=="additional_heat_constant":
            b_dist_list.append(chaospy.Normal(inp[param_dict["variable_name"]], inp[param_dict["bias_name"]]))
            #else:
             #   std_lognormal = np.sqrt(np.log(1+np.exp(-2*np.log(inp[param_dict["variable_name"]])+2*np.log(inp[param_dict["bias_name"]]))))
             #   mean_lognormal = np.log(inp[param_dict["variable_name"]]) - std_lognormal**2/2
             #   b_dist_list.append(chaospy.LogNormal(mean_lognormal, std_lognormal))
        b_dist = chaospy.J(*b_dist_list)

        # Generate quadrature and expansion
        sparse_quads = chaospy.generate_quadrature(self.bias_model_parameters["pol_order"], b_dist, "gaussian")
        expansion = chaospy.generate_expansion(self.bias_model_parameters["pol_order"], b_dist)

        # Preprocess inputs
        theta_quads = []
        for quad in sparse_quads[0].T:
            input_node = inp.copy()
            #TODO: A nicer way to avoid possible problems with the list order would be having a map from variables to bias
            for i_param, param_dict in enumerate(self.bias_model_parameters["parameters"]):
                if param_dict["variable_name"] in input_node.keys():
                    input_node[param_dict["variable_name"]] = quad[i_param]
            theta_quads.append(input_node)


        input_nodes = [{key: value for key, value in node.items() if key in self.parameters_minus_bias} for node in theta_quads]
        # Evaluate the nodes
        sparse_evals = {key: [] for key in self.output_sensor_names}
        paraview_result = {"test_1": []}
        for node in input_nodes:
            count = 0
            # Run timeseries problem
            self.problem.update_parameters(node)
            self.problem.reset_fields()
            self.problem.reset_sensors()

            if not "ic_temperature_field" in self.__dict__:
                initial_condition_steps = self.model_parameters["thermal_model_parameters"]["model_parameters"]["initial_condition_steps"]
                

                for entry in trange(initial_condition_steps, desc="Solving IC steps"):
                    new_parameters = {}
                    for channel in self.input_sensor_names:
                        new_parameters[channel] = inp[channel][entry]
                        #new_parameters[channel] = inp[channel]

                    try:
                        new_parameters["air_temperature"] = new_parameters["air_temperature"] + 273.15
                    except KeyError:
                        pass
                    try:
                        new_parameters["inner_temperature"] = new_parameters["inner_temperature"] + 273.15
                    except KeyError:
                        pass

                    self.problem.update_parameters(new_parameters)
                    self.problem.solve()
                    
                self.problem.fields.temperature.vector.assemble()
                self.ic_temperature_field = deepcopy(self.problem.fields.temperature.vector)
                self.problem.reset_sensors()
                self.problem.reset_fields()

            self.problem.u_old.vector[:] = self.ic_temperature_field
            self.problem.fields.temperature.vector[:] = self.ic_temperature_field
            
            
            if not "burnin_temperature_field" in self.__dict__:
                burn_in_steps = self.model_parameters["thermal_model_parameters"]["model_parameters"]["burn_in_steps"]
                
    
                for entry in trange(initial_condition_steps, burn_in_steps, desc="Solving IC steps"):
                    new_parameters = {}
                    for channel in self.input_sensor_names:
                        new_parameters[channel] = inp[channel][entry]
                        #new_parameters[channel] = inp[channel]
    
                    try:
                        new_parameters["air_temperature"] = new_parameters["air_temperature"] + 273.15
                    except KeyError:
                        pass
                    try:
                        new_parameters["inner_temperature"] = new_parameters["inner_temperature"] + 273.15
                    except KeyError:
                        pass
    
                    self.problem.update_parameters(new_parameters)
                    self.problem.solve()
                    
                self.problem.fields.temperature.vector.assemble()
                self.burnin_temperature_field = deepcopy(self.problem.fields.temperature.vector)
                self.problem.reset_sensors()
                self.problem.reset_fields()
    
            self.problem.u_old.vector[:] = self.burnin_temperature_field
            self.problem.fields.temperature.vector[:] = self.burnin_temperature_field
            #%%
            # Run timeseries problem     
            start_idx = self.model_parameters["thermal_model_parameters"]["model_parameters"]["initial_condition_steps"] + self.model_parameters["thermal_model_parameters"]["model_parameters"]["burn_in_steps"]
            end_idx = len(inp[self.input_sensor_names[0]])      
            
            for entry in trange(start_idx, end_idx, desc="Solving time steps"):
                new_parameters = {}
                for channel in self.input_sensor_names:
                    new_parameters[channel] = inp[channel][entry]

                try:
                    new_parameters["air_temperature"] = new_parameters["air_temperature"] + 273.15
                except KeyError:
                    pass
                try:
                    new_parameters["inner_temperature"] = new_parameters["inner_temperature"] + 273.15
                except KeyError:
                    pass
                
                if data.index[entry-1] <= env_params.time[count] <= data.index[entry]:
                    input_nodes_params = [list(node.keys())[0] for node in input_nodes] ##TODO: Exterior iteration runs through "input_nodes" elements!!! That probably needs to be checked!
                    exclude_columns = input_nodes_params + ["time"]
                    param_dict = {x: env_params[x][count] for x in env_params.columns if x not in exclude_columns}
                    self.problem.update_parameters(param_dict)
                    if count < len(env_params)-1:
                        count += 1

                self.problem.update_parameters(new_parameters)
                self.problem.solve()

            for ikey, key in enumerate(self.output_sensor_names):
                if key in ["bridge_temperature_u", "bridge_temperature_o", "bridge_temperature_n", "bridge_temperature_s"]:
                    sparse_evals[key].append(np.array(self.problem.sensors[self._inverse_sensor_map(key)].data)[self.model_parameters["thermal_model_parameters"]["model_parameters"]["burn_in_steps"]:])
            
                else:
                    sparse_evals[key].append(np.array(self.problem.sensors[key].data)[self.model_parameters["thermal_model_parameters"]["model_parameters"]["burn_in_steps"]:])                    
               
                
            #paraview_result["test_1"].append(np.array(self.problem.fields.temperature.vector[start_idx:end_idx]))
    
                        
        # Generate the expansion of orthogonal polynomials and fit the Fourier coefficients
        fitted_sparse = {}
        for key in self.output_sensor_names:
            fitted_sparse[key] = chaospy.fit_quadrature(expansion, np.array(sparse_quads[0]), np.array(sparse_quads[1]), sparse_evals[key])

        return_dict = {key: fitted_sparse[key] for key in self.output_sensor_names if key in fitted_sparse}
        return_dict["dist"] = b_dist

        # Compute mean and std for each sensor for plotting
        sensor_stats = {}
        for key in self.output_sensor_names:
            mean_val = chaospy.E(fitted_sparse[key], b_dist)
            std_val = chaospy.Std(fitted_sparse[key], b_dist)
            #inferred_noise     ##TODO
            #prescribed_noise   ##TODO
            sensor_stats[key] = {"mean": mean_val, "std": std_val} 
            
        self.all_sensor_plot_data = self.pandas_data_form(data, sensor_stats)

##%%
       # num_chunks = 10  # Define the number of chunks
       # chunk_size = (end_idx - start_idx) // num_chunks
        #chunk_size = len(evaluations_temperature[0, :timesteps, 0]) // num_chunks

       # coefficients_temperature_list = []

        #for i, sample in enumerate(tqdm(range(num_chunks), desc="Evaluating samples")):
        #    chunk_evaluations_temperature = np.array(paraview_result["test_1"][:, i*chunk_size:(i+1)*chunk_size, :])

         #   # Perform the pseudospectral projection for each chunk
          #  chunk_coefficients_temperature = chaospy.fit_quadrature(expansion, np.array(sparse_quads[0]), np.array(sparse_quads[1]), chunk_evaluations_temperature)

          #  coefficients_temperature_list.append(chunk_coefficients_temperature)

          #  print("Assigning full field temperature statistics")
          #  joint_distribution = chaospy.LogNormal(b_dist_list[0]._parameters["shift"], b_dist_list[0]._parameters["scale"])
          #  means_temperature = chaospy.E(chunk_coefficients_temperature, joint_distribution)
          #  stds_temperature = chaospy.Std(chunk_coefficients_temperature, joint_distribution)

         #   self.assign_full_field_values("means_temperature", means_temperature, burn = 0+i*chunk_size)
           # self.assign_full_field_values("stds_temperature", stds_temperature, burn = 0+i*chunk_size)

##%%
        return self.all_sensor_plot_data
    
    def assign_full_field_values(self, field_name: str, values: list[list[float]], burn: int) -> None:
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


        
    def pandas_data_form(self, data, sensor_stats):
        
        len_data = sensor_stats['bridge_temperature_u']["mean"].shape[0]
        plot_df = data.tail(len_data).copy() 
        
        for key, stats in sensor_stats.items():
            plot_df[f"{key}_mean"] = stats["mean"].squeeze()
            plot_df[f"{key}_std"] = stats["std"].squeeze()
                
        return plot_df
        
    def _sensor_map(self, probeye_sensor: str) -> str:
        sensor_map_dict = {
            "Sensor_u": "bridge_temperature_u",
            "Sensor_o": "bridge_temperature_o",
            "Sensor_n": "bridge_temperature_n",
            "Sensor_s": "bridge_temperature_s",
        }
        return sensor_map_dict[probeye_sensor]

    def _inverse_sensor_map(self, sensor: str) -> str:
        sensor_map_dict = {
            "bridge_temperature_u": "Sensor_u",
            "bridge_temperature_o": "Sensor_o",
            "bridge_temperature_n": "Sensor_n",
            "bridge_temperature_s": "Sensor_s",
        }
        return sensor_map_dict[sensor]


    def plot_all_sensors_together(self, sensor_stats):
        """
        Plot mean and uncertainty band for each sensor.
        """
        plt.figure(figsize=(12, 6))
        for sensor_id, stats in sensor_stats.items():
            mean = stats["mean"].squeeze()
            std = stats["std"].squeeze()
            timesteps = np.arange(len(mean))
            plt.plot(timesteps, mean, label=f"{sensor_id} - Mean", linestyle='-')
            plt.fill_between(timesteps, mean - std, mean + std, alpha=0.2, label=f"{sensor_id} ±1σ")
        plt.title("Sensor Data: PCE Mean ± Std (All Sensors)")
        plt.xlabel("Timestep")
        plt.ylabel("Sensor Value")
        plt.legend(loc='best')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    
if __name__ == "__main__": 
    
    model_path = '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh'
    #model_path = 'use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh_3d.msh'
    
    model_parameters = {'model_name': 'thermal_transient',
     'df_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_df_output.csv',
     'meta_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_meta_output.json',
     'MKP_meta_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_meta_output.json',
     'MKP_translated_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_translated.json',
     'virtual_sensor_added_output_path': '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json',
     "API_request_start_time": "2023-08-11T08:00:00Z",
     "API_request_end_time": "2023-09-11T08:01:00Z",
     "API_request_time_step": "10min",
     'paraview_output': True,
     'paraview_output_path': 'use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview',
     'paraview_output_name': 'ThermalModel',
     #'material_parameters': {'E': 40000000000000.0, 'nu': 0.2, 'rho': 2350},
     'material_parameters': {},
     "secret_path" : "/home/darcones/Projects/API_keys/mkp",
     "bias_model_parameters": {
        "parameters": [
        {
            "variable_name": "additional_heat_constant",
            "bias_name": "additional_heat_constant_bias",
            "distribution": "normal",
            "mean": 0.0,
            "std": 0.1
        },
        {
            "variable_name": "wind_forced_convection_parameter_constant",
            "bias_name": "wind_forced_convection_parameter_constant_bias",
            "distribution": "normal",
            "mean": 0.0,
            "std": 0.1
        }
        ],
        "pol_order": 2
        },
     'thermal_model_parameters': {
        "name": "Nibelungenbrücke thermal",
        "experiments": ["TestSeries_1"],
        "input_sensors_path": "./input/sensors/sensors_temperature_probeye_input.json",
        "output_sensors_path": "./input/sensors/sensors_temperature_probeye_output.json",
        "problem_parameters": ["sensor_location_u",
      "sensor_location_n",
      "sensor_location_s",
      "sensor_location_o",
      "wind_forced_convection_parameter_constant",
      "wind_forced_convection_parameter_constant_bias",
      "additional_heat_constant",
      "additional_heat_constant_bias",
      "shortwave_radiation_constant",
      "diffusivity",
      "sigma_u",
      "sigma_n",
      "sigma_s",
      "sigma_o"
    ],

    "parameter_key_paths": [
      [],
      [],
      [],
      [],
      [],
      [],
      [],
      [],
      [],
      [],
      [],
      [],
      []
    ],
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
                "convection": False,
                "natural_convection_coefficient": 10.0,
                "wind_forced_convection": True,
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
    
    
    dm = ThermalModelUQ(model_path, model_parameters, dt_path)
    api_key = ""
    dm.solve(api_key=api_key)