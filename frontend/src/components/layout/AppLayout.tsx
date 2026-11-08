'use client';
import { useEffect, useState } from 'react';
import { useLocale } from 'next-intl';
import { BriefcaseBusiness, FileText, House, LogOut, MessageSquare, Settings, ArrowUpRight, Compass } from 'lucide-react';
import { Link, usePathname, useRouter } from '@/i18n/routing';
import { api } from '@/lib/api';
import { Loading, ErrorBox } from '@/components/career/ui';
import { errorMessage } from '@/lib/career';
const nav = [{ href: '/dashboard', label: '工作台', icon: House }, { href: '/vault', label: '我的经历', icon: FileText }, { href: '/jobs', label: '目标岗位', icon: BriefcaseBusiness }, { href: '/interview', label: '面试准备', icon: MessageSquare }];
export function AppLayout({ children }: {
    children: React.ReactNode;
}) {
    const pathname = usePathname(), router = useRouter(), locale = useLocale();
    const [ready, setReady] = useState(false), [error, setError] = useState(''), [username, setUsername] = useState('');
    const check = async () => {
        setError('');
        if (!localStorage.getItem('token')) {
            router.replace('/login?next=' + encodeURIComponent(pathname + window.location.search));
            return;
        }
        try {
            const { data } = await api.get('/api/auth/me');
            setUsername(data.username);
            localStorage.setItem('username', data.username);
            setReady(true);
        }
        catch (e) {
            setError(errorMessage(e));
        }
    };
    useEffect(() => { void check(); }, []); // Validate the session once per mounted application shell.
    const logout = async () => { if (!window.confirm('确定退出登录？请先保存正在编辑的内容。'))
        return; try { await api.post('/api/auth/logout', {}); } catch { window.alert('退出未完成，请检查网络后重试。'); return; } localStorage.removeItem('token'); localStorage.removeItem('username'); sessionStorage.clear(); window.location.assign('/' + locale + '/login'); };
    return <div className="app-shell"><a className="skip-link" href="#main-content">跳到主要内容</a>
 <aside className="sidebar"><Link href="/dashboard" className="brand"><img className="brand-mark" src="/brand/icon.svg?v=20261103-brand1" width={40} height={40} alt="" /><span>简历指南<small>让每一次申请更有准备</small></span></Link><p className="nav-caption">我的求职空间</p><nav aria-label="主要导航">{nav.map(({ href, label, icon: Icon }) => <Link key={href} href={href} className={'nav-link ' + (pathname.startsWith(href) ? 'active' : '')} aria-current={pathname.startsWith(href) ? 'page' : undefined}><Icon size={19}/><span>{label}</span></Link>)}</nav><div className="sidebar-foot"><div className="sidebar-note"><FileText size={18}/><p>从真实经历出发，<br />为目标岗位做好准备。</p></div><Link className="nav-link" href="/guide"><ArrowUpRight size={18}/>使用指南</Link><Link className={'nav-link ' + (pathname.startsWith('/settings') ? 'active' : '')} href="/settings"><Settings size={18}/>账户设置</Link><button className="nav-link" onClick={logout}><LogOut size={18}/>退出登录</button></div></aside>
 <div className="app-body"><header className="topbar"><span>申请准备工作台</span><Link className="user-link" href="/settings"><span className="avatar">{username.slice(0, 1).toUpperCase() || 'C'}</span><span>{username || '我的账户'}</span></Link></header><main id="main-content" className="workspace">{error ? <ErrorBox message={error} retry={check}/> : ready ? children : <Loading text="正在确认登录状态…"/>}</main></div>
 <nav className="mobile-nav" aria-label="移动端导航">{nav.map(({ href, label, icon: Icon }) => <Link key={href} href={href} className={pathname.startsWith(href) ? 'active' : ''}><Icon size={20}/>{label}</Link>)}</nav></div>;
}

