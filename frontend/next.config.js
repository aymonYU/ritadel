/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'export',
  trailingSlash: true,
  distDir: 'out',
  images: {
    unoptimized: true
  },
  assetPrefix: process.env.NODE_ENV === 'production' ? './' : '',
  experimental: {
    // Enable SWC for faster compilation
    forceSwcTransforms: true,
  },
  // API路由在静态导出时需要重写到云函数
  async rewrites() {
    if (process.env.NODE_ENV === 'production') {
      return [
        {
          source: '/api/:path*',
          destination: 'https://tool-1govrq10c87924fe-1258111923.ap-shanghai.app.tcloudbase.com/ritadel-api/:path*'
        }
      ]
    }
    return []
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