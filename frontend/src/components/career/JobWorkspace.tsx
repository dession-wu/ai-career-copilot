'use client';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, RefreshCw, Save, Trash2 } from 'lucide-react';
import { Link, useRouter } from '@/i18n/routing';
import { api } from '@/lib/api';
import { Job, Vault, confirmed, errorMessage, getVault, statuses, JobStatus, staleAnalysis } from '@/lib/career';
import { PageIntro, ErrorBox, Empty, Loading, Notice } from './ui';
import { ResumeEditor } from './ResumeEditor';
import { InterviewQuestions } from './InterviewQuestions';
import { useLeaveGuard } from '@/hooks/useLeaveGuard';
export default function JobWorkspace() {
    const params = useSearchParams(), id = params.get('id') || '', router = useRouter();
    const [job, setJob] = useState<Job | null>(null), [vault, setVault] = useState<Vault | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState(''), [busy, setBusy] = useState(''), [tab, setTab] = useState(['analysis', 'resume', 'interview'].includes(params.get('tab') || '') ? params.get('tab')! : 'analysis'), [resumeDirty, setResumeDirty] = useState(false);
    const [editing, setEditing] = useState(false), [company, setCompany] = useState(''), [title, setTitle] = useState(''), [jd, setJd] = useState('');
    const edited = Boolean(editing && job && (company !== job.company_name || title !== job.job_title || jd !== job.jd_text));
    useLeaveGuard(edited);
    const load = async () => {
        setLoading(true);
        setError('');
        try {
            if (!id)
                throw new Error('缺少岗位编号，请返回目标岗位列表重新选择。');
            const [j, v] = await Promise.all([api.get<Job>('/api/jobs/' + encodeURIComponent(id)), getVault()]);
            setJob(j.data);
            setVault(v);
        }
        catch (e) {
            setError(errorMessage(e));
        }
        finally {
            setLoading(false);
        }
    };
    useEffect(() => { void load(); }, [id]);
    const run = async (name: string, action: () => Promise<void>) => { if (busy)
        return; setBusy(name); setError(''); try {
        await action();
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy('');
    } };
    const analyze = () => run('正在对照岗位要求与个人经历…', async () => { await api.post('/api/jobs/' + id + '/analyze', null, { timeout: 180000 }); const { data } = await api.get<Job>('/api/jobs/' + id); setJob(data); });
    const updateStatus = (status: JobStatus) => run('正在保存申请状态…', async () => { const { data } = await api.put<Job>('/api/jobs/' + id + '/status', { status }); setJob(data); });
    const editJob = () => { if (!job)
        return; setCompany(job.company_name); setTitle(job.job_title); setJd(job.jd_text); setEditing(true); };
    const saveJob = (e: React.FormEvent) => { e.preventDefault(); void run('正在保存职位信息…', async () => { const { data } = await api.put<Job>('/api/jobs/' + id, { company_name: company.trim(), job_title: title.trim(), jd_text: jd.trim() }); setJob(data); setEditing(false); }); };
    const remove = () => { if (!window.confirm('删除这个岗位及其简历版本、面试准备材料？此操作不能撤销。'))
        return; void run('正在删除岗位…', async () => { await api.delete('/api/jobs/' + id); router.push('/jobs'); }); };
    if (loading)
        return <Loading />;
    if (!job)
        return <ErrorBox message={error || '岗位不存在'} retry={load}/>;
    const stale = staleAnalysis(job, vault), ready = confirmed(vault), analysis = job.match_analysis;
    const evidence = vault?.raw_content || JSON.stringify(vault?.structured_data || {}, null, 2);
    return <div className="stack"><div><Link className="back-link" href="/jobs"><ArrowLeft size={14}/>返回目标岗位</Link><PageIntro title={job.job_title} description={job.company_name} action={<span className={'badge ' + (job.status === 'interviewing' ? 'blue' : '')}>{statuses[job.status] || job.status}</span>}/><div className="actions"><button className="btn small" disabled={Boolean(busy) || resumeDirty} onClick={editJob}>编辑职位信息</button><label className="small-text" htmlFor="application-status">申请状态</label><select id="application-status" className="select" style={{ width: 'auto' }} value={job.status} disabled={Boolean(busy)} onChange={e => updateStatus(e.target.value as JobStatus)}>{Object.entries(statuses).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select><span className="small-text">请在自行投递后，将状态改为“已投递”。</span></div></div>
    {error && <ErrorBox message={error}/>}{busy && <Loading text={busy}/>}
    {editing && <form className="panel stack" onSubmit={saveJob}><div className="section-head"><h2>编辑职位信息</h2><span className="small-text">JD 变化后需重新分析</span></div><div className="form-grid"><label className="field"><span className="field-label">公司名称 *</span><input className="input" value={company} onChange={e => setCompany(e.target.value)} required maxLength={255} disabled={Boolean(busy)}/></label><label className="field"><span className="field-label">岗位名称 *</span><input className="input" value={title} onChange={e => setTitle(e.target.value)} required maxLength={255} disabled={Boolean(busy)}/></label></div><label className="field"><span className="field-label">职位描述 *</span><textarea className="textarea" rows={10} value={jd} onChange={e => setJd(e.target.value)} required maxLength={50000} disabled={Boolean(busy)}/></label><div className="actions"><button className="btn primary" disabled={Boolean(busy) || !company.trim() || !title.trim() || !jd.trim()}><Save size={15}/>保存职位信息</button><button type="button" className="btn" disabled={Boolean(busy)} onClick={() => { if (!edited || window.confirm('丢弃未保存的职位修改？'))
        setEditing(false); }}>取消</button></div></form>}
    {!ready && <Notice>先核对并保存个人经历，才能生成有依据的岗位建议。<Link className="text-link" href="/vault">前往我的经历<ArrowRight size={14}/></Link></Notice>}
    {stale && <Notice>当前分析的经历版本或职位描述已变化，或旧结果缺少来源记录。请重新分析后再生成岗位简历。</Notice>}
    <div><div className="tabs" role="tablist" aria-label="岗位准备步骤">{[['analysis', '匹配分析'], ['resume', '岗位简历'], ['interview', '面试准备']].map(([key, label]) => <button key={key} id={'tab-' + key} role="tab" aria-selected={tab === key} aria-controls={'panel-' + key} className={'tab ' + (tab === key ? 'active' : '')} onClick={() => setTab(key)}>{label}</button>)}</div>
      <section role="tabpanel" id="panel-analysis" aria-labelledby="tab-analysis" hidden={tab !== 'analysis'}><div className="two-col"><div className="stack"><div className="section-head"><div><h2>你的经历，如何对应岗位要求？</h2><p>结果用于整理申请材料，不代表录用概率。</p></div><button className="btn primary" disabled={Boolean(busy) || !ready || edited} onClick={analyze}><RefreshCw size={15}/>{analysis ? '重新分析' : '开始分析'}</button></div>{analysis ? <><section className="panel"><div className="section-head"><h2>匹配参考</h2><span className="badge">依据版本 {analysis.source_vault_version || '未记录'}</span></div><div className="score">{analysis.overall_score}<small> / 100</small></div><p className="small-text">基于岗位文本与经历的匹配参考，不能替代招聘方判断。</p><hr className="divider"/><h3>在经历中找到的技能线索</h3><div className="skill-chips">{analysis.skill_match?.matched?.length ? analysis.skill_match.matched.map((s, i) => <span className="badge green" key={s + i}>{s}</span>) : <p className="muted">暂未提取到明确匹配项，请核对原文。</p>}</div><h3>尚未找到充分证据的要求</h3><div className="skill-chips">{analysis.skill_match?.missing?.length ? analysis.skill_match.missing.map((s, i) => <span className="badge amber" key={s + i}>{s}</span>) : <p className="muted">当前分析没有列出额外缺口，不代表完全满足要求。</p>}</div><p className="small-text">未找到证据不等于你不具备能力。可以回到经历页补充真实项目后重新分析。</p></section><section className="panel"><h2 style={{ fontSize: 17 }}>下一步建议</h2><ul className="evidence-list">{analysis.suggestions?.map((s, i) => <li key={i}>{s}</li>)}</ul><div className="actions" style={{ marginTop: 20 }}><button className="btn primary" disabled={stale || !ready} onClick={() => setTab('resume')}>准备岗位简历<ArrowRight size={15}/></button><Link href="/vault" className="btn">补充经历证据</Link></div></section></> : <Empty title="先理解要求，再决定如何表达" description="分析将对照你的已确认经历与原始 JD，整理匹配线索和需要补充证据的地方。"/>}</div><aside className="stack"><section className="panel"><h2 style={{ fontSize: 16, marginBottom: 15 }}>原始职位描述</h2><p className="jd-text">{job.jd_text}</p></section><section className="panel"><h2 style={{ fontSize: 16, marginBottom: 15 }}>经历依据 · 对照阅读</h2><p className="small-text" style={{ marginBottom: 14 }}>技能匹配是文本线索，请对照原文核实具体职责与成果。</p><p className="jd-text">{evidence || '请先上传并核对经历。'}</p></section></aside></div></section>
      <section role="tabpanel" id="panel-resume" aria-labelledby="tab-resume" hidden={tab !== 'resume'}><ResumeEditor key={job.id} job={job} vault={vault} enabled={ready && Boolean(analysis) && !stale && !edited} onUpdated={setJob} onDirty={setResumeDirty}/></section>
      <section role="tabpanel" id="panel-interview" aria-labelledby="tab-interview" hidden={tab !== 'interview'}><InterviewQuestions key={job.id} jobId={job.id} enabled={ready}/></section>
    </div><div className="form-foot"><span className="small-text">岗位与材料仅保存在你的账户中；申请动作由你自行完成。</span><button className="btn small danger" disabled={Boolean(busy) || resumeDirty} onClick={remove}><Trash2 size={14}/>删除岗位</button></div></div>;
}
