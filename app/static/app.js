const $ = id => document.getElementById(id);
let preview = null, cases = [];
async function api(path, body) {
  const r = await fetch(path, {method: body ? 'POST' : 'GET', headers: {'X-Assessment-Session': window.SESSION,'Content-Type':'application/json'}, ...(body ? {body:JSON.stringify(body)} : {})});
  const data = await r.json(); if (!r.ok) throw Error(data.error || r.status); return data;
}
const spec = () => ({case_id:$('case').value,condition:$('condition').value,variant:$('variant').value});
function notice(text) {$('notice').textContent=text;}
function invalidate(){preview=null;$('run').disabled=true;notice('输入已改变，请重新预览。');}
function selectCase(){
  $('condition').replaceChildren();
  const c=cases.find(c=>c.id===$('case').value);
  for(const condition of c.conditions){const o=new Option(condition,condition);$('condition').add(o);}
  invalidate();
}
function showPassages(passages){
  $('passages').replaceChildren();
  for(const p of passages){const a=document.createElement('article');a.className='passage';a.id='p-'+p.id;
    const h=document.createElement('strong');h.textContent=p.id+' · '+p.source;const t=document.createElement('p');t.textContent=p.text;a.append(h,t);$('passages').append(a);}
}
function showRecord(r){
  $('raw').textContent=JSON.stringify(r,null,2);$('result').replaceChildren();
  const mode={live_api:'真实 API',dry_run:'仅保存输入',offline_replay:'模拟 · 非实验结果'};
  for(const text of [mode[r.run_kind]||r.run_kind,'API: '+r.api_status,'格式: '+r.format_status,'引用定位: '+r.locator_status,'语义: 尚未核验']){
    const tag=document.createElement('span');tag.className='badge';tag.textContent=text;$('result').append(tag);}
  const p=document.createElement('p');p.textContent=r.parsed_output?.answer||'没有模型答案';$('result').append(p);
  for(const id of r.parsed_output?.citations||[]){const a=document.createElement('a');a.textContent=id;a.href='#p-'+encodeURIComponent(id);$('result').append(a);}
  const meta=document.createElement('p');meta.textContent='run_id: '+r.run_id+' / 调用 '+r.call_count+' 次 / 耗时 '+(r.elapsed_seconds??'—')+' 秒';$('result').append(meta);
  showPassages(r.selected_passages||[]);
}
async function refresh(){
  const rows=await api('/api/runs');
  for(const side of ['left','right']){const previous=$(side).value;$(side).replaceChildren(new Option('选择已有记录',''));for(const r of rows)$(side).add(new Option([r.case_id,r.condition,r.variant,r.status,r.run_id.slice(0,8)].join(' · '),r.run_id));if(rows.some(r=>r.run_id===previous))$(side).value=previous;}
}
async function safely(fn){try{await fn();}catch(e){notice('操作失败：'+e.message);}}
$('preview').onclick=()=>safely(async()=>{preview=await api('/api/preview',spec());$('question').textContent=preview.question;showPassages(preview.selected_passages);$('messages').textContent=JSON.stringify({messages:preview.messages,config:preview.config},null,2);$('run').disabled=false;notice('已预览。后端将校验问题、原文、顺序和配置是否一致。');});
$('run').onclick=()=>safely(async()=>{if(!preview)return;$('run').disabled=true;notice('正在处理，请等待…');const body={...spec(),mode:$('mode').value};for(const k of ['question','visible_passages','input_sha256','public_config_sha256'])body[k]=preview[k];try{const r=await api('/api/run',body);showRecord(r);await refresh();notice('记录已保存。'+(r.run_kind==='live_api'?'请核对答案与引用。':'此次未调用模型。'));}finally{$('run').disabled=!preview;}});
$('case').onchange=selectCase;for(const id of ['condition','variant'])$(id).onchange=invalidate;
$('mode').onchange=()=>{$('run').textContent=$('mode').value==='paid'?'执行真实请求':($('mode').value==='mock'?'运行模拟链路':'保存输入');};
$('refresh').onclick=()=>safely(refresh);
for(const side of ['left','right'])$(side).onchange=()=>safely(async()=>{if(!$(side).value){$(side+'-view').textContent='';return;}const r=await api('/api/runs/'+$(side).value);$(side+'-view').textContent=JSON.stringify(r,null,2);});
safely(async()=>{const data=await api('/api/cases');cases=data.cases;for(const c of cases)$('case').add(new Option(c.id+' · '+(c.split==='dev'?'开发':'评测'),c.id));$('mode').querySelector('[value=paid]').disabled=!data.allow_paid;selectCase();await refresh();notice(data.allow_paid?'真实调用已启用；请先预览输入。':'离线模式：预览、保存输入和模拟均不调用模型。');});
