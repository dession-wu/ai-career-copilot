import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';

import path from "path";

const nextConfig: NextConfig = {
  // 静态导出：构建产物输出到 out/，由 nginx 直接托管（对齐 ai_novel_agent 部署模式）
  // 服务端能力（middleware/SSR/serverActions）均不可用，页面全部预渲染
  output: 'export',
  images: {
    // 静态导出必须关闭图片优化（无 server runtime）
    unoptimized: true,
  },
  env: {
    // 构建时注入 API 基地址；默认同源相对路径（空字符串），
    // 浏览器请求 /api/* 由 nginx 反代到 backend 容器
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  turbopack: {
    // monorepo 布局：shared/ 在 frontend 上一级，构建根目录指向上级
    root: path.resolve(__dirname, '..'),
  },
};

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

export default withNextIntl(nextConfig);