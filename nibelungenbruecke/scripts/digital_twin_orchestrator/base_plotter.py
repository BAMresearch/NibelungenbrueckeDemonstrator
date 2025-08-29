from abc import ABC, abstractmethod
import os
import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
import pyvista as pv
import meshio
import xml.etree.ElementTree as ET
import pandas as pd


class BasePlotter(ABC):
    def __init__(self, problem=None, simulation_parameters=None, default_parameters=None, api_data_frame=None):
        self.problem = problem
        self.simulation_parameters = simulation_parameters or {}
        self.default_parameters = default_parameters or {}
        self.api_dataFrame = api_data_frame
        self.sensor_data_json = {}
        
        self.output_file = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/sensor_timeseries.json"
        
        self.extract_virtual_sensor_data(self.output_file)

    def extract_virtual_sensor_data(self, output_file):
        sensors = self.problem.sensors
        self.sensor_data_json = {}

        for sensor_name, sensor in sensors.items():
            data = sensor.data
            times = sensor.time[-len(data):]
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

    @abstractmethod
    def plot(self, *args, **kwargs):
        """Each subclass implements its own plotting or data extraction logic."""
        pass


class FullFieldPlotter(BasePlotter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def plot(self, plot_pyvista=True):      ##TODO: Keep it as "False" fro J4NFDI interface!!
        if not self.simulation_parameters.get("full_field_results", False):
            print("Full-field results are available at the following path.")
            print("NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview")
            
            return

        try:
            timestep = self._get_latest_timestep(self.default_parameters["thermal_xdmf_path"])
            mesh, u_data = self._load_mesh_and_solution(timestep)
            mesh.point_data["temperature"] = u_data
            meshio.write(self.default_parameters["vtk_output_path"], mesh)

            if plot_pyvista:
                self._plot_with_pyvista(self.default_parameters["vtk_output_path"], "temperature")

        except Exception as e:
            print(f"Full-field plotting failed: {e}")

    def _get_latest_timestep(self, xdmf_path):
        tree = ET.parse(xdmf_path)
        time_elements = tree.findall(".//Time")
        if not time_elements:
            raise RuntimeError("No <Time> elements in XDMF.")
        return str(max(int(float(el.attrib["Value"])) for el in time_elements))

    def _load_mesh_and_solution(self, timestep):
        mesh_path = self.default_parameters["mesh_only_xdmf_path"]
        if not os.path.isfile(mesh_path):
            tree = ET.parse(self.default_parameters["thermal_xdmf_path"])
            root = tree.getroot()
            grids = root.findall('.//Grid')
            if not grids:
                raise RuntimeError("No Grid elements in the XDMF file.")
            new_root = ET.Element(root.tag, root.attrib)
            domain = ET.SubElement(new_root, "Domain")
            domain.append(grids[0])
            ET.ElementTree(new_root).write(mesh_path)

        mesh = meshio.read(mesh_path)
        dataset_path = f"Function/temperature/{timestep}"
        with h5py.File(self.default_parameters["thermal_h5py_path"], "r") as f:
            if dataset_path not in f:
                raise KeyError(f"Missing dataset '{dataset_path}' in HDF5.")
            u_data = f[dataset_path][()].flatten()
        return mesh, u_data

    def _plot_with_pyvista(self, vtk_output_path, field_name):
        pv_mesh = pv.read(vtk_output_path)
        pv_mesh.plot(scalars=field_name, cmap="viridis", show_edges=True)


class RealVsVirtualPlotter(BasePlotter):    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def plot(self, sensor_mapping=None):
        json_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/sensor_timeseries.json"
        if not self.sensor_data_json and os.path.exists(json_path):
            with open(json_path, "r") as f:
                self.sensor_data_json = json.load(f)

        if sensor_mapping is None:
            sensor_mapping = {
                "E_plus_040TU_HS--o-_Avg1": "Sensor_o",
                "E_plus_040TU_HSN-m-_Avg1": "Sensor_n",
                "E_plus_040TU_HSS-m-_Avg1": "Sensor_s",
                "E_plus_040TU_HS--u-_Avg1": "Sensor_u",
            }

        df = self.api_dataFrame + 273.15
        measured_times = df.index

        for df_sensor_name, json_sensor_key in sensor_mapping.items():
            if json_sensor_key not in self.sensor_data_json or df_sensor_name not in df.columns:
                continue

            model_data = self.sensor_data_json[json_sensor_key]
            model_times = np.array([entry["time"] for entry in model_data])
            model_values = np.array([entry["value"] for entry in model_data])

            interp_model_values = np.interp(
                (measured_times - measured_times[0]).total_seconds(),
                model_times - model_times[0],
                model_values
            )

            plt.figure(figsize=(10, 4))
            plt.plot(measured_times, df[df_sensor_name], label="Measurement")
            plt.plot(measured_times, interp_model_values, "--", label="Model")
            plt.title(f"Sensor Comparison: {df_sensor_name} vs {json_sensor_key}")
            plt.xlabel("Time")
            plt.ylabel("Temperature (K)")
            plt.legend()
            plt.tight_layout()
            plt.show()


class VirtualSensorPlotter(BasePlotter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def plot(self):
        #if not hasattr(self.problem, "sensors"):
        #    raise AttributeError("Missing 'problem.sensors'.")

        selected_sensors = {x["name"] for x in self.simulation_parameters.get("virtual_sensor_positions", [])}

        for name, sensor in self.problem.sensors.items():
            if name not in selected_sensors:
                continue

            times, values = sensor.time[-len(sensor.data):], [
                float(d[0]) if isinstance(d, np.ndarray) else float(d)
                for d in sensor.data
            ]

            if len(times) != len(values):
                print(f"Skipping '{name}': mismatched time/data lengths.")
                continue

            plt.figure(figsize=(10, 4))
            plt.plot(times, values, "-b")
            plt.title(f"Virtual Sensor: {name}")
            plt.xlabel("Time (s)")
            plt.ylabel("Value")
            plt.grid()
            plt.tight_layout()
            plt.show()



class AdaptedParametersChecker(BasePlotter):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def execute(self):
        path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/results/inference_pilot_noise_daniel.json"
        with open(path, "r") as f:
            data = json.load(f)

        params = data["parameter_list_parameters"]
        problem_params = self.problem.p

        print(f"{'Parameter':40} | {'Calibrated':>15} | {'Adapted':>15}")
        print("-" * 75)
        for param in params:
            name = param.get("name", "N/A")
            value = param.get("value", "—")
            adapted = problem_params.get(name, "—")
            print(f"{name:40} | {str(value):>15} | {str(adapted):>15}")
