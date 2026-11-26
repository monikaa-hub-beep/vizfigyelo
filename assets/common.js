/* Shared helpers for index.html and the city pages. Plain globals on purpose (no build step). */
var MN=["január","február","március","április","május","június","július","augusztus","szeptember","október","november","december"];
var MS=["jan","feb","már","ápr","máj","jún","júl","aug","szep","okt","nov","dec"];
var WD=["V","H","K","Sze","Cs","P","Szo"];
function el(id){return document.getElementById(id)}
function f(x,d){if(d===undefined)d=1;return x==null?"–":Number(x).toLocaleString("hu-HU",{minimumFractionDigits:d,maximumFractionDigits:d})}
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function sum(a){return a.reduce(function(p,q){return p+q},0)}
function sg(x){return x==null?"–":(x>0?"+":"")+f(x,0)}
function lbl(s){var p="";if(s.hmName){p=s.hmName.toLowerCase().indexOf(s.n.toLowerCase())===0?s.hmName.slice(s.n.length).trim():s.hmName}return p?s.n+" – "+p:s.n}
function yrs(s){return s.mtdAvg!=null&&s.mtdAvgFrom?s.mtdAvgFrom+"–"+s.mtdAvgTo+" ("+s.mtdAvgN+" év)":""}
function dlab(d){var x=new Date(d+"T12:00:00");return WD[x.getDay()]+" "+(+d.slice(8))}
function barChart(cats,groups,line,mark){
 const W=640,H=230,L=40,R=10,T=18,B=28,pw=W-L-R,ph=H-T-B;
 const all=groups.flatMap(g=>g.v).filter(v=>v!=null).concat(line!=null?[line]:[]);
 const mx=Math.max(...all,1)*1.1,n=cats.length,gw=pw/n,bw=Math.min(18,gw/(groups.length+.6));
 let s=`<svg viewBox="0 0 ${W} ${H}" role="img">`;
 for(let k=0;k<=4;k++){const y=T+ph-ph*k/4;s+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="var(--bd)"/><text x="${L-4}" y="${y+4}" text-anchor="end" class="lbl" style="fill:var(--mu)">${Math.round(mx*k/4)}</text>`}
 cats.forEach((c,i)=>{const x0=L+gw*i+gw/2-bw*groups.length/2;
  groups.forEach((g,j)=>{const v=g.v[i];if(v==null)return;const h=v/mx*ph,col=Array.isArray(g.c)?g.c[i]:g.c;
   s+=`<rect x="${x0+j*bw}" y="${T+ph-h}" width="${bw-1}" height="${h}" style="fill:${col}"><title>${c}: ${f(v)} mm</title></rect>`});
  s+=`<text x="${L+gw*i+gw/2}" y="${H-10}" text-anchor="middle" class="lbl" style="fill:var(--mu)">${c}</text>`});
 if(line!=null){const y=T+ph-line/mx*ph;s+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" style="stroke:var(--wa)" stroke-width="2" stroke-dasharray="5 4"/>`}
 if(mark&&groups[0].v[mark.i]!=null){const v=groups[0].v[mark.i];s+=`<text x="${L+gw*mark.i+gw/2}" y="${T+ph-v/mx*ph-4}" text-anchor="middle" class="lbl" style="fill:var(--wa);font-weight:700">${mark.t}</text>`}
 return s+"</svg>";
}
function lineChart(dates,vals){
 const W=640,H=250,L=48,R=12,T=14,B=30,pw=W-L-R,ph=H-T-B,pts=vals.filter(v=>v!=null);
 if(pts.length<2)return "<p class='sub'>Nincs elég adat.</p>";
 let mn=Math.min(...pts),mx=Math.max(...pts);const pad=(mx-mn||10)*.12;mn-=pad;mx+=pad;
 const X=i=>L+i/(vals.length-1)*pw,Y=v=>T+ph-(v-mn)/(mx-mn)*ph,dl=d=>`${MS[+d.slice(5,7)-1]} ${+d.slice(8)}.`;
 let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Vízállás napi átlagai">`;
 for(let k=0;k<=4;k++){const y=T+ph-ph*k/4;s+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="var(--bd)"/><text x="${L-5}" y="${y+4}" text-anchor="end" class="lbl" style="fill:var(--mu)">${Math.round(mn+(mx-mn)*k/4)}</text>`}
 let d="",pen=false,lastI=-1;vals.forEach((v,i)=>{if(v==null){pen=false;return}d+=(pen?"L":"M")+X(i).toFixed(1)+","+Y(v).toFixed(1);pen=true;lastI=i});
 s+=`<path d="${d}" fill="none" style="stroke:var(--ac)" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>`;
 if(lastI>=0)s+=`<circle cx="${X(lastI)}" cy="${Y(vals[lastI])}" r="5" style="fill:var(--wa)" stroke="#fff" stroke-width="2"/>`;
 [0,Math.floor((vals.length-1)/2),vals.length-1].forEach((i,k)=>{s+=`<text x="${X(i)}" y="${H-8}" text-anchor="${k==0?"start":k==2?"end":"middle"}" class="lbl" style="fill:var(--mu)">${dl(dates[i])}</text>`});
 return s+"</svg>";
}

/* 7-day model forecast block (data: forecast.json written by collector/forecast.py). fc = {dates,precip,prob,tmax,tmin} */
function forecastHtml(fc){
 if(!fc||!fc.dates||!fc.dates.length)return "";
 var tot=sum(fc.precip.filter(function(v){return v!=null}));
 var hs=!!(fc.snow&&fc.snow.some(function(v){return v>0}));
 var s='<div class="legend"><span><i style="background:var(--ac2)"></i>Várható csapadék (mm), modellezett előrejelzés</span></div>'+
  barChart(fc.dates.map(dlab),[{v:fc.precip,c:"var(--ac2)"}]);
 s+='<div class="sc"><table><tr><th>Nap</th><th class=n>Várható csapadék (mm)</th><th class=n>Csapadék esélye</th><th class=n>Hőmérséklet (°C)</th>'+(hs?'<th class=n>Hó (cm)</th>':'')+'</tr>'+
  fc.dates.map(function(d,i){return '<tr><td>'+esc(dlab(d))+'</td><td class=n>'+f(fc.precip[i])+'</td><td class=n>'+(fc.prob&&fc.prob[i]!=null?f(fc.prob[i],0)+"%":"–")+'</td><td class=n>'+(fc.tmin&&fc.tmin[i]!=null?f(fc.tmin[i],0)+" … "+f(fc.tmax[i],0):"–")+'</td>'+(hs?'<td class=n>'+(fc.snow[i]>0?'❄ '+f(fc.snow[i]):'–')+'</td>':'')+'</tr>'}).join("")+'</table></div>';
 s+=(hs?'<p class="note">❄ A csapadék egy része hóként érkezhet. A milliméterben megadott érték a hó olvadt vízmennyisége, a „Hó (cm)” oszlop a várható friss hóréteg vastagsága.</p>':'')+'<p class="note">A következő '+fc.dates.length+' napban összesen várható: <b>'+f(tot)+' mm</b> csapadék. Ez modellszámítás, nem mérés. Forrás: <a href="https://open-meteo.com/" rel="noopener">Open-Meteo.com</a> (<a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener">CC BY 4.0</a>).</p>';
 return s;
}
/* share button: native share sheet when available, otherwise copy the link */
function shareButton(btn,status,url,title){
 btn.onclick=function(){
  if(navigator.share){navigator.share({title:title,url:url}).catch(function(){});return}
  var done=function(ok){status.textContent=ok?"A link a vágólapra került.":"Másold ki a címet a böngésző címsorából."};
  try{navigator.clipboard.writeText(url).then(function(){done(true)},function(){done(false)})}catch(e){done(false)}
 };
}
