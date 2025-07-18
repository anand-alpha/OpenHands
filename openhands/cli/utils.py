import json
import hashlib
import time
import requests
from pathlib import Path

import toml
from pydantic import BaseModel, Field

from openhands.cli.tui import (
    UsageMetrics,
)
from openhands.events.event import Event
from openhands.llm.metrics import Metrics

_LOCAL_CONFIG_FILE_PATH = Path.home() / '.openhands' / 'config.toml'
_SNOW_AUTH_FILE_PATH = Path.home() / '.openhands' / 'snow_auth.json'
_DEFAULT_CONFIG: dict[str, dict[str, list[str]]] = {'sandbox': {'trusted_dirs': []}}
_SNOW_API_ENDPOINT = 'https://api-kratos.dev.snowcell.io/auth/validate'


# SNOW Authentication functions
def validate_snow_token_with_api(token: str) -> bool:
    """Validate SNOW token with the API endpoint."""
    try:
        headers = {'x-api-token': token, 'Content-Type': 'application/json'}

        response = requests.get(
            _SNOW_API_ENDPOINT, headers=headers, timeout=10  # 10 second timeout
        )

        if response.status_code == 200:
            try:
                data = response.json()
                return data.get('status') == 'success'
            except ValueError:
                return False

        return False
    except requests.RequestException:
        return False
    except Exception:
        return False


def store_snow_token(token: str) -> bool:
    """Store SNOW authentication token after validating with API."""
    try:
        # First validate the token with the API
        if not validate_snow_token_with_api(token):
            return False

        # Ensure the directory exists
        _SNOW_AUTH_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Create auth data with timestamp and actual token
        auth_data = {
            'token': token,  # Store actual token for future API calls
            'token_hash': hashlib.sha256(token.encode()).hexdigest(),
            'timestamp': time.time(),
            'status': 'active',
        }

        with open(_SNOW_AUTH_FILE_PATH, 'w') as f:
            json.dump(auth_data, f)

        return True
    except Exception:
        return False


def verify_snow_token() -> bool:
    """Verify if user is authenticated with SNOW by checking API."""
    try:
        if not _SNOW_AUTH_FILE_PATH.exists():
            return False

        with open(_SNOW_AUTH_FILE_PATH, 'r') as f:
            auth_data = json.load(f)

        # Check if token is active and validate with API
        if auth_data.get('status') != 'active':
            return False

        # Get the actual token and validate with API
        token = auth_data.get('token')
        if not token:
            return False

        # Validate token with API
        return validate_snow_token_with_api(token)
    except Exception:
        return False


def get_snow_auth_info() -> dict:
    """Get SNOW authentication information."""
    try:
        if not _SNOW_AUTH_FILE_PATH.exists():
            return {
                'authenticated': False,
                'token': None,
                'token_age': None,
                'reason': 'No authentication found',
            }

        with open(_SNOW_AUTH_FILE_PATH, 'r') as f:
            auth_data = json.load(f)

        token_age = time.time() - auth_data.get('timestamp', 0)
        authenticated = auth_data.get('status') == 'active'
        token = auth_data.get('token') if authenticated else None

        return {
            'authenticated': authenticated,
            'token': token,
            'token_age': token_age,
            'expires_in': None,  # Token never expires
            'reason': None if authenticated else 'Invalid token status',
        }
    except Exception:
        return {
            'authenticated': False,
            'token': None,
            'token_age': None,
            'reason': 'Error reading authentication data',
        }


def logout_snow() -> bool:
    """Logout from SNOW by removing authentication data."""
    try:
        if _SNOW_AUTH_FILE_PATH.exists():
            _SNOW_AUTH_FILE_PATH.unlink()
        return True
    except Exception:
        return False


def validate_snow_token(token: str) -> bool:
    """Validate SNOW token format (basic validation)."""
    # Basic token validation - adjust according to your SNOW token format
    if not token or len(token) < 10:
        return False

    # Add more specific validation rules based on SNOW token format
    # For example: check for specific patterns, length, character set, etc.
    return True


def get_local_config_trusted_dirs() -> list[str]:
    if _LOCAL_CONFIG_FILE_PATH.exists():
        with open(_LOCAL_CONFIG_FILE_PATH, 'r') as f:
            try:
                config = toml.load(f)
            except Exception:
                config = _DEFAULT_CONFIG
        if 'sandbox' in config and 'trusted_dirs' in config['sandbox']:
            return config['sandbox']['trusted_dirs']
    return []


def add_local_config_trusted_dir(folder_path: str) -> None:
    config = _DEFAULT_CONFIG
    if _LOCAL_CONFIG_FILE_PATH.exists():
        try:
            with open(_LOCAL_CONFIG_FILE_PATH, 'r') as f:
                config = toml.load(f)
        except Exception:
            config = _DEFAULT_CONFIG
    else:
        _LOCAL_CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if 'sandbox' not in config:
        config['sandbox'] = {}
    if 'trusted_dirs' not in config['sandbox']:
        config['sandbox']['trusted_dirs'] = []

    if folder_path not in config['sandbox']['trusted_dirs']:
        config['sandbox']['trusted_dirs'].append(folder_path)

    with open(_LOCAL_CONFIG_FILE_PATH, 'w') as f:
        toml.dump(config, f)


