"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { ArrowRight, Check, Eye, EyeOff, Loader2, LogIn, Sparkles, Target } from "lucide-react";
import { useRouter, Link } from "@/i18n/routing";

interface FormErrors { username?: string; password?: string; }

export default function LoginPage() {
  const t = useTranslations();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    if (localStorage.getItem("token")) router.push("/dashboard");
    else setIsCheckingAuth(false);
  }, [router]);

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
    setErrors((prev) => ({ ...prev, [field]: validateField(field, value) }));
  };

  const handleChange = (field: keyof FormErrors, value: string) => {
    if (field === "username") setUsername(value);
    else setPassword(value);
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const usernameError = validateField("username", username);
    const passwordError = validateField("password", password);
    if (usernameError || passwordError) {
      setErrors({ username: usernameError, password: passwordError });
      return;
    }
    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);
      const response = await api.post("/api/auth/login", formData.toString(), { headers: { "Content-Type": "application/x-www-form-urlencoded" } });
      localStorage.setItem("token", response.data.access_token);
      toast.success(t("auth.loginSuccess") || "登录成功");
      router.push("/dashboard");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string }; status?: number }; message?: string };
      toast.error(error.response?.data?.detail || error.message || t("auth.loginFailed") || "登录失败，请检查用户名和密码");
    } finally { setIsLoading(false); }
  };

  if (isCheckingAuth) return <div className="career-auth-loading"><Loader2 size={22} /></div>;

  return (
    <div className="career-auth-page">
      <style>{` .career-auth-page{min-height:100vh;background:#eef4f8;color:#172235;font-family:Inter,ui-sans-serif,system-ui,sans-serif;position:relative;overflow:hidden}.career-auth-page:before{content:"";position:fixed;inset:0;opacity:.55;pointer-events:none;background-image:linear-gradient(rgba(41,104,215,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(41,104,215,.08) 1px,transparent 1px);background-size:58px 58px}.career-auth-shell{position:relative;z-index:1;width:min(1180px,calc(100% - 64px));min-height:100vh;margin:auto;display:grid;grid-template-rows:auto 1fr auto}.career-auth-header,.career-auth-footer{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(23,34,53,.14);padding:25px 0}.career-auth-footer{border-top:1px solid rgba(23,34,53,.14);border-bottom:0;color:#687487;font:9px ui-monospace,monospace;letter-spacing:.08em}.career-auth-brand{display:flex;align-items:center;gap:10px;color:#172235;text-decoration:none}.career-auth-brand-mark{display:grid;width:32px;height:32px;place-items:center;border:1px solid #172235;border-radius:50%;color:#2968d7}.career-auth-brand strong,.career-auth-brand small{display:block}.career-auth-brand strong{font-size:11px;letter-spacing:.14em}.career-auth-brand small{margin-top:3px;color:#687487;font-size:8px;letter-spacing:.1em}.career-auth-back{color:#687487;font-size:11px;text-decoration:none}.career-auth-back:hover{color:#2968d7}.career-auth-content{display:grid;grid-template-columns:1fr 430px;align-items:center;gap:12%;padding:72px 0}.career-auth-intro{max-width:560px}.career-auth-kicker,.career-auth-card-label{color:#2968d7;font:10px ui-monospace,monospace;letter-spacing:.1em}.career-auth-kicker span{margin-right:8px;color:#172235}.career-auth-intro h1{margin:24px 0 0;font-size:clamp(50px,6.2vw,82px);font-weight:500;letter-spacing:-.06em;line-height:1.02}.career-auth-intro h1 em{color:#2968d7;font-style:normal}.career-auth-intro>p:not(.career-auth-kicker){max-width:420px;margin-top:28px;color:#687487;font-size:15px;line-height:1.9}.career-auth-signal{display:grid;grid-template-columns:22px 1fr auto;gap:10px;align-items:center;max-width:420px;margin-top:54px;padding:16px 0;border-top:1px solid rgba(23,34,53,.14);border-bottom:1px solid rgba(23,34,53,.14);color:#687487;font-size:12px}.career-auth-signal svg{color:#2968d7}.career-auth-signal b{color:#27836d;font:10px ui-monospace,monospace;font-weight:400}.career-auth-card{background:rgba(255,255,255,.86);border:1px solid rgba(23,34,53,.16);padding:29px;box-shadow:16px 16px 0 rgba(41,104,215,.1)}.career-auth-card-top{display:flex;justify-content:space-between;color:#687487;font:9px ui-monospace,monospace;letter-spacing:.1em;padding-bottom:15px;border-bottom:1px solid rgba(23,34,53,.14)}.career-auth-card h2{margin:27px 0 7px;font-size:25px;font-weight:500;letter-spacing:-.04em}.career-auth-card-subtitle{margin:0;color:#687487;font-size:12px}.career-auth-form{margin-top:29px}.career-auth-field+.career-auth-field{margin-top:18px}.career-auth-field label{display:block;margin-bottom:8px;color:#172235;font-size:12px;font-weight:600}.career-auth-field input{width:100%;height:48px;box-sizing:border-box;padding:0 13px;border:1px solid rgba(23,34,53,.18);background:#fff;color:#172235;font:13px inherit;border-radius:0}.career-auth-field input:focus-visible{outline:2px solid #2968d7;outline-offset:2px;border-color:#2968d7}.career-auth-password{position:relative}.career-auth-password input{padding-right:45px}.career-auth-eye{position:absolute;right:5px;top:4px;width:40px;height:40px;border:0;background:transparent;color:#687487;cursor:pointer}.career-auth-eye:focus-visible,.career-auth-submit:focus-visible,.career-auth-card a:focus-visible,.career-auth-brand:focus-visible{outline:2px solid #2968d7;outline-offset:3px}.career-auth-error{margin:14px 0 0;padding:10px 12px;background:#fceeed;border-left:3px solid #c24b45;color:#9f3934;font-size:12px}.career-auth-submit{display:flex;align-items:center;justify-content:center;gap:14px;width:100%;height:52px;margin-top:22px;border:0;background:#2968d7;color:#fff;font-size:12px;font-weight:700;cursor:pointer}.career-auth-submit:hover{background:#1f52ae}.career-auth-submit:disabled{cursor:wait;opacity:.65}.career-auth-register{margin:24px 0 0;color:#687487;text-align:center;font-size:12px}.career-auth-register a{display:inline-flex;align-items:center;gap:4px;margin-left:4px;color:#172235;font-weight:700;text-decoration:underline;text-underline-offset:4px}.career-auth-loading{min-height:100vh;display:grid;place-items:center;color:#2968d7}.career-auth-loading svg{animation:career-spin .8s linear infinite}@keyframes career-spin{to{transform:rotate(360deg)}}@media(max-width:900px){.career-auth-content{grid-template-columns:1fr;gap:45px}.career-auth-card{max-width:520px;width:100%;box-sizing:border-box;margin-left:auto}}@media(max-width:600px){.career-auth-shell{width:calc(100% - 34px)}.career-auth-header{padding:20px 0}.career-auth-content{padding:54px 0 65px}.career-auth-intro h1{font-size:clamp(48px,15vw,70px)}.career-auth-card{padding:23px 20px}.career-auth-footer{flex-wrap:wrap;gap:10px}.career-auth-footer span:last-child{width:100%}}@media(prefers-reduced-motion:reduce){.career-auth-loading svg{animation:none}}`}</style>
      <div className="career-auth-shell">
        <header className="career-auth-header"><Link href="/" className="career-auth-brand" aria-label="返回首页"><span className="career-auth-brand-mark"><Sparkles size={15} /></span><span><strong>CAREER CO-PILOT</strong><small>MAKE YOUR NEXT MOVE CLEAR</small></span></Link><Link href="/" className="career-auth-back">返回首页 <ArrowRight size={13} /></Link></header>
        <main className="career-auth-content">
          <section className="career-auth-intro" aria-labelledby="career-login-title"><p className="career-auth-kicker"><span>01</span> YOUR NEXT MOVE</p><h1 id="career-login-title">从清晰的判断，<br /><em>开始下一步。</em></h1><p>登录你的职业档案，继续查看经历证据、岗位匹配和下一步行动。</p><div className="career-auth-signal"><Check size={15} /><span>你的经历始终是建议的依据</span><b>VERIFIED</b></div></section>
          <section className="career-auth-card" aria-label="登录表单"><div className="career-auth-card-top"><span>CAREER SIGNAL BOARD</span><span>ACCESS / 001</span></div><h2>欢迎回来</h2><p className="career-auth-card-subtitle">进入你的求职工作台。</p><form className="career-auth-form" onSubmit={handleSubmit} noValidate><div className="career-auth-field"><label htmlFor="career-username">用户名</label><input id="career-username" name="username" type="text" autoComplete="username" placeholder="请输入用户名…" value={username} onChange={(e) => handleChange("username", e.target.value)} onBlur={() => handleBlur("username")} aria-invalid={Boolean(errors.username)} aria-describedby={errors.username ? "career-username-error" : undefined} required />{errors.username && <p className="career-auth-error" id="career-username-error">{errors.username}</p>}</div><div className="career-auth-field"><label htmlFor="career-password">密码</label><div className="career-auth-password"><input id="career-password" name="password" type={showPassword ? "text" : "password"} autoComplete="current-password" placeholder="请输入密码…" value={password} onChange={(e) => handleChange("password", e.target.value)} onBlur={() => handleBlur("password")} aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "career-password-error" : undefined} required /><button type="button" className="career-auth-eye" aria-label={showPassword ? "隐藏密码" : "显示密码"} onClick={() => setShowPassword((visible) => !visible)}>{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button></div>{errors.password && <p className="career-auth-error" id="career-password-error">{errors.password}</p>}</div><button type="submit" className="career-auth-submit" disabled={isLoading} aria-busy={isLoading}>{isLoading ? <><Loader2 size={16} /> 登录中…</> : <><LogIn size={16} /> 登录并查看路径</>}</button></form><p className="career-auth-register">还没有职业档案？<Link href="/register">开始建立 <ArrowRight size={13} /></Link></p></section>
        </main>
        <footer className="career-auth-footer"><span>CAREER CO-PILOT</span><span>FACT-BASED CAREER PLANNING</span><span>© 2026</span></footer>
      </div>
    </div>
  );
}
