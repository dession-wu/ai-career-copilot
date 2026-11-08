'use client';
import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { FileUp, Check, Plus, Save, Trash2, ArrowRight } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { api } from '@/lib/api';
import { Vault, getVault, errorMessage, confirmed, dateLabel } from '@/lib/career';
import { PageIntro, Loading, ErrorBox, Notice } from '@/components/career/ui';
import { useLeaveGuard } from '@/hooks/useLeaveGuard';
const labels: Record<string, string> = { personal_info: '基本信息', name: '姓名 / 名称', email: '邮箱', phone: '电话', linkedin: 'LinkedIn', website: '个人网站', education: '教育经历', school: '学校', degree: '学历', field: '专业', start_date: '开始时间', end_date: '结束时间', skills: '技能', level: '熟悉程度', category: '类别', experiences: '工作经历', company: '公司', title: '职位', projects: '项目经历', description: '描述', technologies: '技术 / 工具', star_description: 'STAR 经历描述', summary: '个人概述', achievements: '成果', responsibilities: '职责', certifications: '证书' };
function blank(value: unknown): unknown { if (Array.isArray(value))
    return []; if (value && typeof value === 'object')
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, blank(v)])); return ''; }
function FactEditor({ value, onChange, path = 'fact' }: {
    value: unknown;
    onChange: (v: unknown) => void;
    path?: string;
}) {
    if (Array.isArray(value))
        return <div className="stack">{value.map((v, i) => <div className="fact-item" key={i}><FactEditor value={v} path={path + '-' + i} onChange={next => onChange(value.map((x, n) => n === i ? next : x))}/><button type="button" className="text-link" style={{ fontSize: 12, marginTop: 10 }} onClick={() => onChange(value.filter((_, n) => n !== i))}>移除这一项</button></div>)}<div><button type="button" className="btn small" onClick={() => onChange([...value, value.length ? blank(value[0]) : path.endsWith('projects') ? { name: '', description: '', technologies: [] } : path.endsWith('experiences') ? { company: '', title: '', start_date: '', end_date: '', projects: [] } : path.endsWith('education') ? { school: '', degree: '', field: '', start_date: '', end_date: '' } : path.endsWith('skills') ? { name: '', level: '', category: '' } : ''])}><Plus size={13}/>添加一项</button></div></div>;
    if (value && typeof value === 'object')
        return <div className="form-grid">{Object.entries(value).filter(([k]) => !k.startsWith('_')).map(([k, v]) => <div key={k} className={v && typeof v === 'object' ? 'field full' : 'field'}><label htmlFor={path + '-' + k}>{labels[k] || k}</label><FactEditor path={path + '-' + k} value={v} onChange={next => onChange({ ...value, [k]: next })}/></div>)}</div>;
    return <textarea id={path} className="textarea" rows={typeof value === 'string' && value.length > 100 ? 4 : 1} value={value == null ? '' : String(value)} onChange={e => onChange(e.target.value)}/>;
}
export default function VaultPage() {
    const [vault, setVault] = useState<Vault | null>(null), [data, setData] = useState<Record<string, unknown>>({}), [dirty, setDirty] = useState(false), [checked, setChecked] = useState(false), [loading, setLoading] = useState(true), [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState(''), [task, setTask] = useState(''), [filename, setFilename] = useState(''), [loadFailed, setLoadFailed] = useState(false);
    const input = useRef<HTMLInputElement>(null);
    const [pollVersion, setPollVersion] = useState(0);
    useLeaveGuard(dirty);
    const accept = (v: Vault) => { setVault(v); setData(v.structured_data); setChecked(confirmed(v)); setDirty(false); };
    const load = async () => { setLoading(true); setError(''); setLoadFailed(false); try {
        const v = await getVault();
        if (v)
            accept(v);
        const pending = sessionStorage.getItem('career-upload-task');
        if (pending) {
            setTask(pending);
            setBusy(true);
            setPollVersion(v => v + 1);
        }
    }
    catch (e) {
        setLoadFailed(true);
        setError(errorMessage(e));
    }
    finally {
        setLoading(false);
    } };
    useEffect(() => { void load(); }, []);
    useEffect(() => {
        if (!task)
            return;
        let active = true, attempt = 0, timer: ReturnType<typeof setTimeout>;
        const poll = async () => { try {
            const { data: r } = await api.get('/api/vault/upload-status/' + encodeURIComponent(task));
            if (!active)
                return;
            if (r.status === 'completed' && r.vault) {
                accept(r.vault);
                setMessage('解析完成。请检查并确认以下经历。');
                setBusy(false);
                setTask('');
                sessionStorage.removeItem('career-upload-task');
            }
            else if (r.status === 'error') {
                sessionStorage.removeItem('career-upload-task');
                setTask('');
                setMessage('');
                throw new Error(r.message || '解析失败，请重新上传。');
            }
            else if (++attempt >= 120) {
                setError('解析仍在进行，可稍后重新进入本页查看。请勿重复上传。');
                setBusy(false);
            }
            else {
                timer = setTimeout(poll, 2000);
            }
        }
        catch (e) {
            if (active) {
                const expired = axios.isAxiosError(e) && e.response?.status === 404;
                if (expired) {
                    sessionStorage.removeItem('career-upload-task');
                    setTask('');
                    setMessage('');
                }
                setError(expired ? '解析任务已失效。请先检查下方经历是否已更新，必要时重新上传。' : errorMessage(e));
                setBusy(false);
            }
        } };
        timer = setTimeout(poll, 1000);
        return () => { active = false; clearTimeout(timer); };
    }, [task, pollVersion]);
    const upload = async (file?: File) => {
        if (!file || busy || task || loadFailed)
            return;
        if (!/\.(pdf|docx)$/i.test(file.name)) {
            setError('请选择 PDF 或 DOCX 文件；旧版 DOC 请先另存为 DOCX。');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            setError('文件不能超过 10 MB。');
            return;
        }
        if (vault && !window.confirm('重新上传会替换服务器上的当前经历。现有岗位简历会保留，但需要重新检查分析依据。确定继续？'))
            return;
        setBusy(true);
        setError('');
        setMessage('正在上传并解析，请稍候…');
        setFilename(file.name);
        try {
            const form = new FormData();
            form.append('file', file);
            const r = await api.post('/api/vault/upload', form, { headers: { 'Content-Type': undefined }, timeout: 180000 });
            if (r.status === 202) {
                const id = r.data.detail?.upload_id || r.data.upload_id;
                if (!id)
                    throw new Error('服务未返回有效任务编号，请刷新后查看经历。');
                sessionStorage.setItem('career-upload-task', id);
                setTask(id);
            }
            else {
                accept(r.data);
                setMessage('解析完成。请检查并确认以下经历。');
                setBusy(false);
            }
        }
        catch (e) {
            setError(errorMessage(e));
            setBusy(false);
        }
        finally {
            if (input.current)
                input.current.value = '';
        }
    };
    const change = (key: string, value: unknown) => { setData(d => ({ ...d, [key]: value, _confirmed: false })); setDirty(true); setChecked(false); setMessage('有未保存修改'); };
    const save = async () => { setBusy(true); setError(''); try {
        const { data: v } = await api.put<Vault>('/api/vault', { structured_data: { ...data, _confirmed: checked } });
        accept(v);
        setMessage(checked ? '经历已确认并保存，可以开始岗位分析。' : '修改已保存，核对完成后请勾选确认。');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } };
    const remove = async () => { if (!window.confirm('删除当前经历资料？已有岗位记录会保留。此操作不能撤销。'))
        return; setBusy(true); setError(''); try {
        await api.delete('/api/vault');
        setVault(null);
        setData({});
        setDirty(false);
        setChecked(false);
        setMessage('当前经历已删除。');
        sessionStorage.removeItem('career-upload-task');
        setTask('');
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } };
    if (loading)
        return <Loading />;
    return <div className="stack"><PageIntro title="我的经历" description="这是岗位分析和简历建议共同使用的事实来源。先整理真实经历，再为不同机会做好准备。" action={vault ? <span className={'badge ' + (confirmed(vault) && !dirty ? 'green' : 'amber')}>{confirmed(vault) && !dirty ? '经历已确认' : '经历待核对'}</span> : undefined}/>
 {error && <ErrorBox message={error} retry={load}/>}
 <input ref={input} type="file" accept=".pdf,.docx" hidden onChange={e => void upload(e.target.files?.[0])}/>
 <section className="upload-area" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); void upload(e.dataTransfer.files[0]); }}><FileUp size={30}/><h2>{vault ? '更新你的简历资料' : '从一份已有简历开始'}</h2><p>支持 PDF、DOCX，最大 10 MB。点击选择文件，或拖到这里。</p><button className="btn primary" disabled={busy || Boolean(task) || loadFailed} onClick={() => input.current?.click()}><FileUp size={16}/>{busy ? '正在处理…' : vault ? '选择新简历' : '选择简历文件'}</button>{filename && <p className="small-text">{filename}</p>}</section>
 <p className="small-text">文件用于提取经历和生成求职建议。请先移除不必要的身份证号等信息；你可以删除当前经历资料。扫描件可能无法提取文字。</p>
 {message && <Notice><span role="status">{message}</span>{busy && <Loading text="处理中，可稍后返回本页查看。"/>}</Notice>}
 {vault && <><div className="two-col"><section className="panel"><div className="section-head"><div><h2>核对你的经历</h2><p>自动解析可能遗漏信息，请按实际情况修正。</p></div><span className="small-text">版本 {vault.version}</span></div><fieldset disabled={busy || Boolean(task)} style={{ border: 0, padding: 0, margin: 0 }}>{Object.entries(data).filter(([k]) => !k.startsWith('_') && !['raw_text_preview', 'extraction_metadata', 'metadata'].includes(k)).map(([key, value]) => <section className="fact-group" key={key}><h3>{labels[key] || key}</h3><FactEditor value={value} path={'vault-' + key} onChange={v => change(key, v)}/></section>)}<div className="actions" style={{ marginTop: 20 }}><button className="btn small" onClick={() => change('experiences', [...(Array.isArray(data.experiences) ? data.experiences : []), { company: '', title: '', start_date: '', end_date: '', projects: [{ name: '', description: '', technologies: [] }] }])}><Plus size={14}/>补充工作经历</button><button className="btn small" onClick={() => change('skills', [...(Array.isArray(data.skills) ? data.skills : []), { name: '', level: '', category: '' }])}><Plus size={14}/>补充技能</button><button className="btn small" onClick={() => change('education', [...(Array.isArray(data.education) ? data.education : []), { school: '', degree: '', field: '', start_date: '', end_date: '' }])}><Plus size={14}/>补充教育经历</button></div></fieldset><hr className="divider"/><label className="check-row"><input type="checkbox" checked={checked} disabled={busy || Boolean(task)} onChange={e => { setChecked(e.target.checked); setDirty(true); }}/><span>我已核对以上经历；分析与简历建议将以这些信息为依据。</span></label><div className="form-foot"><span className="small-text">{dirty ? '有未保存修改' : '服务器已保存 · ' + dateLabel(vault.updated_at)}</span><button className="btn primary" onClick={save} disabled={busy || Boolean(task)}><Save size={16}/>保存经历</button></div></section><aside className="stack"><section className="panel"><div className="section-head"><h2>对照原始简历</h2></div><p className="jd-text">{vault.raw_content || '暂无可用原文，请按实际经历核对左侧信息。'}</p></section><Notice>核对公司、时间、职责范围和量化成果。没有做过的事情不要补入经历。</Notice>{confirmed(vault) && !dirty && <Link className="btn primary" href="/jobs/new"><Check size={16}/>添加目标岗位<ArrowRight size={16}/></Link>}<button className="btn danger" disabled={busy || Boolean(task)} onClick={remove}><Trash2 size={15}/>删除当前经历资料</button></aside></div></>}
 </div>;
}
