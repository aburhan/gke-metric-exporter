# GKE Metrics and Asset Fetching Tool


This tool exports CPU and memory usage and request GKE workload metric data from Cloud Monitoring, as well as pod startup details details from Asset Inventory.

## Key Features

- **Fetch GKE Metrics**: Easily collect information about CPU and memory usage.
- **Asset Information**: Optionally gather data about your workloads (pods) and their readiness.
- **Simple File Export**: Save the collected data into easy-to-read formats such as CSV or Parquet.
- **Zipping**: Option to compress all output files for easy sharing and storage.

## How to Use This Tool

### Prerequisites

Before using this tool, make sure you have the following:
- **Permissions**: Read permission to GKE metrics in Cloud Monitoring and read access to read Asset Inventory
- **Google Cloud Project ID**: This is the ID of your Google Cloud project where your GKE clusters are running.
- **GKE Workload Info**: project-id, location, cluster-name, namespace, controller-name

### Installation

1. Ensure you have Python installed on your computer.
2. Download this tool as a zip file or clone the repository.
3. Open a terminal or command prompt in the folder where you saved the tool.

### Running the Tool locally

To run the tool, you only need to provide a few details, such as your project ID and the cluster name. Here's an easy step-by-step guide:

1. **Open a Terminal**: Open a command prompt or terminal on your computer.
2. **Run the Command**: Type the following command, replacing the placeholders with your own values:

    ```bash
    python cli.py --project-id <YOUR_PROJECT_ID> --location <YOUR_LOCATION> --cluster-name <YOUR_CLUSTER_NAME> --namespace <YOUR_NAMESPACE> --controller-name <YOUR_CONTROLLER_NAME> --start-time <START_TIME> --end-time <END_TIME>  --format csv
    ```

    - `<YOUR_PROJECT_ID>`: Replace this with your Google Cloud Project ID.
    - `<YOUR_LOCATION>`: Replace this with the location of your GKE cluster (e.g., `us-central1`).
    - `<YOUR_CLUSTER_NAME>`: Replace this with your GKE cluster name.
    - `<YOUR_NAMESPACE>`: Replace this with the Kubernetes namespace (e.g., `default`).
    - `<YOUR_CONTROLLER_NAME>`: Replace this with the name of the workload or service you're inspecting (e.g., `frontend`).
    - `<START_TIME>` and `<END_TIME>`: Specify the time range for the data collection (e.g., `2024-08-22T15:15:00Z` to `2024-09-22T15:15:00Z`) . 30 days recommended
    - `--format csv`: Choose the format in which you want to save the data (CSV or Parquet).
    - zip-files: Flag to zip files for sending
    - output-dir: Directory where files will be written. Default value is the current directory

3. **Check the Output**: The tool will automatically create files containing the data in the folder you ran the command from. 

### Example Command

Here's an example of what the command might look like if you're running it to get CPU and memory data:

```bash
python cli.py --project-id my-gke-project --location us-central1 --cluster-name my-cluster --namespace default --controller-name frontend --start-time 2024-08-16T00:00:00Z --end-time 2024-09-16T00:00:00Z --format csv
```
- the following command will extract 30 days of CPU and Memory metrics for the date range and write the file as a csv file for easy viewing

### Optional Features

- Zipping Files: If you'd like to save space and combine all the output files into one zip file, you can add the --zip-files option like this:

```bash
python cli.py --project-id my-gke-project --location us-central1 --cluster-name my-cluster --namespace default --controller-name frontend --start-time 2024-08-16T00:00:00Z --end-time 2024-09-16T00:00:00Z --format csv --zip-files
```


### Output Formats

- CSV: A file format that's easy to open in Excel or Google Sheets. You can view the data in a table.
- Parquet: A format used for handling large datasets. Ideal if you need to store large amounts of data efficiently.

## Prepare file for Google

In order to prepare the files for Google to generate recommendations, the file must be in parquet format and zipped. To accomplish this, run the following command. This will generate all files as the example above but format the file as a parquet file and zip the file for sending. 

### Run CLI

```bash
pip install gke-metrics-tool

gke-metrics --project-id <PROJECT_ID> --location <LOCATION>  --cluster-name <CLUSTER_NAME>  --namespace <NAMESPACE> --controller-name <CONTROLLER_NAME> --start-time 2024-08-16T00:00:00Z --end-time 2024-09-16T00:00:00Z --file-prefix metrics --format parquet --zip-files 
```
### Run locally

```bash
python cli.py --project-id <PROJECT_ID> --location <LOCATION> --cluster-name my-cluster --namespace <NAMESPACE>  --controller-name <CONTROLLER_NAME> --start-time 2024-08-16T00:00:00Z --end-time 2024-09-16T00:00:00Z --format parquet --zip-file
```



### Troubleshooting

- Authentication Error: If you see an error about authentication, make sure you're signed into your Google Cloud account and have the necessary permissions.
- No Data Found: Double-check that the cluster name, namespace, and time range you provided are correct. Make sure the workloads are running during the specified time.