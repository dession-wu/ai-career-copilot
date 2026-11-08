'use client';
import PersonalModelSettings from '@/components/career/PersonalModelSettings';
import { useEffect, useState } from 'react';
import { useLocale } from 'next-intl';
import { Link } from '@/i18n/routing';
import { api } from '@/lib/api';
import { errorMessage, dateLabel } from '@/lib/career';
import { PageIntro, Loading, ErrorBox, Notice } from '@/components/career/ui';
interface User {
    id: string;
    username: string;
    email: string;
    created_at: string;
}
export default function SettingsPage() {
    const locale = useLocale();
    const [user, setUser] = useState<User | null>(null), [error, setError] = useState('');
    const load = async () => { setError(''); try {
        setUser((await api.get<User>('/api/auth/me')).data);
    }
    catch (e) {
        setError(errorMessage(e));
    } };
    useEffect(() => { void load(); }, []);
    const logout = async () => { try { await api.post('/api/auth/logout', {}); } catch { window.alert('退出未完成，请检查网络后重试。'); return; } localStorage.removeItem('token'); localStorage.removeItem('username'); sessionStorage.clear(); window.location.assign('/' + locale + '/login'); };
    return <div className="stack"><PersonalModelSettings /><PageIntro title="账户设置" description="查看账户信息与资料使用说明。"/>{error ? <ErrorBox message={error} retry={load}/> : !user ? <Loading /> : <section className="panel"><h2 style={{ fontSize: 18, marginBottom: 20 }}>账户信息</h2><dl className="form-grid"><div><dt className="small-text">用户名</dt><dd style={{ margin: 0 }}>{user.username}</dd></div><div><dt className="small-text">邮箱</dt><dd style={{ margin: 0, overflowWrap: 'anywhere' }}>{user.email}</dd></div><div><dt className="small-text">注册日期</dt><dd style={{ margin: 0 }}>{dateLabel(user.created_at)}</dd></div></dl><p className="small-text" style={{ marginTop: 20 }}>当前版本支持查看账户信息，暂不提供用户名、邮箱和密码修改。</p></section>}<Notice>你的简历用于经历解析和岗位准备。请避免上传不必要的敏感信息；当前经历资料可以在“我的经历”中删除。已有岗位材料需要在对应岗位中管理。</Notice><section className="panel"><div className="section-head"><h2>使用帮助</h2><Link className="text-link" href="/guide">阅读使用指南</Link></div><p className="muted">建议从核对经历开始。分析和生成内容都需要你结合真实情况确认。</p></section><div><button className="btn danger" onClick={logout}>退出登录并清理本次会话草稿</button></div></div>;
}

