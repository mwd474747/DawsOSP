/** @type {import('next').NextConfig} */
const nextConfig = {
  // Fix workspace root warning
  outputFileTracingRoot: '/Users/mdawson/Documents/GitHub/DawsOSP',
  
  // Enable standalone output for Docker
  output: 'standalone',
  
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
  
  // Disable static optimization
  trailingSlash: false,
  
  // Force all pages to be dynamic
  experimental: {
    // Disable static optimization
  },
}

module.exports = nextConfig