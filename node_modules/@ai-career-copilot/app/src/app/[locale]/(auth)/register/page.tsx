"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Loader2, UserPlus, Eye, EyeOff } from "lucide-react";
import { useRouter, Link } from "@/i18n/routing";

interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

export default function RegisterPage() {
  const t = useTranslations();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const validateField = (field: keyof FormErrors, value: string): string | undefined => {
    if (field === "username") {
      if (!value.trim()) return "请输入用户名";
      if (value.trim().length < 2) return "用户名至少 2 位";
    }
    if (field === "email") {
      if (!value.trim()) return "请输入邮箱";
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) return "请输入有效的邮箱地址";
    }
    if (field === "password") {
      if (!value) return "请输入密码";
      if (value.length < 6) return "密码至少 6 位";
    }
    if (field === "confirmPassword") {
      if (!value) return "请确认密码";
    }
    return undefined;
  };

  const handleBlur = (field: keyof FormErrors) => {
    const value =
      field === "username" ? username :
      field === "email" ? email :
      field === "password" ? password :
      confirmPassword;
    const error = validateField(field, value);
    setErrors((prev) => ({ ...prev, [field]: error }));
  };

  const handleChange = (field: keyof FormErrors, value: string) => {
    if (field === "username") setUsername(value);
    else if (field === "email") setEmail(value);
    else if (field === "password") setPassword(value);
    else if (field === "confirmPassword") setConfirmPassword(value);

    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 统一验证所有字段
    const usernameError = validateField("username", username);
    const emailError = validateField("email", email);
    const passwordError = validateField("password", password);
    const confirmPasswordError = validateField("confirmPassword", confirmPassword);

    if (usernameError || emailError || passwordError || confirmPasswordError) {
      setErrors({
        username: usernameError,
        email: emailError,
        password: passwordError,
        confirmPassword: confirmPasswordError,
      });
      return;
    }

    // 密码匹配验证
    if (password !== confirmPassword) {
      toast.error(t('auth.passwordMismatch') || "两次密码输入不一致");
      return;
    }

    setIsLoading(true);
    try {
      await api.post("/api/auth/register", { username, email, password });
      toast.success(t('auth.registerSuccess') || "注册成功");
      router.push("/login");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast.error(error.response?.data?.detail || t('auth.registerFailed') || "注册失败");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-paper">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-lg p-6">
        <h1 className="text-xl font-bold text-dark text-center mb-6">
          AI Career Co-pilot
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          {/* 用户名 */}
          <div>
            <label className="text-sm text-text-secondary mb-1 block">用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => handleChange("username", e.target.value)}
              onBlur={() => handleBlur("username")}
              className={`w-full px-3 py-2 border rounded-lg text-sm transition-colors ${
                errors.username
                  ? "border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                  : "border-border-subtle focus:border-terra focus:ring-1 focus:ring-terra"
              }`}
              placeholder="请输入用户名"
            />
            {errors.username && (
              <p className="text-xs text-red-500 mt-1">{errors.username}</p>
            )}
          </div>

          {/* 邮箱 */}
          <div>
            <label className="text-sm text-text-secondary mb-1 block">邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => handleChange("email", e.target.value)}
              onBlur={() => handleBlur("email")}
              className={`w-full px-3 py-2 border rounded-lg text-sm transition-colors ${
                errors.email
                  ? "border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                  : "border-border-subtle focus:border-terra focus:ring-1 focus:ring-terra"
              }`}
              placeholder="请输入邮箱"
            />
            {errors.email && (
              <p className="text-xs text-red-500 mt-1">{errors.email}</p>
            )}
          </div>

          {/* 密码 */}
          <div>
            <label className="text-sm text-text-secondary mb-1 block">密码</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => handleChange("password", e.target.value)}
                onBlur={() => handleBlur("password")}
                className={`w-full px-3 py-2 pr-10 border rounded-lg text-sm transition-colors ${
                  errors.password
                    ? "border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                    : "border-border-subtle focus:border-terra focus:ring-1 focus:ring-terra"
                }`}
                placeholder="请输入密码"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-dark transition-colors"
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.password && (
              <p className="text-xs text-red-500 mt-1">{errors.password}</p>
            )}
          </div>

          {/* 确认密码 */}
          <div>
            <label className="text-sm text-text-secondary mb-1 block">确认密码</label>
            <div className="relative">
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => handleChange("confirmPassword", e.target.value)}
                onBlur={() => handleBlur("confirmPassword")}
                className={`w-full px-3 py-2 pr-10 border rounded-lg text-sm transition-colors ${
                  errors.confirmPassword
                    ? "border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                    : "border-border-subtle focus:border-terra focus:ring-1 focus:ring-terra"
                }`}
                placeholder="请再次输入密码"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-dark transition-colors"
                tabIndex={-1}
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="text-xs text-red-500 mt-1">{errors.confirmPassword}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 bg-terra text-paper rounded-lg font-medium text-sm disabled:opacity-50 flex items-center justify-center"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <UserPlus className="h-4 w-4 mr-1" />
                注册
              </>
            )}
          </button>
        </form>
        <p className="text-sm text-text-secondary text-center mt-4">
          已有账号？
          <Link
            href="/login"
            className="text-terra font-medium hover:underline ml-1"
          >
            去登录
          </Link>
        </p>
      </div>
    </div>
  );
}
