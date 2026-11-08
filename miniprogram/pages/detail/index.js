const api=require('../../lib/api');

const core=require('../../lib/core');
const view=require('../../lib/presentation');

const base=require('../../lib/page');

const statuses=['preparing','applied','interviewing','offered','rejected'];

const labels=['准备中','已投递','面试中','已获 Offer','未通过'];


function summary(r){return '匹配参考 '+(r.overall_score??r.match_score??'—')+' / 100\n\n找到的技能线索：'+(r.skill_match?.matched||[]).join('、')+'\n\n待补充证据：'+(r.skill_match?.missing||[]).join('、')+'\n\n下一步建议：\n'+(r.suggestions||[]).join('\n')}
Page({
  
...base,
pageKind:'detail',
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
      const job=await api.call('/api/jobs/'+this.id);
      const v=await api.call('/api/vault').catch(e=>{if(e.status===404)return null;throw e});
      const current=!!job.match_analysis&&job.match_analysis.source_vault_version===v?.version&&job.match_analysis.source_jd_text===job.jd_text;
      this.setData({
        analysis:current?view.analysis({...job.match_analysis,match_score:job.match_score}):null,result:current?summary({...job.match_analysis,match_score:job.match_score}):'',ready:!!v?.structured_data?._confirmed,hasAnalysis:!!job.match_analysis&&job.match_analysis.source_vault_version===v?.version&&job.match_analysis.source_jd_text===job.jd_text,job,company_name:job.company_name,job_title:job.job_title,jd_text:job.jd_text,statusIndex:statuses.indexOf(job.status)
      })
    })
  },
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

editJob(){if(!this.data.busy)this.setData({editing:true})},
cancelEdit(){if(this.data.busy)return;const restore=()=>{this.markClean();this.setData({editing:false,company_name:this.data.job.company_name,job_title:this.data.job.job_title,jd_text:this.data.job.jd_text,error:''})};if(this.edited){wx.showModal({title:'放弃本次修改？',content:'岗位将保留上次保存的内容。',success:r=>{if(r.confirm)restore()}})}else restore()},
showDescription(){this.setData({showDescription:!this.data.showDescription})},
go(e){if(this.edited){this.setData({error:'请先保存岗位修改'});return}base.go.call(this,e)},
saveJob(){
    this.run(async()=>{
      const d=this.data;
      const j=await api.call('/api/jobs'+(this.id?'/'+this.id:''),this.id?'PUT':'POST',{
        company_name:d.company_name,job_title:d.job_title,jd_text:d.jd_text
      });
      this.markClean();
      this.setData({job:j,editing:false,result:'',hasAnalysis:false,analysis:null,message:'岗位已保存'})
    })
  },

status(e){
    this.run(async()=>{
      const i=Number(e.detail.value);
      const j=await api.call('/api/jobs/'+this.id,'PUT',{
        status:statuses[i]
      });
      this.setData({
        job:j,statusIndex:i
      })
    })
  },

remove(){
    wx.showModal({
      title:'删除此岗位？',content:'岗位及关联简历将被删除。',success:r=>{
        if(r.confirm)this.run(async()=>{
          await api.call('/api/jobs/'+this.id,'DELETE');
          this.markClean();
      wx.switchTab({
            url:'/pages/jobs/index'
          })
        })
      }
    })
  },

analyze(){
    if(this.edited){this.setData({error:'请先保存岗位修改'});return}
    if(!this.data.ready){this.setData({error:'请先确认经历'});return}
    this.run(async()=>{
      const r=await api.call('/api/jobs/'+this.id+'/analyze','POST');
      this.setData({
        analysis:view.analysis(r),hasAnalysis:true,result:'匹配参考 '+r.overall_score+' / 100\n\n找到的技能线索：'+((r.skill_match||{
          
        }).matched||[]).join('、')+'\n\n待补充证据：'+((r.skill_match||{
          
        }).missing||[]).join('、')+'\n\n下一步建议：\n'+(r.suggestions||[]).join('\n')
      })
    })
  }

});

