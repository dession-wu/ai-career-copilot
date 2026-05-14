"use client";

import { useEffect } from "react";
import { useNotificationStore } from "@/stores/notificationStore";
import { toast } from "sonner";
import {
  ArrowLeft,
  Bell,
  Check,
  Trash2,
  Loader2,
  MessageSquare,
  Settings,
} from "lucide-react";
import { useRouter } from "@/i18n/routing";

export default function NotificationsPage() {
  const router = useRouter();
  const {
    notifications,
    unreadCount,
    loading,
    filter,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    setFilter,
  } = useNotificationStore();

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const filteredNotifications = notifications.filter((n) => {
    if (filter === "all") return true;
    return n.type === filter;
  });

  const handleMarkAllRead = async () => {
    await markAllAsRead();
    toast.success("已全部标记为已读");
  };

  const handleDelete = async (id: number) => {
    await deleteNotification(id);
    toast.success("已删除");
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return "刚刚";
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString("zh-CN");
  };

  const filters = [
    { key: "all" as const, label: "全部" },
    { key: "business" as const, label: "业务" },
    { key: "system" as const, label: "系统" },
  ];

  return (
    <div className="p-4 space-y-4">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => router.push("/settings")}
            className="p-2 -ml-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-dark" />
          </button>
          <h1 className="text-lg font-bold text-dark ml-2">消息通知</h1>
          {unreadCount > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
              {unreadCount}
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="text-sm text-terra flex items-center"
          >
            <Check className="h-4 w-4 mr-1" />
            全部已读
          </button>
        )}
      </div>

      {/* 分类筛选 */}
      <div className="flex gap-2">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filter === f.key
                ? "bg-terra text-paper"
                : "bg-white text-text-muted border border-border-subtle"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* 消息列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-terra" />
        </div>
      ) : filteredNotifications.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Bell className="h-12 w-12 text-text-muted mb-3" />
          <p className="text-sm text-text-muted">暂无消息</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredNotifications.map((notification) => (
            <div
              key={notification.id}
              className={`bg-white rounded-xl border p-4 transition-all ${
                notification.read
                  ? "border-border-subtle"
                  : "border-terra/30 bg-terra/5"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start flex-1 min-w-0">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 flex-shrink-0 ${
                      notification.type === "business"
                        ? "bg-terra/10"
                        : "bg-blue-100"
                    }`}
                  >
                    {notification.type === "business" ? (
                      <MessageSquare className="h-4 w-4 text-terra" />
                    ) : (
                      <Settings className="h-4 w-4 text-blue-600" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-medium text-dark">
                        {notification.title}
                      </h3>
                      {!notification.read && (
                        <span className="w-2 h-2 bg-red-500 rounded-full flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-text-muted mt-1">
                      {notification.content}
                    </p>
                    <p className="text-xs text-text-muted mt-2">
                      {formatTime(notification.createdAt)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1 ml-2">
                  {!notification.read && (
                    <button
                      onClick={() => markAsRead(notification.id)}
                      className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                      title="标记已读"
                    >
                      <Check className="h-4 w-4 text-text-muted" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(notification.id)}
                    className="p-1.5 hover:bg-red-50 rounded-lg transition-colors"
                    title="删除"
                  >
                    <Trash2 className="h-4 w-4 text-text-muted hover:text-red-500" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