def update_usage_metrics(event: Event, usage_metrics: UsageMetrics) -> None:
    if not hasattr(event, 'llm_metrics'):
        return

    llm_metrics: Metrics | None = event.llm_metrics
    if not llm_metrics:
        return

    usage_metrics.metrics = llm_metrics


class ModelInfo(BaseModel):
    """Information about a model and its provider."""

    provider: str = Field(description='The provider of the model')
    model: str = Field(description='The model identifier')
    separator: str = Field(description='The separator used in the model identifier')

    def __getitem__(self, key: str) -> str:
        """Allow dictionary-like access to fields."""
        if key == 'provider':
            return self.provider
        elif key == 'model':
            return self.model
        elif key == 'separator':
            return self.separator
        raise KeyError(f'ModelInfo has no key {key}')


def extract_model_and_provider(model: str) -> ModelInfo:
    """Extract provider and model information from a model identifier.

    Args:
        model: The model identifier string

    Returns:
        A ModelInfo object containing provider, model, and separator information
    """
    separator = '/'
    split = model.split(separator)

    if len(split) == 1:
        # no "/" separator found, try with "."
        separator = '.'
        split = model.split(separator)
        if split_is_actually_version(split):
            split = [separator.join(split)]  # undo the split

    if len(split) == 1:
        # no "/" or "." separator found
        if split[0] in VERIFIED_OPENAI_MODELS:
            return ModelInfo(provider='openai', model=split[0], separator='/')
        if split[0] in VERIFIED_ANTHROPIC_MODELS:
            return ModelInfo(provider='anthropic', model=split[0], separator='/')
        if split[0] in VERIFIED_MISTRAL_MODELS:
            return ModelInfo(provider='mistral', model=split[0], separator='/')
        # return as model only
        return ModelInfo(provider='', model=model, separator='')

    provider = split[0]
    model_id = separator.join(split[1:])
    return ModelInfo(provider=provider, model=model_id, separator=separator)


def organize_models_and_providers(
    models: list[str],
) -> dict[str, 'ProviderInfo']:
    """Organize a list of model identifiers by provider.

    Args:
        models: List of model identifiers

    Returns:
        A mapping of providers to their information and models
    """
    result_dict: dict[str, ProviderInfo] = {}

    for model in models:
        extracted = extract_model_and_provider(model)
        separator = extracted.separator
        provider = extracted.provider
        model_id = extracted.model

        # Ignore "anthropic" providers with a separator of "."
        # These are outdated and incompatible providers.
        if provider == 'anthropic' and separator == '.':
            continue

        key = provider or 'other'
        if key not in result_dict:
            result_dict[key] = ProviderInfo(separator=separator, models=[])

        result_dict[key].models.append(model_id)

    return result_dict


VERIFIED_PROVIDERS = ['anthropic', 'openai', 'mistral']

VERIFIED_OPENAI_MODELS = [
    'o4-mini',
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4-turbo',
    'gpt-4',
    'gpt-4-32k',
    'o1-mini',
    'o1',
    'o3-mini',
    'o3-mini-2025-01-31',
]

VERIFIED_ANTHROPIC_MODELS = [
    'claude-sonnet-4-20250514',
    'claude-opus-4-20250514',
    'claude-3-7-sonnet-20250219',
    'claude-3-sonnet-20240229',
    'claude-3-opus-20240229',
    'claude-3-haiku-20240307',
    'claude-3-5-haiku-20241022',
    'claude-3-5-sonnet-20241022',
    'claude-3-5-sonnet-20240620',
    'claude-2.1',
    'claude-2',
]

VERIFIED_MISTRAL_MODELS = [
    'devstral-small-2505',
]


class ProviderInfo(BaseModel):
    """Information about a provider and its models."""

    separator: str = Field(description='The separator used in model identifiers')
    models: list[str] = Field(
        default_factory=list, description='List of model identifiers'
    )

    def __getitem__(self, key: str) -> str | list[str]:
        """Allow dictionary-like access to fields."""
        if key == 'separator':
            return self.separator
        elif key == 'models':
            return self.models
        raise KeyError(f'ProviderInfo has no key {key}')

    def get(self, key: str, default: None = None) -> str | list[str] | None:
        """Dictionary-like get method with default value."""
        try:
            return self[key]
        except KeyError:
            return default


def is_number(char: str) -> bool:
    return char.isdigit()


def split_is_actually_version(split: list[str]) -> bool:
    return (
        len(split) > 1
        and bool(split[1])
        and bool(split[1][0])
        and is_number(split[1][0])
    )


def read_file(file_path: str | Path) -> str:
    with open(file_path, 'r') as f:
        return f.read()


def write_to_file(file_path: str | Path, content: str) -> None:
    with open(file_path, 'w') as f:
        f.write(content)
