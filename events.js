/* VEXU HQ · logica comună a evenimentelor (calendar + dashboard). Fișier sursă static, încărcat de calendar.html și index.html. */
(function(){
const TZ='Europe/Bucharest';
const es=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function fmt(iso, o){ if(!iso) return ''; const d=iso instanceof Date?iso:new Date(iso); return new Intl.DateTimeFormat('ro-RO',Object.assign({timeZone:TZ},o)).format(d)}
function dayKey(d){return new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(d)}
function relevant(ev, now){
  if(ev.coming_soon) return new Date('2099-01-01');
  if(ev.announced && ev.start) return now;
  if(ev.start){ const s=new Date(ev.start); if(ev.end){ const e=new Date(ev.end); if(now<e) return s>now?s:e; return e;} return s; }
  if(ev.end && ev.end_only) return new Date(ev.end);
  if(ev.start_date){ const s=new Date(ev.start_date+'T12:00:00+03:00'); if(ev.end_date){ const e=new Date(ev.end_date+'T23:59:59+02:00'); return now<e? (now<s?s:e): e;} return s; }
  if(ev.end_date) return new Date(ev.end_date+'T12:00:00+02:00');
  return new Date('2099-01-01');
}
function status(ev, now){
  if(ev.coming_soon) return {kind:'soon', text:'Coming Soon — dată neanunțată', target:null};
  if(ev.announced && ev.start) return {kind:'live', text:'Anunțat oficial pe '+fmt(ev.start,{weekday:'long',day:'numeric',month:'long'})+' — disponibil acum', target:null};
  if(ev.date_only && ev.start_date){
    const day=ev.start_date;
    const today=new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
    if(today<day) return {kind:'soon', text:'Începe pe '+fmt(day+'T12:00:00+03:00',{weekday:'long',day:'numeric',month:'long'})+' (doar data confirmată)'};
    if(today===day) return {kind:'live', text:'LIVE azi (oră neconfirmată)'};
    return {kind:'done', text:'Terminat / trecut'};
  }
  if(ev.end_only && ev.end){
    const e=new Date(ev.end);
    if(now<e) return {kind:'soon', text:'Se termină în…', target:e};
    return {kind:'done', text:'Terminat'};
  }
  if(ev.no_end && ev.start_date){
    const s=new Date(ev.start_date+'T12:00:00+03:00');
    if(now<s) return {kind:'soon', text:'Începe în…', target:s};
    return {kind:'live', text:'LIVE — '+ (ev.end_note||'fără dată de final anunțată'), target:null};
  }
  if(ev.start_date && ev.end_date && !ev.start){
    const s=new Date(ev.start_date+'T00:00:00+03:00');
    const e=new Date(ev.end_date+'T23:59:59+02:00');
    if(now<s) return {kind:'soon', text:'Începe în…', target:s};
    if(now<=e) return {kind:'live', text:'LIVE — se termină în…', target:e};
    return {kind:'done', text:'Terminat'};
  }
  const s=ev.start?new Date(ev.start):null;
  const e=ev.end?new Date(ev.end):null;
  if(s && now<s) return {kind:'soon', text:'Începe în…', target:s};
  if(s && (!e || now<e)) {
    if(ev.end_time_unknown && ev.end_date){
      return {kind:'live', text:'LIVE — final anunțat: '+fmt(ev.end_date+'T12:00:00+02:00',{day:'numeric',month:'long'}), target:null};
    }
    if(e) return {kind:'live', text:'LIVE — se termină în…', target:e};
    return {kind:'live', text:'LIVE', target:null};
  }
  if(ev.end_time_unknown && ev.end_date && s && now>=s){
    const endD=ev.end_date;
    const today=new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
    if(today<=endD) return {kind:'live', text:'LIVE — final: '+fmt(endD+'T12:00:00+02:00',{day:'numeric',month:'long'})+' (oră neanunțată)', target:null};
  }
  return {kind:'done', text:'Terminat'};
}
function windowText(ev){
  if(ev.coming_soon) return 'Dată: Coming Soon (neanunțată oficial)';
  if(ev.announced && ev.start) return 'Anunț oficial: '+fmt(ev.start,{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
  const bits=[];
  if(ev.start) bits.push('Start: '+fmt(ev.start,{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}));
  else if(ev.start_date) bits.push('Start: '+fmt(ev.start_date+'T12:00:00+03:00',{weekday:'short',day:'numeric',month:'short'})+(ev.date_only?' (doar data)':''));
  if(ev.end) bits.push('Final: '+fmt(ev.end,{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}));
  else if(ev.end_date) bits.push('Final: '+fmt(ev.end_date+'T12:00:00+02:00',{weekday:'short',day:'numeric',month:'short'})+(ev.end_time_unknown?' (oră neanunțată)':''));
  else if(ev.no_end) bits.push(ev.end_note||'fără dată de final anunțată');
  if(ev.end_only && ev.end) return 'Se termină: '+fmt(ev.end,{weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
  return bits.join(' · ');
}

// fereastra evenimentului (start/final ca Date, null când nu e cunoscut)
function span(ev){
  if(ev.coming_soon||ev.announced||ev.date_only||ev.no_end) return {s:ev.start?new Date(ev.start):(ev.start_date?new Date(ev.start_date+'T12:00:00+03:00'):null),e:null};
  if(ev.end_only&&ev.end) return {s:null,e:new Date(ev.end)};
  if(ev.start_date&&ev.end_date&&!ev.start) return {s:new Date(ev.start_date+'T00:00:00+03:00'),e:new Date(ev.end_date+'T23:59:59+02:00')};
  return {s:ev.start?new Date(ev.start):null,e:ev.end?new Date(ev.end):null};
}
// cât timp a trecut din durata evenimentului (0..1) sau null
function progress(ev,now){const w=span(ev);if(!w.s||!w.e)return null;const k=(now-w.s)/(w.e-w.s);return Math.max(0,Math.min(1,k))}
// timp rămas, compact: „12 min”, „3h 42m”, „2z 04h”
function left(ms){ms=Math.max(0,ms);const m=Math.floor(ms/6e4);if(m<1)return Math.max(0,Math.floor(ms/1000))+'s';if(m<60)return m+' min';const h=Math.floor(m/60);if(h<48)return h+'h '+String(m%60).padStart(2,'0')+'m';const d=Math.floor(h/24);return d+'z '+String(h%24).padStart(2,'0')+'h'}
function cdHtml(ms){let s=Math.max(0,Math.floor(ms/1000));return [[Math.floor(s/86400),'zile'],[Math.floor(s%86400/3600),'ore'],[Math.floor(s%3600/60),'min'],[s%60,'sec']].map(([v,l])=>`<div><b>${String(v).padStart(2,'0')}</b><span>${l}</span></div>`).join('')}
// culoare consecventă pentru fiecare joc (din slug)
function gameHue(k){let h=0;k=String(k||'');for(let i=0;i<k.length;i++)h=(h*31+k.charCodeAt(i))%360;return h}

const fs_=d=>fmt(d,T_SHORT).replace(/\./g,'');
function winCompact(ev,now){const w=span(ev);if(w.s&&w.e)return fs_(w.s)+' → '+fs_(w.e);if(w.e&&!w.s)return 'final '+fs_(w.e);if(w.s&&ev.start&&!ev.date_only&&!ev.announced)return 'start '+fs_(w.s)+(ev.no_end?' · '+(ev.end_note||'fără final anunțat'):'');return windowText(ev).replace(/\./g,'')}
const T_SHORT={day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'};
// rând de eveniment (dashboard + calendar). Timerul și bara se actualizează cu tick(), fără re-randare.
function evRow(ev,now,opt){
  opt=opt||{};const st=status(ev,now),w=span(ev),k=st.kind,tg=st.target||null;
  const left_=tg?tg-now:null,urg=k==='live'&&tg&&left_<3*36e5;
  const pr=k==='live'?progress(ev,now):null;
  let big,sub;
  if(tg){big=left(left_);const same=dayKey(tg)===dayKey(now);sub=(k==='live'?'final ':'start ')+(same?fmt(tg,{hour:'2-digit',minute:'2-digit'}):fmt(tg,T_SHORT).replace(/\./g,''))}
  else if(k==='live'){big='LIVE';sub=ev.announced?'anunțat oficial':(ev.no_end?'fără final anunțat':(ev.end_date?'final '+fmt(ev.end_date+'T12:00:00+02:00',{day:'numeric',month:'short'}):'în desfășurare'))}
  else if(k==='done'){big='Terminat';sub=''}
  else{big='Curând';sub=ev.coming_soon?'dată neanunțată':(ev.start_date?fmt(ev.start_date+'T12:00:00+03:00',{day:'numeric',month:'short'})+' (doar data)':'')}
  const gl=ev.gameLabel||ev.game||'',h=gameHue(ev.gameSlug||gl);
  const href=ev.slug?'posts/'+es(ev.slug)+'.html':(ev.link||'');
  const tag=href?'a':'div',ext=!ev.slug&&ev.link?' target="_blank" rel="noopener"':'';
  const cl='ev '+(k==='live'?'live':k==='done'?'done':'soon')+(urg?' urg':'');
  const dat=(tg?` data-t="${+tg}"`:'')+(pr!==null?` data-s="${+w.s}" data-e="${+w.e}"`:'');
  return `<${tag} class="${cl}"${href?` href="${href}"${ext}`:''} style="--h:${h}"${dat}>`+
    `<img class="th fx" src="${es(ev.img||'generic-neon.png')}" alt="" width="56" height="56" loading="lazy">`+
    `<span class="tx"><span class="gm"><i class="gd" style="--h:${h}"></i>${es(gl)}</span><b class="nm">${es(ev.name)}</b>${opt.meta?`<span class="mt2">${es(opt.meta===true?winCompact(ev,now):opt.meta)}</span>`:''}</span>`+
    `<span class="tmr"><b>${es(big)}</b><span>${es(sub)}</span></span>`+
    (pr!==null?`<span class="pbar"><u style="width:${(pr*100).toFixed(1)}%"></u></span>`:'')+
    (opt.note&&ev.zvon_note?`<span class="nt">${es(ev.zvon_note)}</span>`:'')+
    `</${tag}>`;
}
// actualizează timerele și barele din rădăcină; returnează true dacă vreun eveniment și-a schimbat starea (trebuie re-randat)
function tick(root,now){let flip=false;const n=+now;
  root.querySelectorAll('.ev[data-t]').forEach(el=>{const t=+el.dataset.t,b=el.querySelector('.tmr b');if(t<=n){flip=true;return}
    const l=left(t-n);if(b&&b.textContent!==l)b.textContent=l;if(el.classList.contains('live')){el.classList.toggle('urg',t-n<3*36e5)}});
  root.querySelectorAll('.ev[data-s]').forEach(el=>{const s=+el.dataset.s,e=+el.dataset.e,u=el.querySelector('.pbar u');if(u)u.style.width=Math.max(0,Math.min(100,(n-s)/(e-s)*100)).toFixed(1)+'%'});
  return flip}

window.VX={evRow,tick,TZ,es,fmt,dayKey,relevant,status,windowText,span,progress,left,cdHtml,gameHue};
})();
