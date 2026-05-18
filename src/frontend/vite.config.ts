import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const previewPort = Number(process.env.PORT ?? 4173);
const railwayPublicDomain = process.env.RAILWAY_PUBLIC_DOMAIN;
const apiBaseUrl = cspOrigin(process.env.VITE_API_BASE_URL);
const previewAllowedHosts = [
  "wk-pool.up.railway.app",
  ...(railwayPublicDomain ? [railwayPublicDomain] : []),
];
const connectSources = [
  "'self'",
  "http://127.0.0.1:8000",
  "http://localhost:8000",
  ...(apiBaseUrl ? [apiBaseUrl] : []),
];
const contentSecurityPolicy = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self' https://flagcdn.com data:",
  `connect-src ${connectSources.join(" ")}`,
  "object-src 'none'",
  "base-uri 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
].join("; ");

const securityHeaders = {
  "Content-Security-Policy": contentSecurityPolicy,
  "Cross-Origin-Resource-Policy": "same-origin",
  "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
};

export default defineConfig({
  plugins: [react()],
  server: {
    headers: securityHeaders,
  },
  preview: {
    host: "0.0.0.0",
    port: previewPort,
    strictPort: true,
    allowedHosts: previewAllowedHosts,
    headers: securityHeaders,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});

function cspOrigin(value: string | undefined): string | undefined {
  const trimmedValue = value?.trim();
  if (!trimmedValue) {
    return undefined;
  }

  try {
    return new URL(trimmedValue).origin;
  } catch {
    return undefined;
  }
}
