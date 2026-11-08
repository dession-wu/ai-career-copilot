const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('fs'),path=require('path');
test('all dynamic WXML conditions are bound expressions',()=>{
 const root=path.join(__dirname,'..','pages');
 for(const dir of fs.readdirSync(root)){
  const file=path.join(root,dir,'index.wxml');
  const text=fs.readFileSync(file,'utf8');
  assert.doesNotMatch(text,/wx:(?:if|elif)="(?!\{\{)[^"]+"/,file);
 }
});
