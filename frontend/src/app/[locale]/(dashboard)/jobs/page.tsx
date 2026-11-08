'use client';
import { useEffect, useState } from 'react';
import { Plus, ChevronRight, ArrowUpRight } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { PageIntro, Loading, ErrorBox, Empty } from '@/components/career/ui';
import { Job, getJobs, errorMessage, jobPath, statuses, dateLabel } from '@/lib/career';
export default function JobsPage() {
    const [jobs, setJobs] = useState<Job[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState(''), [query, setQuery] = useState(''), [filter, setFilter] = useState('');
    const load = async () => { setLoading(true); setError(''); try {
        setJobs((await getJobs()).sort((a, b) => b.updated_at.localeCompare(a.updated_at)));
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setLoading(false);
    } };
    useEffect(() => { void load(); }, []);
    const visible = jobs.filter(j => (!filter || j.status === filter) && (j.company_name + ' ' + j.job_title).toLowerCase().includes(query.toLowerCase()));
    return <><PageIntro title="目标岗位" description="每个岗位，都是一份独立的准备计划。分析要求、修改简历，再跟进申请。" action={<Link className="btn primary" href="/jobs/new"><Plus size={16}/>添加目标岗位</Link>}/>
 <div className="toolbar"><input className="input" aria-label="搜索公司或岗位" placeholder="搜索公司或岗位…" value={query} onChange={e => setQuery(e.target.value)}/><select className="select" aria-label="筛选申请状态" value={filter} onChange={e => setFilter(e.target.value)}><option value="">全部申请状态</option>{Object.entries(statuses).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select><Link className="text-link" href="/analytics">申请复盘<ArrowUpRight size={15}/></Link></div>
 {loading ? <Loading /> : error ? <ErrorBox message={error} retry={load}/> : !jobs.length ? <Empty title="从一个感兴趣的岗位开始" description="准备好公司、岗位名称和职位描述。保存岗位不会向企业提交申请。" href="/jobs/new" label="添加第一个岗位"/> : !visible.length ? <Empty title="没有符合条件的岗位" description="尝试其他关键词，或切换申请状态。"/> : <div className="job-list"><div className="job-row job-row-head"><span>岗位 / 公司</span><span>申请状态</span><span>准备进度</span><span className="job-updated">最近更新</span><span /></div>{visible.map(j => <Link key={j.id} className="job-row" href={jobPath(j.id)}><div><div className="job-title">{j.job_title}</div><div className="job-company">{j.company_name}</div></div><span className={'badge ' + (j.status === 'interviewing' ? 'blue' : j.status === 'offered' ? 'green' : '')}>{statuses[j.status] || j.status}</span><span className="small-text job-progress">{j.tailored_resume_md ? '简历已生成 · 待核对' : j.match_analysis ? '分析已完成' : '待岗位分析'}</span><span className="small-text job-updated">{dateLabel(j.updated_at)}</span><ChevronRight size={16}/></Link>)}</div>}</>;
}
