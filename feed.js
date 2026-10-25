/* VEXU HQ · derulare infinită (blog, Shorts, pagini de joc). Fișier sursă static, încărcat cu ?v=<hash>.
   Primele carduri sunt în HTML (SEO / fără JS); restul vin din JSON (posts-index.json / shorts.json) și se adaugă pe bucăți cu IntersectionObserver. */
(function(){
const es=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cls=l=>String(l).replace(/[^A-Za-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
const ne=s=>String(s||'').replace(/^[\p{Extended_Pictographic}\uFE0F\u200D\s]+/u,'');
function gHue(k){let h=0;k=String(k||'');for(let i=0;i<k.length;i++)h=(h*31+k.charCodeAt(i))%360;return h}
const gm=p=>p.joc?`<span class="gm"><i class="gd" style="--h:${gHue(p.jocSlug)}"></i>${es(p.joc)}</span>`:'';
// rând dens de postare (același markup ca prow() din build_posts.py). hp = prefix link (ex. „../posts/”), ip = prefix imagine (ex. „../”)
function rowHtml(p,hp,ip){
  const chips=(p.labels||[]).map(l=>`<span class="l ${cls(l)}">${es(l)}</span>`).join(' ')+`<span class="dt">${es(p.dateRo)}</span>`;
  return `<a class="p ${cls((p.labels||[''])[0])}" href="${hp}${es(p.slug)}.html"><span class="im"><img class="fx" src="${ip}${es(p.img)}" alt="" width="296" height="185" loading="lazy"></span><span class="b"><span class="mt">${chips}</span><h2>${es(ne(p.title))}</h2><span class="ex">${es(p.excerpt)}</span>${gm(p)}</span></a>`}
const nv=n=>n>=1e6?((n/1e6).toFixed(n>=1e7?1:2)).replace(/\.?0+$/,'').replace('.',',')+'M':n>=1e4?Math.round(n/1e3)+'K':n>=1e3?((n/1e3).toFixed(1)).replace(/\.0$/,'').replace('.',',')+'K':String(n);
function dtRo(t){return new Intl.DateTimeFormat('ro-RO',{timeZone:'Europe/Bucharest',day:'numeric',month:'long',hour:'2-digit',minute:'2-digit'}).format(new Date(t))}
// card de Short (același markup ca short_cards() din build_posts.py)
function shortHtml(s,pre){
  const v=typeof s.views==='number'?s.views:null,t=Date.parse(s.published);
  return `<a class="sc" href="${pre}posts/${es(s.slug)}.html" data-id="${es(s.id)}" data-g="${es(s.jocSlug||'')}" data-t="${t}" data-v="${v===null?'':v}"${v!==null&&s.views_t?` title="${es(v.toLocaleString('ro-RO'))} vizionări, citite pe YouTube ${es(dtRo(s.views_t))}"`:''}><span class="sim"><img class="fx" src="${pre}${es(s.img)}" alt="" width="405" height="720" loading="lazy">${v!==null?`<span class="sv">${nv(v)}</span>`:''}</span><span class="sb">${gm(s)}<b class="st">${es(s.title)}</b><span class="sd">${es(s.dateRo||'')}</span></span></a>`}
/* endless({el, left(), more(), total(), btn})
   el = santinela (div.sent). left() = câte elemente mai sunt; more() = adaugă o bucată (poate întoarce Promise). btn = buton de rezervă fără IntersectionObserver. */
function endless(o){
  const el=o.el,io_=('IntersectionObserver' in window);let busy=false,io=null;
  el.innerHTML='<span class="sl" role="status" aria-live="polite"><i></i><i></i><i></i><span class="vh">Se încarcă</span></span><span class="se">Ai ajuns la capăt</span>';
  function state(){const l=o.left();el.classList.toggle('end',l<=0&&o.total()>0);el.classList.toggle('has',l>0);el.classList.toggle('ld',busy);
    if(o.btn){o.btn.style.display=(!io_&&l>0)?'inline-block':'none';if(!io_&&l>0)o.btn.textContent=`Vezi mai multe (${l})`}}
  function watch(){if(!io)return;io.unobserve(el);if(o.left()>0)io.observe(el)}
  async function step(){if(busy||o.left()<=0)return;busy=true;state();try{await o.more()}catch(e){}busy=false;state();watch()}
  if(io_){io=new IntersectionObserver(es_=>{if(es_.some(x=>x.isIntersecting))step()},{rootMargin:'600px 0px'})}
  if(o.btn)o.btn.onclick=()=>step();
  state();watch();
  return {refresh(){state();watch()},step};
}
window.VF={es,cls,ne,gHue,gm,rowHtml,shortHtml,nv,dtRo,endless};
})();
