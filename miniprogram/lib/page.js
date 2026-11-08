const core=require('./core');
function safeTarget(value){
  if(typeof value!=='string')return '/pages/home/index';
  try{value=decodeURIComponent(value)}catch(_){return '/pages/home/index'}
  if(value==='/pages/vault/index?upload=1')return value;
  return /^\/pages\/(home|vault|jobs|detail|resume|settings)\/index(?:\?id=[A-Za-z0-9%._~-]+)?$/.test(value)?value:'/pages/home/index';
}
function loginURL(page){return '/pages/login/index?next='+encodeURIComponent('/pages/'+page.pageKind+'/index'+(page.id?'?id='+encodeURIComponent(page.id):page.autoUpload?'?upload=1':''))}


module.exports={
  
markClean(){this.edited=false;if(wx.disableAlertBeforeUnload)wx.disableAlertBeforeUnload()},
markDirty(){
    this.edited=true;
    if(wx.enableAlertBeforeUnload)wx.enableAlertBeforeUnload({
      message:"编辑尚未保存，确定离开？"
    })
  },

reset(){
    this.stop();
    this.structured=null;
    this.source={};
    this.edited=false;
    this.setData({
      modelKey:'',modelSettings:null,showModelHelp:false,showRecords:false,summary:null,analysis:null,groups:[],showPrivacy:false,editing:false,showMore:false,showHistory:false,sourceRaw:'',sourceStale:false,result:'',ready:false,showForm:false,showRaw:false,authenticated:false,loaded:false,hasVault:false,confirmed:false,jobCount:0,pending:false,busy:false,error:'',message:'',username:'',email:'',company_name:'',job_title:'',jd_text:'',query:'',fallback:'',vault:null,fields:[],jobs:[],filtered:[],job:null,content:'',versions:[],result:'',password:'',...core.dirty()
    })
  },

onLoad(o){
    this.id=o.id;
    this.autoUpload=o.upload==='1';
    this.returnTo=safeTarget(o.next);
    this.kind=this.pageKind
  },

onShow(){
    this.visible=true;
    this.setData({authenticated:!!(getApp().session&&getApp().session.user)});
    if(getApp().session&&!getApp().session.user){
      getApp().clear();
      wx.redirectTo({
        url:loginURL(this)
      });
      return
    }if(this.pageKind!=='login'&&!getApp().session){
      wx.redirectTo({
        url:loginURL(this)
      });
      return
    }if(this.reload)return this.reload()
  },

onHide(){
    this.visible=false;
    this.stop()
  },

onUnload(){
    this.visible=false;
    this.stop()
  },

stop(){
    this.pollRevision=(this.pollRevision||0)+1;
    clearTimeout(this.timer)
  },

async run(fn){
    if(this.data.busy)return;
    const g=getApp().generation;
    this.setData({
      busy:true,error:'',message:''
    });
    try{
      await fn(g)
    }catch(e){
      if(g===getApp().generation)this.setData({
        error:e.message
      })
    }finally{
      if(g===getApp().generation)this.setData({
        busy:false
      })
    }
  },

go(e){
    const target=safeTarget('/pages/'+e.currentTarget.dataset.page+'/index'+(e.currentTarget.dataset.id?'?id='+encodeURIComponent(e.currentTarget.dataset.id):e.currentTarget.dataset.upload?'?upload=1':''));
    const session=getApp().session;
    if(session&&session.user){if(['/pages/home/index','/pages/jobs/index','/pages/settings/index'].includes(target))wx.switchTab({url:target});else wx.navigateTo({url:target})}else wx.navigateTo({url:'/pages/login/index?next='+encodeURIComponent(target)})
  }
};
