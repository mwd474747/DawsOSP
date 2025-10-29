# DawsOS Next.js UI Dockerfile
# Purpose: Next.js application container
# Updated: 2025-10-28

# ============================================================================
# Stage 1: Dependencies
# ============================================================================
FROM node:18-alpine AS deps

# Install dependencies only when needed
WORKDIR /app

# Copy package files from dawsos-ui directory
COPY dawsos-ui/package.json dawsos-ui/package-lock.json* ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# ============================================================================
# Stage 2: Builder
# ============================================================================
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code from dawsos-ui directory
COPY dawsos-ui/ .

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Install all dependencies (including dev)
RUN npm install

# Build the application
RUN npm run build

# ============================================================================
# Stage 3: Runner
# ============================================================================
FROM node:18-alpine AS runner

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app ./

# Set user
USER nextjs

# Expose port
EXPOSE 3000

# Set environment variables
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

# Start the application
CMD ["npm", "start"]
