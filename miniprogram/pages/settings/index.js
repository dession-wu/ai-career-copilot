const api=require('../../lib/api');

const core=require('../../lib/core');

const base=require('../../lib/page');

const statuses=['preparing','applied','interviewing','offered','rejected'];

const labels=['准备中','已投递','面试中','已获 Offer','未通过'];


Page({
  
...base,
pageKind:'settings',
async reload(){return this.run(async g=>{const modelSettings=await api.call('/api/model-settings');if(g===getApp().generation)this.setData({modelSettings})})},
modelKeyInput(e){this.setData({modelKey:e.detail.value})},
toggleModelHelp(){this.setData({showModelHelp:!this.data.showModelHelp})},
async saveModelKey(){if(!this.data.modelKey)return;return this.run(async g=>{await api.call('/api/model-settings','PUT',{provider:'bailian',key:this.data.modelKey});if(g!==getApp().generation)return;this.setData({modelKey:'',message:'个人百炼 Key 已保存'});const modelSettings=await api.call('/api/model-settings');if(g===getApp().generation)this.setData({modelSettings})})},
async deleteModelKey(){return this.run(async g=>{await api.call('/api/model-settings','DELETE');const modelSettings=await api.call('/api/model-settings');if(g===getApp().generation)this.setData({modelSettings,message:'个人 Key 已删除'})})},
data:{
    
  "busy": false,
  "modelKey": "",
  "modelSettings": null,
  "showModelHelp": false,
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
togglePrivacy(){this.setData({showPrivacy:!this.data.showPrivacy})},
logout(){
 wx.showModal({title:'退出登录？',content:'已保存的资料会保留，未保存的编辑将清除。',success:r=>{if(r.confirm){getApp().clear();wx.reLaunch({url:'/pages/login/index'})}}})
}
});
