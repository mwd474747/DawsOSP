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
    unoptimized: true, // For development
  },
  
  // Build configuration
  typescript: {
    // Type checking handled by separate process
    ignoreBuildErrors: false,
  },
  
  // Disable static optimization for now
  trailingSlash: false,
}

module.exports = nextConfig
