const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  output: "standalone",
  rewrites: async () => {
    //if (process.env.NODE_ENV === "production") return [];
    return {
      beforeFiles: [
        {
          source: "/api/:path*",
          destination: `${process.env.NEXT_PUBLIC_BACKEND_HTTP_URL}/:path*`, 
        },
      ],
    };
  },
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Note: we provide webpack here to avoid importing it

    // aliases
    config.resolve.alias["@/components"] = path.join(__dirname, 'components')
    config.resolve.alias["@/utils"] = path.join(__dirname, 'lib/utils')

    return config
  }
};

module.exports = nextConfig;