'use client';
import { useEffect, useState } from 'react';
import { ArrowRight, Check, ChevronRight, Plus } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { PageIntro, Loading, ErrorBox } from '@/components/career/ui';
import { Job, Vault, confirmed, dateLabel, errorMessage, getJobs, getVault, jobPath, statuses } from '@/lib/career';
export default function DashboardPage() {
    const [jobs, setJobs] = useState<Job[]>([]), [vault, setVault] = useState<Vault | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState('');
    const load = async () => { setLoading(true); setError(''); try {
        const [j, v] = await Promise.all([getJobs(), getVault()]);
        setJobs(j.sort((a, b) => b.updated_at.localeCompare(a.updated_at)));
        setVault(v);
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setLoading(false);
    } };
    useEffect(() => { void load(); }, []);
    if (loading)
        return <Loading />;
    if (error)
        return <ErrorBox message={error} retry={load}/>;
    const active = jobs.find(j => j.status === 'preparing') || jobs[0];
    const stage = !vault ? 0 : !confirmed(vault) ? 1 : !jobs.length ? 2 : 3;
    const title = ['先让我们了解你的真实经历', '核对经历，让建议有据可依', '你想为哪个岗位做准备？', active?.tailored_resume_md ? '继续打磨你的岗位简历' : '开始一次有依据的岗位分析'][stage];
    const desc = ['上传已有简历，整理可复用的个人经历，为不同岗位做好准备。', '自动解析可能存在遗漏。请检查姓名、任职时间、项目与成果，再把它们用作分析依据。', '粘贴职位描述，我们会将岗位要求与你已确认的经历逐项对照。', '查看匹配依据、补充经历证据，再核对并导出适合这个岗位的简历。'][stage];
    const href = stage < 2 ? '/vault' : stage === 2 ? '/jobs/new' : jobPath(active.id, active.tailored_resume_md ? 'resume' : 'analysis');
    const label = ['上传我的简历', '核对我的经历', '添加目标岗位', '继续准备'][stage];
    return <div className="stack"><PageIntro title="把下一次申请，准备得更好" description="整理真实经历，理解岗位要求，一步步完成你的求职准备。"/>
 <section className="welcome-panel"><div><span className="badge blue">你的下一步</span><h2>{title}</h2><p>{desc}</p><Link className="btn primary" href={href}>{label}<ArrowRight size={16}/></Link></div><ol className="journey">{['上传简历', '核对经历', '添加目标岗位', '分析与准备'].map((s, i) => <li key={s} className={i < stage ? 'done' : i === stage ? 'current' : ''}><b>{i < stage ? <Check size={13}/> : i + 1}</b>{s}</li>)}</ol></section>
 <section><div className="section-head"><div><h2>最近的目标岗位</h2><p>从上次停下的地方继续。</p></div><Link className="text-link" href="/jobs/new"><Plus size={16}/>添加岗位</Link></div>{jobs.length ? <div className="job-list">{jobs.slice(0, 4).map(j => <Link className="job-row" key={j.id} href={jobPath(j.id)}><div><div className="job-title">{j.job_title}</div><div className="job-company">{j.company_name}</div></div><span className={'badge ' + (j.status === 'interviewing' ? 'blue' : '')}>{statuses[j.status] || j.status}</span><span className="small-text job-progress">{j.tailored_resume_md ? '简历已生成' : j.match_analysis ? '分析已完成' : '待岗位分析'}</span><span className="small-text job-updated">{dateLabel(j.updated_at)}</span><ChevronRight size={16}/></Link>)}</div> : <div className="panel"><p className="muted">还没有目标岗位。先完成经历核对，再添加你感兴趣的职位。</p></div>}</section>
 <section className="panel"><div className="section-head"><div><h2>你的申请概况</h2><p>仅统计你在这里记录的岗位，不代表已向企业自动投递。</p></div><Link href="/analytics" className="text-link">查看复盘<ArrowRight size={15}/></Link></div><div className="metric-row">{[['目标岗位', jobs.length], ['准备中', jobs.filter(j => j.status === 'preparing').length], ['面试中', jobs.filter(j => j.status === 'interviewing').length], ['已获 Offer', jobs.filter(j => j.status === 'offered').length]].map(([name, n]) => <div key={name}><strong>{n}</strong><span className="small-text">{name}</span></div>)}</div></section></div>;
}
