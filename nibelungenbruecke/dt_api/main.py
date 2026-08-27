#%% Works for single input predict and graph is also wokring for single input but require some modifications
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
import os
import traceback
import plotly.express as px
from plotly.io import to_html

from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator import Orchestrator
import plotly.graph_objects as go
from fastapi.responses import HTMLResponse
import numpy as np
import matplotlib.pyplot as plt


app = FastAPI()

class OrchestratorManager:
    def __init__(self):
        self.orchestrator = None

    def initialize(self, file_path: str):
        """Initializes the orchestrator with the given file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.orchestrator = Orchestrator(file_path)

    def run_computation(self, input_value: dict, model_to_run: str):
        """Runs the computation using the initialized orchestrator."""
        if self.orchestrator is None:
            raise RuntimeError("Orchestrator not initialized")
        self.orchestrator.run(input_value, model_to_run)

    def get_json_content(self, file_path: str):
        """Reads and returns JSON content from the specified file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r') as file:
            return json.load(file)
        
    def graph_creation(self, data):
        fig = go.Figure()

        timestamps = data.get("df", {}).get("index", [])
        columns = data.get("df", {}).get("columns", [])
        real_values = data.get("df", {}).get("data", [])
        virtual_values = data.get("virtual_sensors", {})

        if not timestamps or not real_values or not virtual_values:
            raise ValueError("JSON file does not contain valid time-series data.")

        for i, column in enumerate(columns):
            column_values = [row[i] for row in real_values]

            # Check for virtual sensor data and interpolate if necessary
            if column in virtual_values and "displacements" in virtual_values[column]:
                virtual_column_values = [row[1] for row in virtual_values[column]["displacements"]]
                interp_virtual_values = np.interp(
                    np.linspace(0, len(column_values) - 1, len(column_values)),
                    np.linspace(0, len(column_values) - 1, len(virtual_column_values)),
                    virtual_column_values
                )
                fig.add_trace(go.Scatter(x=timestamps, y=interp_virtual_values, mode='lines', name=f"{column}_virtual", line=dict(dash="dash")))

            #fig.add_trace(go.Scatter(x=timestamps, y=column_values, mode='lines', name=column))

        # Update the layout for the graph
        fig.update_layout(title="Displacement Over Time", xaxis_title="Time", yaxis_title="Displacement")

        # Generate the graph as HTML with Plotly JS inline
        graph_html = fig.to_html(full_html=False)

        # Return the graph's HTML in a minimal wrapper
        return graph_html



orchestrator_manager = OrchestratorManager()

class Parameters(BaseModel):
    input_value: dict
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
        orchestrator_manager.run_computation(params.input_value, params.model_to_run)
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Computation error: {str(e)}\n{error_trace}")

@app.get("/create_graph", response_class=HTMLResponse)
async def create_graph():
    try:
        # Load the JSON content from file
        json_file_path = "../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/output/sensors/virtual_sensor_added_translated.json"
        json_content = orchestrator_manager.get_json_content(json_file_path)

        # Generate the HTML content with the Plotly graph
        graph_html = orchestrator_manager.graph_creation(json_content)

        # HTML with a button that triggers computation and asks for input values
        graph_with_button_html = f"""
        <html>
            <head>
                <meta http-equiv="refresh" content="100">
            </head>
            <body>
                <h2>Graph Display</h2>
                <div>{graph_html}</div>
                <button id="computeButton">Run Computation</button>
                <script>
                    document.getElementById("computeButton").onclick = function() {{
                        // Prompt for inputs
                        var rho = prompt("Please enter the value for rho (e.g., 2050):");
                        if (rho === null || rho === "") {{
                            alert("You must provide a value for rho!");
                            return;
                        }}

                        var modelToRun = prompt("Please enter the model to run (e.g., Displacement_1):");
                        if (modelToRun === null || modelToRun === "") {{
                            alert("You must provide a model to run!");
                            return;
                        }}

                        // Construct the JSON payload
                        var computationPayload = {{
                            "input_value": {{ "rho": parseFloat(rho) }},
                            "model_to_run": modelToRun
                        }};

                        // Send the POST request to /run_computation
                        fetch('/run_computation', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify(computationPayload)
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            alert('Computation Started: ' + JSON.stringify(data));
                        }})
                        .catch(error => {{
                            alert('Error during computation: ' + error);
                        }});
                    }};
                </script>
            </body>
        </html>
        """

        return HTMLResponse(content=graph_with_button_html)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating graph: {str(e)}")
