/* VEXU HQ · derulare infinită (blog, Shorts, pagini de joc). Fișier sursă static, încărcat cu ?v=<hash>.
   Primele carduri sunt în HTML (SEO / fără JS); restul vin din JSON (posts-index.json / shorts.json) și se adaugă pe bucăți cu IntersectionObserver. */
(function(){
const es=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cls=l=>String(l).replace(/[^A-Za-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
const ne=s=>String(s||'').replace(/^[\p{Extended_Pictographic}\uFE0F\u200D\s]+/u,'');
function gHue(k){let h=0;k=String(k||'');for(let i=0;i<k.length;i++)h=(h*31+k.charCodeAt(i))%360;return h}
const gm=p=>p.joc?`<span class="gm"><i class="gd" style="--h:${gHue(p.jocSlug)}"></i>${es(p.joc)}</span>`:'';
const nv=n=>n>=1e6?((n/1e6).toFixed(n>=1e7?1:2)).replace(/\.?0+$/,'').replace('.',',')+'M':n>=1e4?Math.round(n/1e3)+'K':n>=1e3?((n/1e3).toFixed(1)).replace(/\.0$/,'').replace('.',',')+'K':String(n);
function dtRo(t){return new Intl.DateTimeFormat('ro-RO',{timeZone:'Europe/Bucharest',day:'numeric',month:'long',hour:'2-digit',minute:'2-digit'}).format(new Date(t))}
// insignă „NOU · 4 h”: postări publicate în ultimele 6 ore (din câmpul published, ora reală)
function nouHtml(p){const t=Date.parse(p.published||'');if(!t)return '';const m=Math.floor((Date.now()-t)/6e4);if(m<0||m>=360)return '';return `<span class="nou">NOU · ${m<1?'acum':m<60?m+' min':Math.floor(m/60)+' h'}</span>`}
/* Cardul UNIC al site-ului (blog, joc, Shorts, dashboard): imagine mare sus, insigne pe imagine, dată · joc, titlu mare, extras.
   p: {slug,title,labels,dateRo,published,cimg|img,fit,joc,jocSlug,excerpt}; o: {hp:prefix link, ip:prefix imagine, first, nou:false, views, attrs, tip}
   Același markup ca card_html() din build_posts.py (HTML-ul de la build trebuie să coincidă ca să-l păstrăm la hidratare). */
function cardHtml(p,o){o=o||{};const fit=p.fit||'cover',img=p.cimg===undefined?p.img:p.cimg,lb=(p.labels&&p.labels.length)?p.labels:[''];
  const media=fit==='none'||!img?`<span class="fb">${es(p.joc||'VEXU HQ')}</span>`:`<img class="fx" src="${o.ip||''}${es(img)}" alt="" width="640" height="360"${o.first?' fetchpriority="high"':' loading="lazy"'}>`;
  const rib='<span class="ribs">'+lb.map(l=>`<span class="rib ${cls(l)}">${es(l)}</span>`).join('')+'</span>';
  const sv=typeof o.views==='number'?`<span class="sv">${nv(o.views)}</span>`:'';
  return `<a class="pc ${cls(lb[0])}" href="${o.hp===undefined?'posts/':o.hp}${es(p.slug)}.html"${o.attrs||''}${o.tip||''}><span class="im f-${fit==='none'||!img?'none':fit}" style="--h:${gHue(p.jocSlug)}">${media}${rib}${o.nou===false?'':nouHtml(p)}${sv}</span><span class="b"><span class="mt"><span class="dt">${es(p.dateRo||'')}</span>${gm(p)}</span><h2>${es(ne(p.title))}</h2><span class="ex">${es(p.excerpt||'')}</span></span></a>`}
const rowHtml=(p,hp,ip)=>cardHtml(p,{hp,ip});
// card de Short din shorts.json (+ vizionări); pre = prefix pagină ('' sau '../')
function shortHtml(s,pre){
  const v=typeof s.views==='number'?s.views:null,t=Date.parse(s.published);
  return cardHtml({slug:s.slug,title:s.title,labels:s.labels||['TREND SHORTS'],dateRo:s.dateRo,published:s.published,cimg:s.img,fit:s.fit,joc:s.joc,jocSlug:s.jocSlug,excerpt:s.excerpt},
    {hp:pre+'posts/',ip:pre,nou:false,views:v===null?undefined:v,attrs:` data-id="${es(s.id)}" data-g="${es(s.jocSlug||'')}" data-t="${t}" data-v="${v===null?'':v}"`,
     tip:v!==null&&s.views_t?` title="${es(v.toLocaleString('ro-RO'))} vizionări, citite pe YouTube ${es(dtRo(s.views_t))}"`:''})}
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
window.VF={es,cls,ne,gHue,gm,cardHtml,rowHtml,shortHtml,nouHtml,nv,dtRo,endless};
})();
