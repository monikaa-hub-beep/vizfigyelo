/* City page: draws the charts from the embedded station data and loads the forecast. */
(function(){
 var node=el("cd"),slug=document.body.getAttribute("data-slug"),url=document.body.getAttribute("data-url")||location.href;
 shareButton(el("sh"),el("shs"),url,document.title);
 if(node){
  var s=JSON.parse(node.textContent);
  var d=(s.daily||[]).map(function(v){return v||0}),mx=Math.max.apply(null,d.concat([1]))*1.1;
  var X=function(i){return 20+i*(290/(d.length-1||1))},Y=function(v){return 120-v/mx*100};
  var c14=el("c14");
  if(c14&&d.length)c14.innerHTML='<svg viewBox="0 0 320 140" role="img" aria-label="Napi csapadék, 14 nap"><line x1="20" y1="120" x2="310" y2="120" stroke="var(--bd)"/>'+
   d.map(function(v,i){return '<rect x="'+(X(i)-8)+'" y="'+Y(v)+'" width="16" height="'+(120-Y(v))+'" style="fill:var(--ac)" opacity=".85"><title>'+esc((s.dates&&s.dates[i])||"")+': '+f(s.daily[i])+' mm</title></rect>'}).join("")+
   '<text x="20" y="135" class="lbl" style="fill:var(--mu)">−14 nap</text><text x="285" y="135" class="lbl" style="fill:var(--mu)">legutóbbi</text></svg>';
  var cm=el("cm"),Yr=s.years||{};
  if(cm&&Object.keys(Yr).length){
   var ys=Object.keys(Yr).sort(),cur=String(s.mtd&&s.mtd.year||ys[ys.length-1]);if(!Yr[cur])cur=ys[ys.length-1];
   var others=ys.filter(function(y){return y!==cur});
   var avg=MS.map(function(_,m){var v=others.map(function(y){return Yr[y][m]}).filter(function(x){return x!=null});return v.length>=3?sum(v)/v.length:null});
   cm.innerHTML=barChart(MS,[{v:avg,c:"var(--ac3)"},{v:Yr[cur],c:"var(--ac)"}]);
  }
 }
 fetch("../forecast.json",{cache:"no-store"}).then(function(r){return r.ok?r.json():Promise.reject()}).then(function(F){
  var fc=F&&F.stations&&F.stations[slug];if(!fc)return;
  el("fc").innerHTML=forecastHtml(fc);el("fcc").hidden=false;
 }).catch(function(){});
})();
