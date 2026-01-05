"use client";

import { useState } from "react";
import { useSettings } from "@/hooks/useSettings";
import APIKeyInput from "./APIKeyInput";
import ValidationMessage from "./ValidationMessage";

const PROVIDERS = [
  { id: "openai", name: "OpenAI", color: "bg-green-600" },
  { id: "anthropic", name: "Anthropic", color: "bg-orange-600" },
  { id: "google", name: "Google", color: "bg-blue-600" },
  { id: "cohere", name: "Cohere", color: "bg-purple-600" },
];

export default function APIKeysSection() {
  const { settings, validateKey, setAPIKey, removeAPIKey } = useSettings();
  const [validating, setValidating] = useState<Set<string>>(new Set());
  const [validationResults, setValidationResults] = useState<Record<string, { valid: boolean; message: string }>>({});

  const handleValidate = async (provider: string) => {
    const providerData = settings?.api_keys?.[provider];
    if (!providerData?.key) return;

    setValidating((prev) => new Set(prev).add(provider));

    try {
      const result = await validateKey(provider, providerData.key);

      setValidationResults((prev) => ({
        ...prev,
        [provider]: {
          valid: result.valid,
          message: result.message,
        },
      }));

      if (result.valid) {
        // Update settings with validation result
        // Note: This would require updating the settings with the validated models
      }
    } finally {
      setValidating((prev) => {
        const next = new Set(prev);
        next.delete(provider);
        return next;
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-2">API Keys</h2>
        <p className="text-sm text-gray-400">
          Add your API keys to enable different language models. Keys are stored encrypted locally.
        </p>
      </div>

      <div className="space-y-4">
        {PROVIDERS.map((provider) => {
          const providerData = settings?.api_keys?.[provider.id];
          const result = validationResults[provider.id];
          const isValidating = validating.has(provider.id);

          return (
            <div key={provider.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-8 h-8 rounded ${provider.color} flex items-center justify-center text-white font-bold text-xs`}>
                  {provider.name[0]}
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-white">{provider.name}</h3>
                  <p className="text-xs text-gray-500">
                    {providerData?.validated
                      ? `Last validated: ${providerData.last_validated ? new Date(providerData.last_validated).toLocaleDateString() : "N/A"}`
                      : "Not validated"}
                  </p>
                </div>
                {providerData?.validated && (
                  <span className="px-2 py-1 bg-green-900/30 text-green-400 text-xs rounded-full border border-green-700">
                    Validated
                  </span>
                )}
              </div>

              <APIKeyInput
                provider={provider.id}
                value={providerData?.key || ""}
                onChange={(key) => setAPIKey(provider.id, key)}
                onValidate={() => handleValidate(provider.id)}
                validated={providerData?.validated}
                lastValidated={providerData?.last_validated}
              />

              {result && (
                <ValidationMessage
                  type={result.valid ? "success" : "error"}
                  message={result.message}
                />
              )}

              {providerData?.models && providerData.models.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-1">Available Models:</p>
                  <div className="flex flex-wrap gap-1">
                    {providerData.models.slice(0, 5).map((model) => (
                      <span
                        key={model}
                        className="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded"
                      >
                        {model}
                      </span>
                    ))}
                    {providerData.models.length > 5 && (
                      <span className="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded">
                        +{providerData.models.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
