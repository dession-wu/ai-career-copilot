const api=require('../../lib/api');

const core=require('../../lib/core');

const base=require('../../lib/page');

const statuses=['preparing','applied','interviewing','offered','rejected'];

const labels=['准备中','已投递','面试中','已获 Offer','未通过'];


Page({
  
...base,
pageKind:'login',
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
input(e){
    const k=e.currentTarget.dataset.key;
    this.setData({
      [k]:e.detail.value,...(k==='content'?core.dirty():{
        
      })
    });
    if(k==='query')this.filter()
  },

toggleAccount(){this.setData({showAccount:!this.data.showAccount,error:''})},

toggle(){
    this.setData({
      register:!this.data.register
    })
  },

login(){
    this.run(async()=>{
      const d=this.data;
      if(d.register)await api.call('/api/auth/register','POST',{
        username:d.username,email:d.email,password:d.password
      });
      const s=await api.call('/api/auth/login','POST',{
        username:d.username,password:d.password
      },true);
      const user=await api.call('/api/auth/me','GET',undefined,false,{token:s.access_token});
      getApp().login({...s,user});
      wx.reLaunch({
        url:this.returnTo||'/pages/home/index'
      })
    })
  },

wechat(){
    this.run(async()=>{
      const r=await new Promise((resolve,reject)=>wx.login({
        success:resolve,fail:reject
      }));
      const s=await api.call('/api/auth/wechat','POST',{
        code:r.code
      });
      const user=await api.call('/api/auth/me','GET',undefined,false,{token:s.access_token});
      getApp().login({...s,user});
      wx.reLaunch({
        url:this.returnTo||'/pages/home/index'
      })
    })
  }

});

