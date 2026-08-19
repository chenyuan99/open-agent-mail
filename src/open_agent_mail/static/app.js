const state={mailboxes:[],messages:[],mailbox:null,folder:'inbox',query:''};
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const escapeHtml=s=>String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const formatDate=iso=>{const d=new Date(iso),now=new Date();return d.toDateString()===now.toDateString()?d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}):d.toLocaleDateString([],{month:'short',day:'numeric'})};
async function api(url,options){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...options});const data=await r.json();if(!r.ok)throw new Error(data.error||'Something went wrong');return data}
function toast(text){const el=$('#toast');el.textContent=text;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2200)}
function render(){
  $('#mailboxes').innerHTML=state.mailboxes.map(m=>`<button class="mailbox ${m===state.mailbox?'active':''}" data-mailbox="${escapeHtml(m)}"><strong>${escapeHtml(m)}</strong><small>↳ agent workspace</small></button>`).join('');
  $('#address').textContent=state.mailbox;
  const mine=state.messages.filter(m=>m.mailbox===state.mailbox), unread=mine.filter(m=>m.folder==='inbox'&&!m.read).length;
  $('#unread').textContent=unread;$('#inboxCount').textContent=mine.filter(m=>m.folder==='inbox').length;
  $('#storage').textContent=Math.max(1,Math.ceil(new Blob([JSON.stringify(mine)]).size/1024))+' KB';
  const q=state.query.toLowerCase(), shown=mine.filter(m=>m.folder===state.folder&&[m.sender,m.recipient,m.subject,m.body].some(v=>v.toLowerCase().includes(q))).sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
  $('#messages').innerHTML=shown.map(m=>`<article class="message-row ${!m.read?'unread':''}" data-id="${m.id}"><strong>${escapeHtml(state.folder==='inbox'?m.sender:m.recipient)}</strong><div class="summary"><b>${escapeHtml(m.subject)}</b><span>${escapeHtml(m.body)}</span></div><time>${formatDate(m.created_at)}</time></article>`).join('');
  $('#empty').hidden=shown.length>0;
  $$('.mailbox').forEach(b=>b.onclick=()=>{state.mailbox=b.dataset.mailbox;render()});
  $$('.message-row').forEach(row=>row.onclick=()=>openMessage(Number(row.dataset.id)));
}
async function load(){Object.assign(state,await api('/api/state'));state.mailbox=state.mailbox||state.mailboxes[0];render()}
async function openMessage(id){const m=state.messages.find(x=>x.id===id);if(!m)return;$('#messageMeta').textContent=formatDate(m.created_at).toUpperCase();$('#messageSubject').textContent=m.subject;$('#messageRoute').textContent=`${m.sender} → ${m.recipient}`;$('#messageBody').textContent=m.body;$('#messageDialog').showModal();if(!m.read){m.read=true;render();await api(`/api/messages/${id}/read`,{method:'POST',body:'{}'})}}
$$('.close').forEach(b=>b.onclick=()=>b.closest('dialog').close());
$$('.tab').forEach(t=>t.onclick=()=>{$$('.tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');state.folder=t.dataset.folder;render()});
$('#search').oninput=e=>{state.query=e.target.value;render()};
$('#compose').onclick=()=>{$('#composeForm').reset();$('#formStatus').textContent='';$('#composeDialog').showModal()};
$('#composeForm').onsubmit=async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.target));data.mailbox=state.mailbox;try{state.messages.push(await api('/api/messages',{method:'POST',body:JSON.stringify(data)}));$('#composeDialog').close();state.folder='sent';$$('.tab').forEach(t=>t.classList.toggle('active',t.dataset.folder==='sent'));render();toast('Message sent')}catch(err){$('#formStatus').textContent=err.message}};
$('#addMailbox').onclick=async()=>{const name=prompt('Choose a mailbox name (for example: builder)');if(!name)return;try{const result=await api('/api/mailboxes',{method:'POST',body:JSON.stringify({name})});state.mailboxes.push(result.address);state.mailbox=result.address;render();toast('Mailbox created')}catch(err){toast(err.message)}};
document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('#compose').click()}if(e.key==='Escape')$$('dialog[open]').forEach(d=>d.close())});
load().catch(err=>toast(err.message));
