from nibelungenbruecke.scripts.utilities.checks import assert_path_exists
from nibelungenbruecke.scripts.utilities.request_api import request_sensor_data_MKP, request_sensor_data_PVGIS
from nibelungenbruecke.scripts.data_generation.generator_model_base_class import GeneratorModel
import pandas as pd


class WeatherAPIGenerator(GeneratorModel):
    ''' Generator of weather data from MKP API.'''

    def __init__(self, model_path:str, sensor_positions_path: str, model_parameters: dict, output_parameters: dict = None):

        default_parameters = self._get_default_parameters()
        for key, value in default_parameters.items():
            if key not in model_parameters:
                model_parameters[key] = value

        self.model_parameters = model_parameters
        self.output_parameters = output_parameters

    def Generate(self):
        ''' Generate the data from the start'''

        self.GenerateData()

    def LoadGeometry(self):
        ''' Load the meshed geometry from a .msh file'''
        # Not needed for weather data
        pass
        
    def GenerateModel(self):
        ''' Generate the FEM model.'''
        # Not needed for weather data
        pass

    def GenerateData(self):
        ''' Call the APIs and generate the data'''
        # Differentiate sensors from different APIs
        mkp_sensors = [sensor for sensor in self.model_parameters["sensors"] if sensor["sensor_origin"] == "MKP_API"]
        pvgis_sensors = [sensor for sensor in self.model_parameters["sensors"] if sensor["sensor_origin"] == "PVGIS"]
        other_sensors = [sensor for sensor in self.model_parameters["sensors"] if sensor["sensor_origin"] not in ["MKP_API", "PVGIS"]]
        if len(other_sensors) != 0:
            raise ValueError("Unknown sensor origin: {}".format([sensor["sensor_origin"] for sensor in other_sensors]))

        df_data = None
        # Call the APIs
        ## MKP
        mkp_sensors_names = [sensor["sensor_name"] for sensor in mkp_sensors]
        if len(mkp_sensors_names) != 0:
            df_mkp = request_sensor_data_MKP(self.model_parameters["start_time"], self.model_parameters["end_time"], self.model_parameters["secrets_path"],mkp_sensors_names)

            if df_data is None:
                df_data = df_mkp.rename(columns={sensor["sensor_name"]: sensor["data_name"] for sensor in mkp_sensors})
            else:
                df_data = df_data.join(df_mkp.rename(columns={sensor["sensor_name"]: sensor["data_name"] for sensor in mkp_sensors}))

        ## PVGIS
        # Group sensors by location
        if len(pvgis_sensors) != 0:
            grouped_pvgis_sensors = {}
            for sensor in pvgis_sensors:
                location = tuple(sensor["sensor_location"])
                if location not in grouped_pvgis_sensors:
                    grouped_pvgis_sensors[location] = []
                grouped_pvgis_sensors[location].append(sensor)
            # Call the API for each location
            for location, sensors in grouped_pvgis_sensors.items():
                df_pvgis_location = request_sensor_data_PVGIS(self.model_parameters["start_time"], self.model_parameters["end_time"], location)
                sensors_names = [sensor["sensor_name"] for sensor in sensors]
                df_pvgis_location = df_pvgis_location[sensors_names]
                if df_data is None:
                    df_data = df_pvgis_location.rename(columns={sensor["sensor_name"]: sensor["data_name"] for sensor in sensors})
                else:
                    df_data = df_data.join(df_pvgis_location.rename(columns={sensor["sensor_name"]: sensor["data_name"] for sensor in sensors}))

                    df_data.index = pd.to_datetime(df_data.index)
        
        ## Preprocessing


        # Fill in missing values to the same rate
        df_data = df_data.ffill().bfill()

        # Downsample the data to the specified sample rate
        df_data = df_data.resample(self.model_parameters["sample_rate"]).mean()
        
        # Fill in missing values with intermediate values
        df_data = df_data.interpolate()

        # Save DataFrame to HDF5 with metadata
        sensor_metadata = {sensor["data_name"]: sensor for sensor in self.model_parameters["sensors"]}
        storedata = pd.HDFStore(self.output_parameters["output_path"]+self.output_parameters["output_format"], mode='w')
        storedata.put(self.output_parameters["output_key"], df_data, format='table', data_columns=True)
        storedata.get_storer(self.output_parameters["output_key"]).attrs.metadata = sensor_metadata
        storedata.close()


    @staticmethod
    def _get_default_parameters():
        ''' Get the default parameters for the model'''
        default_parameters = {
            "model_name":"weather_api_data",
            "start_time": "2024-01-01T01:00:00Z",
            "end_time": "2024-01-05T01:00:00Z",
            "secrets_path": "input/secrets/secrets.json",
            "sample_rate": "1h",
            "sensors": [{
                "sensor_name": "F_plus_000TA_KaS-o-_Avg1",
                "sensor_type": "temperature",
                "sensor_origin": "MKP_API",
                "sensor_unit": "°C",
                "sensor_location": [0.0, 0.0, 0.0],
                "data_name": "air_temperature",
            },
            {
                "sensor_name": "F_plus_000S_KaS-o-_Avg1",
                "sensor_type": "irradiation",
                "sensor_origin": "MKP_API",
                "sensor_unit": "W/m²",
                "sensor_location": [0.0, 0.0, 0.0],
                "data_name": "shortwave_irradiation",
            },
            {
                "sensor_name": "E_plus_040TU_HS--u-_Avg1",
                "sensor_type": "temperature",
                "sensor_origin": "MKP_API",
                "sensor_unit": "°C",
                "sensor_location": [0.0, 0.0, 0.0],
                "data_name": "bridge_temperature",
            },
            {
                "sensor_name": "wind_speed",
                "sensor_type": "wind_speed",
                "sensor_origin": "PVGIS",
                "sensor_unit": "m/s",
                "sensor_location": [ 52.5, 13.4],
                "data_name": "wind_speed",
            },
            {
                "sensor_name": "wind_direction",
                "sensor_type": "wind_direction",
                "sensor_origin": "PVGIS",
                "sensor_unit": "°",
                "sensor_location": [ 52.5, 13.4],
                "data_name": "wind_direction",
            }],
        }

        return default_parameters
    
if __name__ == "__main__":
    output_path = "example.hdf5"
    outuput_key = "example_key"
    api_key_path = "/home/darcones/Projects/API_keys/mkp.txt"
    model_parameters = {"secrets_path": api_key_path}
    output_parameters = {"output_path": output_path, "output_key": outuput_key}
    weather_api_generator = WeatherAPIGenerator(None, None, model_parameters, output_parameters)
    weather_api_generator.Generate()