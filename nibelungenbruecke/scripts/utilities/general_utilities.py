def modify_key(data, key, new_value, path=[]):
    "Looks for a key in a dictionary and modifies it"
    if path == []:
        if key in data:
            data[key] = new_value
            return True
    else:
        for k in path:
            data = data[k]
        if modify_key(data, key, new_value, []):
            return True
    raise Exception(f"[Inference response] Key {key} not present in path.")