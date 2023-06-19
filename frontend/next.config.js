/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  output: "standalone",
  rewrites: async () => {
    if (process.env.NODE_ENV === "production") return [];
    
    return {
      beforeFiles: [
        {
          source: "/api/:path*",
          destination: "http://localhost:8080/:path*", 
        },
      ],
    };
  },
};

module.exports = nextConfig;
