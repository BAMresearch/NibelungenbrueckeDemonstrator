
"Testing to see if the class of data retrieving from API is working correctly"

from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request
import pandas as pd
import numpy as np

#%%
# Sensors output from webpage
#path = 'E+080DU_HSN-u-_d10-data-14 May 2024, 17 32 45.csv'
path = 'E+040TU_HS--o--data-14 May 2024, 18 22 54.csv'
DU_data = pd.read_csv(path)


#%%
# Sensors outputs through api request
api = API_Request()
api.body = {'startTime': '2024-05-01T16:00:00Z',
 'endTime': '2024-05-01T18:00:00Z',
 'meta_channel': True,
 'columns': []}

api.body = {
    "startTime": "2024-05-01T08:00:00Z",
    "endTime": "2024-05-14T20:00:00Z",
    "meta_channel": True,
    "columns": ['E_plus_413TU_HS--o-_Avg1']
    }

output_data = api.fetch_data()
DU_data_api = output_data["E_plus_080DU_HSN-u-_Avg1"]

# Convert to numpy array for easier manipulation
data_array = np.array(output_data)

# Reshape the array to have 10 columns
reshaped_data = data_array.reshape(-1, 10)

# Calculate the average across the columns (axis 1)
averaged_data = reshaped_data.mean(axis=1)

# Convert back to list if necessary
averaged_data_list = averaged_data.tolist()

print(averaged_data_list)
