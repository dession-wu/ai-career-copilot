const {test}=require('node:test');
const assert=require('node:assert/strict');
const api=require('../lib/api');
const core=require('../lib/core');
let app;
function setup(){app={generation:1,session:{access_token:'token',user:{id:'owner'}},clear(){this.generation++;this.session=null}};global.getApp=()=>app;global.wx={reLaunch(){},request(){},uploadFile(){}}}
test('204 deletion succeeds with empty body',()=>assert.equal(core.accepted(204,''),null));
test('request sends bearer and preserves form content type',async()=>{setup();wx.request=o=>{assert.equal(o.header.Authorization,'Bearer token');assert.equal(o.header['content-type'],'application/x-www-form-urlencoded');o.success({statusCode:200,data:{ok:true}})};assert.deepEqual(await api.call('/api/auth/login','POST',{username:'a'},true),{ok:true})});
test('request 401 clears personal session and navigates login',async()=>{setup();let navigated=false;wx.reLaunch=()=>navigated=true;wx.request=o=>o.success({statusCode:401,data:{detail:'expired'}});await assert.rejects(api.call('/api/vault'));assert.equal(app.session,null);assert(navigated)});
test('old request cannot cross account generation',async()=>{setup();let request;wx.request=o=>request=o;const promise=api.call('/api/jobs');app.generation++;request.success({statusCode:200,data:[{id:'private'}]});await assert.rejects(promise,/会话已切换/)});
test('upload accepts asynchronous detail envelope',async()=>{setup();wx.uploadFile=o=>{assert.equal(o.name,'file');o.success({statusCode:202,data:JSON.stringify({detail:{upload_id:'task',status:'processing'}})})};assert.deepEqual(await api.upload({path:'/tmp/a.pdf'}),{pending:true,upload_id:'task',status:'processing'})});
test('upload 401 clears session and old upload is rejected',async()=>{setup();wx.uploadFile=o=>o.success({statusCode:401,data:'{}'});await assert.rejects(api.upload({path:'a'}));assert.equal(app.session,null);setup();let request;wx.uploadFile=o=>request=o;const promise=api.upload({path:'a'});app.generation++;request.success({statusCode:200,data:'{}'});await assert.rejects(promise,/会话已切换/)});
