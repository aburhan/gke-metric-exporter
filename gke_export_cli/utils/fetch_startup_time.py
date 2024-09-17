from google.auth import default
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pandas as pd
import click
import json

def fetch_and_process_assets(project_id, location, cluster_name, controller_name, namespace):
    """
    Fetches Kubernetes asset inventory data from Google Cloud API and returns it as a DataFrame.
    """

    # Initialize the API client
    try:
        credentials, project_id = default()
        credentials.refresh(Request())
        service = build('cloudasset', 'v1', credentials=credentials)
    except Exception as e:
        click.echo(f"Failed to authenticate and initialize the Google Cloud Asset API: {e}")
        return pd.DataFrame()

    asset_data = []
    next_page_token = None

    # Paginate through all pages of results
    while True:
        # Make the request for asset inventory with pagination handling
        try:
            request = service.assets().list(
                parent=f"projects/{project_id}",
                assetTypes=["k8s.io/Pod"],
                contentType="RESOURCE",
                pageToken=next_page_token
            )
            response = request.execute()
        except Exception as e:
            click.echo(f"Error fetching asset inventory: {e}")
            return pd.DataFrame()

        # Process the current page's response and extract relevant data
        if 'assets' in response:
            for asset in response['assets']:
                name = asset.get('name', '')

                # Construct the expected name format
                expected_name = f'projects/{project_id}/locations/{location}/clusters/{cluster_name}/k8s/namespaces/{namespace}/pods/{controller_name}'
                
                # Check if the name exactly matches the constructed expected name
                if expected_name in name:  # Use `startswith` to handle pod suffix like '-68f5d8498d-67bzg'
                    resource = asset.get('resource', {}).get('data', {})

                    # Extract container information and check for readinessProbe
                    containers_info = extract_container_info(resource, location, cluster_name, namespace, controller_name, project_id)
                    
                    # Add the containers info to the asset data
                    if containers_info:
                        asset_data.extend(containers_info)

        # Check if there is a next page token
        next_page_token = response.get('nextPageToken', None)
        if not next_page_token:
            break

    # Convert the list of asset data into a DataFrame
    return pd.DataFrame(asset_data)


def extract_container_info(resource, location, cluster_name, namespace, controller_name, project_id):
    """
    Extracts the workload information from a resource and checks if readinessProbe exists.
    Also includes metadata like location, cluster_name, namespace, etc.

    Parameters:
    - resource (dict): The resource data from the asset API response.
    - location (str): The location to filter by.
    - cluster_name (str): The cluster name to filter by.
    - namespace (str): The namespace to filter by.
    - controller_name (str): The controller name to filter by.

    Returns:
    - list: A list of dictionaries containing container information, readinessProbe, status conditions, and metadata.
    """
    container_list = []

    # Ensure that all relevant fields are present before proceeding
    if 'spec' not in resource or 'status' not in resource:
        return []

    # Extract container information
    for container in resource.get('spec', {}).get('containers', []):
        container_info = {}
        
        # Add metadata (location, cluster_name, namespace, etc.)
        container_info['project_id'] = project_id
        container_info['location'] = location
        container_info['cluster_name'] = cluster_name
        container_info['namespace'] = namespace
        container_info['controller_name'] = controller_name
        container_info['container_name'] = container.get('name', 'Unknown')
        container_info['readiness_probe_exists'] = 'readinessProbe' in container

        # Extract status conditions with lastTransitionTime
        status_conditions = extract_status_conditions(resource.get('status', {}).get('conditions', []))
        container_info.update(status_conditions)

        # Append to the list of containers
        container_list.append(container_info)

    return container_list


def extract_status_conditions(conditions):
    """
    Extracts the 'PodScheduled' and 'Ready' conditions and their lastTransitionTime from a list of conditions.

    Parameters:
    - conditions (list): A list of status conditions.

    Returns:
    - dict: A dictionary with 'PodScheduled' and 'Ready' statuses and lastTransitionTimes.
    """
    status_conditions = {
        'PodScheduled_lastTransitionTime': 'Unknown',
        'Ready_lastTransitionTime': 'Unknown'
    }

    for condition in conditions:
        if condition['type'] == 'PodScheduled':
            status_conditions['PodScheduled_lastTransitionTime'] = condition.get('lastTransitionTime', 'Unknown')
        elif condition['type'] == 'Ready':
            status_conditions['Ready_lastTransitionTime'] = condition.get('lastTransitionTime', 'Unknown')

    return status_conditions
