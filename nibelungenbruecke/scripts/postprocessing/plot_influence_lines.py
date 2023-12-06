import matplotlib.pyplot as plt
import numpy as np
from nibelungenbruecke.scripts.utilities.loaders import load_influence_lines, load_sensors

def plot_influence_lines(parameters:dict):
    ''' Plot a list of influence lines from a h5 file into np.arrays'''

    input_parameters = _get_default_parameters()
    for key, value in parameters.items():
        input_parameters[key] = value
    
    parameters = input_parameters

    sensors_path = parameters["sensors_path"]
    influence_lines_path = parameters["influence_lines_path"]
    output_path = parameters["output_path"]
    output_format = parameters["output_format"]
    show = parameters["show"]
    sensors = load_sensors(sensors_path)
    influence_lines = load_influence_lines(influence_lines_path, sensors)
    for name, sensor in influence_lines.items():
        plt.plot(sensor["time"], sensor["displacements"][:,1], label=name)
    plt.legend()
    plt.savefig(output_path + "." + output_format)
    if show:
        plt.show()
    return

def _get_default_parameters():
    return {
        "sensors_path": "input/sensors/sensors_displacements.json",
        "influence_lines_path": "input/data/line_test.h5",
        "output_path": "output/figures/influence_lines",
        "output_format": "png"
    }