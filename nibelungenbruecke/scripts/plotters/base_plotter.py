from abc import ABC, abstractmethod
import os
import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pyvista as pv
import meshio
import xml.etree.ElementTree as ET
import pandas as pd
from dolfinx.io import VTKFile
from mpi4py import MPI


class BasePlotter(ABC):
    """ Base class for all plotters """

    def __init__(self, problem=None, simulation_parameters=None, default_parameters=None, api_data_frame=None):
        self.problem = problem
        self.simulation_parameters = simulation_parameters or {}
        #self.default_parameters = default_parameters or {}
        self.default_parameters = self.plotter_default_parameters()
        self.api_dataFrame = api_data_frame
        self.sensor_data_json = {}
        
        #self.output_file = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/sensor_timeseries.json"
        
    def set_attributes(self, problem, simulation_parameters, default_parameters, api_data_frame, all_sensors_combined):
        self.problem = problem
        self.simulation_parameters = simulation_parameters
        #self.default_parameters = default_parameters
        self.api_dataFrame = api_data_frame
        self.all_sensor_plot_data = all_sensors_combined
        
        
    def extract_virtual_sensor_data(self):
        
        df = self.all_sensor_plot_data
        
        sensors = self.problem.sensors
        for sensor_id in sensors.keys():
            if sensor_id in df.columns:
                continue
            else:
                temperature_value = self.problem.sensors.get(sensor_id, None)
                
                if temperature_value is not None:
                    temperature_value_list = [float(x) for x in temperature_value.data]
                    df[sensor_id] = temperature_value_list

        return df
    
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
    
    def _sensor_map_to_real(self) -> str:
        sensor_map_dict = {
            "E_plus_040TU_HS--o-_Avg1": "Sensor_o",
            "E_plus_040TU_HSN-m-_Avg1": "Sensor_n",
            "E_plus_040TU_HSS-m-_Avg1": "Sensor_s",
            "E_plus_040TU_HS--u-_Avg1": "Sensor_u",
            }
        return sensor_map_dict
    
    
    def plotter_default_parameters(self):       ##TODO: hard coded paths!!

        return {
            'model_parameter_path': '/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json',
            'displacement_mesh_path': '/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh',
            'thermal_mesh_path': '/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh_3d_thermal.msh',
            'thermal_h5py_path': 'NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_thermal.h5',
            'thermal_xdmf_path': '/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_thermal.xdmf',
            'mesh_only_xdmf_path': '/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_thermal_mesh_only.xdmf',
            'vtk_output_path': '/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_thermal.vtk',
            'displacement_h5py_path': '/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_displacement.h5',
            'displacement_xdmf_path': '/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview/Nibelungenbruecke_displacement.xdmf',
        }


    @abstractmethod
    def plot(self, *args, **kwargs):
        """Each subclass implements its own plotting or data extraction logic."""
        pass


class RealvsVirtualAllTogether(BasePlotter):
    
    def plot(self):
        
        df = self.all_sensor_plot_data
        
        plt.figure(figsize=(14, 6))
        for col in df.columns:
            if not col.endswith("_virtual_sensor"):
                vs_col = col + "_virtual_sensor"
                if vs_col in df.columns:
                    plt.plot(df.index, df[col], label=f"{col} (real)", linestyle='-')
                    plt.plot(df.index, df[vs_col], label=f"{col} (virtual)", linestyle='--')
        
        plt.title("Real vs Virtual Sensor Data")
        plt.xlabel("Time")
        plt.ylabel("Sensor Value")
        plt.legend(loc="best")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        
