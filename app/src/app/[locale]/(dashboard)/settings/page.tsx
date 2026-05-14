"use client";

import { useEffect } from "react";
import { Link } from "@/i18n/routing";
import { useUserStore } from "@/stores/userStore";
import { useNotificationStore } from "@/stores/notificationStore";
import {
  User,
  Bell,
  Shield,
  HelpCircle,
  LogOut,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { useRouter } from "@/i18n/routing";

export default function SettingsPage() {
  const router = useRouter();
  const { user, loading, fetchUser } = useUserStore();
  const { unreadCount, fetchNotifications } = useNotificationStore();

  useEffect(() => {
    fetchUser();
    fetchNotifications();
  }, [fetchUser, fetchNotifications]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    router.push("/login");
  };

  const menuItems = [
    {
      icon: User,
      label: "个人资料",
      desc: "修改头像、昵称等信息",
      href: "/settings/profile",
    },
    {
      icon: Bell,
      label: "消息通知",
      desc: "面试提醒、投递状态通知",
      href: "/settings/notifications",
      badge: unreadCount,
    },
    {
      icon: Shield,
      label: "账号安全",
      desc: "修改密码、绑定手机",
      href: "#",
    },
    {
      icon: HelpCircle,
      label: "帮助与反馈",
      desc: "常见问题、联系客服",
      href: "#",
    },
  ];

  return (
    <div className="p-4 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-dark">我的</h1>
        <p className="text-sm text-text-muted mt-1">管理个人资料和账号设置</p>
      </div>

      {/* 用户信息卡片 */}
      <div className="bg-white rounded-xl border border-border-subtle p-4">
        <div className="flex items-center">
          <div className="w-14 h-14 bg-terra/10 rounded-full flex items-center justify-center">
            <User className="h-7 w-7 text-terra" />
          </div>
          <div className="ml-3">
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin text-terra" />
            ) : (
              <>
                <h2 className="font-medium text-dark">{user?.name || "求职者"}</h2>
                <p className="text-sm text-text-muted">{user?.email || "user@example.com"}</p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 功能菜单 */}
      <div className="space-y-2">
        {menuItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className="bg-white rounded-xl border border-border-subtle p-4 flex items-center justify-between hover:shadow-sm transition-shadow block"
          >
            <div className="flex items-center">
              <item.icon className="h-5 w-5 text-text-muted mr-3" />
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-medium text-dark">{item.label}</h3>
                  {item.badge && item.badge > 0 && (
                    <span className="px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full min-w-[18px] text-center">
                      {item.badge}
                    </span>
                  )}
                </div>
                <p className="text-xs text-text-muted">{item.desc}</p>
              </div>
            </div>
            <ChevronRight className="h-4 w-4 text-text-muted" />
          </Link>
        ))}
      </div>

      {/* 退出登录 */}
      <button
        onClick={handleLogout}
        className="w-full py-3 bg-white rounded-xl border border-border-subtle text-red-500 font-medium text-sm flex items-center justify-center hover:bg-red-50 transition-colors"
      >
        <LogOut className="h-4 w-4 mr-2" />
        退出登录
      </button>

      <p className="text-center text-xs text-text-muted">AI Career Co-pilot v1.0</p>
    </div>
  );
}
