from pathlib import Path
import sqlite3
import numpy as np
import datetime
import pandas as pd
import random
import os
from typing import Optional, List, Dict, Union

class Database:
    def __init__(self, db_name="NB_database_rev1.db"):
        base_dir = Path(__file__).resolve().parent
        self.db_path = base_dir / db_name
        
        #self.db_name = db_name
        self.conn = sqlite3.connect(self.db_path)
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

    def get_data_aligned(self, start_time, end_time, parameters):
        results = {}
    
        for table in parameters:
            self.cursor.execute(
                f"SELECT time, parameter FROM {table} WHERE time <= ? ORDER BY time DESC LIMIT 1",
                (start_time.isoformat(),)
            )
            row_start = self.cursor.fetchone()
    
            self.cursor.execute(
                f"SELECT time, parameter FROM {table} WHERE time >= ? ORDER BY time ASC LIMIT 1",
                (end_time.isoformat(),)
            )
            row_end = self.cursor.fetchone()
    
            if row_start and row_end:
                self.cursor.execute(
                    f"SELECT time, parameter FROM {table} WHERE time BETWEEN ? AND ? ORDER BY time ASC",
                    (row_start[0], row_end[0])
                )
                data = self.cursor.fetchall()
            else:
                data = []
    
            if data:
                data[0] = (start_time.isoformat(), data[0][1])
                data[-1] = (end_time.isoformat(), data[-1][1])
    
            results[table] = data
    
        return results


        
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
            
            
        merged_df["time"] = pd.to_datetime(merged_df["time"])
        merged_df = merged_df.sort_values("time")
        
        '''
        for col in merged_df.columns:
            if col != "time":
                merged_df[col] = (
                    merged_df
                    .set_index("time")[col]
                    .interpolate(method="nearest", limit_area="inside")
                    .reset_index(drop=True)
                )
        '''
        
        #X = merged_df.copy(deep=True)
        
        for col in merged_df.columns:
            if col != "time":
                s = merged_df[["time", col]].dropna()
                merged_df[col] = pd.merge_asof(
                    merged_df[["time"]],
                    s,
                    on="time",
                    direction="nearest"
                )[col]

            
        return merged_df
    
    def trim_time_range(self, dataframe, start_time, end_time):
        
        df = dataframe.copy()
    
        df["time"] = pd.to_datetime(df["time"], utc=True)
        start_time = pd.to_datetime(start_time, utc=True)
        end_time = pd.to_datetime(end_time, utc=True)
    
        df = df.sort_values("time")
    
        start_idx = (df["time"] - start_time).abs().idxmin()
        end_idx = (df["time"] - end_time).abs().idxmin()
    
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx

        df_trim = df.loc[start_idx:end_idx].copy()
    
        df_trim.iloc[0, df_trim.columns.get_loc("time")] = start_time
        df_trim.iloc[-1, df_trim.columns.get_loc("time")] = end_time
    
        return df_trim.reset_index(drop=True)


    def _insert_testing_data(self, seed=None):
        """Generate random data using NumPy and insert into tables."""
        if seed is not None:
            np.random.seed(seed)

        start_date = datetime.datetime(2022, 1, 1)
        end_date = datetime.datetime.today()
        days_between = (end_date - start_date).days
        
        data_dict = {
            "natural_convection_coefficient": [np.random.normal(10, 1) for _ in range(random.randint(10, 20))],
            "wind_forced_convection": [np.random.normal(2, 1) for _ in range(random.randint(10, 20))],
            "wind_forced_convection_parameter_constant": [np.random.normal(2, 1) for _ in range(random.randint(10, 20))],
            "wind_speed": [np.random.normal(5, 1) for _ in range(random.randint(10, 20))],
            "shortwave_radiation": [np.random.normal(0, 1) for _ in range(random.randint(10, 20))],
            "shortwave_radiation_constant": [np.random.normal(1, 0.5) for _ in range(random.randint(10, 20))],
            "shortwave_irradiation": [np.random.normal(0, 1) for _ in range(random.randint(10, 20))],
            "calculate_shortwave_irradiation": [np.random.normal(0, 1) for _ in range(random.randint(10, 20))],
        }

        for table in self.tables_list:
            parameters = data_dict[table]
            rows = []
            for param in parameters:
                rand_days = random.randint(0, days_between)
                rand_date = start_date + datetime.timedelta(days=rand_days)
            
                rows.append((rand_date.isoformat(), float(param)))
                
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
        
    
    def insert_parameter(self, table_name: str, time: datetime.datetime, value: float):
        self.cursor.execute(
            f"INSERT OR IGNORE INTO {table_name} (time, parameter) VALUES (?, ?)",
            (time.isoformat(), value)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    
    #%% get complete db (tables and data for each table)
    # checkt the time ranges!
    
    db = Database()
    # db._insert_testing_data()
    start_time = datetime.datetime(2023, 5, 5, 0, 0)
    end_time = datetime.datetime(2023, 11, 19, 16, 6, 2, 938178)
    parameters = ['natural_convection_coefficient',
     'wind_forced_convection',
     'wind_forced_convection_parameter_constant',
     'wind_speed',
     'shortwave_radiation',
     'shortwave_radiation_constant',
     'shortwave_irradiation',
     'calculate_shortwave_irradiation']
    #db_get_data = db.get_data_aligned(start_time, end_time, parameters)
    new_time = datetime.datetime(2025, 11, 20, 12, 0)
    new_value = 2.5
    
    #db.insert_parameter("wind_forced_convection", new_time, new_value)
    
    df = db.request_data()
    print(df)
    
    df_trim = db.trim_time_range(df, start_time, end_time)
