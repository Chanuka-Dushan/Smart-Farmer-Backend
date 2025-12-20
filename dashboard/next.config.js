/** @type {import('next').NextConfig} */

const nextConfig = {
  reactStrictMode: true,
  // Disable Turbopack due to path alias resolution issues
  experimental: {
    turbopack: false,
  },
};

module.exports = nextConfig;
