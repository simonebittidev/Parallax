import type { NextConfig } from "next";

const nextConfig = {
  // ...
  output: 'export',      // genera solo file statici
  // facoltativo, per risolvere asset paths
  // assetPrefix: process.env.NODE_ENV === 'production' ? '' : '',
  eslint: {
    ignoreDuringBuilds: true,
  },
  trailingSlash: true
}

module.exports = nextConfig