class RealvsVirtualAllTogetherUQ(BasePlotter):
    
    def plot(self):
        
        df = self.all_sensor_plot_data
        
        sensor_names = sorted(
            set(
                col.replace('_mean', '')
                for col in df.columns
                if col.endswith('_mean') and f"{col.replace('_mean', '')}_std" in df.columns
            )
        )
        
        sensor_names = [s for s in sensor_names if "Sensor" not in s and "bridge" not in s and "TU" in s]
        
        plt.figure(figsize=(14, 6))
        
        for i, sensor in enumerate(sensor_names):
            mean_col = f"{sensor}_mean"
            std_col = f"{sensor}_std"
            
            api_data = df[sensor]+275
            mean = df[mean_col]
            std = df[std_col]
            
            plt.plot(df.index, api_data, linestyle='--', alpha=0.6, label=sensor)
            plt.plot(df.index, mean, label=f"{sensor}_mean ± Std")
            plt.fill_between(df.index, mean - std, mean + std, alpha=0.2)
        
        plt.title("Sensor Temperature (Raw vs Mean ± Std)")
        plt.xlabel("Time / Index")
        plt.ylabel("Temperature (K)")
        plt.legend(loc='upper right', fontsize='small')
        plt.tight_layout()
        plt.show()
            
        
class AllSensorsTogetherPlotter(BasePlotter):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def plot(self):
        df = self.extract_virtual_sensor_data()
        sensor_map_dict = self._sensor_map_to_real()
        
        real_cols_to_plot = [col for col in sensor_map_dict.keys() if col in df.columns]

        vs_cols_to_plot = [sensor_map_dict[i] for i in real_cols_to_plot]
        
        #plot_df_real = df[real_cols_to_plot]
        plot_df_vs = df[vs_cols_to_plot].rename(columns=lambda x: self._sensor_map(x))
        
        #plot_df = pd.concat([plot_df_real, plot_df_vs], axis=1)
        
        plot_df_vs.plot(figsize=(14, 6))
        plt.title("Virtual Sensors")
        plt.xlabel("Index")
        plt.ylabel("Value")
        plt.legend(title="Sensors")
        plt.grid(True)
        plt.show()
        
class AllSensorsTogetherPlotterUQ(BasePlotter):
    
    def plot(self):
        
        df = self.all_sensor_plot_data
        
        sensor_names = sorted(
            set(
                col.replace('_mean', '')
                for col in df.columns
                if col.endswith('_mean') and f"{col.replace('_mean', '')}_std" in df.columns
            )
        )
        
        sensor_names = [s for s in sensor_names if "bridge" in s]
        
        plt.figure(figsize=(14, 6))
        
        for i, sensor in enumerate(sensor_names):
            
            mean_col = f"{sensor}_mean"
            std_col = f"{sensor}_std"

            mean = df[mean_col]
            std = df[std_col]
            
            plt.plot(df.index, mean, label=f"{sensor}_mean± Std")
            plt.fill_between(df.index, mean - std, mean + std, alpha=0.2)
        
        plt.title("Sensor Temperature (Raw vs Mean ± Std)")
        plt.xlabel("Time / Index")
        plt.ylabel("Temperature (K)")
        plt.legend(loc='upper right', fontsize='small')
        plt.tight_layout()
        plt.show()
    


class RealVsVirtualPlotter(BasePlotter):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def plot(self, sensor_mapping=None):
        df = self.extract_virtual_sensor_data()
        
        if sensor_mapping is None:
            sensor_mapping = {
                "E_plus_040TU_HS--o-_Avg1": "Sensor_o",
                "E_plus_040TU_HSN-m-_Avg1": "Sensor_n",
                "E_plus_040TU_HSS-m-_Avg1": "Sensor_s",
                "E_plus_040TU_HS--u-_Avg1": "Sensor_u",
            }

        #df = self.api_dataFrame + 273.15
        #measured_times = df.index

        for real_col, mapped_col in sensor_mapping.items():
            if real_col not in df.columns or mapped_col not in df.columns:
                print(f"Skipping mapping: {real_col} -> {mapped_col} (column missing)")
                continue
        
            plt.figure(figsize=(14, 6))
            plt.plot(df.index, df[real_col], label=f"{real_col}", linestyle='-')
            plt.plot(df.index, df[mapped_col], label=f"{self._sensor_map(mapped_col)}", linestyle='--')
        
            plt.title(f"Sensor Comparison: {real_col} vs {self._sensor_map(mapped_col)}")
            plt.xlabel("Time index")
            plt.ylabel("Sensor Value")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()

