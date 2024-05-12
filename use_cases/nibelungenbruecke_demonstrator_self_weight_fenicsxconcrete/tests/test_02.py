## Testing of displacement model validity and real sensor data vs virtual sensor data
#import os
#print(os.getcwd())

from nibelungenbruecke.scripts.data_generation.displacement_generator_fenicsxconcrete import GeneratorFeniCSXConcrete
import json

path = "../input/settings/generate_data_parameters.json"
with open(path, "r") as file:
    parameters = json.load(file)

model_path = parameters["model_path"]
generation_models_list = parameters["generation_models_list"]
sensor_positions_path = generation_models_list[0]["sensors_path"]
model_parameters = generation_models_list[0]["model_parameters"]

displacement_generator_test_model = GeneratorFeniCSXConcrete(model_path, sensor_positions_path, model_parameters)

x = id(displacement_generator_test_model)


from nibelungenbruecke.scripts.data_generation.displacement_generator_fenicsxconcrete import GeneratorFeniCSXConcrete
import json

path = "../input/settings/generate_data_parameters.json"
with open(path, "r") as file:
    parameters = json.load(file)

model_path = parameters["model_path"]
generation_models_list = parameters["generation_models_list"]
sensor_positions_path = generation_models_list[0]["sensors_path"]
model_parameters = generation_models_list[0]["model_parameters"]

displacement_generator_test_model = GeneratorFeniCSXConcrete(model_path, sensor_positions_path, model_parameters)

y = id(displacement_generator_test_model)