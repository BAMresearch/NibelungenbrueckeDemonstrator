from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
import os
import traceback
from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator import Orchestrator
import matplotlib.pyplot as plt
from datetime import datetime

app = FastAPI()

class OrchestratorManager:
    def __init__(self):
        self.orchestrator = None

    def initialize(self, file_path: str):
        """Initializes the orchestrator with the given file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.orchestrator = Orchestrator(file_path)

    def run_computation(self, input_values: list, model_to_run: str):
        """Runs the computation using the initialized orchestrator."""
        if self.orchestrator is None:
            raise RuntimeError("Orchestrator not initialized")
        # Ensure you handle each value in the list correctly in your computation
        self.orchestrator.run(input_values, model_to_run)

    def get_json_content(self, file_path: str):
        """Reads and returns JSON content from the specified file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r') as file:
            return json.load(file)

    def graph_input_virtualsensor(self, file_path: str):
        """Creates a graph from JSON data, plotting virtual_sensor_output vs Input_parameter."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r") as file:
            data = json.load(file)

        # Extract data
        virtual_sensor_output = data.get("virtual_sensor_output", [])
        input_parameter = data.get("Input_parameter", [])

        # Check if lengths match
        if len(virtual_sensor_output) != len(input_parameter):
            raise ValueError("Length of virtual_sensor_output does not match the length of Input_parameter.")

        plt.figure(figsize=(12, 6))

        # Plot Virtual Sensor Output vs Input Data
        plt.plot(input_parameter, virtual_sensor_output, label='Virtual Sensor Output vs Input Parameter', marker='x', linestyle='--', color='green')
        plt.xlabel('Input Parameter')
        plt.ylabel('Virtual Sensor Output')
        plt.title('Virtual Sensor Output vs Input Parameter')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        # Show the plot
        plt.show()
        plt.close()




    def graph_creation(self, input_list: list, file_path: str):
        """Creates a graph from the input list and JSON data."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r") as file:
            data = json.load(file)

        # Extract data
        real_sensor_output = data.get("real_sensor_output", [])
        virtual_sensor_output = data.get("virtual_sensor_output", [])
        time_strs = data.get("time", [])
        
        # Convert time strings to datetime objects
        try:
            times = [datetime.strptime(t, "%y-%m-%d %H:%M:%S") for t in time_strs]
        except ValueError as e:
            raise ValueError(f"Error parsing time data: {e}")

        plt.figure(figsize=(12, 6))

        # Plot Real Sensor Output vs Time
        plt.plot(times, real_sensor_output, label='Real Sensor Output', marker='o', linestyle='-', color='blue')

        # Plot Virtual Sensor Output vs Time
        plt.plot(times, virtual_sensor_output, label='Virtual Sensor Output', marker='x', linestyle='--', color='orange')

        # Check if the length of input_list and virtual_sensor_output match
        if len(input_list) == len(virtual_sensor_output):
            # Plot Virtual Sensor Output vs Input Data
            plt.figure(figsize=(12, 6))
            plt.plot(input_list, virtual_sensor_output, label='Virtual Sensor Output vs Input Data', marker='x', linestyle='--', color='green')
            plt.xlabel('Input Data')
            plt.ylabel('Virtual Sensor Output')
            plt.title('Virtual Sensor Output vs Input Data')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()
        else:
            print("Warning: Length of input_list does not match the length of virtual_sensor_output. Skipping this plot.")

        # Show the initial plot
        plt.figure(figsize=(12, 6))
        plt.plot(times, real_sensor_output, label='Real Sensor Output', marker='o', linestyle='-', color='blue')
        plt.plot(times, virtual_sensor_output, label='Virtual Sensor Output', marker='x', linestyle='--', color='orange')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title('Sensor Outputs vs Time')
        plt.grid(True)
        plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
        plt.legend()
        plt.tight_layout()
        plt.show()
        plt.close()



orchestrator_manager = OrchestratorManager()

class Parameters(BaseModel):
    E: list  # Expect a list of floats
    model_to_run: str = Field(..., alias='model_to_run')

@app.post("/initialize_orchestrator")
async def initialize_orchestrator():
    file_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/settings/digital_twin_default_parameters.json"

    try:
        orchestrator_manager.initialize(file_path)
        return {"message": "Orchestrator initialized successfully"}
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Initialization error: {str(e)}\n{error_trace}")

@app.post("/run_computation")
async def run_computation(params: Parameters):
    try:
        orchestrator_manager.run_computation(params.E, params.model_to_run)
        json_file_path = f"../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/{params.model_to_run}.json"
        json_content = orchestrator_manager.get_json_content(json_file_path)
        #orchestrator_manager.graph_creation(params.E, json_file_path)
        orchestrator_manager.graph_input_virtualsensor(json_file_path)

        return {"json_content": json_content}
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Computation error: {str(e)}\n{error_trace}")
