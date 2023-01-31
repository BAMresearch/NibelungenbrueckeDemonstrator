import os

def check_path_exists(path):
    'Checks if a path exists with an if statement (always checked)'
    
    if not os.path.exists(path):
        raise FileNotFoundError("Path " + path + " doesn't exist.")

def assert_path_exists(path):
    'Checks if a path exists with an assert (usually turned off in deployment)'
    
    assert os.path.exists(path), "Path " + path + " doesn't exist."

def check_lists_same_length(list_1, list_2, m:str):
    'Checks if two lists/dicts are the same lenght'

    if not len(list_1) == len(list_2):
        raise Exception(m)

def assert_lists_same_length(list_1, list_2, m:str):
    'Checks if two lists/dicts are the same lenght'

    assert len(list_1) == len(list_2), m