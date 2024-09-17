import logging
from google.auth import default
from google.auth.transport.requests import Request
from utils.fetch_startup_time import fetch_and_process_assets
from googleapiclient.discovery import build
import pandas as pd
import click
# Exclude namespaces that should not be included in the metrics gathering
EXCLUDED_NAMESPACES = [
    "kube-system", "istio-system", "gatekeeper-system", "gke-system",
    "gmp-system", "gke-gmp-system", "gke-managed-filestorecsi", "gke-mcs"
]

# Fields to be used in the groupBy in the API query
GROUP_BY_FIELDS = [
    "resource.labels.project_id", 
    "resource.labels.location", 
    "resource.labels.cluster_name",
    "resource.labels.namespace_name", 
    "resource.labels.container_name", 
    "resource.labels.pod_name",
    "metadata.system_labels.top_level_controller_name", 
    "metadata.system_labels.top_level_controller_type"
    
]

def build_filter_string(
    metric: str,
    project_id: str = '',
    location: str = '',
    cluster_name: str = '',
    namespace: str = '',
    container_name: str = '',
    controller_name: str = '',
    controller_type: str = ''
) -> str:
    """
    Constructs a filter string for querying based on provided parameters.

    Parameters:
    - metric (str): The metric type to be used in the filter.
    - project_id (str): The project ID for the filter.
    - location (str): The location for the filter.
    - cluster_name (str): The cluster name for the filter.
    - namespace (str): The namespace for the filter.
    - container_name (str): The container name for the filter.
    - controller_name (str): The controller name for the filter.
    - controller_type (str): The controller type for the filter.

    Returns:
    - str: A constructed filter string.
    """
    filter_conditions = [
        f'metric.type = "{metric}"',
        'resource.type = "k8s_container"'
    ]

    if 'memory/used_bytes' in metric.lower():
        filter_conditions.append('metric.label.memory_type = "non-evictable"')

    if project_id:
        filter_conditions.append(f'resource.labels.project_id = "{project_id}"')
    
    if location:
        filter_conditions.append(f'resource.labels.location = "{location}"')
    
    if cluster_name:
        filter_conditions.append(f'resource.labels.cluster_name = "{cluster_name}"')

    if namespace:
        filter_conditions.append(f'resource.labels.namespace_name = "{namespace}"')
    
    if container_name:
        filter_conditions.append(f'resource.labels.container_name = "{container_name}"')
    if controller_name:
        filter_conditions.append(f'metadata.system_labels.top_level_controller_name = "{controller_name}"')
    if controller_type:
        filter_conditions.append(f'metadata.system_labels.top_level_controller_type = "{controller_type}"')

    # Exclude unwanted namespaces
    excluded_filter = ' AND '.join(
        f'NOT resource.labels.namespace_name = "{namespace}"' for namespace in EXCLUDED_NAMESPACES
    )
    filter_conditions.append(excluded_filter)
    
    return ' AND '.join(filter_conditions)

def fetch_metrics_from_api(
    project_id, location, cluster_name, namespace, container_name, 
    controller_name, controller_type, metric, start_time, end_time, 
    per_series_aligner, cross_series_reducer):
    """
    Fetches metrics from Google Cloud Monitoring API based on the provided parameters.
    """
    # Initialize the API client
    try:
        credentials, project_id = default()
        credentials.refresh(Request())
        service = build('monitoring', 'v3', credentials=credentials)
    except Exception as e:
        click.echo(f"Failed to authenticate and initialize the Google Cloud Asset API: {e}")
        return
    
    filter_ = build_filter_string(
        metric=metric,
        project_id=project_id,
        location=location,
        cluster_name=cluster_name,
        namespace=namespace,
        container_name=container_name,
        controller_name=controller_name,
        controller_type=controller_type
    )

    click.echo(f"Fetching data for metric: {metric} ...")
  
    try:
        all_time_series_data = []
        request = service.projects().timeSeries().list(
            name=f"projects/{project_id}",
            aggregation_alignmentPeriod="60s",
            aggregation_crossSeriesReducer=cross_series_reducer,
            aggregation_groupByFields=GROUP_BY_FIELDS,
            aggregation_perSeriesAligner=per_series_aligner,
            filter=filter_,
            interval_endTime=end_time,
            interval_startTime=start_time
        )
        
        while request is not None:
            response = request.execute()
            all_time_series_data.extend(response.get('timeSeries', []))
            nextPageToken = response.get('nextPageToken')
            
            request = service.projects().timeSeries().list_next(previous_request=request, previous_response=response) if nextPageToken else None

        df = pd.json_normalize(
            all_time_series_data,
            record_path='points',
            meta=[
                ['metric', 'type'],
                ['resource', 'type'],
                ['resource', 'labels', 'project_id'],
                ['resource', 'labels', 'location'],
                ['resource', 'labels', 'cluster_name'],
                ['resource', 'labels', 'namespace_name'],
                ['resource', 'labels', 'container_name'],
                ['resource', 'labels', 'pod_name'],
                ['metadata', 'systemLabels', 'top_level_controller_name'],
                ['metadata', 'systemLabels', 'top_level_controller_type']
            ],
            errors='ignore'
        )

        if df.empty:
            click.echo(f"No data found for metric: {metric}")
        else:
            click.echo(f"Successfully fetched.")

        return df if not df.empty else pd.DataFrame()

    except Exception as e:
        click.echo(f"Error fetching metrics: {e}")
        return pd.DataFrame()


def fetch_all_metrics(
    project_id, location, cluster_name, namespace, container_name, 
    controller_name, controller_type, start_time, end_time, metrics_info):
    """
    Fetch all required metrics as per the metrics info configuration.
    """
    click.echo(f"Starting to fetch metrics for the following configuration: "
               f"Project ID: {project_id}, Location: {location}, "
               f"Cluster Name: {cluster_name}, Namespace: {namespace}, "
               f"Controller Name: {controller_name}")

    all_metrics_data = {}

    for key, info in metrics_info.items():

        metric_type = info["metric_type"]
        aligner = info.get("aligner", "ALIGN_MEAN")
        reducer = info.get("reducer", "REDUCE_MEAN")

        metric_data = fetch_metrics_from_api(
            project_id, location, cluster_name, namespace, container_name, 
            controller_name, controller_type, metric_type, start_time, end_time, 
            aligner, reducer
        )

        if not metric_data.empty:
            all_metrics_data[key] = metric_data
        else:
            click.echo(f"No data found for {metric_type}.")
    
    # Fetch pod startup time from Asset Inventory
    all_metrics_data['pod_startup']  = fetch_and_process_assets(
        project_id, 
        location, 
        cluster_name, 
        controller_name, 
        namespace
        )
    
    click.echo("Completed fetching all metrics.")
    return all_metrics_data
