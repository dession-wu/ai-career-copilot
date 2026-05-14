"use client";

import { MessageSquare, Calendar, CheckCircle, Clock } from "lucide-react";

export default function InterviewPage() {
  const upcomingInterviews = [
    { company: "字节跳动", position: "前端工程师", date: "2026-05-06", type: "视频面试" },
    { company: "阿里巴巴", position: "高级前端", date: "2026-05-08", type: "现场面试" },
  ];

  return (
    <div className="p-4 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-dark">面试准备</h1>
        <p className="text-sm text-text-muted mt-1">管理面试安排，准备面试问题</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-xl border border-border-subtle p-3 text-center">
          <Calendar className="h-5 w-5 text-terra mx-auto mb-1" />
          <p className="text-lg font-bold text-dark">2</p>
          <p className="text-xs text-text-muted">待面试</p>
        </div>
        <div className="bg-white rounded-xl border border-border-subtle p-3 text-center">
          <CheckCircle className="h-5 w-5 text-green-600 mx-auto mb-1" />
          <p className="text-lg font-bold text-dark">5</p>
          <p className="text-xs text-text-muted">已完成</p>
        </div>
        <div className="bg-white rounded-xl border border-border-subtle p-3 text-center">
          <Clock className="h-5 w-5 text-blue-600 mx-auto mb-1" />
          <p className="text-lg font-bold text-dark">3</p>
          <p className="text-xs text-text-muted">待反馈</p>
        </div>
      </div>

      {/* 即将面试 */}
      <div>
        <h2 className="text-sm font-semibold text-dark mb-3">即将面试</h2>
        <div className="space-y-3">
          {upcomingInterviews.map((item, index) => (
            <div key={index} className="bg-white rounded-xl border border-border-subtle p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-dark">{item.company}</h3>
                  <p className="text-sm text-text-muted">{item.position}</p>
                </div>
                <span className="text-xs px-2 py-1 bg-terra/10 text-terra rounded-full">
                  {item.type}
                </span>
              </div>
              <div className="flex items-center mt-3 text-sm text-text-muted">
                <Calendar className="h-4 w-4 mr-1" />
                {item.date}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 面试题库入口 */}
      <div className="bg-white rounded-xl border border-border-subtle p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <MessageSquare className="h-5 w-5 text-terra mr-2" />
            <div>
              <h3 className="font-medium text-dark">面试题库</h3>
              <p className="text-xs text-text-muted">常见面试问题与参考答案</p>
            </div>
          </div>
          <span className="text-xs text-text-muted">开发中</span>
        </div>
      </div>
    </div>
  );
}
