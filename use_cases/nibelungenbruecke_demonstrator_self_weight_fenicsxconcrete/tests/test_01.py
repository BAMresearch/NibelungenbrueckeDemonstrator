#import os
#print(os.getcwd())

##TODO: The importing error needs t solved first!!!
"Testing to see if the class of data retrieving from API is working correctly"

from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request
api = API_Request()
print(api.fetch_data())


#Manual_data_from_MKP = 