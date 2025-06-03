/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'dist',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  experimental: {
    // Enable SWC for faster compilation
    forceSwcTransforms: true,
  },
  // Ensure hot reloading works properly
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      }
    }
    return config
  },
}

module.exports = nextConfig 