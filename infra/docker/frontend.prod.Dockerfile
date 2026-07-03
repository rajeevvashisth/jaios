# Production image using Next.js standalone output (next.config.js sets
# `output: "standalone"`) — ships a minimal self-contained server instead
# of the full node_modules tree the local dev Dockerfile uses. Alpine base
# for a much smaller CVE surface than the Debian-based node:*-slim images.

FROM node:22-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
# Every page here is a client component that reads NEXT_PUBLIC_API_BASE_URL
# at fetch time — Next.js inlines NEXT_PUBLIC_* vars into the client bundle
# at BUILD time, not read at container start, so it must be a build arg
# (`docker build --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.example.com`),
# not just a runtime `-e`/ECS task env var.
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser

COPY --from=builder --chown=appuser:appuser /app/.next/standalone ./
COPY --from=builder --chown=appuser:appuser /app/.next/static ./.next/static
COPY --from=builder --chown=appuser:appuser /app/public ./public

USER appuser
EXPOSE 3000

CMD ["node", "server.js"]
