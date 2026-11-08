'use client';

// 静态导出模式：无 server runtime，redirect() 不可用，改为客户端跳转
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/zh/register");
  }, [router]);

  return null;
}