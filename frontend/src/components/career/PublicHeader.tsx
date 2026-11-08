'use client';
import { Compass } from 'lucide-react';
import { Link } from '@/i18n/routing';
export function PublicHeader() { return <header className="public-header"><Link href="/" className="brand"><img className="brand-mark" src="/brand/icon.svg?v=20261103-brand1" width={40} height={40} alt="" /><span>简历指南<small>让每一次申请更有准备</small></span></Link><nav><Link href="/guide">使用指南</Link><Link href="/login" className="btn">登录</Link><Link href="/register" className="btn primary">注册</Link></nav></header>; }

