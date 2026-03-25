import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // Prevent Next.js from stripping trailing slashes on /api/* routes.
  // FastAPI requires trailing slashes; without this, Next.js 308-redirects
  // /api/rfcs/ -> /api/rfcs, causing an infinite loop with FastAPI's 307.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    const backendUrl =
      process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
