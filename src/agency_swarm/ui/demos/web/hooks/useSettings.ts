"use client";

import { useState, useCallback, useEffect } from "react";
import {
  type SettingsData,
  type ValidateKeyResponse,
  type UnlockSettingsResponse,
  type ModelConfig,
  type APIData,
} from "@/types";

const DRAFT_KEY = "agency_settings_draft";

const DEFAULT_MODEL_CONFIG: ModelConfig = {
  default_model: "gpt-4o-mini",
  temperature: 0.7,
  max_tokens: 2048,
  top_p: 1.0,
  frequency_penalty: 0.0,
  presence_penalty: 0.0,
};

interface UseSettingsOptions {
  apiBase?: string;
  autoSaveDraft?: boolean;
}

interface UseSettingsResult {
  // State
  settings: SettingsData | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  isEncrypted: boolean;
  hasUnsavedChanges: boolean;

  // Actions
  loadSettings: (password?: string) => Promise<void>;
  saveSettings: (password?: string) => Promise<boolean>;
  unlockSettings: (password: string) => Promise<UnlockSettingsResponse>;
  validateKey: (provider: string, key: string) => Promise<ValidateKeyResponse>;
  updateSettings: (updates: Partial<SettingsData>) => void;
  updateModelConfig: (config: Partial<ModelConfig>) => void;
  setAPIKey: (provider: string, key: string) => void;
  removeAPIKey: (provider: string) => void;
  setAgentOverride: (agentName: string, config: Record<string, unknown>) => void;
  removeAgentOverride: (agentName: string) => void;
  discardDraft: () => void;
}

