import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  basePath: "/main-repo",
  assetPrefix: "/main-repo/",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
