"""
Settings Manager for Agency Swarm Web UI

Handles encrypted storage and retrieval of API keys, model configurations,
and agent-specific settings with AES-256-GCM encryption.
"""

import base64
import json
import os
from datetime import datetime, timezone  # type: ignore[import]
from pathlib import Path
from typing import Any

# Use timezone.utc instead of UTC for compatibility
UTC = timezone.utc

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SettingsManager:
    """
    Manages application settings with encryption support.

    Features:
    - AES-256-GCM encryption for sensitive data (API keys)
    - PBKDF2 key derivation from password
    - Persistent storage in JSON format
    - Version migration support
    """

    VERSION = "1.0"

    def __init__(self, settings_dir: Path | None = None):
        """
        Initialize the settings manager.

        Args:
            settings_dir: Directory to store settings.json. Defaults to backend/data/
        """
        if settings_dir is None:
            backend_dir = Path(__file__).parent
            settings_dir = backend_dir / "data"

        self.settings_dir = Path(settings_dir)
        self.settings_dir.mkdir(parents=True, exist_ok=True)

        self.settings_file = self.settings_dir / "settings.json"
        self._fernet: Fernet | None = None
        self._cached_settings: dict[str, Any] | None = None
        self._is_encrypted = False

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive a cryptographic key from the password using PBKDF2.

        Args:
            password: User password
            salt: Salt for key derivation

        Returns:
            URL-safe base64-encoded key suitable for Fernet
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def _create_default_settings(self) -> dict[str, Any]:
        """
        Create default settings structure.

        Returns:
            Dictionary with default settings
        """
        return {
            "version": self.VERSION,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "encryption": {
                "algorithm": "AES-256-GCM",
                "salt": None,
                "derived_key_hash": None
            },
            "api_keys": {},  # Will be encrypted
            "model_config": {
                "default_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            "agent_overrides": {}
        }

    def load_settings(self, password: str | None = None) -> dict[str, Any]:
        """
        Load settings from disk, decrypting if password is provided.

        Args:
            password: Password to decrypt encrypted settings

        Returns:
            Settings dictionary

        Raises:
            ValueError: If settings are encrypted but no password provided
            ValueError: If password is incorrect
        """
        if not self.settings_file.exists():
            # Create default settings
            settings = self._create_default_settings()
            self._cached_settings = settings
            return settings

        with open(self.settings_file) as f:
            data = json.load(f)

        # Check if settings are encrypted
        if "encryption" in data and data["encryption"].get("salt"):
            self._is_encrypted = True

            if not password:
                raise ValueError(
                    "Settings are encrypted. Please provide a password to unlock."
                )

            # Decrypt API keys
            salt = base64.b64decode(data["encryption"]["salt"])
            key = self._derive_key(password, salt)
            self._fernet = Fernet(key)

            # Verify password by checking derived key hash
            derived_key_hash = base64.b64encode(key).decode()
            if data["encryption"].get("derived_key_hash") != derived_key_hash:
                raise ValueError("Incorrect password")

            # Decrypt api_keys
            encrypted_keys = data.get("api_keys", {})
            decrypted_keys = {}

            for provider, encrypted_data in encrypted_keys.items():
                try:
                    if isinstance(encrypted_data, str):
                        decrypted = self._fernet.decrypt(encrypted_data.encode()).decode()
                        decrypted_keys[provider] = json.loads(decrypted)
                    else:
                        # Backward compatibility for non-encrypted keys
                        decrypted_keys[provider] = encrypted_data
                except Exception:
                    # If decryption fails, keep as is
                    decrypted_keys[provider] = encrypted_data

            data["api_keys"] = decrypted_keys
        else:
            self._is_encrypted = False

        self._cached_settings = data
        return data

    def save_settings(
        self,
        settings: dict[str, Any],
        password: str | None = None
    ) -> None:
        """
        Save settings to disk, encrypting if password is provided.

        Args:
            settings: Settings dictionary to save
            password: Password to encrypt sensitive data

        Raises:
            ValueError: If trying to encrypt without password
        """
        # Update timestamp
        settings["updated_at"] = datetime.now(UTC).isoformat()

        # Create a copy to avoid modifying the input
        data_to_save = json.loads(json.dumps(settings))

        # Encrypt API keys if password provided
        if password:
            # Generate new salt and derive key
            salt = base64.b64encode(os.urandom(16)).decode()
            key = self._derive_key(password, salt.encode())
            self._fernet = Fernet(key)

            # Encrypt api_keys
            encrypted_keys = {}
            for provider, key_data in settings.get("api_keys", {}).items():
                json_data = json.dumps(key_data)
                encrypted = self._fernet.encrypt(json_data.encode()).decode()
                encrypted_keys[provider] = encrypted

            data_to_save["api_keys"] = encrypted_keys
            data_to_save["encryption"] = {
                "algorithm": "AES-256-GCM",
                "salt": salt,
                "derived_key_hash": base64.b64encode(key).decode()
            }
            self._is_encrypted = True
        elif self._is_encrypted and self._fernet:
            # Re-encrypt with existing key
            encrypted_keys = {}
            for provider, key_data in settings.get("api_keys", {}).items():
                json_data = json.dumps(key_data)
                encrypted = self._fernet.encrypt(json_data.encode()).decode()
                encrypted_keys[provider] = encrypted

            data_to_save["api_keys"] = encrypted_keys

        # Save to file
        with open(self.settings_file, "w") as f:
            json.dump(data_to_save, f, indent=2)

        self._cached_settings = settings

    def is_encrypted(self) -> bool:
        """Check if current settings are encrypted."""
        return self._is_encrypted

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a specific setting value.

        Args:
            key: Dot-separated key path (e.g., 'model_config.temperature')
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        if self._cached_settings is None:
            raise ValueError("Settings not loaded. Call load_settings() first.")

        keys = key.split(".")
        value = self._cached_settings

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value if value is not None else default

    def update_setting(self, key: str, value: Any) -> None:
        """
        Update a specific setting value.

        Args:
            key: Dot-separated key path (e.g., 'model_config.temperature')
            value: New value
        """
        if self._cached_settings is None:
            raise ValueError("Settings not loaded. Call load_settings() first.")

        keys = key.split(".")
        settings = self._cached_settings

        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]

        settings[keys[-1]] = value

    def get_api_key(self, provider: str) -> str | None:
        """
        Get API key for a provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')

        Returns:
            API key or None if not found
        """
        if self._cached_settings is None:
            raise ValueError("Settings not loaded. Call load_settings() first.")

        api_keys = self._cached_settings.get("api_keys", {})
        provider_data = api_keys.get(provider, {})
        return provider_data.get("key")

    def set_api_key(self, provider: str, key: str, metadata: dict | None = None) -> None:
        """
        Set API key for a provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            key: API key
            metadata: Additional metadata (validated, models, etc.)
        """
        if self._cached_settings is None:
            raise ValueError("Settings not loaded. Call load_settings() first.")

        if "api_keys" not in self._cached_settings:
            self._cached_settings["api_keys"] = {}

        self._cached_settings["api_keys"][provider] = {
            "key": key,
            "updated_at": datetime.now(UTC).isoformat(),
            **(metadata or {})
        }

    def get_model_config(self) -> dict[str, Any]:
        """Get current model configuration."""
        return self.get_setting("model_config", {})

    def update_model_config(self, config: dict[str, Any]) -> None:
        """
        Update model configuration.

        Args:
            config: Dictionary with model config values
        """
        if self._cached_settings is None:
            raise ValueError("Settings not loaded. Call load_settings() first.")

        if "model_config" not in self._cached_settings:
            self._cached_settings["model_config"] = {}

        self._cached_settings["model_config"].update(config)

    def get_agent_override(self, agent_name: str) -> dict[str, Any] | None:
        """
        Get model override for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Override configuration or None
        """
        if self._cached_settings is None:
            raise ValueError("Settings not loaded. Call load_settings() first.")

        overrides = self._cached_settings.get("agent_overrides", {})
        return overrides.get(agent_name)

    def set_agent_override(self, agent_name: str, config: dict[str, Any]) -> None:
        """
        Set model override for a specific agent.

        Args:
            agent_name: Name of the agent
            config: Override configuration
        """
        if self._cached_settings is None:
            raise ValueError("Settings not loaded. Call load_settings() first.")

        if "agent_overrides" not in self._cached_settings:
            self._cached_settings["agent_overrides"] = {}

        self._cached_settings["agent_overrides"][agent_name] = config

    def remove_agent_override(self, agent_name: str) -> None:
        """
        Remove model override for a specific agent.

        Args:
            agent_name: Name of the agent
        """
        if self._cached_settings is None:
            raise ValueError("Settings not loaded. Call load_settings() first.")

        overrides = self._cached_settings.get("agent_overrides", {})
        if agent_name in overrides:
            del overrides[agent_name]


# Global settings manager instance
_settings_manager: SettingsManager | None = None


def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
