"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import {
  Send,
  MessageSquare,
  Calendar,
  TrendingUp,
  Plus,
  ChevronRight,
  Bell,
  Clock,
} from "lucide-react";

interface TodoItem {
  id: number;
  title: string;
  time: string;
  type: "interview" | "deadline" | "followup";
}

interface ActivityItem {
  id: number;
  title: string;
  desc: string;
  time: string;
}

export default function DashboardPage() {
  const t = useTranslations();
  const [username, setUsername] = useState("");

  useEffect(() => {
    const stored = localStorage.getItem("username");
    if (stored) setUsername(stored);
  }, []);

  const todos: TodoItem[] = [
    { id: 1, title: "字节跳动 - 前端工程师视频面试", time: "今天 14:00", type: "interview" },
    { id: 2, title: "腾讯 - 投递截止日期", time: "明天 23:59", type: "deadline" },
    { id: 3, title: "阿里巴巴 - 跟进面试结果", time: "后天", type: "followup" },
  ];

  const activities: ActivityItem[] = [
    { id: 1, title: "投递了美团 - 高级前端", desc: "简历已通过初筛", time: "2小时前" },
    { id: 2, title: "京东 - 面试已完成", desc: "等待 HR 反馈", time: "昨天" },
    { id: 3, title: "更新了个人简历", desc: "完善了项目经历", time: "3天前" },
  ];

  const stats = [
    { label: "本周投递", value: 12, icon: Send, href: "/jobs" },
    { label: "待面试", value: 2, icon: MessageSquare, href: "/interview" },
    { label: "待办事项", value: 3, icon: Calendar, href: "/jobs" },
    { label: "通过率", value: "25%", icon: TrendingUp, href: "/analytics" },
  ];

  const quickActions = [
    { label: "添加投递", icon: Plus, href: "/jobs/new" },
    { label: "面试准备", icon: MessageSquare, href: "/interview" },
    { label: "查看数据", icon: TrendingUp, href: "/analytics" },
  ];

  const getTodoIcon = (type: string) => {
    switch (type) {
      case "interview":
        return <MessageSquare className="h-4 w-4 text-terra" />;
      case "deadline":
        return <Clock className="h-4 w-4 text-orange-500" />;
      case "followup":
        return <Bell className="h-4 w-4 text-blue-500" />;
      default:
        return <Calendar className="h-4 w-4 text-text-muted" />;
    }
  };

  return (
    <div className="p-4 space-y-6">
      {/* 欢迎语 */}
      <div>
        <h1 className="text-xl font-bold text-dark">
          {t("dashboard.welcome")}，{username || "求职者"}
        </h1>
        <p className="text-sm text-text-muted mt-1">今天有 2 个待办事项需要处理</p>
      </div>

      {/* 数据概览 */}
      <div className="grid grid-cols-4 gap-3">
        {stats.map((stat) => (
          <Link key={stat.label} href={stat.href} className="block">
            <div className="bg-white rounded-xl border border-border-subtle p-3 text-center hover:shadow-sm transition-shadow">
              <stat.icon className="h-5 w-5 text-terra mx-auto mb-1" />
              <p className="text-lg font-bold text-dark">{stat.value}</p>
              <p className="text-xs text-text-muted">{stat.label}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* 快捷操作 */}
      <div>
        <h2 className="text-sm font-semibold text-dark mb-3">快捷操作</h2>
        <div className="flex gap-3">
          {quickActions.map((action) => (
            <Link
              key={action.label}
              href={action.href}
              className="flex-1 bg-white rounded-xl border border-border-subtle p-3 flex flex-col items-center hover:shadow-sm transition-shadow"
            >
              <action.icon className="h-5 w-5 text-terra mb-1" />
              <span className="text-xs text-dark">{action.label}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* 今日待办 */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-dark">今日待办</h2>
          <Link href="/jobs" className="text-xs text-terra flex items-center">
            查看全部 <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="space-y-2">
          {todos.map((todo) => (
            <div
              key={todo.id}
              className="bg-white rounded-xl border border-border-subtle p-3 flex items-center"
            >
              <div className="w-8 h-8 bg-terra/10 rounded-lg flex items-center justify-center mr-3">
                {getTodoIcon(todo.type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-dark truncate">{todo.title}</p>
                <p className="text-xs text-text-muted">{todo.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 最近动态 */}
      <div>
        <h2 className="text-sm font-semibold text-dark mb-3">最近动态</h2>
        <div className="space-y-2">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className="bg-white rounded-xl border border-border-subtle p-3"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm text-dark">{activity.title}</p>
                <span className="text-xs text-text-muted">{activity.time}</span>
              </div>
              <p className="text-xs text-text-muted mt-1">{activity.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
