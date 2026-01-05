"use client";

import { useSettings } from "@/hooks/useSettings";

interface SliderInputProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  unit?: string;
  description?: string;
}

function SliderInput({ label, value, onChange, min, max, step, unit, description }: SliderInputProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-300">{label}</label>
        <span className="text-sm text-gray-400">
          {value}
          {unit && <span className="text-gray-600"> {unit}</span>}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
      />
      {description && <p className="text-xs text-gray-500">{description}</p>}
    </div>
  );
}

const MODEL_OPTIONS = [
  "gpt-4o-mini",
  "gpt-4o",
  "gpt-4-turbo",
  "gpt-4",
  "claude-3-haiku-20240307",
  "claude-3-sonnet-20240229",
  "claude-3-opus-20240229",
  "gemini-pro",
];

export default function ModelConfigSection() {
  const { settings, updateModelConfig } = useSettings();
  const config = settings?.model_config_data;

  if (!config) return null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-2">Model Configuration</h2>
        <p className="text-sm text-gray-400">
          Configure default parameters for language model requests.
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Default Model
          </label>
          <select
            value={config.default_model}
            onChange={(e) => updateModelConfig({ default_model: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {MODEL_OPTIONS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>

        <SliderInput
          label="Temperature"
          value={config.temperature}
          onChange={(value) => updateModelConfig({ temperature: value })}
          min={0}
          max={2}
          step={0.1}
          description="Controls randomness in responses. Higher = more creative."
        />

        <SliderInput
          label="Max Tokens"
          value={config.max_tokens}
          onChange={(value) => updateModelConfig({ max_tokens: value })}
          min={1}
          max={128000}
          step={1}
          unit="tokens"
          description="Maximum number of tokens to generate."
        />

        <SliderInput
          label="Top P"
          value={config.top_p}
          onChange={(value) => updateModelConfig({ top_p: value })}
          min={0}
          max={1}
          step={0.05}
          description="Controls diversity via nucleus sampling."
        />

        <div className="grid grid-cols-2 gap-4">
          <SliderInput
            label="Frequency Penalty"
            value={config.frequency_penalty}
            onChange={(value) => updateModelConfig({ frequency_penalty: value })}
            min={-2}
            max={2}
            step={0.1}
            description="Reduce repetition of frequent tokens."
          />

          <SliderInput
            label="Presence Penalty"
            value={config.presence_penalty}
            onChange={(value) => updateModelConfig({ presence_penalty: value })}
            min={-2}
            max={2}
            step={0.1}
            description="Encourage talking about new topics."
          />
        </div>
      </div>
    </div>
  );
}
