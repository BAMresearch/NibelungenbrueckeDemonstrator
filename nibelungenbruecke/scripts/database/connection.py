import sqlite3
import numpy as np
import datetime
import pandas as pd
from typing import Optional, List, Dict, Union

class Database:
    def __init__(self, db_name="NB_database.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        self.tables_list = [
            "natural_convection_coefficient",
            "wind_forced_convection",
            "wind_forced_convection_parameter_constant",
            "wind_speed",
            "shortwave_radiation",
            "shortwave_radiation_constant",
            "shortwave_irradiation",
            "calculate_shortwave_irradiation"
        ]

        for table in self.tables_list:
            self.cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table} (
                    time TEXT PRIMARY KEY,
                    parameter REAL
                )
            ''')
        self.conn.commit()
    
    def request_data(self, query_dict: Optional[Dict[str, Dict[str, str]]] = None) -> pd.DataFrame:
        
        tables_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", self.conn)
        table_names = tables_df["name"].tolist()
        
        merged_df = None
        
        for table in table_names:
            if query_dict and table in query_dict:
                start_time = query_dict[table]["start_time"]
                end_time = query_dict[table]["end_time"]
                query = f"SELECT * FROM {table} WHERE time BETWEEN ? AND ?"
                params = (start_time, end_time)
            else:
                query = f"SELECT * FROM {table}"
                params = None 
            
            df = pd.read_sql(query, self.conn, params=params)
            
            if "parameter" in df.columns:
                df = df.rename(columns={"parameter": table})
                
            if merged_df is None:
                merged_df = df
                
            else:
                merged_df = pd.merge(merged_df, df, on="time", how="outer")
                
        if merged_df is not None:
            merged_df = merged_df.sort_values("time").reset_index(drop=True)
            
        return merged_df
            

    def _insert_random_data(self, num_days=1000, seed=None):
        """Generate random data using NumPy and insert into tables."""
        if seed is not None:
            np.random.seed(seed)

        time_table = np.array([datetime.datetime(2022,1,1) + datetime.timedelta(days=i) for i in range(num_days)])

        data_dict = {
            "natural_convection_coefficient": np.random.normal(10, 1, num_days),
            "wind_forced_convection": np.random.normal(2, 1, num_days),
            "wind_forced_convection_parameter_constant": np.random.normal(2, 1, num_days),
            "wind_speed": np.random.normal(5, 1, num_days),
            "shortwave_radiation": np.random.normal(0, 1, num_days),
            "shortwave_radiation_constant": np.random.normal(1, 0.5, num_days),
            "shortwave_irradiation": np.random.normal(0, 1, num_days),
            "calculate_shortwave_irradiation": np.random.normal(0, 1, num_days)
        }

        for table in self.tables_list:
            parameters = data_dict[table]
            rows = [(time_table[i].isoformat(), float(parameters[i])) for i in range(num_days)]
            self.cursor.executemany(f"INSERT OR IGNORE INTO {table} (time, parameter) VALUES (?, ?)", rows)

        self.conn.commit()
        
        
    def insert_data(self, data_dict: Dict[str, Dict[str, int|float]]) -> None:
        
        for table in data_dict.keys():
            #data_dict[table]["time"] = [t.isoformat() for t in data_dict[table]["time"]]
            
            if len(data_dict[table]["time"]) != len(data_dict[table]["parameter"]):
                raise ValueError(
                    f"Parameter length ({len(data_dict[table]['parameter'])}) for table '{table}' does not match number of times ({len(data_dict[table]['time'])})"
                )
                
            else:
                rows = list(zip(data_dict[table]["time"], data_dict[table]["parameter"]))
                self.cursor.executemany(f"INSERT OR IGNORE INTO {table} (time, parameter) VALUES (?, ?)", rows)
                
        self.conn.commit()
    

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    
    #%% get complete db (tables and data for each table)
    # checkt the time ranges!
    
    db = Database()
    
    query_dict = {"natural_convection_coefficient": {"start_time": "2022-01-01T00:00:00", "end_time": "2022-01-05T00:00:00"},
                "wind_forced_convection": {"start_time": "2022-01-01T00:00:00", "end_time": "2022-01-10T00:00:00"},
                "wind_forced_convection_parameter_constant": {"start_time": "2022-04-11T00:00:00", "end_time": "2022-05-15T00:00:00"},
                "wind_speed": {"start_time": "2022-07-20T00:00:00", "end_time": "2022-08-09T00:00:00"},
                "shortwave_irradiation": {"start_time": "2023-05-16T00:00:00", "end_time": "2023-06-05T00:00:00"},
                "calculate_shortwave_irradiation": {"start_time": "2023-05-28T00:00:00", "end_time": "2023-07-05T00:00:00"},
                "shortwave_radiation_constant": {"start_time": "2024-01-21T00:00:00", "end_time": "2024-02-10T00:00:00"},
                "shortwave_radiation": {"start_time": "2024-01-14T00:00:00", "end_time": "2024-03-10T00:00:00"}}
    
    dfs = db.request_data(query_dict)
    
    dfs_complete_data = db.request_data()
    
    #%%
    insert_data_dict = {"natural_convection_coefficient": 
                               {
                                   "time": ['2024-09-27T00:00:00', '2024-09-28T00:00:00', '2024-09-29T00:00:00', '2024-09-30T00:00:00', '2024-09-31T00:00:00'],
                                   "parameter": [10, 11, 12, 10, 9]
                                   },
                               "shortwave_radiation": 
                                   {
                                       "time": ['2024-10-20T00:00:00', '2024-10-21T00:00:00', '2024-10-22T00:00:00'],
                                       "parameter": [0.1, 1.1, 1.2]
                                       }
                                   }
        
    db.insert_data(insert_data_dict)
    
    dbs_after_insertion = db.request_data()
    
    db.close()