const c=require('../config'),core=require('./core');
const pendingOperations=new Map();
function call(path,method='GET',data,form=false,options={}){
  const a=getApp(),g=a.generation;
  const signature=JSON.stringify([path,method,data]);
  if(!pendingOperations.has(signature))pendingOperations.set(signature,Date.now().toString(36)+'-'+Math.random().toString(36).slice(2));
  return new Promise((resolve,reject)=>wx.request({
    url:c.baseURL+path,method,data,timeout:180000,header:{
      'Idempotency-Key':pendingOperations.get(signature),Authorization:options.token?'Bearer '+options.token:(a.session?'Bearer '+a.session.access_token:''),'content-type':form?'application/x-www-form-urlencoded':'application/json'
    },success:r=>{
      if(g!==a.generation)return reject(Error('会话已切换'));
      if(r.statusCode===401&&!options.token){
        a.clear();
        wx.reLaunch({
          url:'/pages/login/index'
        });
        return reject(Error('登录已过期'))
      }try{
        const result=core.accepted(r.statusCode,r.data);pendingOperations.delete(signature);resolve(result)
      }catch(e){
        reject(e)
      }
    },fail:()=>reject(Error('无法连接服务，请检查网络后重试'))
  }))
}function upload(file){
  const a=getApp(),g=a.generation;
  return new Promise((resolve,reject)=>wx.uploadFile({
    url:c.baseURL+'/api/vault/upload',filePath:file.path,name:'file',header:{
      Authorization:'Bearer '+a.session.access_token
    },success:r=>{
      if(g!==a.generation)return reject(Error('会话已切换'));
      if(r.statusCode===401){
        a.clear();
        wx.reLaunch({
          url:'/pages/login/index'
        });
        return reject(Error('请重新登录'))
      }try{
        resolve(core.accepted(r.statusCode,r.data))
      }catch(e){
        reject(e)
      }
    },fail:()=>reject(Error('上传失败，请重试'))
  }))
}module.exports={
  call,upload
};
