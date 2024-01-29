import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd


def plot_weather_data_run(parameters: dict):
    """Plot a list of influence lines from a h5 file into Dataframe"""

    input_parameters = _get_default_parameters()
    for key, value in parameters.items():
        input_parameters[key] = value

    parameters = input_parameters

    weather_data_path = parameters["weather_data_path"]
    output_path = parameters["output_path"]
    output_format = parameters["output_format"]
    output_key = parameters["output_key"]
    show = parameters["show"]

    with pd.HDFStore(weather_data_path, mode="r") as store:
        data = store[output_key]
        metadata = store.get_storer(output_key).attrs.metadata

    for data_name, sensor in metadata.items():
        temperature_names_array = []
        temperature_sensors_array = []
        if sensor["sensor_type"] == "temperature":
            plot_temperature(data[data_name], sensor, output_path, output_format, show)
            temperature_names_array.append(data_name)
            temperature_sensors_array.append(sensor)
        elif sensor["sensor_type"] == "radiation":
            plot_radiation(data[data_name], sensor, output_path, output_format, show)
        elif sensor["sensor_type"] == "wind_speed":
            plot_wind_speed(data[data_name], sensor, output_path, output_format, show)
        if sensor["sensor_type"] == "wind_direction":
            plot_wind_direction(
                data[["wind_speed", "wind_direction"]],
                sensor,
                output_path,
                output_format,
                show,
            )

    if len(temperature_names_array) > 1:
        plot_temperature_comparation(
            data[temperature_names_array],
            temperature_sensors_array,
            output_path,
            output_format,
            show,
        )


def plot_temperature(
    data: pd.Series,
    metadata: dict,
    output_path: str,
    output_format: str,
    show: bool = False,
):
    """Plot the temperature data of one sensor."""

    fig, ax = plt.subplots(figsize=(10, 5))
    locator = mdates.AutoDateLocator(maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
    ax.plot(data.index, data, label=metadata["sensor_name"])
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Temperature [{metadata['sensor_unit']}]")
    ax.legend()
    plt.title(f"Temperature data of {metadata['sensor_name']}")
    plt.tight_layout()
    plt.savefig(output_path + "_" + metadata["data_name"] + "." + output_format)
    if show:
        plt.show()


def plot_temperature_comparation(
    data: type[pd.DataFrame | pd.Series],
    metadata: list[dict],
    output_path: str,
    output_format: str,
    show: bool = False,
):
    """Plot the temperature data comparison for all sensors."""

    fig, ax = plt.subplots(figsize=(10, 5))
    locator = mdates.AutoDateLocator(maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
    for index, series in enumerate(data):
        ax.plot(series.index, series, label=metadata[index]["sensor_name"])
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Temperature [{metadata[0]['sensor_unit']}]")
    ax.legend()
    plt.title("Temperature data comparison")
    plt.tight_layout()
    plt.savefig(output_path + "_temperature_comparison." + output_format)
    if show:
        plt.show()


def plot_radiation(
    data: pd.Series,
    metadata: dict,
    output_path: str,
    output_format: str,
    show: bool = False,
):
    """Plot the radiation data of one sensor."""

    fig, ax = plt.subplots(figsize=(10, 5))
    locator = mdates.AutoDateLocator(maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
    ax.plot(data.index, data, label=metadata["sensor_name"])
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Radiation [{metadata['sensor_unit']}]")
    ax.legend()
    plt.title(f"Radiation data of {metadata['sensor_name']}")
    plt.tight_layout()
    plt.savefig(output_path + "_" + metadata["data_name"] + "." + output_format)
    if show:
        plt.show()


def plot_wind_speed(
    data: pd.Series,
    metadata: dict,
    output_path: str,
    output_format: str,
    show: bool = False,
):
    """Plot the wind speed data of one sensor."""

    fig, ax = plt.subplots(figsize=(10, 5))
    locator = mdates.AutoDateLocator(maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
    ax.plot(data.index, data, label=metadata["sensor_name"])
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Wind speed [{metadata['sensor_unit']}]")
    ax.legend()
    plt.title(f"Wind speed data of {metadata['sensor_name']}")
    plt.tight_layout()
    plt.savefig(output_path + "_" + metadata["data_name"] + "." + output_format)
    if show:
        plt.show()


def plot_wind_direction(
    data: pd.DataFrame,
    metadata: dict,
    output_path: str,
    output_format: str,
    show: bool = False,
):
    """Plot the wind direction data of one sensor in polar coordinates."""

    fig, ax = plt.subplots(figsize=(10, 5))
    ax = plt.subplot(111, projection="polar")
    ax.plot(
        data["wind_direction"].values * 2 * np.pi / 360,
        data["wind_speed"].values,
        label=metadata["sensor_name"],
    )
    ax.set_ylabel("Wind speed [m/s]")
    ax.set_xlabel(f"Wind direction [{metadata['sensor_unit']}]")
    ax.legend()
    plt.title(f"Wind direction data of {metadata['sensor_name']}")
    plt.tight_layout()
    plt.savefig(output_path + "_polar_" + metadata["data_name"] + "." + output_format)
    if show:
        plt.show()

    fig, ax = plt.subplots(figsize=(10, 5))
    locator = mdates.AutoDateLocator(maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
    ax.plot(
        data["wind_direction"].index,
        data["wind_direction"],
        label=metadata["sensor_name"],
    )
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Wind direction [{metadata['sensor_unit']}]")
    ax.legend()
    plt.title(f"Wind direction data of {metadata['sensor_name']}")
    plt.tight_layout()
    plt.savefig(output_path + "_" + metadata["data_name"] + "." + output_format)
    if show:
        plt.show()


def _get_default_parameters():
    return {
        "weather_data_path": "input/data/weather_data.h5",
        "file_dep": ["input/data/weather_data.h5"],
        "output_key": "data_with_metadata",
        "output_path": "output/figures/weather_data",
        "output_format": "png",
        "show": False,
    }
