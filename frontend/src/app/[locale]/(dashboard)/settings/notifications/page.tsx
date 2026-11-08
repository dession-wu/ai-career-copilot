'use client';
import { Link } from '@/i18n/routing';
import { PageIntro, Notice } from '@/components/career/ui';
export default function NotificationsPage() { return <div className="stack"><PageIntro title="通知说明" description="当前版本尚未提供可靠的通知与面试提醒服务。"/><Notice>请自行管理面试时间和企业消息。这里不会展示示例提醒或承诺已向你发送通知。</Notice><Link className="btn" href="/settings">返回账户设置</Link></div>; }
