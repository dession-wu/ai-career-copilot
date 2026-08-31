import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "AI Career Co-pilot",
  description: "智能求职副驾 - 移动版",
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
