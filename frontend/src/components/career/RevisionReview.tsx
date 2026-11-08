'use client';
import { useMemo, useState } from 'react';
type Segment = {
    old: string[];
    next: string[];
    changed: boolean;
};
// A bounded line diff keeps long resumes responsive and never invents a correspondence.
function segments(before: string, after: string): Segment[] {
    const a = before.split('\n'), b = after.split('\n');
    if (a.length * b.length > 250000)
        return [{ old: a, next: b, changed: before !== after }];
    const dp = Array.from({ length: a.length + 1 }, () => new Uint16Array(b.length + 1));
    for (let i = a.length - 1; i >= 0; i--)
        for (let j = b.length - 1; j >= 0; j--)
            dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    const result: Segment[] = [];
    let i = 0, j = 0;
    const add = (old: string[], next: string[], changed: boolean) => { const last = result[result.length - 1]; if (last && last.changed === changed) {
        last.old.push(...old);
        last.next.push(...next);
    }
    else
        result.push({ old, next, changed }); };
    while (i < a.length || j < b.length) {
        if (i < a.length && j < b.length && a[i] === b[j]) {
            add([a[i++]], [b[j++]], false);
        }
        else if (j < b.length && (i === a.length || dp[i][j + 1] >= dp[i + 1][j]))
            add([], [b[j++]], true);
        else
            add([a[i++]], [], true);
    }
    return result;
}
export function RevisionReview({ before, after, onApply }: {
    before: string;
    after: string;
    onApply: (content: string) => void;
}) {
    const diff = useMemo(() => segments(before, after), [before, after]);
    const [choices, setChoices] = useState<Record<number, boolean>>({});
    const changed = diff.map((s, i) => ({ ...s, i })).filter(s => s.changed);
    return <section className="panel stack"><div><h2 style={{ fontSize: 17 }}>逐项核对表达变化</h2><p className="small-text">对比参考原文与生成结果。接受表达调整，不代表新增事实已经得到证实。</p></div>{changed.length ? changed.map((s, n) => <details key={s.i} className="revision-item"><summary>变化 {n + 1} · {choices[s.i] === undefined ? '待核对' : choices[s.i] ? '使用建议表达' : '保留参考原文'}</summary><div className="two-col" style={{ margin: '15px 0' }}><div><p className="small-text">参考原文</p><p className="fact-text">{s.old.join('\n') || '（原文中没有这部分）'}</p></div><div><p className="small-text">建议表达</p><p className="fact-text">{s.next.join('\n') || '（建议移除这部分）'}</p></div></div><div className="actions"><button type="button" className={'btn small ' + (choices[s.i] === true ? 'primary' : '')} onClick={() => setChoices(c => ({ ...c, [s.i]: true }))}>使用建议表达</button><button type="button" className={'btn small ' + (choices[s.i] === false ? 'primary' : '')} onClick={() => setChoices(c => ({ ...c, [s.i]: false }))}>保留参考原文</button></div></details>) : <p className="muted">当前参考内容与生成结果没有变化。</p>}<div><button type="button" className="btn" disabled={!changed.length || changed.some(s => choices[s.i] === undefined)} onClick={() => { if (window.confirm('将按以上选择替换编辑区当前内容，尚未保存的手动修改将被覆盖。确定继续？'))
        onApply(diff.flatMap((s, i) => s.changed && choices[i] === false ? s.old : s.next).join('\n')); }}>将核对结果写入编辑区</button></div></section>;
}
