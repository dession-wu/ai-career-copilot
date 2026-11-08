'use client';
import { ArrowRight, FileText, ListChecks, MessagesSquare, Check } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { PublicHeader } from '@/components/career/PublicHeader';

export default function LandingPage() {
  return <div className="public-shell resume-public"><PublicHeader /><main>
    <section className="resume-hero"><p className="resume-kicker"><FileText size={16}/> 从真实经历，到有针对性的申请</p><h1><span>你的经历，</span><span>值得被清楚看见。</span></h1><p className="resume-lead">对照目标岗位，写出有依据的简历。</p><div className="actions"><Link className="btn primary" href="/register">开始整理我的简历 <ArrowRight size={17}/></Link><a className="text-link" href="#example">看看如何优化 ↓</a></div><p className="resume-caption">先准备一份简历，再带上一个感兴趣的岗位。</p></section>
    <section className="resume-example" id="example" aria-label="简历优化示例"><header><div><FileText size={17}/><strong>一次有依据的简历修改</strong></div><span>示例内容</span></header><div className="resume-compare">
      <article><p className="resume-step">01 <span>找到经历依据</span></p><h2>你确实做过什么？</h2><p className="resume-original">整理访谈，参与注册流程优化。</p><small>以已有简历和补充经历为事实来源。</small></article>
      <article><p className="resume-step">02 <span>理解岗位要求</span></p><h2>这个岗位看重什么？</h2><p className="resume-requirement">用户研究<br/>问题分析<br/>产品体验改进</p><small>对照 JD 寻找相关线索，识别证据缺口。</small></article>
      <article className="resume-result"><p className="resume-step">03 <span>调整简历表达</span></p><h2>让相关能力更清楚。</h2><p>归纳注册问题，参与优化方案设计。</p><div className="resume-verified"><Check size={15}/><span>保留真实工作，不编造提升数据。</span></div></article>
    </div><footer>示例展示修改思路。生成内容需逐项核对，不代表录用概率。</footer></section>
    <section className="resume-workflow"><div className="resume-section-heading"><p className="resume-kicker">一条清晰的准备路径</p><h2>围绕一个岗位，把准备做扎实。</h2><p>从经历整理到面试准备，每一步都能回到你的真实材料。</p></div><div className="resume-flow-list">{[
      {icon:FileText,title:'把经历整理好',description:'上传简历，核对工作、项目与技能，建立可反复使用的经历库。'},
      {icon:ListChecks,title:'把简历写具体',description:'添加职位描述，查看匹配依据，编辑岗位简历、保存版本并导出。'},
      {icon:MessagesSquare,title:'把面试准备足',description:'围绕目标岗位梳理面试问题，用自己的经历组织回答。'}
    ].map(({icon:Icon,title,description},index)=><article key={title}><span className="resume-flow-index">0{index+1}</span><Icon size={22}/><h3>{title}</h3><p>{description}</p></article>)}</div></section>
    <section className="resume-ending"><div><h2>下一站，从准备好这份简历开始。</h2><p>建议由 AI 辅助，经历与选择由你掌握。</p></div><Link className="btn primary" href="/register">建立我的工作台 <ArrowRight size={16}/></Link></section>
  </main><footer className="public-footer"><span>简历指南 · 让每一次申请更有准备</span><Link href="/guide">使用指南与资料说明</Link></footer></div>;
}
