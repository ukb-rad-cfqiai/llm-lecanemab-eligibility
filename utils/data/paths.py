"""Locations for input data, cached model responses, and evaluation results."""

import os


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def configured_path(env_name, default_name):
    """Resolve a path from an environment variable or repository default."""
    path = os.environ.get(env_name) or os.path.join(PROJECT_DIR, default_name)
    return os.path.abspath(os.path.expanduser(path))


INPUT_TABLE_PATH = configured_path("INPUT_TABLE_PATH", "input_table.xlsx")
RESULTS_CACHE_DIR = configured_path("RESULTS_CACHE_DIR", "results_cache")
EVALUATION_RESULTS_DIR = configured_path("EVALUATION_RESULTS_DIR", "evaluation_results")
