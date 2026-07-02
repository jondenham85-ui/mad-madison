/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: { serverComponentsExternalPackages: ['openai'] },
  images: { domains: ['lh3.googleusercontent.com'] },
}
module.exports = nextConfig