class RealVsVirtualPlotterUQ(BasePlotter):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        
    def plot(self, sensor_mapping=None):
        
        if sensor_mapping is None:
            sensor_mapping = {
                "E_plus_040TU_HS--o-_Avg1": "Sensor_o",
                "E_plus_040TU_HSN-m-_Avg1": "Sensor_n",
                "E_plus_040TU_HSS-m-_Avg1": "Sensor_s",
                "E_plus_040TU_HS--u-_Avg1": "Sensor_u",
            }
            
        vs_sensor_map_dict = {
            "Sensor_u": "bridge_temperature_u",
            "Sensor_o": "bridge_temperature_o",
            "Sensor_n": "bridge_temperature_n",
            "Sensor_s": "bridge_temperature_s",
        }

        df = self.all_sensor_plot_data
        
        sensor_names = sorted(
            set(
                col.replace('_mean', '')
                for col in df.columns
                if col.endswith('_mean') and f"{col.replace('_mean', '')}_std" in df.columns
            )
        )
        
        sensor_names = [i for i in sensor_mapping.keys()]
        #selected_sensors.extend([n for n in vs_sensor_map_dict.keys()])
        #sensor_names = [s for s in sensor_names if s in selected_sensors]

        

        
        for i, sensor in enumerate(sensor_names):
            
            plt.figure(figsize=(14, 6))
            
            mean_col = f"{vs_sensor_map_dict[sensor_mapping[sensor]]}_mean"
            std_col = f"{vs_sensor_map_dict[sensor_mapping[sensor]]}_std"
            
            api_data = df[sensor] + 275
            mean = df[mean_col]
            std = df[std_col]
            
            plt.plot(df.index, api_data, label=f"{sensor}")
            plt.plot(df.index, mean, label=f"{vs_sensor_map_dict[sensor_mapping[sensor]]}_mean ± Std")
            plt.fill_between(df.index, mean - std, mean + std, alpha=0.2)
        
            plt.title("Sensor Temperature (real vs virtual UQ)")
            plt.xlabel("Time")
            plt.ylabel("Temperature (K)")
            plt.legend(loc='upper right', fontsize='small')
            plt.tight_layout()
            plt.show()
    

class VirtualSensorPlotter(BasePlotter):

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def plot(self):

        selected_sensors = {x["name"] for x in self.simulation_parameters.get("virtual_sensor_positions", [])}

        for name, sensor in self.problem.sensors.items():
            if name not in selected_sensors:
                continue
        

            times = self.all_sensor_plot_data.index 
            values = [
                float(d[0]) if isinstance(d, np.ndarray) else float(d)
                for d in sensor.data
            ]
        
            # Skip if lengths mismatch
            if len(times) != len(values):
                print(f"Skipping '{name}': mismatched time/data lengths.")
                continue
        
            # Plotting
            plt.figure(figsize=(14, 6))
            plt.plot(times, values, "-b", label="Virtual Sensor Value")
            plt.title(f"Virtual Sensor: {name}")
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()
            
class VirtualSensorPlotterUQ(BasePlotter):

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def plot(self):
            
        df = self.all_sensor_plot_data
        
        sensor_names = sorted(
            set(
                col.replace('_mean', '')
                for col in df.columns
                if col.endswith('_mean') and f"{col.replace('_mean', '')}_std" in df.columns
            )
        )
        
        selected_sensors = {x["name"] for x in self.simulation_parameters.get("virtual_sensor_positions", [])}
        sensor_names = [s for s in sensor_names if s in selected_sensors]

        
        plt.figure(figsize=(14, 6))
        
        for i, sensor in enumerate(sensor_names):
            
            mean_col = f"{sensor}_mean"
            std_col = f"{sensor}_std"

            mean = df[mean_col]
            std = df[std_col]
            
            plt.plot(df.index, mean, label=f"{sensor}_mean ± Std")
            plt.fill_between(df.index, mean - std, mean + std, alpha=0.2)
        
        plt.title("Sensor Temperature (Raw vs Mean ± Std)")
        plt.xlabel("Time / Index")
        plt.ylabel("Temperature (K)")
        plt.legend(loc='upper right', fontsize='small')
        plt.tight_layout()
        plt.show()
    
    

    
            


