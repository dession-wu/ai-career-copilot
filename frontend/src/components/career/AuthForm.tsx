'use client';
import { useEffect, useState } from 'react';
import { Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';
import { Link, useRouter } from '@/i18n/routing';
import { api } from '@/lib/api';
import { errorMessage } from '@/lib/career';
import { ErrorBox, Notice } from './ui';
import { PublicHeader } from './PublicHeader';
export default function AuthForm({ register = false }: {
    register?: boolean;
}) {
    const router = useRouter();
    const [username, setUsername] = useState(''), [email, setEmail] = useState(''), [password, setPassword] = useState(''), [show, setShow] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState(''), [success, setSuccess] = useState(false);
    const nextPath = () => { const next = new URLSearchParams(window.location.search).get('next') || '/dashboard'; return next.startsWith('/') && !next.startsWith('//') && !next.includes('\\') && !/^\/(?:zh\/|en\/)?(?:login|register)/.test(next) ? next : '/dashboard'; };
    useEffect(() => { let active = true; if (localStorage.getItem('token')) {
        api.get('/api/auth/me').then(() => { if (active)
            router.replace(nextPath()); }).catch(() => { localStorage.removeItem('token'); });
    } return () => { active = false; }; }, [router]);
    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (busy)
            return;
        setBusy(true);
        setError('');
        try {
            if (register) {
                await api.post('/api/auth/register', { username: username.trim(), email: email.trim(), password });
                setSuccess(true);
            }
            else {
                const form = new URLSearchParams({ username: username.trim(), password });
                const { data } = await api.post('/api/auth/login', form.toString(), { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('username', username.trim());
                sessionStorage.clear();
                router.replace(nextPath());
            }
        }
        catch (e) {
            setError(errorMessage(e));
        }
        finally {
            setBusy(false);
        }
    };
    return <div className="auth-shell"><div className="public-shell" style={{ width: '100%' }}><PublicHeader /></div><main className="auth-main"><aside className="auth-aside"><h2>让经历成为申请的底气。</h2><p>对照岗位要求，找到相关经历，让简历里的每句话都有依据。</p><div className="auth-proof"><h3>从经历中找到亮点</h3><p>整理用户访谈中的注册问题，参与注册流程优化方案设计。</p><span>具体行动 + 真实贡献</span></div></aside><section className="panel"><h1>{register ? '建立你的简历工作台' : '欢迎回来'}</h1><p className="muted" style={{ marginTop: 10 }}>{register ? '建立账户，整理经历并为目标岗位做好准备。' : '继续整理经历、准备岗位简历与面试。'}</p>{success ? <div className="stack" style={{ marginTop: 25 }}><Notice>账户已创建，请登录后继续。</Notice><Link href="/login" className="btn primary">前往登录<ArrowRight size={16}/></Link></div> : <form onSubmit={submit}><label className="field"><span className="field-label">用户名</span><input name="username" className="input" autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required minLength={2} maxLength={50} disabled={busy}/></label>{register && <label className="field"><span className="field-label">邮箱</span><input name="email" type="email" className="input" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required disabled={busy}/></label>}<div className="field"><label htmlFor="password">密码</label><div style={{ position: 'relative' }}><input id="password" name="password" type={show ? 'text' : 'password'} className="input" style={{ paddingRight: 46 }} autoComplete={register ? 'new-password' : 'current-password'} value={password} onChange={e => setPassword(e.target.value)} required minLength={register ? 6 : 1} disabled={busy}/><button type="button" aria-label={show ? '隐藏密码' : '显示密码'} onClick={() => setShow(!show)} style={{ position: 'absolute', right: 8, top: 9, border: 0, background: 'none', color: '#64748b', padding: 4 }}>{show ? <EyeOff size={18}/> : <Eye size={18}/>}</button></div>{register && <small>至少 6 位，请使用与其他网站不同的密码。</small>}</div>{error && <ErrorBox message={error}/>}<button className="btn primary" disabled={busy}>{busy ? <Loader2 size={16} className="spin"/> : <ArrowRight size={16}/>}{busy ? '正在处理…' : register ? '创建账户' : '登录并继续'}</button><p className="small-text" style={{ textAlign: 'center' }}>{register ? '已经有账户？' : '还没有账户？'} <Link className="text-link" href={register ? '/login' : '/register'}>{register ? '前往登录' : '注册账户'}</Link></p></form>}</section><p className="small-text" style={{ textAlign: 'center', marginTop: 20 }}>以真实经历为依据，所有生成建议都由你核对。</p></main></div>;
}
