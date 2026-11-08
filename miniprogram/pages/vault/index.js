const api=require('../../lib/api');

const core=require('../../lib/core');
const view=require('../../lib/presentation');

const base=require('../../lib/page');

const statuses=['preparing','applied','interviewing','offered','rejected'];

const labels=['准备中','已投递','面试中','已获 Offer','未通过'];


Page({
  
...base,
pageKind:'vault',
toggleRecords(){this.setData({showRecords:!this.data.showRecords})},
data:{
    
  "busy": false,
  "pending": false,
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
onShow(){
    const session=getApp().session;
    this.setData({pending:!!(session&&session.user&&wx.getStorageSync(this.pendingKey()))});
    const loading=base.onShow.call(this);
      Promise.resolve(loading).then(()=>{if(this.autoUpload&&this.visible&&getApp().session?.user){this.autoUpload=false;if(!this.data.vault&&!this.data.error&&!this.data.busy&&!this.data.pending)this.choose()}});
  },
async reload(){
    if(this.data.vault){
      this.poll();
      return
    }return this.run(async()=>{
      try{
        this.showVault(await api.call('/api/vault'))
      }catch(e){
        if(e.status!==404)throw e
      }this.poll()
    })
  },
editVault(){if(!this.data.busy&&!this.data.pending)this.setData({editing:true})},
toggleMore(){this.setData({showMore:!this.data.showMore})},
toggleRaw(){this.setData({showRaw:!this.data.showRaw})},
showVault(v){
    this.structured=v.structured_data;
    this.setData({showRaw:false,editing:!v.structured_data._confirmed,showMore:false});
    this.setData({
      vault:v,summary:view.archive(v),groups:view.groups(core.fields(this.structured)),fields:core.fields(this.structured)
    })
  },

async choose(){
    if(this.data.busy||this.data.pending)return;
    if(this.data.vault){
      const r=await new Promise(resolve=>wx.showModal({
        title:'替换经历资料？',content:'上传会覆盖当前经历，请确认已保留需要的内容。',success:resolve
      }));
      if(!r.confirm||this.data.pending||this.data.busy)return
    }wx.chooseMessageFile({
      count:1,type:'file',extension:['pdf','docx'],success:r=>this.run(async()=>{
        const f=r.tempFiles[0];
        if(!core.validFile(f))throw Error('请选择 10MB 以内的 PDF 或 DOCX');
        const v=await api.upload(f);
        if(v.pending){
          wx.setStorageSync(this.pendingKey(),{
            id:v.upload_id,time:Date.now()
          });
          this.setData({
            pending:true,message:'正在解析，请稍候'
          });
          this.poll()
        }else this.showVault(v)
      })
    })
  },

pendingKey(){
    return 'pending:'+getApp().session.user.id
  },

async poll(){
    this.stop();
    const revision=this.pollRevision||0;
    if(!this.visible||!getApp().session)return;
    const key=this.pendingKey(),p=wx.getStorageSync(key),g=getApp().generation;
    if(!p){this.setData({pending:false});return;}
    this.setData({pending:true});
    if(Date.now()-p.time>15*60*1000){
      wx.removeStorageSync(key);
      this.setData({
        pending:false,error:'解析等待超时，请检查经历或重新上传'
      });
      return
    }try{
      const r=await api.call('/api/vault/upload-status/'+p.id);
      if(!this.visible||g!==getApp().generation||revision!==(this.pollRevision||0))return;
      if(r.status==='completed'){
        wx.removeStorageSync(key);
        this.setData({pending:false});
        this.showVault(r.vault);
        this.setData({
          message:'解析完成，请逐项核对'
        });
        return
      }if(r.status==='error'){
        wx.removeStorageSync(key);
        this.setData({pending:false});
        throw Error(r.message)
      }this.timer=setTimeout(()=>this.poll(),2500)
    }catch(e){
      if(g!==getApp().generation||revision!==(this.pollRevision||0)||!this.visible)return;
      if(e.status===404){wx.removeStorageSync(key);this.setData({pending:false})}
      this.setData({
        error:e.message
      })
    }
  },

addRecord(e){
    if(this.data.busy||this.data.pending)return;
    this.markDirty();
    const k=e.currentTarget.dataset.kind;
    const defaults={
      experiences:{
        company:'',title:'',start_date:'',end_date:'',projects:[{
          name:'',description:'',technologies:[]
        }]
      },skills:{
        name:'',level:'familiar',category:''
      },education:{
        school:'',degree:'',field:'',start_date:'',end_date:''
      }
    };
    if(!Array.isArray(this.structured[k]))this.structured[k]=[];
    this.structured[k].push(defaults[k]);
    this.structured._confirmed=false;
    this.setData({
      groups:view.groups(core.fields(this.structured)),fields:core.fields(this.structured), vault:{...this.data.vault,structured_data:this.structured}
    })
  },

field(e){
    if(this.data.busy||this.data.pending)return;
    this.structured=core.patch(this.structured,e.currentTarget.dataset.path,e.detail.value);
    this.structured._confirmed=false;
    this.setData({
      groups:view.groups(core.fields(this.structured)),fields:core.fields(this.structured),vault:{...this.data.vault,structured_data:this.structured}
    });
    this.markDirty()
  },

removeVault(){
    if(this.data.busy||this.data.pending)return;
    wx.showModal({
      title:'删除全部经历资料？',content:'删除后需重新导入，已有简历的来源确认也会失效。',success:r=>{
        if(r.confirm&&!this.data.pending)this.run(async()=>{
          this.stop();
          await api.call('/api/vault','DELETE');
          wx.removeStorageSync(this.pendingKey());
          this.structured=null;this.markClean();
          this.setData({
            vault:null,fields:[]
          })
        })
      }
    })
  },removeProject(e){
 if(this.data.busy||this.data.pending)return;
 const i=Number(e.currentTarget.dataset.parent),j=Number(e.currentTarget.dataset.index);
 this.structured.experiences[i].projects.splice(j,1);
 this.structured._confirmed=false;
 this.setData({groups:view.groups(core.fields(this.structured)),fields:core.fields(this.structured),vault:{...this.data.vault,structured_data:this.structured}});
 this.markDirty();
},
removeEntry(e){
    if(this.data.busy||this.data.pending)return;
    const key=e.currentTarget.dataset.kind,index=Number(e.currentTarget.dataset.index);
    this.structured[key].splice(index,1);
    this.structured._confirmed=false;
    this.setData({
      groups:view.groups(core.fields(this.structured)),fields:core.fields(this.structured),vault:{
        ...this.data.vault,structured_data:this.structured
      }
    });
    this.markDirty()
  },addProject(e){
    if(this.data.busy||this.data.pending)return;
    const x=this.structured.experiences[Number(e.currentTarget.dataset.index)];
    if(!Array.isArray(x.projects))x.projects=[];
    x.projects.push({
      name:'',description:'',technologies:[]
    });
    this.structured._confirmed=false;
    this.setData({
      groups:view.groups(core.fields(this.structured)),fields:core.fields(this.structured), vault:{...this.data.vault,structured_data:this.structured}
    });
    this.markDirty()
  },saveVault(){
    if(this.data.busy||this.data.pending)return;
    this.run(async()=>{
      const submitted=JSON.parse(JSON.stringify(this.structured));
      submitted._confirmed=true;
      this.showVault(await api.call('/api/vault','PUT',{
        structured_data:submitted
      }));
      this.markClean();
      this.setData({
        message:'经历已核对保存'
      })
    })
  }

});

