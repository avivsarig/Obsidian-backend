import os

import yaml


def get_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)
