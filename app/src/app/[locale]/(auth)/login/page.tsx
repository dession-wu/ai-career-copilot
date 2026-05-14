"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Loader2, LogIn, Eye, EyeOff } from "lucide-react";
import { useRouter, Link } from "@/i18n/routing";

interface FormErrors {
  username?: string;
  password?: string;
}

export default function LoginPage() {
  const t = useTranslations();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Fix 3: 已登录用户自动跳转
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      router.push("/dashboard");
    } else {
      setIsCheckingAuth(false);
    }
  }, [router]);

  // Fix 6: 实时输入验证
  const validateField = (field: keyof FormErrors, value: string): string | undefined => {
    if (field === "username") {
      if (!value.trim()) return "请输入用户名";
      if (value.trim().length < 2) return "用户名至少 2 位";
    }
    if (field === "password") {
      if (!value) return "请输入密码";
      if (value.length < 6) return "密码至少 6 位";
    }
    return undefined;
  };

  const handleBlur = (field: keyof FormErrors) => {
    const value = field === "username" ? username : password;
    const error = validateField(field, value);
    setErrors((prev) => ({ ...prev, [field]: error }));
  };

  const handleChange = (field: keyof FormErrors, value: string) => {
    if (field === "username") setUsername(value);
    else setPassword(value);
    // 清除该字段的错误
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 提交前统一验证
    const usernameError = validateField("username", username);
    const passwordError = validateField("password", password);
    if (usernameError || passwordError) {
      setErrors({ username: usernameError, password: passwordError });
      return;
    }

    setIsLoading(true);
    try {
      // 后端使用 OAuth2PasswordRequestForm，需要发送 form-data 格式
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const response = await api.post("/api/auth/login", formData.toString(), {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });
      localStorage.setItem("token", response.data.access_token);
      toast.success(t("auth.loginSuccess") || "登录成功");
      router.push("/dashboard");
    } catch (err: unknown) {
      const error = err as {
        response?: { data?: { detail?: string }; status?: number };
        message?: string;
      };
      // Fix 1: 401 错误现在不会被 interceptor 刷新页面，toast 可以正常显示
      let errorMsg =
        error.response?.data?.detail ||
        error.message ||
        t("auth.loginFailed") ||
        "登录失败，请检查用户名和密码";

      // 处理 422 验证错误（数组格式）
      if (error.response?.status === 422 && Array.isArray(error.response.data?.detail)) {
        errorMsg = "请求格式错误，请稍后重试";
      }

      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  // 检查登录状态中显示 loading
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-paper">
        <Loader2 className="h-8 w-8 animate-spin text-terra" />
      </div>
    );
  }

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

          {/* 密码 - Fix 4: 可见性切换 */}
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

          {/* 登录按钮 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 bg-terra text-paper rounded-lg font-medium text-sm disabled:opacity-50 flex items-center justify-center"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <LogIn className="h-4 w-4 mr-1" />
                登录
              </>
            )}
          </button>
        </form>

        {/* Fix 5: 注册入口链接 */}
        <p className="text-sm text-text-secondary text-center mt-4">
          还没有账号？
          <Link
            href="/register"
            className="text-terra font-medium hover:underline ml-1"
          >
            去注册
          </Link>
        </p>
      </div>
    </div>
  );
}
