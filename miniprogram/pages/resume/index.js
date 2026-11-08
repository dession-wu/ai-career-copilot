const api=require('../../lib/api');

const core=require('../../lib/core');
const view=require('../../lib/presentation');

const base=require('../../lib/page');

const statuses=['preparing','applied','interviewing','offered','rejected'];

const labels=['准备中','已投递','面试中','已获 Offer','未通过'];


Page({
  
...base,
pageKind:'resume',
data:{
    
  "busy": false,
  "error": "",
  "message": "",
  "username": "",
  "password": "",
  "email": "",
  "register": false,
  "query": "",
  "jobs": [],
  "filtered": [],
  "company_name": "",
  "job_title": "",
  "jd_text": "",
  "job": null,
  "vault": null,
  "fields": [],
  "content": "",
  "versions": [],
  "verified": false,
  "reviewed": false,
  "saved": "",
  "result": "",
  "labels": [
    "准备中",
    "已投递",
    "面试中",
    "已获 Offer",
    "未通过"
  ],
  "statusIndex": 0

  },
async reload(){
    if(this.data.job)return this.run(async()=>{
      const v=await api.call('/api/vault'),j=await api.call('/api/jobs/'+this.id);
      const stale=!!this.data.content&&(this.source?.source_vault_version!==v.version||this.source?.source_jd_text!==j.jd_text);
      this.setData({job:j,sourceRaw:v.raw_content||'',ready:!!v.structured_data._confirmed,sourceStale:stale,...(stale?core.dirty():{})});
    });
    return this.run(async()=>{
      const job=await api.call('/api/jobs/'+this.id),versions=(await api.call('/api/jobs/'+this.id+'/tailor/versions')).versions;
      const vault=await api.call('/api/vault');
      const latest=versions.slice().reverse().find(v=>v.content===job.tailored_resume_md);
      this.source=latest?{
        source_vault_version:latest.source_vault_version,source_jd_text:latest.source_jd_text
      }:{
        
      };
      this.setData({
        job,versions,sourceRaw:vault.raw_content||'',ready:!!vault.structured_data._confirmed,sourceStale:!!job.tailored_resume_md&&(!latest||latest.source_vault_version!==vault.version||latest.source_jd_text!==job.jd_text),content:job.tailored_resume_md||'',...(latest?.reviewed&&vault.structured_data._confirmed&&latest.source_vault_version===vault.version&&latest.source_jd_text===job.jd_text?{verified:true,reviewed:true,saved:latest.content}:{})
      })
    })
  },
toggleSource(){this.setData({showSource:!this.data.showSource})},
toggleHistory(){this.setData({showHistory:!this.data.showHistory})},
input(e){
    if(this.data.busy)return;
    this.markDirty();
    const k=e.currentTarget.dataset.key;
    this.setData({
      [k]:e.detail.value,...(k==='content'?core.dirty():{
        
      })
    });
    if(k==='query')this.filter()
  },

async generate(){
    if(this.data.busy)return;
    if(this.data.content){const answer=await new Promise(resolve=>wx.showModal({title:"替换当前简历？",content:"重新生成会替换当前编辑内容，请先保存需要的版本。",success:resolve}));if(!answer.confirm)return}
    this.run(async()=>{
      const v=await api.call('/api/vault'),j=await api.call('/api/jobs/'+this.id);
      if(!v.structured_data._confirmed)throw Error('请先确认经历');
      const source={
        source_vault_version:v.version,source_jd_text:j.jd_text
      };
      const r=await api.call('/api/jobs/'+this.id+'/tailor','POST',{
        
      });
      this.source=source;this.markDirty();
      this.setData({
        content:r.content,sourceRaw:v.raw_content||'',sourceStale:false,ready:true,...core.dirty(),result:r.mode==='fallback'?'基础整理模式，请仔细核对':'内容已生成，请核对事实'
      })
    })
  },

verify(){
    if(this.data.sourceStale){this.setData({error:'资料已变化，请先更新来源并重新核对'});return}
    this.run(async()=>{
      const content=this.data.content,r=await api.call('/api/jobs/'+this.id+'/verify','POST',{
        resume_content:content
      });
      if(content===this.data.content)this.setData({
        findings:((r.details||{}).suspicious_terms||[]).map(x=>typeof x==='string'?x:(x.term||x.claim||x.description||'待核对事实')+'：'+(x.reason||'请对照原文')),
        verified:true,reviewed:false,result:'辅助核验完成：发现 '+(r.suspicious_count||0)+' 项待核对线索。\n'+(r.suggestions||[]).join('\n')+'\n'+((r.details||{
          
        }).suspicious_terms||[]).map(x=>(x.term||x.claim||x.description||'待核对事实')+'：'+(x.reason||'请对照原文')).join('\n')
      })
    })
  },

reconfirm(){
    wx.showModal({
      title:'以当前经历和岗位重新核对？',content:'请先对照当前经历与岗位重新审核此简历。重新关联来源会解除已有核验与确认。',success:r=>{
        if(r.confirm)this.run(async()=>{
          const v=await api.call('/api/vault'),j=await api.call('/api/jobs/'+this.id);
          this.source={
            source_vault_version:v.version,source_jd_text:j.jd_text
          };
          this.setData({
            ...core.dirty(),sourceStale:false,sourceRaw:v.raw_content||'',message:'已更新来源，请重新核对'
          })
        })
      }
    })
  },review(e){
    if(this.data.busy)return;
    this.setData({
      reviewed:this.data.verified&&e.detail.value.length>0
    })
  },

saveResume(){
    this.run(async()=>{
      const content=this.data.content,reviewed=this.data.reviewed&&this.data.verified;
      await api.call('/api/jobs/'+this.id+'/tailor/versions','POST',{
        content,note:reviewed?'用户已核对事实':'编辑草稿',reviewed,...this.source
      });
      this.setData({
        saved:reviewed?content:'',versions:(await api.call('/api/jobs/'+this.id+'/tailor/versions')).versions,message:'版本已保存'
      });this.markClean()
    })
  },

loadVersion(e){
    if(this.data.busy)return;
    const v=this.data.versions[e.currentTarget.dataset.index];
    wx.showModal({
      title:'载入历史版本？',content:'将替换当前未保存的编辑内容。',success:r=>{
        if(r.confirm){
          this.markDirty();
          this.source={
            source_vault_version:v.source_vault_version,source_jd_text:v.source_jd_text
          };
          this.setData({
            content:v.content,sourceStale:true,...core.dirty()
          })
        }
      }
    })
  },

exportFile(){
    this.run(async g=>{
      if(!this.data.reviewed||!this.data.verified||this.data.saved!==this.data.content)throw Error('请先核验、人工确认并保存当前版本');
      const c=require('../../config'),a=getApp();
      const r=await new Promise((resolve,reject)=>wx.downloadFile({
        url:c.baseURL+'/api/jobs/'+this.id+'/export/pdf',header:{
          Authorization:'Bearer '+a.session.access_token
        },success:resolve,fail:()=>reject(Error('下载失败'))
      }));
      if(g!==a.generation)return;
      if(r.statusCode===401){
        a.clear();
        wx.reLaunch({
          url:'/pages/login/index'
        });
        throw Error('请重新登录')
      }const fs=wx.getFileSystemManager(),bytes=fs.readFileSync(r.tempFilePath);
      const u=new Uint8Array(bytes);
      if(r.statusCode===200&&String.fromCharCode(...u.slice(0,5))==='%PDF-'){
        await new Promise((resolve,reject)=>wx.openDocument({
          filePath:r.tempFilePath,fileType:'pdf',showMenu:true,success:resolve,fail:reject
        }));
        this.setData({exportDone:true,message:'PDF 已打开，可在文件菜单中保存或分享'});
        return
      }let d;
      try{
        d=JSON.parse(fs.readFileSync(r.tempFilePath,'utf8'))
      }catch(e){
        throw Error('服务未返回有效文件')
      }if(r.statusCode===200&&d.fallback_format==='markdown'){
        this.setData({
          fallback:d.content,exportDone:true,message:''
        });
        return
      }throw Error(typeof d.detail==='string'?d.detail:'导出未完成')
    })
  },

closeExport(){this.setData({exportDone:false})},
copy(){
    wx.setClipboardData({
      data:view.plainText(this.data.fallback)
    })
  }

});

