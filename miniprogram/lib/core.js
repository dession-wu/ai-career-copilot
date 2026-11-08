function decode(v){
  if(typeof v==='string'){
    try{
      return JSON.parse(v)
    }catch(e){
      throw Error('服务返回格式无效')
    }
  }return v
}function accepted(status,v){
  if(status===204)return null;
  v=decode(v);
  if(status===202)return {
    pending:true,...(v.detail||v)
  };
  if(status<200||status>=300){
    const e=Error(typeof v.detail==='string'?v.detail:'操作未完成，请重试');
    e.status=status;
    throw e
  }return v
}function dirty(){
  return {
    verified:false,reviewed:false,saved:'',fallback:'',result:'',exportDone:false,findings:[]
  }
}function validFile(f){
  return /\.(pdf|docx)$/i.test(f.name)&&f.size>0&&f.size<=10*1024*1024
}function fields(obj,path=[]){
  return Object.keys(obj||{
    
  }).flatMap(k=>{
    const v=obj[k],q=path.concat(k);
    if(k==='_confirmed')return [];
    return v!==null&&typeof v==='object'?fields(v,q):[{
      path:JSON.stringify(q),label:q.map(x=>({
        personal_info:'个人信息',name:'名称',email:'邮箱',phone:'电话',education:'教育经历',school:'学校',degree:'学位',field:'专业',start_date:'开始日期',end_date:'结束日期',skills:'技能',level:'熟练程度',category:'类别',experiences:'工作经历',company:'公司',title:'职位',projects:'项目',description:'描述',technologies:'技术',star_description:'成果与职责',linkedin:'领英',website:'个人网站'
      }[x]||(/^\d+$/.test(x)?'第 '+(Number(x)+1)+' 项':x))).join(' · '),value:String(v==null?'':v)
    }]
  })
}function patch(obj,path,value){
  const out=JSON.parse(JSON.stringify(obj)),q=JSON.parse(path);
  let cur=out;
  for(let i=0;
  i<q.length-1;
  i++)cur=cur[q[i]];
  const key=q[q.length-1],old=cur[key];
  cur[key]=typeof old==='number'?Number(value):typeof old==='boolean'?value==='true':value;
  return out
}module.exports={
  decode,accepted,dirty,validFile,fields,patch
};
