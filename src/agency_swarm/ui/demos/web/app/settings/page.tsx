"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSettings } from "@/hooks/useSettings";
import PasswordModal from "@/components/settings/PasswordModal";
import APIKeysSection from "@/components/settings/APIKeysSection";
import ModelConfigSection from "@/components/settings/ModelConfigSection";
import ValidationMessage from "@/components/settings/ValidationMessage";

type Tab = "api-keys" | "model-config" | "agent-overrides";

export default function SettingsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("api-keys");
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [isNewPassword, setIsNewPassword] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [unlockError, setUnlockError] = useState("");

  const {
    settings,
    isLoading,
    isSaving,
    error,
    isEncrypted,
    hasUnsavedChanges,
    loadSettings,
    saveSettings,
    unlockSettings,
    discardDraft,
  } = useSettings();

  // Try to load settings on mount
  useEffect(() => {
    loadSettings().catch((err) => {
      if (err.message.includes("encrypted")) {
        setShowPasswordModal(true);
      }
    });
  }, []);

  const handleUnlock = async (password: string) => {
    setUnlockError("");

    try {
      const result = await unlockSettings(password);

      if (result.success) {
        setShowPasswordModal(false);
      } else {
        setUnlockError(result.error || "Failed to unlock");
      }
    } catch (err) {
      setUnlockError(err instanceof Error ? err.message : "Failed to unlock");
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    try {
      // If encrypted and no password, prompt for password
      if (isEncrypted) {
        setShowPasswordModal(true);
        setIsNewPassword(false);
        return;
      }

      const success = await saveSettings();
      if (success) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      console.error("Save error:", err);
    }
  };

  const tabs = [
    { id: "api-keys" as Tab, label: "API Keys", icon: "🔑" },
    { id: "model-config" as Tab, label: "Model Config", icon: "⚙️" },
    { id: "agent-overrides" as Tab, label: "Agent Overrides", icon: "🤖" },
  ];

  if (isLoading && !settings) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-400">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/")}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              title="Back to chat"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <h1 className="text-xl font-bold">Settings</h1>
            {settings?.version && (
              <span className="text-sm text-gray-500">v{settings.version}</span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {hasUnsavedChanges && (
              <button
                onClick={discardDraft}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
              >
                Discard
              </button>
            )}

            <button
              onClick={handleSave}
              disabled={isSaving || !hasUnsavedChanges}
              className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {error && (
          <ValidationMessage
            type="error"
            message={error}
            onDismiss={() => setError(null)}
          />
        )}

        {saveSuccess && (
          <div className="mb-4 bg-green-900/30 border border-green-700 rounded-lg p-3">
            <p className="text-sm text-green-400">Settings saved successfully!</p>
          </div>
        )}

        {isEncrypted && !settings && (
          <div className="text-center py-12">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 max-w-md mx-auto">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <h2 className="text-xl font-bold mb-2">Encrypted Settings</h2>
              <p className="text-gray-400 mb-4">
                Your settings are encrypted. Enter your password to unlock them.
              </p>
              <button
                onClick={() => {
                  setIsNewPassword(false);
                  setShowPasswordModal(true);
                }}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
              >
                Unlock Settings
              </button>
            </div>
          </div>
        )}

        {settings && (
          <>
            {/* Tabs */}
            <div className="border-b border-gray-800 mb-6">
              <nav className="flex gap-4">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? "border-indigo-600 text-white"
                        : "border-transparent text-gray-400 hover:text-white"
                    }`}
                  >
                    <span className="mr-1">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              {activeTab === "api-keys" && <APIKeysSection />}
              {activeTab === "model-config" && <ModelConfigSection />}
              {activeTab === "agent-overrides" && (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <h3 className="text-lg font-medium mb-2">Agent Overrides</h3>
                  <p className="text-gray-400 mb-4">Coming soon</p>
                  <p className="text-sm text-gray-500">
                    Configure custom model parameters for specific agents.
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </main>

      {/* Password Modal */}
      {showPasswordModal && (
        <PasswordModal
          isOpen={showPasswordModal}
          onClose={() => setShowPasswordModal(false)}
          onUnlock={isNewPassword ? () => Promise.resolve() : handleUnlock}
          error={unlockError}
          isNewPassword={isNewPassword}
        />
      )}
    </div>
  );
}
