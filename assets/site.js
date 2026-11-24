(function(){"use strict";
var KEY="vf_consent",cbs=[];
function get(){try{return JSON.parse(localStorage.getItem(KEY))}catch(e){return null}}
function fire(){var c=get();if(c)cbs.forEach(function(f){f(c)})}
function set(a){try{localStorage.setItem(KEY,JSON.stringify({necessary:true,analytics:!!a,ts:Date.now()}))}catch(e){}var b=document.getElementById("cb");if(b)b.remove();fire()}
// Hook for later: VF.onConsent(c=>{ if(c.analytics){ /* load analytics here */ } })
window.VF={consent:get,onConsent:function(f){cbs.push(f);var c=get();if(c)f(c)}};
// links must work from sub-folders too (eso/…): derive the site root from this script's own address
var BASE=(document.currentScript&&document.currentScript.src||"").replace(/assets\/site\.js.*$/,"");
var NAV=[["index.html","Kezdőlap"],["modszertan.html","Módszertan"],["blog.html","Blog"],["forrasok.html","Források és jogszabályok"],["kapcsolat.html","Kapcsolat"]];
var here=document.body.getAttribute("data-nav")||location.pathname.split("/").pop()||"index.html";
var h=document.createElement("header");h.className="site";
h.innerHTML='<div class="w bar"><a class="brand" href="'+BASE+'index.html">💧 Vízfigyelő</a><button id="mb" aria-label="Menü" aria-expanded="false">☰</button><nav id="nv">'+
 NAV.map(function(n){return '<a href="'+BASE+n[0]+'"'+(n[0]===here?' aria-current="page"':'')+'>'+n[1]+'</a>'}).join("")+'</nav></div>';
document.body.prepend(h);
document.getElementById("mb").onclick=function(){var o=document.getElementById("nv").classList.toggle("open");this.setAttribute("aria-expanded",o)};
var f=document.createElement("footer");f.className="site";
f.innerHTML='<div class="w">© Vízfigyelő · <a href="'+BASE+'adatvedelem.html">Adatvédelem</a> · <a href="#" id="ck">Süti beállítások</a></div>';
document.body.appendChild(f);
function banner(){
 if(document.getElementById("cb"))return;
 var b=document.createElement("div");b.id="cb";b.className="card";b.setAttribute("role","dialog");b.setAttribute("aria-label","Süti beállítások");
 b.innerHTML='<b>Sütik és tárolás</b><p class="note" style="margin:.4em 0 0">Az oldal jelenleg csak a működéséhez szükséges tárolást használja (például ezt a választásodat). Statisztikai sütiket csak a hozzájárulásoddal használnánk. <a href="'+BASE+'adatvedelem.html">Részletek</a></p><div class="row"><button class="btn alt" id="c0">Csak a szükségesek</button><button class="btn" id="c1">Mindet elfogadom</button></div>';
 document.body.appendChild(b);
 document.getElementById("c0").onclick=function(){set(false)};
 document.getElementById("c1").onclick=function(){set(true)};
}
document.getElementById("ck").onclick=function(e){e.preventDefault();banner()};
if(!get())banner();else fire();
})();
