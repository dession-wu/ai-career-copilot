"use client";
import { useEffect, useState } from 'react';
export default function PersonalModelSettings() {
  const [provider,setProvider]=useState('bailian');
  const [quota,setQuota]=useState<any>(null);
  const [key,setKey]=useState('');
  const [configured,setConfigured]=useState(false);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  async function request(method='GET') {
    const response=await fetch((process.env.NEXT_PUBLIC_API_URL || '')+'/api/model-settings',{method,headers:{'Content-Type':'application/json',Authorization:'Bearer '+localStorage.getItem('token')},...(method==='PUT'?{body:JSON.stringify({provider,key})}:{})});
    const data=await response.json();
    if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'设置未保存，请重新登录后重试。');
    return data;
  }
  useEffect(()=>{request().then(data=>{setConfigured(data.configured);setProvider(data.provider);setQuota(data);}).catch(()=>setMessage('请登录后配置模型。'));},[]);
  async function save(method:string){
    setBusy(true);setMessage('');
    try{const data=await request(method);setConfigured(data.configured);setKey('');setMessage(method==='DELETE'?'已删除个人 Key。':'个人模型设置已保存。');}
    catch(error){setMessage(error instanceof Error?error.message:'操作失败，请重试。');}
    finally{setBusy(false);}
  }
  return <section className="panel stack" aria-labelledby="personal-model-title">
    <h2 id="personal-model-title" className="text-xl font-semibold">我的 AI 模型</h2>
    <p className="text-sm text-muted-foreground mt-2">{configured?'已配置个人 Key。':'尚未配置个人 Key。'} 个人 Key 优先；未配置时可累计免费使用 3 次，所有 AI 功能共用。</p>
    <p>默认模型：qwen3.7-flash（非思考）。免费剩余 {quota?.free_remaining ?? '—'} / 3，处理中 {quota?.free_reserved ?? 0}。删除个人 Key 不重置免费次数。</p>
    <p>在阿里云百炼控制台开通模型服务与按量付费，在北京地域创建 API Key，并确认余额和模型权限。将 Key 填入下方密码框。401 请检查 Key/地域，403 检查模型权限，429 稍后重试或检查限额。个人 Key 失败不会转用平台额度。</p>
    <a href="https://bailian.console.aliyun.com/" target="_blank" rel="noreferrer">打开百炼控制台</a>
    <form onSubmit={e=>{e.preventDefault();void save('PUT');}} className="mt-4 space-y-4">
      <label className="block text-sm">服务商<select value={provider} onChange={e=>setProvider(e.target.value)} className="block w-full rounded border bg-background p-2 mt-2"><option value="bailian">百炼（北京）qwen3.7-flash</option><option value="deepseek">DeepSeek</option><option value="openai">OpenAI</option></select></label>
      <label className="block text-sm">API Key<input type="password" autoComplete="off" required maxLength={512} value={key} onChange={e=>setKey(e.target.value)} className="block w-full rounded border bg-background p-2 mt-2" placeholder="输入新 Key，不显示已保存的内容"/></label>
      <div className="flex gap-4"><button disabled={busy} className="btn primary">{busy?'保存中…':'保存个人设置'}</button><button type="button" disabled={busy||!configured} onClick={()=>void save('DELETE')} className="btn">删除 Key</button></div>
    </form><p role="status" className="text-sm mt-3">{message}</p>
  </section>;
}
