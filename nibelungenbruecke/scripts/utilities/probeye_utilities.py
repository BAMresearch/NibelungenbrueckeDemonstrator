import json
import h5py
import numpy as np
import pandas as pd

# local imports (problem definition)
from probeye.definition.inverse_problem import InverseProblem
import probeye.definition.distribution
from probeye.definition.sensor import Sensor

def add_parameter_wrapper(problem: InverseProblem, parameters: dict):
    '''Loads a parameter to the inverse problem from its definition in the json file.'''
    input_parameters={
        "prm_type": "not defined",
        "dim": 1,
        "domain": "(-oo, +oo)",
        "value": None,
        "prior": None,
        "info": "No explanation provided",
        "tex": None,
    }
    for key, value in parameters.items():
        input_parameters[key] = value

    if not input_parameters["prior"] is None:
        prior_model_cls = getattr(probeye.definition.distribution, parameters["prior"].pop("name"))
        input_parameters["prior"] = prior_model_cls(**parameters["prior"])

    problem.add_parameter(**input_parameters)

def add_experiment_wrapper(problem: InverseProblem, parameters: dict):
    '''Loads a experiment to the inverse problem from its definition in the json file.'''

    input_parameters={
        "name": None,
        "input_data_path": None,
        "data_format": ".h5",
        "sensor_names": [],
        "data_values": [],
        "parameter_names": [],
        "index_or_values": []
    }
    for key, value in parameters.items():
        input_parameters[key] = value

    if input_parameters["data_format"] == ".h5":
        with h5py.File(input_parameters["input_data_path"], 'r') as f:
            data = {}
            for parameter, sensor, data_value in zip(input_parameters["parameter_names"],input_parameters["sensor_names"], input_parameters["data_values"]):
                data[parameter] = np.squeeze(f[sensor][data_value][()])
    elif input_parameters["data_format"] == "pandash5":
        with pd.HDFStore(input_parameters["input_data_path"], 'r') as f:
            data = {}
            if input_parameters["index_or_values"] == []:
                input_parameters["index_or_values"] = ["values"]*len(input_parameters["parameter_names"])
            for parameter, sensor, data_value, index_flag in zip(input_parameters["parameter_names"],input_parameters["sensor_names"], input_parameters["data_values"], input_parameters["index_or_values"]):
                try:
                    if index_flag == "index":
                        data[parameter] = np.squeeze(f[data_value][sensor].index.to_numpy())
                    elif index_flag == "values":
                        data[parameter] = np.squeeze(f[data_value][sensor].values)
                except AttributeError:
                    data[parameter] = float(f[data_value][sensor]) #TODO: It transforms everything to float because numpy types, which may be a problem in the future
    else:
        raise Exception(f"[Add Experiment] Data format {input_parameters['data_format']} not implemented.")

    problem.add_experiment(name = input_parameters["name"], sensor_data = data)

def load_probeye_sensors(sensors_path: str):
    ''' Load a list of probeye sensors from a json into Sensor() variables'''
    # TODO: The sensor definition should be unified, right now probeye and FenicsConcrete sensors are mixed
    with open(sensors_path, 'r') as f:
        sensors = json.load(f)

    loaded_sensors = []
    for sensor_name, sensor_params in sensors.items():
        loaded_sensors.append(Sensor(name = sensor_name, **sensor_params))

    return loaded_sensors

