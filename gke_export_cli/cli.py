import os
from google.auth import default
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import click
import pandas as pd
from utils.fetch_gke_metrics import fetch_all_metrics
from utils.config import get_storage_directory, load_config, save_config
from utils.file import save_dataframes  # Import the save utility
from pathlib import Path
from datetime import datetime
import uuid

@click.command()
@click.option('--project-id', required=True, help="GCP Project ID")
@click.option('--location', required=True, help="Location (e.g., 'us-central1')")
@click.option('--cluster-name', required=True, help="Cluster Name (e.g., 'online-shop')")
@click.option('--namespace', required=True, help="Namespace (e.g., 'default')")
@click.option('--controller-name', required=True, help="Controller Name (e.g., 'frontend')")
@click.option('--controller-type', required=False, default= 'Deployment', help="Controller Type (e.g., 'Deployment')")
@click.option('--container-name', required=False, help="Container Name (e.g., 'server')")
@click.option('--start-time', required=True, help="Start time in RFC3339 format (e.g., '2024-08-22T15:10:00Z')")
@click.option('--end-time', required=True, help="End time in RFC3339 format (e.g., '2024-09-22T15:15:00Z')")
@click.option('--format', type=click.Choice(['csv', 'parquet'], case_sensitive=False), default='parquet', help="File format (csv or parquet)")
@click.option('--zip-files', is_flag=True, help="If set, compress and zip the output files")
@click.option('--output-dir', help="Override the default storage directory with a custom directory path")

def main(project_id, location, cluster_name, namespace, container_name, controller_name, 
         controller_type, start_time, end_time, format, zip_files, output_dir):
    """Fetch GKE metrics, save each metric type to its own file, optionally fetch the asset inventory, and optionally zip all files into one folder."""
    
    unique_prefix = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:4]}"

    # Load configuration and set up storage directory
    config = load_config()
    storage_dir = Path(output_dir) if output_dir else get_storage_directory()
    
    # Ensure storage directory exists
    if not storage_dir.exists():
        storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Full path for output files
    output_dir = storage_dir / unique_prefix
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Metric Info Configuration for Fetching Multiple Metrics
    metrics_info = {
        "cpu_usage": {
            "metric_type": "kubernetes.io/container/cpu/core_usage_time",
            "aligner": "ALIGN_RATE",
            "reducer": "REDUCE_MEAN",
        },
        "memory_usage": {
            "metric_type": "kubernetes.io/container/memory/used_bytes",
            "aligner": "ALIGN_MAX",
            "reducer": "REDUCE_MAX",
        },
        "cpu_request": {
            "metric_type": "kubernetes.io/container/cpu/request_cores",
            "aligner": "ALIGN_MEAN",
            "reducer": "REDUCE_MEAN",
        },
        "memory_request": {
            "metric_type": "kubernetes.io/container/memory/request_bytes",
            "aligner": "ALIGN_MEAN",
            "reducer": "REDUCE_MEAN",
        }
    }

    # Initialize placeholders for data
    all_metrics_data = {}


    # Try block for fetching both metrics and asset inventory data
    try:
        # Fetch GKE metrics
        all_metrics_data = fetch_all_metrics(
            project_id=project_id,
            location=location,
            cluster_name=cluster_name,
            namespace=namespace,
            container_name=container_name,
            controller_name=controller_name,
            controller_type=controller_type,
            start_time=start_time,
            end_time=end_time,
            metrics_info=metrics_info
        )
        if not all_metrics_data:
            click.echo("No metrics data found. Please ensure the parameters are correct.")
            return

    except Exception as e:
        click.echo(f"Error fetching data: {e}. Please check your input parameters.")
        return

    # Save all dataframes (metrics and assets), and optionally zip them
    save_dataframes(output_dir, format, all_metrics_data, unique_prefix, zip_files)

if __name__ == '__main__':
    main()
