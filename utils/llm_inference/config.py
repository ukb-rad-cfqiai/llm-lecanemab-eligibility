"""Resolve the inference endpoint and verify its served model."""

import os

import httpx
from dotenv import load_dotenv


def load_inference_settings(profile_path, expected_model_id):
    """Load the localhost batch endpoint selected by this test set's profile."""
    if not os.path.isfile(profile_path):
        raise FileNotFoundError(f"Inference profile not found: {profile_path}")

    load_dotenv(dotenv_path=profile_path, override=True)
    if os.getenv("BATCH_CLIENT_MODE_ON", "").lower() != "true":
        raise RuntimeError(
            f"{profile_path} must enable BATCH_CLIENT_MODE_ON=true."
        )

    listen_port = int(os.getenv("BATCH_CLIENT_LISTEN_PORT", "30000"))
    base_url = os.getenv(
        "API_BASE_URL",
        f"http://127.0.0.1:{listen_port}/v1",
    ).rstrip("/")
    api_key = os.getenv("API_KEY", "dummy_key")
    return base_url, expected_model_id, api_key


def verify_inference_stack(base_url, model_id, api_key):
    """Fail early when the batch ingress is down or serves another model."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = httpx.get(
            f"{base_url}/models",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        model_ids = {
            item.get("id")
            for item in response.json().get("data", [])
            if isinstance(item, dict)
        }
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError(
            f"Could not query the UKB-GPT batch API at {base_url}/models: {exc}"
        ) from exc

    if model_id not in model_ids:
        available = ", ".join(sorted(item for item in model_ids if item)) or "none"
        raise RuntimeError(
            f"Expected model {model_id!r} is not available at {base_url}. "
            f"Available models: {available}."
        )

