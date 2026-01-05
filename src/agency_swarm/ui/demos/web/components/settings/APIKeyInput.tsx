"use client";

import { useState } from "react";

interface APIKeyInputProps {
  provider: string;
  value: string;
  onChange: (key: string) => void;
  onValidate?: () => Promise<boolean>;
  validated?: boolean;
  lastValidated?: string;
  placeholder?: string;
}

export default function APIKeyInput({
  provider,
  value,
  onChange,
  onValidate,
  validated = false,
  lastValidated,
  placeholder,
}: APIKeyInputProps) {
  const [showKey, setShowKey] = useState(false);
  const [isValidating, setIsValidating] = useState(false);

  const getPlaceholder = () => {
    if (placeholder) return placeholder;

    switch (provider.toLowerCase()) {
      case "openai":
        return "sk-...";
      case "anthropic":
        return "sk-ant-...";
      case "google":
        return "AIza...";
      case "cohere":
        return "Your Cohere API key";
      default:
        return "Enter API key";
    }
  };

  const handleValidate = async () => {
    if (!onValidate) return;

    setIsValidating(true);
    try {
      await onValidate();
    } finally {
      setIsValidating(false);
    }
  };

  const getStatusColor = () => {
    if (isValidating) return "border-yellow-500";
    if (validated) return "border-green-500";
    if (value) return "border-gray-700";
    return "border-gray-700";
  };

  const getStatusIcon = () => {
    if (isValidating) {
      return (
        <div className="animate-spin h-4 w-4 border-2 border-yellow-500 border-t-transparent rounded-full" />
      );
    }
    if (validated) {
      return (
        <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      );
    }
    if (value) {
      return (
        <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      );
    }
    return null;
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="flex-1 relative">
          <input
            type={showKey ? "text" : "password"}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={getPlaceholder()}
            className={`w-full bg-gray-800 border rounded-lg px-4 py-2 pr-24 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 ${getStatusColor()}`}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {getStatusIcon()}

            {value && (
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="p-1 hover:bg-gray-700 rounded transition-colors text-gray-400 hover:text-white"
                title={showKey ? "Hide" : "Show"}
              >
                {showKey ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                )}
              </button>
            )}

            {onValidate && value && !validated && (
              <button
                type="button"
                onClick={handleValidate}
                disabled={isValidating}
                className="p-1 hover:bg-gray-700 rounded transition-colors text-gray-400 hover:text-white disabled:opacity-50"
                title="Validate API key"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {lastValidated && (
        <p className="text-xs text-gray-500">
          Last validated: {new Date(lastValidated).toLocaleString()}
        </p>
      )}
    </div>
  );
}