class FullFieldResponsePlotter(BasePlotter):
    
    def plot(self, plot_pyvista=True):
        
        if plot_pyvista:
            if self.simulation_parameters.get("full_field_results", False):
                print(
                    "Please find the full-field response at the following paths:\n"
                    f"  HDF5 file: {self.default_parameters['thermal_h5py_path']}\n"
                    f"  XDMF file: {self.default_parameters['thermal_xdmf_path']}\n"
                )
            else:
                print(
                    "Full-field results are not available. "
                    "To enable them, set 'full_field_results' to True in simulation_parameters."
                )
        else:
            print(
                "Full-field responses are not plotted. "
                "To plot them, set 'plot_pyvista' to True when calling this method."
            )

#%%
# =============================================================================
# 
# 
# class FullFieldResponse(BasePlotter):
#     
#     def plot(self, plot_pyvista=True):
#         if plot_pyvista:    
#             mesh = self.problem.mesh
#             temperature = self.problem.fields.temperature
#             #fem_file = File("../../../FullFieldResponse/solution.pvd")
#             
#             with VTKFile(MPI.COMM_WORLD, "../../../FullFieldResponse/solution.pvd", "w") as vtk:
#                 vtk.write_function(temperature)
#         
#             mesh = pv.read("../../../FullFieldResponse/solution.pvd")  # or .vtu / .xdmf
#             mesh.plot(scalars="temperature", cmap="plasma")
#         
# 
# 
# 
# 
# class FullFieldPlotter(BasePlotter):
#         
#     def plot(self, plot_pyvista=True):      ##TODO: Keep it as "False" fro J4NFDI interface!!
#         if not self.simulation_parameters.get("full_field_results", False):
#             print("Full-field results are available at the following path.")
#             print("NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview")
#             
#             return
# 
#         try:
#             timestep = self._get_latest_timestep(self.default_parameters["thermal_xdmf_path"])
#             mesh, u_data = self._load_mesh_and_solution(timestep)
#             mesh.point_data["temperature"] = u_data
#             meshio.write(self.default_parameters["vtk_output_path"], mesh)
# 
#             if plot_pyvista:
#                 self._plot_with_pyvista(self.default_parameters["vtk_output_path"], "temperature")
# 
#         except Exception as e:
#             print(f"Full-field plotting failed: {e}")
# 
#     def _get_latest_timestep(self, xdmf_path):
#         tree = ET.parse(xdmf_path)
#         time_elements = tree.findall(".//Time")
#         if not time_elements:
#             raise RuntimeError("No <Time> elements in XDMF.")
#         return str(max(int(float(el.attrib["Value"])) for el in time_elements))
# 
#     def _load_mesh_and_solution(self, timestep):
#         mesh_path = self.default_parameters["mesh_only_xdmf_path"]
#         if not os.path.isfile(mesh_path):
#             tree = ET.parse(self.default_parameters["thermal_xdmf_path"])
#             root = tree.getroot()
#             grids = root.findall('.//Grid')
#             if not grids:
#                 raise RuntimeError("No Grid elements in the XDMF file.")
#             new_root = ET.Element(root.tag, root.attrib)
#             domain = ET.SubElement(new_root, "Domain")
#             domain.append(grids[0])
#             ET.ElementTree(new_root).write(mesh_path)
# 
#         mesh = meshio.read(mesh_path)
#         dataset_path = f"Function/temperature/{timestep}"
#         with h5py.File(self.default_parameters["thermal_h5py_path"], "r") as f:
#             if dataset_path not in f:
#                 raise KeyError(f"Missing dataset '{dataset_path}' in HDF5.")
#             u_data = f[dataset_path][()].flatten()
#         return mesh, u_data
# 
#     def _plot_with_pyvista(self, vtk_output_path, field_name):
#         pv_mesh = pv.read(vtk_output_path)
#         pv_mesh.plot(scalars=field_name, cmap="viridis", show_edges=True)
# =============================================================================
#%%