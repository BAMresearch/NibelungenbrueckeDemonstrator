import importlib

def postprocess_run(parameters: dict):
    
    for task, load_task in parameters.items():
        module = importlib.import_module("nibelungenbruecke.scripts.postprocessing."+task)
        functions = {name: value for name, value in vars(module).items() if callable(value)and name.endswith("_run")}
        for name, value in functions.items():
            value(load_task)