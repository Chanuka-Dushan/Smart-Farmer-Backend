/** @type {import('next').NextConfig} */

const nextConfig = {
  reactStrictMode: true,
  // Configure Turbopack to use dashboard as root
  experimental: {
    turbopack: {
      root: __dirname,
    },
  },
};

module.exports = nextConfig;
