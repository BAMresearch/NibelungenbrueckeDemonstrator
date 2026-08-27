import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import numpy as np

BASE_URL = "http://127.0.0.1:8001"

# Authentication #TODO
USERNAME = "user"
PASSWORD = "password"

url = f"{BASE_URL}/initialize_orchestrator"

try:
    response = requests.post(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    response.raise_for_status()
    df = pd.DataFrame(response.json())
except requests.exceptions.RequestException as e:
    raise f"Error during initialization: {e}"
    
    


# def initialize_orchestrator():
#     url = f"{BASE_URL}/initialize_orchestrator"
#     try:
#         global df
#         response = requests.post(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
#         response.raise_for_status()
#         #print("Orchestrator initialized successfully.")
#         #print("Response JSON:", response.json())
#         df = pd.DataFrame(np.ndarray(response.json()))
#         print(df)
#         return df
#     except requests.exceptions.RequestException as e:
#         print(f"Error during initialization: {e}")

# if __name__ == "__main__":
#     initialize_orchestrator()
