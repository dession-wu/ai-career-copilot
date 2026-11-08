'use client';
import { AlertCircle, ArrowRight, Loader2 } from 'lucide-react';
import { Link } from '@/i18n/routing';
export function PageIntro({ title, description, action }: {
    title: string;
    description: string;
    action?: React.ReactNode;
}) { return <div className="page-intro"><div><h1>{title}</h1><p>{description}</p></div>{action}</div>; }
export function Loading({ text = '正在读取你的资料…' }: {
    text?: string;
}) { return <div className="loading-state" role="status"><Loader2 size={20} className="spin"/>{text}</div>; }
export function ErrorBox({ message, retry }: {
    message: string;
    retry?: () => void;
}) { return <div className="error-box" role="alert"><AlertCircle size={18}/><div>{message}{retry && <button type="button" onClick={retry}>重新尝试</button>}</div></div>; }
export function Empty({ title, description, href, label }: {
    title: string;
    description: string;
    href?: string;
    label?: string;
}) { return <div className="empty-state"><span className="empty-symbol"><ArrowRight size={24}/></span><h2>{title}</h2><p>{description}</p>{href && <Link className="btn primary" href={href}>{label}<ArrowRight size={16}/></Link>}</div>; }
export function Notice({ children }: {
    children: React.ReactNode;
}) { return <div className="notice">{children}</div>; }
