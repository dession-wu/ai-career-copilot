const api=require('../../lib/api');

const core=require('../../lib/core');

const base=require('../../lib/page');

const statuses=['preparing','applied','interviewing','offered','rejected'];

const labels=['准备中','已投递','面试中','已获 Offer','未通过'];


Page({
  
...base,
pageKind:'jobs',
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
    if(this.edited)return;
    return this.run(async()=>{
      this.setData({
        jobs:(await api.call('/api/jobs')).map(j=>({...j,statusLabel:labels[statuses.indexOf(j.status)]||'准备中'}))
      });
      const v=await api.call('/api/vault').catch(e=>{if(e.status===404)return null;throw e});
      this.setData({ready:!!v?.structured_data?._confirmed,showForm:this.data.jobs.length===0,jobs:this.data.jobs.map(j=>{const current=!!j.match_analysis&&j.match_analysis.source_vault_version===v?.version&&j.match_analysis.source_jd_text===j.jd_text;return {...j,analysisLabel:current&&typeof j.match_score==='number'?'匹配参考 '+j.match_score+' / 100':j.match_analysis?'需重新分析':'未分析',resumeLabel:j.tailored_resume_md?'已有岗位简历':'尚未生成简历'}})});
      this.filter()
    })
  },
input(e){
    if(this.data.busy)return;
    if(e.currentTarget.dataset.key!=='query')this.markDirty();
    const k=e.currentTarget.dataset.key;
    this.setData({
      [k]:e.detail.value,...(k==='content'?core.dirty():{
        
      })
    });
    if(k==='query')this.filter()
  },

filter(){
    const q=this.data.query.toLowerCase();
    this.setData({
      filtered:this.data.jobs.filter(j=>(j.company_name+j.job_title).toLowerCase().includes(q))
    })
  },

toggleForm(){if(this.data.busy)return;if(this.data.showForm&&this.edited){wx.showModal({title:'放弃未保存的岗位？',content:'当前填写的内容将被清除。',success:r=>{if(r.confirm){this.markClean();this.setData({showForm:false,company_name:'',job_title:'',jd_text:''})}}});return}this.setData({showForm:!this.data.showForm})},
saveJob(){
    if(!this.data.ready){this.setData({error:'请先上传并确认简历'});return}
    this.run(async()=>{
      const d=this.data;
      const j=await api.call('/api/jobs'+(this.id?'/'+this.id:''),this.id?'PUT':'POST',{
        company_name:d.company_name,job_title:d.job_title.trim(),jd_text:d.jd_text.trim()
      });
      this.markClean();
      this.setData({company_name:'',job_title:'',jd_text:'',showForm:false});
      wx.navigateTo({
        url:'/pages/detail/index?id='+encodeURIComponent(j.id)
      })
    })
  }

});

