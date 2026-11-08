'use client';

// 静态导出模式：无 server runtime，redirect() 不可用，改为客户端跳转
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    // 改为指向落地页（[locale]/page.tsx），未登录用户不再被直接送进 dashboard
    router.replace("/zh");
  }, [router]);

  return null;
}