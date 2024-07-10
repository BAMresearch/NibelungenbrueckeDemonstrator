import json
from invoke import task
from nibelungenbruecke.scripts.digital_twin_orchestrator.orchestrator import Orchestrator

@task
def task_digital_twin():    
    data_parameters_path = "./input/settings/generate_data_parameters.json"
    with open(data_parameters_path, 'r') as f:
        data_parameters = json.load(f)
    
    orchestrator = Orchestrator()
    orchestrator.run(data_parameters)

    output_path = data_parameters["output_parameters"]["output_path"]
    output_format = data_parameters["output_parameters"]["output_format"]
    output_target = output_path + output_format

    print(f"Digital twin task completed. Output generated at: {output_target}")

    
    """
    return {'actions': [(Orchestrator,[],{})],
            'file_dep': [data_parameters["model_path"], data_parameters_path],
            'targets': [data_parameters["output_parameters"]["output_path"]+data_parameters["output_parameters"]["output_format"]],
            'uptodate': [True]}

    """


#%%

def task():
    data_parameters_path = "./input/settings/generate_data_parameters.json"
    with open(data_parameters_path, 'r') as f:
        data_parameters = json.load(f)
        
    orchestrator = Orchestrator()
    orchestrator.run(data_parameters)
    
    


if __name__ == "__main__":
        
    task()
    
    