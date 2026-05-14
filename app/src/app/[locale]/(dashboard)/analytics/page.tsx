"use client";

import { TrendingUp, Send, MessageSquare, FileText, Target } from "lucide-react";

export default function AnalyticsPage() {
  const stats = [
    { label: "本周投递", value: 12, icon: Send, color: "text-terra" },
    { label: "面试邀请", value: 3, icon: MessageSquare, color: "text-green-600" },
    { label: "简历完善度", value: "85%", icon: FileText, color: "text-blue-600" },
    { label: "目标完成", value: "60%", icon: Target, color: "text-purple-600" },
  ];

  return (
    <div className="p-4 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-dark">数据分析</h1>
        <p className="text-sm text-text-muted mt-1">求职数据洞察与进度追踪</p>
      </div>

      {/* 核心指标 */}
      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-border-subtle p-4">
            <stat.icon className={`h-6 w-6 ${stat.color} mb-2`} />
            <p className="text-2xl font-bold text-dark">{stat.value}</p>
            <p className="text-xs text-text-muted">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* 投递趋势 */}
      <div className="bg-white rounded-xl border border-border-subtle p-4">
        <h2 className="text-sm font-semibold text-dark mb-4">近7天投递趋势</h2>
        <div className="flex items-end justify-between h-32 px-2">
          {[
            { day: "周一", count: 2 },
            { day: "周二", count: 4 },
            { day: "周三", count: 1 },
            { day: "周四", count: 5 },
            { day: "周五", count: 3 },
            { day: "周六", count: 0 },
            { day: "周日", count: 2 },
          ].map((item) => (
            <div key={item.day} className="flex flex-col items-center flex-1">
              <div
                className="w-6 bg-terra/80 rounded-t"
                style={{ height: `${item.count * 20}px` }}
              />
              <span className="text-xs text-text-muted mt-1">{item.day}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 面试转化率 */}
      <div className="bg-white rounded-xl border border-border-subtle p-4">
        <h2 className="text-sm font-semibold text-dark mb-3">求职漏斗</h2>
        <div className="space-y-3">
          <div className="flex items-center">
            <span className="text-sm text-text-muted w-20">投递简历</span>
            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden mx-3">
              <div className="h-full bg-terra rounded-full" style={{ width: "100%" }} />
            </div>
            <span className="text-sm font-medium text-dark">50</span>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-text-muted w-20">简历通过</span>
            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden mx-3">
              <div className="h-full bg-terra/80 rounded-full" style={{ width: "60%" }} />
            </div>
            <span className="text-sm font-medium text-dark">30</span>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-text-muted w-20">面试邀请</span>
            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden mx-3">
              <div className="h-full bg-terra/60 rounded-full" style={{ width: "24%" }} />
            </div>
            <span className="text-sm font-medium text-dark">12</span>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-text-muted w-20">拿到offer</span>
            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden mx-3">
              <div className="h-full bg-terra/40 rounded-full" style={{ width: "8%" }} />
            </div>
            <span className="text-sm font-medium text-dark">4</span>
          </div>
        </div>
      </div>
    </div>
  );
}
