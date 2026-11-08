'use client';
import { useEffect, useState } from 'react';
import { ChevronRight } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { Job, getJobs, errorMessage, jobPath, statuses } from '@/lib/career';
import { PageIntro, Empty, Loading, ErrorBox, Notice } from '@/components/career/ui';
export default function InterviewPage() {
    const [jobs, setJobs] = useState<Job[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState('');
    const load = async () => { setLoading(true); setError(''); try {
        setJobs((await getJobs()).sort((a, b) => Number(b.status === 'interviewing') - Number(a.status === 'interviewing') || b.updated_at.localeCompare(a.updated_at)));
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setLoading(false);
    } };
    useEffect(() => { void load(); }, []);
    return <div className="stack"><PageIntro title="面试准备" description="选一个目标岗位，把你的真实经历整理成能讲清楚的回答。"/><Notice>这里的材料与具体岗位关联。系统不会自动安排面试，也不会代替你向企业申请。</Notice>{loading ? <Loading /> : error ? <ErrorBox message={error} retry={load}/> : !jobs.length ? <Empty title="先选定一个准备方向" description="添加目标岗位并上传经历后，再围绕要求准备问题与回答。" href="/jobs/new" label="添加目标岗位"/> : <div className="job-list">{jobs.map(j => <Link key={j.id} className="job-row" href={jobPath(j.id, 'interview')}><div><div className="job-title">{j.job_title}</div><div className="job-company">{j.company_name}</div></div><span className="badge">{statuses[j.status] || j.status}</span><span className="job-progress small-text">进入岗位面试准备</span><span className="job-updated"/><ChevronRight size={16}/></Link>)}</div>}</div>;
}
