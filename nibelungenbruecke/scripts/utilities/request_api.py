# Importieren der erforderlichen Bibliotheken
import requests
from pvlib.iotools import get_pvgis_tmy
import pandas as pd

def request_sensor_data_MKP(start_time: str, end_time: str, secrets_location:str, sensors: list = []):
    """Request sensor data from the Nibelungen API.

        Args:
            start_time (str): start time of the request in ISO-8601 format
            end_time (str): end time of the request in ISO-8601 format
            secrets_location (str): path to the secrets file
            sensors (list, optional): list of sensors to request. Defaults to all.
        returns:
            pd.DataFrame: DataFrame containing the requested data
    """

    # /samples API-Endpunkt 
    url = "https://func-70021-nibelungen-export.azurewebsites.net/samples"

    headers = {
        "Content-Type": "application/json"
    }

    # url parameter 
    params = {
        "code": open(secrets_location).read().strip() # der Code aus den über Keeper mitgetielten Zugangdaten
    }

    body = {
        "startTime": start_time,       # ISO-8601-Format ("Z" bedeutet UTC)
        "endTime": end_time,         # ISO-8601-Format ("Z" bedeutet UTC)
        "columns": sensors                            # [] Fragt alle Kanäle ab. Wenn die Liste nicht leer ist, werden nur die Daten der angegebenen Kanäle abgefragt.
    }

    # Senden der POST-Anfrage
    response = requests.post(url, headers=headers, params=params, json=body)

    # Überprüfen, ob die Anfrage erfolgreich war
    if response.status_code != 200:
        raise ValueError(f"Anfrage fehlgeschlagen mit Statuscode {response.status_code}: {response.text}")

    # Daten aus der Antwort extrahieren 
    data = response.json()

    # in einen DataFrame laden
    df = pd.DataFrame(data["rows"], columns=[col["ColumnName"] for col in data["columns"]])

    # Optional: Timestamp-Spalte konvertieren und als Index setzen
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.set_index("Timestamp")

    return df

def request_sensor_data_PVGIS(start_time: str, end_time: str, location: (float, float)):
    """Request sensor data from the PVGIS database. It returns the yearly average (TMY).
       of all the weather conditions and then the hourly values for the requested period.

        Args:
            start_time (str): start time of the request in ISO-8601 format
            end_time (str): end time of the request in ISO-8601 format
            location (tuple): tuple of latitude and longitude of the location
        returns:
            pd.DataFrame: DataFrame containing the requested data
    """

    weather = get_pvgis_tmy(location[0], location[1])[0]
    df_grouped = weather.groupby([weather.index.month, weather.index.day, weather.index.hour]).mean()
    # Create data for 29th of February
    for i, value in enumerate(df_grouped.loc[(2,28)].values):
        df_grouped.loc[(2,29,i)] = value

    # Parse start_time and end_time to Timestamp objects
    start_timestamp = pd.Timestamp(start_time, tz='UTC')
    end_timestamp = pd.Timestamp(end_time, tz='UTC')

    df_result_index = pd.date_range(start_timestamp, end_timestamp, freq='H', tz='UTC')
    df_result = pd.DataFrame(index=df_result_index, columns=df_grouped.columns)

    # Check if the entire year is within the range
    if start_timestamp.year == end_timestamp.year:
        year_start = max(start_timestamp, pd.Timestamp(f'{start_timestamp.year}-01-01', tz='UTC'))
        year_end = min(end_timestamp, pd.Timestamp(f'{start_timestamp.year}-12-31 23:00:00', tz='UTC'))
        year_index = pd.date_range(year_start, year_end, freq='H', tz='UTC')
        year_index_tuples = list(zip(year_index.month, year_index.day, year_index.hour))
        # Assign the corresponding data from df_grouped
        df_result.loc[year_index] = df_grouped.loc[year_index_tuples].values
    else:
        # Iterate over each year in the time span
        current_timestamp = start_timestamp
        while current_timestamp <= end_timestamp:
            year_start = max(start_timestamp, pd.Timestamp(f'{current_timestamp.year}-01-01', tz='UTC'))
            year_end = min(end_timestamp, pd.Timestamp(f'{current_timestamp.year}-12-31 23:00:00', tz='UTC'))
            year_index = pd.date_range(year_start, year_end, freq='H', tz='UTC')
            year_index_tuples = list(zip(year_index.month, year_index.day, year_index.hour))

            if current_timestamp.year < end_timestamp.year and current_timestamp.year > start_timestamp.year:
                # Assign the corresponding data from df_grouped
                df_result.loc[year_index] = df_grouped.loc[year_index_tuples].values
            else:
                while current_timestamp.month <= year_end.month:
                # Check if the entire month is within the range
                    month_start = max(current_timestamp, pd.Timestamp(f'{current_timestamp.year}-{current_timestamp.month}-01', tz='UTC'))
                    month_end = min(end_timestamp, pd.Timestamp(f'{current_timestamp.year}-{current_timestamp.month}-{current_timestamp.days_in_month} 23:00:00', tz='UTC'))
                    month_index = pd.date_range(month_start, month_end, freq='H', tz='UTC')
                    month_index_tuples = list(zip(month_index.month, month_index.day, month_index.hour))

                    if current_timestamp.month < end_timestamp.month and current_timestamp.month > start_timestamp.month:
                        # Assign the corresponding data from df_grouped
                        df_result.loc[month_index] = df_grouped.loc[month_index_tuples].values
                    else:
                        # Iterate over each index in the current month

                        while current_timestamp.day <= month_end.day:
                            # Check if the entire day is within the range
                            day_start = max(current_timestamp, pd.Timestamp(f'{current_timestamp.year}-{current_timestamp.month}-{current_timestamp.day}', tz='UTC'))
                            day_end = min(end_timestamp, pd.Timestamp(f'{current_timestamp.year}-{current_timestamp.month}-{current_timestamp.day} 23:00:00', tz='UTC'))
                            day_index = pd.date_range(day_start, day_end, freq='H', tz='UTC')
                            day_index_tuples = list(zip(day_index.month, day_index.day, day_index.hour))

                            if current_timestamp.day < end_timestamp.day and current_timestamp.day > start_timestamp.day:
                                # Assign the corresponding data from df_grouped
                                df_result.loc[day_index] = df_grouped.loc[day_index_tuples].values
                            else:
                                # Assign hour by hour for days that are not complete
                                for hour_idx in day_index:
                                    df_result.loc[hour_idx] = df_grouped.loc[(hour_idx.month, hour_idx.day, hour_idx.hour)].values
                            
                            if current_timestamp.day == month_end.day:
                                break
                            else:
                                current_timestamp = pd.Timestamp(f'{current_timestamp.year}-{current_timestamp.month}-{current_timestamp.day+1}', tz='UTC')
                    
                    if current_timestamp.month == year_end.month:
                        break
                    else:
                        current_timestamp = pd.Timestamp(f'{current_timestamp.year}-{current_timestamp.month+1}-01', tz='UTC')

            # Move to the next year
            current_timestamp = pd.Timestamp(f'{current_timestamp.year + 1}-01-01', tz='UTC')

    return df_result


