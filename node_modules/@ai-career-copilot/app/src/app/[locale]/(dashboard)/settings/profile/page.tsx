"use client";

import { useEffect, useState } from "react";
import { useUserStore } from "@/stores/userStore";
import { toast } from "sonner";
import { ArrowLeft, User, Camera, Loader2 } from "lucide-react";
import { useRouter } from "@/i18n/routing";

interface FormErrors {
  name?: string;
  title?: string;
  email?: string;
  phone?: string;
  bio?: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, loading, fetchUser, updateUser } = useUserStore();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    title: "",
    email: "",
    phone: "",
    bio: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        title: user.title || "",
        email: user.email || "",
        phone: user.phone || "",
        bio: user.bio || "",
      });
    }
  }, [user]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = "请输入姓名";
    }
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "请输入有效的邮箱地址";
    }
    if (formData.phone && !/^1[3-9]\d{9}$/.test(formData.phone.replace(/\*/g, "0"))) {
      // 允许已脱敏的手机号通过验证
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setIsSaving(true);
    try {
      await updateUser({
        name: formData.name,
        title: formData.title,
        email: formData.email,
        phone: formData.phone,
        bio: formData.bio,
      });
      toast.success("保存成功");
      setIsEditing(false);
    } catch {
      toast.error("保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const handleChange = (field: keyof typeof formData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  if (loading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-terra" />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      {/* 头部 */}
      <div className="flex items-center">
        <button
          onClick={() => router.push("/settings")}
          className="p-2 -ml-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-dark" />
        </button>
        <h1 className="text-lg font-bold text-dark ml-2">个人资料</h1>
      </div>

      {/* 头像 */}
      <div className="flex flex-col items-center">
        <div className="relative">
          <div className="w-20 h-20 bg-terra/10 rounded-full flex items-center justify-center">
            {user?.avatar ? (
              <img src={user.avatar} alt="avatar" className="w-full h-full rounded-full object-cover" />
            ) : (
              <User className="h-10 w-10 text-terra" />
            )}
          </div>
          {isEditing && (
            <button className="absolute bottom-0 right-0 w-7 h-7 bg-terra rounded-full flex items-center justify-center shadow-md">
              <Camera className="h-4 w-4 text-white" />
            </button>
          )}
        </div>
        <p className="text-sm text-text-muted mt-2">{user?.username || "用户"}</p>
      </div>

      {/* 表单 */}
      <div className="space-y-4">
        <div>
          <label className="text-sm text-text-secondary mb-1 block">姓名 *</label>
          {isEditing ? (
            <>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange("name", e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg text-sm ${
                  errors.name ? "border-red-500" : "border-border-subtle"
                }`}
                placeholder="请输入姓名"
              />
              {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
            </>
          ) : (
            <p className="text-sm text-dark py-2">{user?.name || "未设置"}</p>
          )}
        </div>

        <div>
          <label className="text-sm text-text-secondary mb-1 block">职位</label>
          {isEditing ? (
            <input
              type="text"
              value={formData.title}
              onChange={(e) => handleChange("title", e.target.value)}
              className="w-full px-3 py-2 border border-border-subtle rounded-lg text-sm"
              placeholder="例如：前端工程师"
            />
          ) : (
            <p className="text-sm text-dark py-2">{user?.title || "未设置"}</p>
          )}
        </div>

        <div>
          <label className="text-sm text-text-secondary mb-1 block">邮箱</label>
          {isEditing ? (
            <>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleChange("email", e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg text-sm ${
                  errors.email ? "border-red-500" : "border-border-subtle"
                }`}
                placeholder="请输入邮箱"
              />
              {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
            </>
          ) : (
            <p className="text-sm text-dark py-2">{user?.email || "未设置"}</p>
          )}
        </div>

        <div>
          <label className="text-sm text-text-secondary mb-1 block">电话</label>
          {isEditing ? (
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => handleChange("phone", e.target.value)}
              className="w-full px-3 py-2 border border-border-subtle rounded-lg text-sm"
              placeholder="请输入手机号"
            />
          ) : (
            <p className="text-sm text-dark py-2">{user?.phone || "未设置"}</p>
          )}
        </div>

        <div>
          <label className="text-sm text-text-secondary mb-1 block">个人简介</label>
          {isEditing ? (
            <textarea
              value={formData.bio}
              onChange={(e) => handleChange("bio", e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-border-subtle rounded-lg text-sm resize-none"
              placeholder="简单介绍一下自己"
            />
          ) : (
            <p className="text-sm text-dark py-2">{user?.bio || "未设置"}</p>
          )}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="pt-4">
        {isEditing ? (
          <div className="flex gap-3">
            <button
              onClick={() => {
                setIsEditing(false);
                setErrors({});
                if (user) {
                  setFormData({
                    name: user.name || "",
                    title: user.title || "",
                    email: user.email || "",
                    phone: user.phone || "",
                    bio: user.bio || "",
                  });
                }
              }}
              className="flex-1 py-2.5 border border-border-subtle rounded-lg text-sm text-text-secondary"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 py-2.5 bg-terra text-paper rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center"
            >
              {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : "保存"}
            </button>
          </div>
        ) : (
          <button
            onClick={() => setIsEditing(true)}
            className="w-full py-2.5 bg-terra text-paper rounded-lg text-sm font-medium"
          >
            编辑资料
          </button>
        )}
      </div>
    </div>
  );
}