export function useSettings(options: UseSettingsOptions = {}): UseSettingsResult {
  const { apiBase = "/api", autoSaveDraft = true } = options;

  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEncrypted, setIsEncrypted] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [currentPassword, setCurrentPassword] = useState<string | undefined>();

  // Load draft from localStorage on mount
  useEffect(() => {
    if (autoSaveDraft) {
      try {
        const draft = localStorage.getItem(DRAFT_KEY);
        if (draft) {
          setSettings(JSON.parse(draft));
          setHasUnsavedChanges(true);
        }
      } catch (e) {
        // Ignore draft errors
        console.warn("Failed to load draft settings:", e);
      }
    }
  }, [autoSaveDraft]);

  const loadSettings = useCallback(async (password?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBase}/settings`, {
        method: "GET",
        headers: password ? { "X-Password": password } : {},
      });

      if (!response.ok) {
        if (response.status === 401) {
          setIsEncrypted(true);
          throw new Error("Settings are encrypted. Please provide a password.");
        }
        throw new Error(`Failed to load settings: ${response.statusText}`);
      }

      const data = await response.json();
      setSettings(data);
      setCurrentPassword(password);
      setHasUnsavedChanges(false);
      setIsEncrypted(!!data.encryption?.salt);

      // Clear draft after successful load
      if (autoSaveDraft) {
        localStorage.removeItem(DRAFT_KEY);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to load settings";
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [apiBase, autoSaveDraft]);

  const saveSettings = useCallback(async (password?: string) => {
    if (!settings) {
      setError("No settings to save");
      return false;
    }

    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch(`${apiBase}/settings`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(password ? { "X-Password": password } : {}),
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        if (response.status === 401) {
          setIsEncrypted(true);
          throw new Error("Incorrect password");
        }
        throw new Error(`Failed to save settings: ${response.statusText}`);
      }

      const result = await response.json();

      // Update state after successful save
      setCurrentPassword(password);
      setHasUnsavedChanges(false);
      setIsEncrypted(!!settings.encryption?.salt);

      // Clear draft after successful save
      if (autoSaveDraft) {
        localStorage.removeItem(DRAFT_KEY);
      }

      return true;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to save settings";
      setError(errorMsg);
      throw err;
    } finally {
      setIsSaving(false);
    }
  }, [apiBase, settings, autoSaveDraft]);

  const unlockSettings = useCallback(async (password: string): Promise<UnlockSettingsResponse> => {
    setError(null);

    try {
      const response = await fetch(`${apiBase}/settings/unlock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      const result: UnlockSettingsResponse = await response.json();

      if (result.success && result.data) {
        setSettings(result.data);
        setCurrentPassword(password);
        setIsEncrypted(result.is_encrypted || false);
        setHasUnsavedChanges(false);

        // Clear draft after successful unlock
        if (autoSaveDraft) {
          localStorage.removeItem(DRAFT_KEY);
        }
      }

      return result;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to unlock settings";
      setError(errorMsg);
      return {
        success: false,
        error: errorMsg,
        is_encrypted: true,
      };
    }
  }, [apiBase, autoSaveDraft]);

  const validateKey = useCallback(async (
    provider: string,
    key: string
  ): Promise<ValidateKeyResponse> => {
    setError(null);

    try {
      const response = await fetch(`${apiBase}/settings/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, key }),
      });

      if (!response.ok) {
        throw new Error(`Validation failed: ${response.statusText}`);
      }

      const result: ValidateKeyResponse = await response.json();
      return result;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Validation failed";
      setError(errorMsg);
      return {
        valid: false,
        provider,
        message: "Validation request failed",
        error: errorMsg,
        models: [],
      };
    }
  }, [apiBase]);

  const updateSettings = useCallback((updates: Partial<SettingsData>) => {
    setSettings((prev) => {
      if (!prev) return null;

      const updated = { ...prev, ...updates };
      updated.updated_at = new Date().toISOString();

      // Auto-save draft to localStorage
      if (autoSaveDraft) {
        try {
          localStorage.setItem(DRAFT_KEY, JSON.stringify(updated));
        } catch (e) {
          console.warn("Failed to save draft:", e);
        }
      }

      setHasUnsavedChanges(true);
      return updated;
    });
  }, [autoSaveDraft]);

  const updateModelConfig = useCallback((config: Partial<ModelConfig>) => {
    setSettings((prev) => {
      if (!prev) return null;

      const updated = {
        ...prev,
        model_config_data: {
          ...prev.model_config_data,
          ...config,
        },
      };
      updated.updated_at = new Date().toISOString();

      // Auto-save draft to localStorage
      if (autoSaveDraft) {
        try {
          localStorage.setItem(DRAFT_KEY, JSON.stringify(updated));
        } catch (e) {
          console.warn("Failed to save draft:", e);
        }
      }

      setHasUnsavedChanges(true);
      return updated;
    });
  }, [autoSaveDraft]);

  const setAPIKey = useCallback((provider: string, key: string) => {
    setSettings((prev) => {
      if (!prev) return null;

      const updated = {
        ...prev,
        api_keys: {
          ...prev.api_keys,
          [provider]: {
            provider,
            key,
            validated: false,
            last_validated: undefined,
            models: [],
          } as APIData,
        },
      };
      updated.updated_at = new Date().toISOString();

      // Auto-save draft to localStorage
      if (autoSaveDraft) {
        try {
          localStorage.setItem(DRAFT_KEY, JSON.stringify(updated));
        } catch (e) {
          console.warn("Failed to save draft:", e);
        }
      }

      setHasUnsavedChanges(true);
      return updated;
    });
  }, [autoSaveDraft]);

  const removeAPIKey = useCallback((provider: string) => {
    setSettings((prev) => {
      if (!prev) return null;

      const apiKeys = { ...prev.api_keys };
      delete apiKeys[provider];

      const updated = {
        ...prev,
        api_keys: apiKeys,
      };
      updated.updated_at = new Date().toISOString();

      // Auto-save draft to localStorage
      if (autoSaveDraft) {
        try {
          localStorage.setItem(DRAFT_KEY, JSON.stringify(updated));
        } catch (e) {
          console.warn("Failed to save draft:", e);
        }
      }

      setHasUnsavedChanges(true);
      return updated;
    });
  }, [autoSaveDraft]);

  const setAgentOverride = useCallback((agentName: string, config: Record<string, unknown>) => {
    setSettings((prev) => {
      if (!prev) return null;

      const updated = {
        ...prev,
        agent_overrides: {
          ...prev.agent_overrides,
          [agentName]: {
            agent_name: agentName,
            ...config,
          },
        },
      };
      updated.updated_at = new Date().toISOString();

      // Auto-save draft to localStorage
      if (autoSaveDraft) {
        try {
          localStorage.setItem(DRAFT_KEY, JSON.stringify(updated));
        } catch (e) {
          console.warn("Failed to save draft:", e);
        }
      }

      setHasUnsavedChanges(true);
      return updated;
    });
  }, [autoSaveDraft]);

  const removeAgentOverride = useCallback((agentName: string) => {
    setSettings((prev) => {
      if (!prev) return null;

      const agentOverrides = { ...prev.agent_overrides };
      delete agentOverrides[agentName];

      const updated = {
        ...prev,
        agent_overrides: agentOverrides,
      };
      updated.updated_at = new Date().toISOString();

      // Auto-save draft to localStorage
      if (autoSaveDraft) {
        try {
          localStorage.setItem(DRAFT_KEY, JSON.stringify(updated));
        } catch (e) {
          console.warn("Failed to save draft:", e);
        }
      }

      setHasUnsavedChanges(true);
      return updated;
    });
  }, [autoSaveDraft]);

  const discardDraft = useCallback(() => {
    if (autoSaveDraft) {
      localStorage.removeItem(DRAFT_KEY);
    }
    setHasUnsavedChanges(false);

    // Reload current settings
    if (currentPassword || !isEncrypted) {
      loadSettings(currentPassword);
    }
  }, [autoSaveDraft, currentPassword, isEncrypted, loadSettings]);

  return {
    settings,
    isLoading,
    isSaving,
    error,
    isEncrypted,
    hasUnsavedChanges,

    loadSettings,
    saveSettings,
    unlockSettings,
    validateKey,
    updateSettings,
    updateModelConfig,
    setAPIKey,
    removeAPIKey,
    setAgentOverride,
    removeAgentOverride,
    discardDraft,
  };
}
