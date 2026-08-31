'use client';

// 静态导出模式：无 server runtime，redirect() 不可用，改为客户端跳转
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/zh/dashboard");
  }, [router]);

  return null;
}