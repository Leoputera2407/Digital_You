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
          destination: `${process.env.NEXT_PUBLIC_BACKEND_HTTP_URL}/:path*`, 
        },
      ],
    };
  },
};

module.exports = nextConfig;
