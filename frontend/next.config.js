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
          destination: "https://a035-2600-1700-2f71-4890-ddfc-3ad4-c1ad-3dcf.ngrok-free.app/:path*", 
        },
      ],
    };
  },
};

module.exports = nextConfig;
