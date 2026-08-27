import json
from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator import Orchestrator

def task_digital_twin():
    """Run the digital twin task."""
    data_parameters_path = "./input/settings/generate_data_parameters.json"

    with open(data_parameters_path, 'r') as f:
        data_parameters = json.load(f)

    # Define output target
    output_path = data_parameters["output_parameters"]["output_path"]
    output_format = data_parameters["output_parameters"]["output_format"]
    output_target = output_path + output_format

    return {
        'actions': [(run_digital_twin_task, [data_parameters_path])],
        'file_dep': [data_parameters_path, data_parameters["model_path"]],
        'targets': [output_target],
        'uptodate': [True]
    }

def run_digital_twin_task(data_parameters_path):
    """Run the orchestrator with the given parameters."""
    with open(data_parameters_path, 'r') as f:
        data_parameters = json.load(f)

    orchestrator = Orchestrator()
    orchestrator.run(data_parameters)

    print(f"Digital twin task completed. Output generated at: {data_parameters['output_parameters']['output_path']}{data_parameters['output_parameters']['output_format']}")
