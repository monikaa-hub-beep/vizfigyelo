(function(){"use strict";
var KEY="vf_consent",cbs=[];
// Google Analytics 4: put your Measurement ID here (looks like G-ABC123XYZ9). Loaded ONLY after the visitor accepts statistics.
var GA_ID="G-515KG3269B";
function get(){try{return JSON.parse(localStorage.getItem(KEY))}catch(e){return null}}
function fire(){var c=get();if(c)cbs.forEach(function(f){f(c)})}
function set(a){try{localStorage.setItem(KEY,JSON.stringify({necessary:true,analytics:!!a,ts:Date.now()}))}catch(e){}var b=document.getElementById("cb");if(b)b.remove();fire()}
function loadGA(){
 if(!/^G-[A-Z0-9]{6,}$/.test(GA_ID)||GA_ID==="G-XXXXXXXXXX"||window.__vfga)return;
 window.__vfga=1;window.dataLayer=window.dataLayer||[];window.gtag=function(){window.dataLayer.push(arguments)};
 window.gtag("js",new Date());window.gtag("config",GA_ID,{anonymize_ip:true,allow_google_signals:false,allow_ad_personalization_signals:false});
 var g=document.createElement("script");g.async=true;g.src="https://www.googletagmanager.com/gtag/js?id="+GA_ID;document.head.appendChild(g);
}
function stopGA(){window["ga-disable-"+GA_ID]=true}
function applyConsent(c){if(c&&c.analytics){window["ga-disable-"+GA_ID]=false;loadGA()}else stopGA()}
cbs.push(applyConsent);
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
 b.innerHTML='<b>Sütik és tárolás</b><p class="note" style="margin:.4em 0 0">Az oldal a működéséhez szükséges tárolást használja (például ezt a választásodat). A látogatottsági statisztikát (Google Analytics) csak a hozzájárulásoddal kapcsoljuk be. <a href="'+BASE+'adatvedelem.html">Részletek</a></p><div class="row"><button class="btn alt" id="vfno">Csak a szükségesek</button><button class="btn" id="vfyes">Statisztika engedélyezése</button></div>';
 document.body.appendChild(b);
 document.getElementById("vfno").onclick=function(){set(false)};
 document.getElementById("vfyes").onclick=function(){set(true)};
}
document.getElementById("ck").onclick=function(e){e.preventDefault();banner()};
if(!get())banner();else fire();
})();
