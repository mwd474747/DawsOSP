/** @type {import('next').NextConfig} */
const nextConfig = {
  // API configuration
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // External packages for server components
  serverExternalPackages: ['@tanstack/react-query'],
  
  // Image optimization
  images: {
    domains: ['localhost'],
    unoptimized: true,
  },
  
  // Build configuration
  typescript: {
    ignoreBuildErrors: false,
  },
  
  trailingSlash: false,
}

module.exports = nextConfig
