from nibelungenbruecke.scripts.utilities.API_sensor_retrieval import API_Request
import pandas as pd
import numpy as np

def fetch_and_process_data(api_request):
    # Fetch data from the API
    output_data = api_request.fetch_data()
    DU_data_api = output_data["E_plus_413TU_HS--o-_Avg1"]

    # Convert to numpy array for easier manipulation
    data_array = np.array(DU_data_api)

    # Check if the length of the data is a multiple of 10, if not, truncate the excess
    remainder = len(data_array) % 10
    if remainder != 0:
        data_array = data_array[:-remainder]

    # Reshape the array to have 10 columns
    reshaped_data = data_array.reshape(-1, 10)

    # Calculate the average across the columns (axis 1)
    averaged_data = reshaped_data.mean(axis=1)

    # Convert back to list if necessary
    averaged_data_list = averaged_data.tolist()

    return averaged_data_list

def test_fetch_and_process_data():
    # Path to the CSV file
    path = 'E+040TU_HS--o--data-14 May 2024, 18 22 54.csv'
    DU_data = pd.read_csv(path)

    # Initialize API request object
    api = API_Request()
    api.body = {
        "startTime": "2024-05-01T08:00:00Z",
        "endTime": "2024-05-14T20:00:00Z",
        "meta_channel": True,
        "columns": ['E_plus_413TU_HS--o-_Avg1']
    }

    # Call the function to fetch and process data
    averaged_data_list = fetch_and_process_data(api)

    # Perform some basic checks
    assert isinstance(averaged_data_list, list), "Output should be a list"
    assert all(isinstance(x, float) for x in averaged_data_list), "All elements should be floats"

    # Compare the CSV data with the averaged data list
    DU_data_values = DU_data['E_plus_413TU_HS--o-_Avg1'].values

    # Check if the length of the data is a multiple of 10, if not, truncate the excess
    remainder = len(DU_data_values) % 10
    if remainder != 0:
        DU_data_values = DU_data_values[:-remainder]

    # Reshape the array to have 10 columns
    reshaped_DU_data = DU_data_values.reshape(-1, 10)

    # Calculate the average across the columns (axis 1)
    averaged_DU_data = reshaped_DU_data.mean(axis=1)

    # Calculate the difference level (e.g., mean absolute difference)
    difference = np.abs(np.array(averaged_data_list) - averaged_DU_data)
    mean_absolute_difference = np.mean(difference)

    # Print results for verification
    print("Averaged Data List from API:", averaged_data_list)
    print("Averaged Data List from CSV:", averaged_DU_data.tolist())
    print("Mean Absolute Difference:", mean_absolute_difference)

    # Additional assertion to check the mean absolute difference is within an acceptable range
    # This range can be adjusted based on acceptable difference levels in your context
    assert mean_absolute_difference < 1e-5, f"Mean absolute difference is too high: {mean_absolute_difference}"

# Run the test function
if __name__ == "__main__":
    test_fetch_and_process_data()
