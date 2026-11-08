'use client';
import { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, Loader2 } from 'lucide-react';
import { Link, useRouter } from '@/i18n/routing';
import { api } from '@/lib/api';
import { errorMessage, Job, jobPath } from '@/lib/career';
import { PageIntro, ErrorBox, Notice } from '@/components/career/ui';
import { useLeaveGuard } from '@/hooks/useLeaveGuard';
export default function NewJobPage() {
    const router = useRouter();
    const [company, setCompany] = useState(''), [title, setTitle] = useState(''), [jd, setJd] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState(''), [draft, setDraft] = useState(false), [saved, setSaved] = useState(false), [initialized, setInitialized] = useState(false);
    useEffect(() => { setDraft(Boolean(sessionStorage.getItem('career-job-draft'))); setInitialized(true); }, []);
    useLeaveGuard(Boolean(!saved && (company || title || jd)));
    const restore = () => { try {
        const d = JSON.parse(sessionStorage.getItem('career-job-draft') || '{}');
        setCompany(d.company || '');
        setTitle(d.title || '');
        setJd(d.jd || '');
        setDraft(false);
    }
    catch {
        sessionStorage.removeItem('career-job-draft');
        setDraft(false);
    } };
    useEffect(() => { if (initialized && !draft && !saved && (company || title || jd)) {
        try {
            sessionStorage.setItem('career-job-draft', JSON.stringify({ company, title, jd }));
        }
        catch { /* Saving remains available when browser draft storage is full. */ }
    } }, [company, title, jd, initialized, draft, saved]);
    const submit = async (e: React.FormEvent) => { e.preventDefault(); if (busy)
        return; setBusy(true); setError(''); try {
        const { data } = await api.post<Job>('/api/jobs', { company_name: company.trim(), job_title: title.trim(), jd_text: jd.trim() });
        sessionStorage.removeItem('career-job-draft');
        setSaved(true);
        router.push(jobPath(data.id));
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } };
    return <><Link className="back-link" href="/jobs"><ArrowLeft size={14}/>返回目标岗位</Link><PageIntro title="添加一个目标岗位" description="把职位描述放在这里，开始准备一份有针对性的申请。"/>
 <div className="two-col"><section className="panel">{draft && <div className="notice"><p>发现本次浏览器会话中未提交的草稿。</p><div className="actions" style={{ marginTop: 10 }}><button className="btn small" onClick={restore}>恢复草稿</button><button className="btn small" onClick={() => { sessionStorage.removeItem('career-job-draft'); setDraft(false); }}>丢弃草稿</button></div></div>}<form onSubmit={submit} className="stack" style={{ marginTop: draft ? 20 : 0 }}><div className="form-grid"><div className="field"><label htmlFor="company">公司名称 *</label><input id="company" className="input" value={company} onChange={e => setCompany(e.target.value)} required maxLength={255} placeholder="例如：你感兴趣的公司" disabled={busy}/></div><div className="field"><label htmlFor="job-title">岗位名称 *</label><input id="job-title" className="input" value={title} onChange={e => setTitle(e.target.value)} required maxLength={255} placeholder="例如：产品经理" disabled={busy}/></div></div><div className="field"><label htmlFor="jd">职位描述（JD）*</label><textarea id="jd" className="textarea" rows={13} value={jd} onChange={e => setJd(e.target.value)} required maxLength={50000} placeholder="粘贴完整的岗位职责、任职要求和加分项…" disabled={busy}/><small>保留原始要求，有助于理解分析依据。请勿粘贴招聘方未公开的敏感信息。</small></div>{error && <ErrorBox message={error}/>}<div className="form-foot"><span className="small-text">保存到服务器后，进入岗位准备工作区。</span><button className="btn primary" disabled={busy || !company.trim() || !title.trim() || !jd.trim()}>{busy ? <Loader2 className="spin" size={16}/> : <ArrowRight size={16}/>}保存并进入工作区</button></div></form></section><aside className="stack"><Notice>添加岗位不会自动向企业投递。你可以先分析、修改简历，准备好后再自行申请并更新状态。</Notice><section className="panel"><h2 style={{ fontSize: 17, marginBottom: 16 }}>接下来可以做什么？</h2><ol className="evidence-list"><li>对照职位要求，查看经历匹配。</li><li>核对建议，编辑岗位简历。</li><li>导出简历，准备岗位面试。</li></ol><p className="small-text" style={{ marginTop: 20 }}>还没有上传简历？岗位可先保存，随后补充经历再分析。</p></section></aside></div></>;
}
