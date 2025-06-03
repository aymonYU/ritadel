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
  // 静态导出模式下使用相对路径
  assetPrefix: process.env.NODE_ENV === 'production' ? './' : '',
  experimental: {
    // Enable SWC for faster compilation
    forceSwcTransforms: true,
  },
  // 静态导出模式下不支持 rewrites，已移除
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