const api=require('../../lib/api');
const base=require('../../lib/page');
const view=require('../../lib/presentation');
Page({...base,pageKind:'home',data:{authenticated:false,busy:false,error:'',message:'',hasVault:false,confirmed:false,jobCount:0,loaded:false},
reload(){return this.run(async()=>{
 const [vault,jobs]=await Promise.all([api.call('/api/vault').catch(e=>{if(e.status===404)return null;throw e}),api.call('/api/jobs')]);
 this.setData({summary:view.archive(vault),pending:!!wx.getStorageSync('pending:'+getApp().session.user.id),hasVault:!!vault,confirmed:!!(vault&&vault.structured_data._confirmed),jobCount:jobs.length,loaded:true});
})}});
