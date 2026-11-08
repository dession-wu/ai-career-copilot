'use client';
import { useState } from 'react';
import { Download, FileText, Save, ShieldCheck, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { Job, Vault, ResumeVersion, errorMessage, downloadBlob, dateLabel } from '@/lib/career';
import { Empty, ErrorBox, Loading, Notice } from './ui';
import { useLeaveGuard } from '@/hooks/useLeaveGuard';
import { RevisionReview } from './RevisionReview';
export function ResumeEditor({ job, vault, enabled, onUpdated, onDirty }: {
    job: Job;
    vault: Vault | null;
    enabled: boolean;
    onUpdated: (j: Job) => void;
    onDirty: (dirty: boolean) => void;
}) {
    const [content, setContent] = useState(job.tailored_resume_md || ''), [saved, setSaved] = useState(job.tailored_resume_md || ''), [busy, setBusy] = useState(''), [error, setError] = useState(''), [message, setMessage] = useState(''), [reviewed, setReviewed] = useState(false), [verified, setVerified] = useState(false), [preview, setPreview] = useState(false), [baseline, setBaseline] = useState(job.tailored_resume_md || ''), [showCompare, setShowCompare] = useState(false);
    const [proposal, setProposal] = useState('');
    const [confirmedContent, setConfirmedContent] = useState('');
    const dirty = content !== saved;
    useLeaveGuard(dirty);
    const edit = (text: string) => { setContent(text); setReviewed(false); setVerified(false); setMessage(''); onDirty(text !== saved); };
    const run = async (name: string, action: () => Promise<void>) => { if (busy)
        return; setBusy(name); setError(''); setMessage(''); try {
        await action();
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy('');
    } };
    const generate = () => {
        if (content && !window.confirm('生成结果会替换编辑区，并保存为当前生成版本。需要保留的修改请先保存为历史版本。确定继续？'))
            return;
        void run('正在整理岗位简历…', async () => {
            setBaseline(content || vault?.raw_content || '');
            const { data } = await api.post('/api/jobs/' + job.id + '/tailor', {}, { timeout: 180000 });
            setContent(data.content);
            setSaved(data.content);
            setReviewed(false);
            setVerified(false);
            onDirty(false);
            setProposal(data.content);
            onUpdated({ ...job, tailored_resume_md: data.content });
            setMessage(data.mode === 'fallback' ? '当前使用基础模板整理，未启用 AI 深度定制。请逐项核对后保存。' : '生成内容已保存为当前草稿。请对照原始经历核对，再保存确认版本。');
        });
    };
    const save = () => run('正在保存版本…', async () => {
        const { data } = await api.post<ResumeVersion>('/api/jobs/' + job.id + '/tailor/versions', { content, note: reviewed ? '已由用户核对事实' : '编辑草稿', reviewed: reviewed && verified, source_vault_version: vault?.version, source_jd_text: job.jd_text });
        setSaved(content);
        onDirty(false);
        onUpdated({ ...job, tailored_resume_md: content, tailored_resume_versions: [...(job.tailored_resume_versions || []), data] });
        setConfirmedContent(reviewed && verified ? content : '');
        setMessage(reviewed && verified ? '已确认版本保存成功，可以导出 PDF。' : '草稿已保存。导出前请执行辅助核验，并确认全部事实。');
    });
    const verify = () => run('正在核验经历依据…', async () => {
        const { data } = await api.post('/api/jobs/' + job.id + '/verify', { resume_content: content }, { timeout: 180000 });
        setVerified(Boolean(data.verified));
        setReviewed(false);
        setMessage(data.verified ? '辅助核验未发现明显异常，但不能替代人工检查。请继续核对姓名、日期、职责和数字。' : '辅助核验发现待检查内容，请修正后重新核验。' + (Array.isArray(data.suggestions) ? data.suggestions.join('；') : ''));
    });
    const exportPdf = () => run('正在生成 PDF…', async () => {
        const { data } = await api.get<Blob>('/api/jobs/' + job.id + '/export/pdf', { responseType: 'blob', timeout: 90000 });
        if (!data.type.includes('application/pdf')) {
            let text = 'PDF 服务暂不可用，编辑内容与版本仍已保留。';
            try {
                const json = JSON.parse(await data.text());
                text = json.message || json.detail || text;
            }
            catch { /* Non-PDF output must never be downloaded as PDF. */ }
            throw new Error(text);
        }
        downloadBlob(data, job.company_name + '_' + job.job_title + '.pdf');
        setMessage('PDF 已生成，请检查下载文件中的排版。');
    });
    return <div className="stack"><div className="section-head"><div><h2>岗位简历</h2><p>以你的经历为依据，保留每次核对后的版本。</p></div><button className="btn" onClick={generate} disabled={Boolean(busy) || !enabled}><Sparkles size={16}/>{content ? '重新生成' : '生成岗位简历'}</button></div>{!enabled && <Notice>请先确认个人经历，并完成当前岗位的有效分析。资料变化后需要重新分析。</Notice>}{error && <ErrorBox message={error}/>}{message && <Notice><span role="status">{message}</span></Notice>}{busy && <Loading text={busy}/>}
    {!content ? <Empty title="把合适的经历，放到合适的位置" description="生成岗位简历后，你可以编辑表达、对照原始经历，并在核对事实后保存与导出。"/> : <>
      <div className="actions"><button className="btn small" onClick={() => setPreview(!preview)}>{preview ? '返回编辑' : '阅读预览'}</button><button className="btn small" onClick={() => setShowCompare(!showCompare)}>{showCompare ? '收起对照' : '对照生成前内容'}</button><span className="small-text" role="status">{dirty ? '有未保存修改' : '当前内容已保存到服务器'}</span></div>
      <div className={showCompare ? 'two-col' : ''}><section className="panel">{preview ? <div className="document-preview">{content}</div> : <label className="field"><span className="field-label">编辑简历（支持 Markdown，导出时排版）</span><textarea className="textarea resume-editor" value={content} disabled={Boolean(busy)} onChange={e => edit(e.target.value)}/></label>}</section>{showCompare && <section className="panel"><h3 style={{ marginBottom: 15 }}>生成前 / 打开时的内容</h3><p className="jd-text">{baseline || vault?.raw_content || '暂无原始内容'}</p><button className="btn small" style={{ marginTop: 18 }} disabled={Boolean(busy)} onClick={() => edit(baseline || vault?.raw_content || '')}>使用这份内容替换编辑区</button></section>}</div>
      {proposal && <RevisionReview key={proposal} before={baseline} after={proposal} onApply={edit}/>}
      <section className="panel stack"><Notice>请核对每项任职、职责范围、时间和量化成果。系统核验只能辅助发现问题，无法保证内容完全真实。</Notice><label className="check-row"><input type="checkbox" checked={reviewed} disabled={!verified || Boolean(busy)} onChange={e => setReviewed(e.target.checked)}/><span>我已对照真实经历核对当前内容，确认没有新增未经证实的事实。（先执行辅助核验）</span></label><div className="actions"><button className="btn" disabled={Boolean(busy) || !content.trim()} onClick={verify}><ShieldCheck size={16}/>辅助核验</button><button className="btn primary" disabled={Boolean(busy) || !content.trim()} onClick={save}><Save size={16}/>{reviewed && verified ? '保存确认版本' : '保存草稿版本'}</button><button className="btn" disabled={Boolean(busy) || dirty || !reviewed || !verified || !enabled || confirmedContent !== content} onClick={exportPdf}><Download size={16}/>导出 PDF</button></div></section>
      <section className="panel"><div className="section-head"><h2>已保存的版本</h2><FileText size={18}/></div>{job.tailored_resume_versions?.length ? <div className="stack">{[...job.tailored_resume_versions].reverse().map((v, i) => <div key={v.version + '-' + i} className="section-head"><div><strong>版本 {v.version}</strong><p>{dateLabel(v.created_at)} · {v.note || '简历草稿'}</p></div><button className="btn small" disabled={Boolean(busy)} onClick={() => { if (dirty && !window.confirm('替换未保存的修改？'))
            return; edit(v.content); }}>载入编辑区</button></div>)}</div> : <p className="muted">尚无手动保存的历史版本。</p>}</section>
    </>}
  </div>;
}
