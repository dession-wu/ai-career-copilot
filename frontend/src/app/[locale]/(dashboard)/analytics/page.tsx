'use client';
import { useEffect, useState } from 'react';
import { Link } from '@/i18n/routing';
import { Job, getJobs, errorMessage, statuses } from '@/lib/career';
import { PageIntro, Loading, ErrorBox, Empty, Notice } from '@/components/career/ui';
export default function AnalyticsPage() {
    const [jobs, setJobs] = useState<Job[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState('');
    const load = async () => { setLoading(true); setError(''); try {
        setJobs(await getJobs());
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setLoading(false);
    } };
    useEffect(() => { void load(); }, []);
    return <div className="stack"><PageIntro title="申请复盘" description="基于你记录的全部目标岗位与当前状态，回顾自己的准备进度。" action={<Link href="/jobs" className="btn">返回目标岗位</Link>}/>{loading ? <Loading /> : error ? <ErrorBox message={error} retry={load}/> : !jobs.length ? <Empty title="有了真实记录，再来回顾进展" description="添加岗位并更新申请状态后，这里会显示你的实际数据。" href="/jobs/new" label="添加目标岗位"/> : <><div className="stat-grid">{[['目标岗位', jobs.length], ['已完成分析', jobs.filter(j => j.match_analysis).length], ['已有岗位简历', jobs.filter(j => j.tailored_resume_md).length]].map(([label, n]) => <div className="panel stat-block" key={label}><p className="muted">{label}</p><strong>{n}</strong></div>)}</div><section className="panel"><div className="section-head"><h2>当前申请状态分布</h2><span className="small-text">全部已记录岗位 · 当前快照</span></div>{Object.entries(statuses).map(([key, label]) => { const count = jobs.filter(j => j.status === key).length; return <div key={key} style={{ margin: '20px 0' }}><div className="section-head" style={{ marginBottom: 8 }}><span>{label}</span><strong>{count}</strong></div><div style={{ height: 7, background: '#f1f5f9', borderRadius: 5 }}><div style={{ height: '100%', width: (count / jobs.length * 100) + '%', background: '#2563eb', borderRadius: 5 }}/></div></div>; })}</section><Notice>统计只覆盖你在本系统记录的岗位，按当前状态计数，不是历史转化漏斗或招聘通过率。删除岗位后相应计数会变化。</Notice></>}</div>;
}
