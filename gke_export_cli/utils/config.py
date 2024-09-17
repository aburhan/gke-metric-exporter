import json
from pathlib import Path
from typing import Any

# Define the config directory and file (in the user's home directory)
CONFIG_DIR = Path.home()    / ".config" / "gke_metrics_fetcher"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Use the current working directory (cwd) as the default storage directory
DEFAULT_STORAGE_DIR = Path.cwd()

def load_config(config_path: Path = CONFIG_FILE) -> dict[str, Any]:
    """
    Load the configuration from a JSON file.

    Args:
    - config_path: The path to the config file.

    Returns:
    - A dictionary with the configuration settings. Defaults to the current directory if not present.
    """
    if not config_path.exists():
        # Return the default config if the file doesn't exist
        return {"storage_dir": str(DEFAULT_STORAGE_DIR)}
    
    # Load the configuration from the file
    with open(config_path, "r") as file:
        return json.load(file)


def save_config(config: dict[str, Any]):
    """
    Save the configuration to a JSON file.

    Args:
    - config: A dictionary containing configuration settings.
    """
    # Create the config directory if it doesn't exist
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Save the configuration to the file
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)


def get_storage_directory() -> Path:
    """
    Get the directory where metrics files should be stored.

    Returns:
    - A Path object representing the storage directory.
    """
    config = load_config()
    storage_dir = Path(config.get("storage_dir", str(DEFAULT_STORAGE_DIR)))

    # Create the storage directory if it doesn't exist
    if not storage_dir.exists():
        storage_dir.mkdir(parents=True, exist_ok=True)

    return storage_dir
