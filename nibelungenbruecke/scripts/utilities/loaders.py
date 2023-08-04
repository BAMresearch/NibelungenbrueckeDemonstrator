import json
import h5py

from nibelungenbruecke.scripts.utilities.sensors import *

def load_sensors(sensors_path: str):
    ''' Load a list of sensors from a json into Sensor() variables'''
    with open(sensors_path, 'r') as f:
        sensors = json.load(f)

    loaded_sensors = []
    for sensor_name, sensor_params in sensors.items():
        loaded_sensors.append(load_sensor(sensor_params))

    return loaded_sensors

def load_sensor(sensor_params: dict):
    ''' Loads a specific sensor from is parameters'''
    if "where" in sensor_params:
        sensor = globals()[sensor_params["type"]](sensor_params["where"])
    else:
        sensor = globals()[sensor_params["type"]]()

    return sensor

def load_influence_lines(influence_lines_path: str, list_of_sensors: list):
    ''' Load a list of influence lines from a h5 file into np.arrays'''
    with h5py.File(influence_lines_path, 'r') as f:
        influence_lines = {}
        for sensor in list_of_sensors:
            displacements = f[sensor]["Data"][:]
            time = f[sensor]["Time"][:]
            influence_lines[sensor] = {"displacements": displacements, "time": time}

    return influence_lines