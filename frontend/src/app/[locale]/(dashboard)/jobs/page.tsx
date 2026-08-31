"use client";

import { useEffect } from "react";
import { useApplicationStore } from "@/stores/applicationStore";
import { Link } from "@/i18n/routing";
import {
  Briefcase,
  Plus,
  Building2,
  Clock,
  Loader2,
  Send,
  MessageSquare,
  CheckCircle,
  XCircle,
  Archive,
} from "lucide-react";

const statusConfig = {
  投递中: { color: "bg-blue-100 text-blue-700", icon: Send },
  面试中: { color: "bg-terra/10 text-terra", icon: MessageSquare },
  已offer: { color: "bg-green-100 text-green-700", icon: CheckCircle },
  已拒绝: { color: "bg-red-100 text-red-700", icon: XCircle },
  已结束: { color: "bg-gray-100 text-gray-700", icon: Archive },
};

export default function JobsPage() {
  const { applications, loading, fetchApplications } = useApplicationStore();

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("zh-CN", {
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="p-4 space-y-4">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-dark">求职</h1>
          <p className="text-sm text-text-muted">
            共 {applications.length} 条投递记录
          </p>
        </div>
        <Link
          href="/jobs/new"
          className="p-2 bg-terra text-paper rounded-lg flex items-center"
        >
          <Plus className="h-5 w-5" />
        </Link>
      </div>

      {/* 投递列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-terra" />
        </div>
      ) : applications.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Briefcase className="h-12 w-12 text-text-muted mb-3" />
          <p className="text-sm text-text-muted">暂无投递记录</p>
          <p className="text-xs text-text-muted mt-1">
            点击右上角 + 添加您的第一条投递
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {applications.map((app) => {
            const status = statusConfig[app.status] || statusConfig["投递中"];
            const StatusIcon = status.icon;

            return (
              <div
                key={app.id}
                className="bg-white rounded-xl border border-border-subtle p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start flex-1 min-w-0">
                    <div className="w-10 h-10 bg-terra/10 rounded-lg flex items-center justify-center flex-shrink-0 mr-3">
                      <Building2 className="h-5 w-5 text-terra" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-dark truncate">
                        {app.company}
                      </h3>
                      <p className="text-xs text-text-muted mt-0.5">
                        {app.position}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}
                        >
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {app.status}
                        </span>
                        {app.channel && (
                          <span className="text-xs text-text-muted">
                            {app.channel}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end ml-2">
                    <span className="text-xs text-text-muted flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {formatDate(app.createdAt)}
                    </span>
                    {app.salary && (
                      <span className="text-xs text-terra mt-1">
                        {app.salary}
                      </span>
                    )}
                  </div>
                </div>

                {app.note && (
                  <p className="text-xs text-text-muted mt-3 bg-gray-50 p-2 rounded-lg">
                    {app.note}
                  </p>
                )}

                {app.link && (
                  <a
                    href={app.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-terra mt-2 inline-block hover:underline"
                  >
                    查看招聘详情 →
                  </a>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
