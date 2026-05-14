"use client";

import { useTranslations } from "next-intl";
import { FileUp, Shield, Sparkles, Briefcase } from "lucide-react";

export default function VaultPage() {
  return (
    <div className="p-4">
      <h1 className="text-lg font-bold text-dark mb-4">经历总库</h1>
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileUp className="h-12 w-12 text-text-muted mb-4" />
        <p className="text-dark font-medium mb-2">暂无简历数据</p>
        <p className="text-sm text-text-muted mb-6">上传简历，系统将自动解析并结构化</p>
        <div className="grid grid-cols-3 gap-3 w-full max-w-xs mb-6">
          <div className="flex flex-col items-center p-3 bg-sand/30 rounded-lg">
            <Shield className="h-6 w-6 text-terra mb-1" />
            <span className="text-xs text-text-muted">智能解析</span>
          </div>
          <div className="flex flex-col items-center p-3 bg-sand/30 rounded-lg">
            <Sparkles className="h-6 w-6 text-terra mb-1" />
            <span className="text-xs text-text-muted">结构管理</span>
          </div>
          <div className="flex flex-col items-center p-3 bg-sand/30 rounded-lg">
            <Briefcase className="h-6 w-6 text-terra mb-1" />
            <span className="text-xs text-text-muted">精准匹配</span>
          </div>
        </div>
      </div>
    </div>
  );
}
