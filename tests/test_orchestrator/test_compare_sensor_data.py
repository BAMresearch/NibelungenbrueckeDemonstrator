from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request
from nibelungenbruecke.scripts.digital_twin_orchestrator.displacement_model import DisplacementModel
import pandas as pd
import numpy as np

def fetch_api_data(api):
    return api.fetch_data()

def initialize_displacement_model(model_path, model_parameters, dt_path):
    return DisplacementModel(model_path, model_parameters, dt_path)

def compare_sensor_data(api_data, displacement_model, sensor_list):
    results = []
    for sensor in sensor_list:
        real_data = api_data[sensor].iloc[-1]
        virtual_data = displacement_model.problem.sensors.get(sensor, None).data[-1][0]
        difference = abs(real_data - virtual_data)
        results.append((sensor, real_data, virtual_data, difference))
    return results

def test_compare_sensor_data():
    # Initialize API request object
    api = API_Request()

    # Fetch data from the API
    api_data = fetch_api_data(api)

    # Define inputs for the DisplacementModel class
    model_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh'
    model_parameters = {'model_name': 'displacements',
     'df_output_path': '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_df_output.csv',
     'meta_output_path': '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/sensors/API_meta_output.json',
     'MKP_meta_output_path': '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_meta_output.json',
     'MKP_translated_output_path': '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/MKP_translated.json',
     'virtual_sensor_added_output_path': '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json',
     'paraview_output': True,
     'paraview_output_path': '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/paraview',
     'material_parameters': {},
     'tension_z': 0.0,
     'boundary_conditions': {'bc1': {'model': 'clamped_boundary',
       'side_coord': 0.0,
       'coord': 2},
      'bc2': {'model': 'clamped_boundary', 'side_coord': 95.185, 'coord': 2}}}
    
    dt_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_parameters.json'
    

    # Initialize and solve the DisplacementModel
    displacement_model = initialize_displacement_model(model_path, model_parameters, dt_path)
    displacement_model.solve()

    # List of sensors to compare
    sensor_list = ['E_plus_413TU_HSS-m-_Avg1', 'E_plus_080DU_HSN-o-_Avg1', 'E_plus_080DU_HSN-u-_Avg1']

    # Compare sensor data
    comparison_results = compare_sensor_data(api_data, displacement_model, sensor_list)

    # Print and assert results for testing
    for sensor, real_data, virtual_data, difference in comparison_results:
        print(f"Sensor: {sensor}")
        print(f"Real Data (API): {real_data}")
        print(f"Virtual Data (Model): {virtual_data}")
        print(f"Difference: {difference}")
        print()


# Run the test function
if __name__ == "__main__":
    test_compare_sensor_data()
