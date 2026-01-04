import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable React strict mode
  reactStrictMode: true,

  // Disable server components features for simpler setup
  experimental: {
    // Allow client-side only app for now
  },
};

export default nextConfig;
