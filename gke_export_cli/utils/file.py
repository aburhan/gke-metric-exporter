import pandas as pd
from pathlib import Path
import zipfile
import os

def save_dataframes(output_dir: Path, format: str, metrics_data: dict, prefix: str, zip_files: bool):
    """
    Save all dataframes (metrics and asset) to disk in the specified format, and optionally zip the files.

    Args:
    - output_dir (Path): Directory where files will be saved.
    - format (str): File format, either 'csv' or 'parquet'.
    - metrics_data (dict): Dictionary of metrics dataframes.
    - prefix (str): Unique prefix for all files.
    - zip_files (bool): If True, zip the files after saving.
    """
    
    # Save all metric dataframes
    for metric_name, df in metrics_data.items():
        file_path = output_dir / f"{prefix}_{metric_name}.{format}"
        try:
            if format == 'csv':
                df.to_csv(file_path, index=False)
            elif format == 'parquet':
                df.to_parquet(file_path, index=False)
            print(f"Saved {metric_name} metrics to {file_path}")
        except Exception as e:
            print(f"Failed to save {metric_name} metrics to {file_path}. Error: {e}")


    # Optionally zip the files
    if zip_files:
        zip_file_path = output_dir.parent / f"{prefix}_metrics_and_assets.zip"
        try:
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for root, _, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, output_dir))
            print(f"Zipped files into {zip_file_path}")
        except Exception as e:
            print(f"Failed to zip files into {zip_file_path}. Error: {e}")
