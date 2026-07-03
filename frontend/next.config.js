const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: path.join(__dirname),
  // Standalone output lets the production Docker image ship a minimal
  // self-contained server (infra/docker/frontend.prod.Dockerfile) instead
  // of the full node_modules tree.
  output: "standalone",
};

module.exports = nextConfig;
