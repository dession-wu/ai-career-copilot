import type { Metadata } from "next";
import "../styles/globals.css";
import "../styles/resume.css";

export const metadata: Metadata = {
  icons: {
    icon: [{ url: "/brand/icon.svg?v=20261103-brand1", type: "image/svg+xml" }, { url: "/favicon.ico?v=20261103-brand1" }],
    apple: "/brand/icon-180.png",
  },
  title: "简历指南 · 简历优化与求职准备",
  description: "用真实经历准备有针对性的求职申请：岗位分析、简历核对与面试准备。",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh" suppressHydrationWarning>
      <body className="antialiased">{children}</body>
    </html>
  );
}
