"use client";

import { useState } from "react";

interface PasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUnlock: (password: string) => Promise<void>;
  error?: string;
  isNewPassword?: boolean;
}

export default function PasswordModal({
  isOpen,
  onClose,
  onUnlock,
  error,
  isNewPassword = false,
}: PasswordModalProps) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError("");

    // Validate password
    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters");
      return;
    }

    if (isNewPassword && password !== confirmPassword) {
      setLocalError("Passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      await onUnlock(password);
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Failed to unlock");
    } finally {
      setIsLoading(false);
    }
  };

  const getPasswordStrength = (pwd: string): "weak" | "medium" | "strong" => {
    if (pwd.length < 8) return "weak";
    if (pwd.length < 12) return "medium";
    const hasLower = /[a-z]/.test(pwd);
    const hasUpper = /[A-Z]/.test(pwd);
    const hasNumber = /\d/.test(pwd);
    const hasSpecial = /[^a-zA-Z0-9]/.test(pwd);
    const variety = [hasLower, hasUpper, hasNumber, hasSpecial].filter(Boolean).length;
    if (variety >= 3) return "strong";
    return "medium";
  };

  const strength = getPasswordStrength(password);
  const strengthColors = {
    weak: "bg-red-500",
    medium: "bg-yellow-500",
    strong: "bg-green-500",
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold text-white mb-4">
          {isNewPassword ? "Set Password" : "Unlock Settings"}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-400 mb-2">
              {isNewPassword ? "Create Password" : "Password"}
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter your password"
              autoFocus
            />
            {password && !isNewPassword && (
              <div className="mt-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${strengthColors[strength]} transition-all`}
                      style={{ width: strength === "weak" ? "33%" : strength === "medium" ? "66%" : "100%" }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 capitalize">{strength}</span>
                </div>
              </div>
            )}
          </div>

          {isNewPassword && (
            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-400 mb-2">
                Confirm Password
              </label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Confirm your password"
              />
            </div>
          )}

          {(error || localError) && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
              <p className="text-sm text-red-400">{error || localError}</p>
            </div>
          )}

          <div className="text-sm text-gray-500">
            {!isNewPassword ? (
              <p>Your settings are encrypted. Enter your password to unlock them.</p>
            ) : (
              <div className="space-y-1">
                <p>Create a password to encrypt your API keys and settings.</p>
                <p className="text-xs">Password must be at least 8 characters. Use a mix of letters, numbers, and symbols for better security.</p>
              </div>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg font-medium transition-colors text-white"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors text-white disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? "Processing..." : isNewPassword ? "Set Password" : "Unlock"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
