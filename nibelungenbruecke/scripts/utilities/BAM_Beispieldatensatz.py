from os import PathLike
from typing import Union, Tuple

import pandas as pd
import json
import datetime


def load_bam(file: Union[str, bytes, PathLike],
             columns: list) -> Tuple[pd.DataFrame, dict]:
    # load file
    with open(file=file, mode='r') as f:
        j = json.load(f)
    # create objects
    df = pd.DataFrame(columns=j['df']['columns'], index=j['df']['index'], data=j['df']['data'])
    meta = j['meta']
    # filter by columns given
    df_filtered = df[columns]
    meta_filtered = {column: meta[column] for column in columns}

    return df_filtered, meta_filtered


def save_bam(df: pd.DataFrame, meta: dict, path: str) -> None:
    # bring data into required format
    df_dict = json.loads(df.to_json(orient='split'))
    output = json.dumps({'df': df_dict, 'meta': meta})
    # write to file
    filename = path + '/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json'
    with open(filename, 'x') as f:
        f.write(output)


if __name__ == '__main__':
    file_ = '/home/msoenmez/Desktop/Exper/20230215092338.json'
    columns_ = ['Temp', 'Move']

    df, meta = load_bam(file_, columns_)
    #save_bam(df, meta)
        
        
# file = '20230215092338.json'
# columns = ['Temp', 'Move']

#df, meta = load_bam(file_, columns_)
#save_bam(df, meta)

