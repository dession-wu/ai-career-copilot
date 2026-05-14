"use client";

import { useState } from "react";
import { useApplicationStore } from "@/stores/applicationStore";
import { toast } from "sonner";
import {
  ArrowLeft,
  Building2,
  Briefcase,
  Link as LinkIcon,
  DollarSign,
  FileText,
  MessageSquare,
  Loader2,
  Check,
  ChevronRight,
} from "lucide-react";
import { useRouter } from "@/i18n/routing";

interface FormErrors {
  company?: string;
  position?: string;
  link?: string;
}

const steps = [
  { id: 1, title: "职位信息", icon: Building2 },
  { id: 2, title: "附加信息", icon: FileText },
  { id: 3, title: "预览确认", icon: Check },
];

const channels = ["官网", "内推", "猎头", "其他"] as const;

export default function NewApplicationPage() {
  const router = useRouter();
  const { addApplication } = useApplicationStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const [formData, setFormData] = useState({
    company: "",
    position: "",
    link: "",
    salary: "",
    channel: "官网" as (typeof channels)[number],
    note: "",
  });

  const validateStep1 = (): boolean => {
    const newErrors: FormErrors = {};
    if (!formData.company.trim()) {
      newErrors.company = "请输入公司名称";
    } else if (formData.company.trim().length < 2) {
      newErrors.company = "公司名称至少2个字符";
    }
    if (!formData.position.trim()) {
      newErrors.position = "请输入职位名称";
    } else if (formData.position.trim().length < 2) {
      newErrors.position = "职位名称至少2个字符";
    }
    if (formData.link && !/^https?:\/\/.+/.test(formData.link)) {
      newErrors.link = "请输入有效的链接地址";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (currentStep === 1 && !validateStep1()) return;
    setCurrentStep((prev) => Math.min(prev + 1, 3));
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await addApplication({
        company: formData.company,
        position: formData.position,
        link: formData.link || undefined,
        salary: formData.salary || undefined,
        channel: formData.channel,
        note: formData.note || undefined,
      });
      toast.success("投递添加成功");
      router.push("/jobs");
    } catch {
      toast.error("添加失败，请重试");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof typeof formData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div className="p-4 space-y-6">
      {/* 头部 */}
      <div className="flex items-center">
        <button
          onClick={() => router.push("/jobs")}
          className="p-2 -ml-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-dark" />
        </button>
        <h1 className="text-lg font-bold text-dark ml-2">添加投递</h1>
      </div>

      {/* 步骤指示器 */}
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center">
            <div
              className={`flex flex-col items-center ${
                currentStep >= step.id ? "text-terra" : "text-text-muted"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  currentStep >= step.id
                    ? "bg-terra text-paper"
                    : "bg-gray-100 text-text-muted"
                }`}
              >
                {currentStep > step.id ? (
                  <Check className="h-4 w-4" />
                ) : (
                  step.id
                )}
              </div>
              <span className="text-xs mt-1">{step.title}</span>
            </div>
            {index < steps.length - 1 && (
              <ChevronRight className="h-4 w-4 text-text-muted mx-2" />
            )}
          </div>
        ))}
      </div>

      {/* 步骤内容 */}
      {currentStep === 1 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-dark">职位信息</h2>

          <div>
            <label className="text-sm text-text-secondary mb-1 block">
              公司名称 *
            </label>
            <div className="relative">
              <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="text"
                value={formData.company}
                onChange={(e) => handleChange("company", e.target.value)}
                className={`w-full pl-9 pr-3 py-2 border rounded-lg text-sm ${
                  errors.company ? "border-red-500" : "border-border-subtle"
                }`}
                placeholder="例如：字节跳动"
              />
            </div>
            {errors.company && (
              <p className="text-xs text-red-500 mt-1">{errors.company}</p>
            )}
          </div>

          <div>
            <label className="text-sm text-text-secondary mb-1 block">
              职位名称 *
            </label>
            <div className="relative">
              <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="text"
                value={formData.position}
                onChange={(e) => handleChange("position", e.target.value)}
                className={`w-full pl-9 pr-3 py-2 border rounded-lg text-sm ${
                  errors.position ? "border-red-500" : "border-border-subtle"
                }`}
                placeholder="例如：前端工程师"
              />
            </div>
            {errors.position && (
              <p className="text-xs text-red-500 mt-1">{errors.position}</p>
            )}
          </div>

          <div>
            <label className="text-sm text-text-secondary mb-1 block">
              招聘链接
            </label>
            <div className="relative">
              <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="url"
                value={formData.link}
                onChange={(e) => handleChange("link", e.target.value)}
                className={`w-full pl-9 pr-3 py-2 border rounded-lg text-sm ${
                  errors.link ? "border-red-500" : "border-border-subtle"
                }`}
                placeholder="https://..."
              />
            </div>
            {errors.link && (
              <p className="text-xs text-red-500 mt-1">{errors.link}</p>
            )}
          </div>

          <div>
            <label className="text-sm text-text-secondary mb-1 block">
              薪资范围
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="text"
                value={formData.salary}
                onChange={(e) => handleChange("salary", e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-border-subtle rounded-lg text-sm"
                placeholder="例如：25k-35k"
              />
            </div>
          </div>
        </div>
      )}

      {currentStep === 2 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-dark">附加信息</h2>

          <div>
            <label className="text-sm text-text-secondary mb-1 block">
              投递渠道
            </label>
            <div className="grid grid-cols-4 gap-2">
              {channels.map((ch) => (
                <button
                  key={ch}
                  onClick={() => handleChange("channel", ch)}
                  className={`py-2 rounded-lg text-sm font-medium transition-colors ${
                    formData.channel === ch
                      ? "bg-terra text-paper"
                      : "bg-white border border-border-subtle text-text-muted"
                  }`}
                >
                  {ch}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm text-text-secondary mb-1 block">
              备注
            </label>
            <div className="relative">
              <MessageSquare className="absolute left-3 top-3 h-4 w-4 text-text-muted" />
              <textarea
                value={formData.note}
                onChange={(e) => handleChange("note", e.target.value)}
                rows={4}
                className="w-full pl-9 pr-3 py-2 border border-border-subtle rounded-lg text-sm resize-none"
                placeholder="添加备注信息，如面试官、面试进度等"
              />
            </div>
          </div>
        </div>
      )}

      {currentStep === 3 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-dark">预览确认</h2>

          <div className="bg-white rounded-xl border border-border-subtle p-4 space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-text-muted">公司名称</span>
              <span className="text-sm text-dark font-medium">
                {formData.company}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-text-muted">职位名称</span>
              <span className="text-sm text-dark font-medium">
                {formData.position}
              </span>
            </div>
            {formData.link && (
              <div className="flex justify-between">
                <span className="text-sm text-text-muted">招聘链接</span>
                <span className="text-sm text-terra truncate max-w-[200px]">
                  {formData.link}
                </span>
              </div>
            )}
            {formData.salary && (
              <div className="flex justify-between">
                <span className="text-sm text-text-muted">薪资范围</span>
                <span className="text-sm text-dark">{formData.salary}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-sm text-text-muted">投递渠道</span>
              <span className="text-sm text-dark">{formData.channel}</span>
            </div>
            {formData.note && (
              <div>
                <span className="text-sm text-text-muted">备注</span>
                <p className="text-sm text-dark mt-1 bg-gray-50 p-2 rounded-lg">
                  {formData.note}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 底部按钮 */}
      <div className="flex gap-3 pt-4">
        {currentStep > 1 && (
          <button
            onClick={handleBack}
            className="flex-1 py-2.5 border border-border-subtle rounded-lg text-sm text-text-secondary"
          >
            上一步
          </button>
        )}
        {currentStep < 3 ? (
          <button
            onClick={handleNext}
            className="flex-1 py-2.5 bg-terra text-paper rounded-lg text-sm font-medium"
          >
            下一步
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex-1 py-2.5 bg-terra text-paper rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "确认提交"
            )}
          </button>
        )}
      </div>
    </div>
  );
}
