'use client';
import { useState } from 'react';
import { MessageSquare, Save, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';
import { Question, errorMessage } from '@/lib/career';
import { Empty, ErrorBox, Loading, Notice } from './ui';
import { useLeaveGuard } from '@/hooks/useLeaveGuard';
function QuestionItem({ question, onSaved }: {
    question: Question;
    onSaved: (q: Question) => void;
}) {
    const [answer, setAnswer] = useState(question.suggested_answer_star || ''), [busy, setBusy] = useState(false), [error, setError] = useState('');
    const dirty = answer !== (question.suggested_answer_star || '');
    useLeaveGuard(dirty);
    const save = async () => { setBusy(true); setError(''); try {
        const { data } = await api.put<Question>('/api/interview/questions/' + question.id, { suggested_answer_star: answer });
        onSaved(data);
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } };
    return <article className="question"><span className="badge">{({ technical: '能力与技术', behavioral: '经历追问', situational: '情景问题' } as Record<string, string>)[question.question_type || ''] || '岗位问题'}</span><h3>{question.question_text}</h3>{question.intent_analysis && <p>{question.intent_analysis}</p>}<details><summary>准备我的回答</summary><p style={{ marginBottom: 12 }}>可以按背景、任务、行动、结果组织回答。以下初始内容可能由系统生成，请用真实事实核对和修改。</p><label className="field"><span className="field-label">回答草稿与准备笔记</span><textarea className="textarea" rows={7} value={answer} onChange={e => setAnswer(e.target.value)} disabled={busy}/></label>{error && <ErrorBox message={error}/>}<div className="form-foot"><span className="small-text">{dirty ? '有未保存修改' : '与服务器内容一致'}</span><button className="btn small" disabled={!dirty || busy} onClick={save}><Save size={14}/>保存回答</button></div></details></article>;
}
export function InterviewQuestions({ jobId, enabled }: {
    jobId: string;
    enabled: boolean;
}) {
    const [questions, setQuestions] = useState<Question[]>([]), [loaded, setLoaded] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
    const load = async (regenerate = false) => {
        if (regenerate && !window.confirm('重新生成会替换当前问题与已保存的回答。请先保留需要的内容。确定继续？'))
            return;
        setBusy(true);
        setError('');
        try {
            const base = '/api/interview/jobs/' + encodeURIComponent(jobId) + '/interview-prep';
            const { data } = regenerate ? await api.post<Question[]>(base + '/regenerate', null, { timeout: 180000 }) : await api.get<Question[]>(base, { timeout: 180000 });
            setQuestions(data);
            setLoaded(true);
        }
        catch (e) {
            setError(errorMessage(e));
        }
        finally {
            setBusy(false);
        }
    };
    return <div className="stack"><div className="section-head"><div><h2>为这个岗位准备面试</h2><p>围绕岗位要求与个人经历，逐题整理你的真实回答。</p></div><button className="btn" disabled={busy || !enabled} onClick={() => load(loaded)}>{loaded ? <RefreshCw size={16}/> : <MessageSquare size={16}/>}{loaded ? '重新生成问题' : '读取 / 生成面试题'}</button></div>{!enabled && <Notice>请先在“我的经历”中核对并保存经历，再准备岗位面试。</Notice>}{error && <ErrorBox message={error} retry={() => load()}/>}{busy ? <Loading text="正在整理岗位问题，请稍候…"/> : questions.length ? <><Notice>问题和回答要点仅用于准备，不代表面试官一定会提问。系统可能使用基础题目模板，请核对是否适用于这个岗位。</Notice>{questions.map(q => <QuestionItem key={q.id + q.suggested_answer_star} question={q} onSaved={next => setQuestions(old => old.map(item => item.id === next.id ? next : item))}/>)}</> : <Empty title={loaded ? '暂未生成可用问题' : '把经历，整理成能讲清楚的故事'} description="点击上方按钮读取已有问题；没有记录时，系统会尝试生成。你可以编辑并保存每题的回答。"/>}</div>;
}
