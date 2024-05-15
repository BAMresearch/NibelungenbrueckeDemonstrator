
"Testing to see if the class of data retrieving from API is working correctly"

from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request
#from nibelungenbruecke.scripts.data_generation.displacement_generator_fenicsxconcrete import displacement_generator_fenicsxconcrete
from nibelungenbruecke.scripts.digital_twin_orchestrator.displacement_model import DisplacementModel

# API_request object called
api = API_Request()

# output of the api request assigned to data_output
data = api.fetch_data()
#print(data)

#%%
# Inputs of DisplacementModel class
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

#%%
# Comparison of extracted real sensor data with virtual sensor data

#DM = displacement_generator_fenicsxconcrete(model_path, model_parameters, dt_path)
DM = DisplacementModel(model_path, model_parameters, dt_path)
DM.solve()
#a = DM.api_dataFrame
#print(a)
#DM.problem.sensors.get(data.columns[2], None).data[0].tolist()
#%%
# Comparison of predefined sensors ('E_plus_413TU_HSS-m-_Avg1', 'E_plus_080DU_HSN-o-_Avg1', 'E_plus_080DU_HSN-u-_Avg1')

sensor_list = ['E_plus_413TU_HSS-m-_Avg1', 'E_plus_080DU_HSN-o-_Avg1', 'E_plus_080DU_HSN-u-_Avg1']

for i in sensor_list:
    print(data[i].iloc[-1], DM.problem.sensors.get(i, None).data[0][2], sep="<-->")

#K = displacement_generator_fenicsxconcrete(model_path, model_parameters, dt_path)
