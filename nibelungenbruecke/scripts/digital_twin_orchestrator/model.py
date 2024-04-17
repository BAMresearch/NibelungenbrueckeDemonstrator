import json
from fenicsxconcrete.util import ureg

from nibelungenbruecke.scripts.digital_twin_orchestrator.displacement_model import DisplacementModel

class Model:
    def __init__(self, model_path, model_parameters):
        self.DM = DisplacementModel(model_path, model_parameters)
        
    def reinitialize(self):
        self.DM.LoadGeometry()
        self.DM.GenerateModel()
        self.DM.GenerateData()    
    
    def update_input(self, sensor_input):
        if isinstance(sensor_input, (int, float)):
            self.DM.default_p["E"] = sensor_input * ureg("N/m^2")
            #self.sensor_in = sensor_input
            return True
        else:
            return False
        
    def solve(self):
        self.reinitialize()
        self.sensor_out = self.DM.api_dataFrame['E_plus_445LVU_HS--u-_Avg1'][-1]
        
        file_path = '/home/msoenmez/Desktop/NibelungenbrueckeDemonstrator/use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json'
        with open(file_path, 'r') as file:
            vs_data = json.load(file)
        
        self.vs_sensor_out = vs_data['virtual_sensors']['E_plus_445LVU_HS--u-_Avg1']['displacements'][-1][0]
        
    def export_output(self):
        json_path = "output_data.json"
        
        try:
            with open(json_path, 'r') as file:
                output_data = json.load(file)
                
        except FileNotFoundError:
            output_data = {}
            
        output_data.setdefault('real_sensor_data', []).append(self.sensor_out)
        output_data.setdefault('virtual_sensor_data', []).append(self.vs_sensor_out)
        
        with open(json_path, 'w') as file:
            json.dump(output_data, file)
            
        return json_path