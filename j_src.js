// Copyright (C) 2014 bt4baidu@pdawiki forum
// http://pdawiki.com/forum
//
// This program is a free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3 of the License.
//
// You can get a copy of GNU General Public License along this program
// But you can always get it from http://www.gnu.org/licenses/gpl.txt
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU General Public License for more details.
var v0r=(function(){
Z=null;
var M=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
var D=[null,"F","A","N","B","S","M","T"];
function j_(c,w,o){
if(o){
var h=r_(o);
if(h){
c.parentNode.nextSibling.innerHTML=h;
w[4].push(h);
A(c,"v0r.n(this,Z"+w[0]+")");
if(w[4].length>1)A(c.previousSibling,"v0r.p(this,Z"+w[0]+")");
w[2]+=1;
w[1]+=5;
}
}
}
function g(c,w){
R(c);
var f="";
var p=c.parentNode;
var i=p.parentNode.previousSibling;
if(i.nodeName=="INPUT")
	f="&filter="+i.value;
var d=w[3]?"&domain="+w[3]:"";
var s=document.createElement("script");
var j="j"+Math.floor(Math.random()*1000000);
eval(j+"=function(o){j_(c,w,o);p.removeChild(s);}");
var u="http://corpus.vocabulary.com/api/1.0/examples.json?jsonp="+j+"&query="+w[5]+"&maxResults=3&startOffset="+w[1]+d+f;
s.setAttribute("src",u);
p.appendChild(s);
}
function r_(j){
var h="";
var a=j.result.sentences;
for(var i=0;i<a.length;i++){
var f=a[i].offsets;
var s=a[i].sentence;
s=s.substr(0,f[0])+"<b>"+s.substr(f[0],f[1]-f[0])+"</b>"+s.substr(f[1]);
var v=a[i].volume;
var t=("datePublished"in v)?v.datePublished:v.dateAdded;
var y=t.substr(0,4);
var n=v.corpus.id;
if(n=="LIT"||n=="GUT"){
var d=/^[^\n\r]+/.exec(v.title);
n=d.length>35?' title="'+d.replace(/\"/g,'&quot;')+'">'+d.substr(0,35)+'</i>...':'>'+d+'</i>';
n=v.author+", <i"+n;
}else{
n=v.corpus.name;
if(parseInt(y,10)<=1900){
t=v.dateAdded;
y=t.substr(0,4);
}
y=M[parseInt(t.substr(5,2),10)-1]+" "+t.substr(8,2)+", "+y;
}
h+='<div class=n>'+s+'</div><div class="g r">'+n+'('+y+')</div>';
}
return h;
}
function R(c){
c.setAttribute("onclick","javascript:void(0);");
c.className="e";
}
function A(c,f){
c.setAttribute("onclick",f);
c.className="n";
}
function W(){
var w=window.innerWidth||document.documentElement.clientWidth||document.body.clientWidth;
return parseInt(w*0.8);
}
function z(t){
var g=t.getElementsByTagName("img");
var a=t.getElementsByTagName("audio");
var w=W();
for(var i=0;i<g.length;i++)
if(g[i].width>w)
g[i].width=w;
for(var i=0;i<a.length;i++){
var s=a[i].style;
if(parseInt(s.width,10)>w)
s.width=w;
}
}
function k(){
var l=document.getElementsByTagName("span");
var m=document.getElementsByTagName("div");
for(var i=0;i<l.length;i++){
if(l[i].id=="I9l")
l[i].style.visibility="visible";
}
for(var i=0;i<m.length;i++){
if(m[i].id=="mIq")
m[i].style.display="none";
}
}
function x_(c,f){
var p=c.parentNode;
var h=p.childNodes[0].offsetHeight;
var b=p.childNodes[2];
if(b.offsetHeight>h*6){
b.style.height=h*6+"px";
c.className="i_";
if(f)window.scrollTo(c.offsetLeft,c.offsetTop);
}else{
b.style.height="auto";
c.className="j_";
}
}
function k_(v){
var e = v || window.event;
if(e && e.keyCode==17){
var m=document.getElementsByTagName("img");
for(var i=0;i<m.length;i++)
if(m[i].className=="m"){
m[i].click();
break;
}
}
}
function d(){
if(Z)
return;
Z=new Array();
var f=document.getElementsByTagName("fieldset");
for(var i=0;i<f.length;i++)
if(f[i].className=="a")z(f[i]);
if(!window.ActiveXObject&&window.addEventListener)
window.addEventListener("resize",z,false);
if(window.addEventListener)
document.addEventListener("click",k,false);
else document.attachEvent("onclick",k);
var s="";
var a=["All Sources","Fiction","Arts/Culture","News","Business","Sports","Science/Medicine","Technology"];
for(var i=0;i<a.length;i++)
	s+='<span onclick="v0r.c(this,event,'+i+',Z#)"class=f>'+a[i]+'</span>';
s='<span id="I9l"onclick="v0r.e(this,event)"class="p k">All Sources</span><div id="mIq"class=f>'+s+'</div><span class="p q"><span onclick="javascript:void(0);"style="margin-left:.4em"class=e>&lt;Prev</span><span onclick="v0r.n(this,Z#)"style="text-align:right;border-left:1px solid gray"class=n>Next&gt;</span></span>';
var u=document.getElementsByTagName("div");
var c=0;
var t=[];
for(var i=0;i<u.length;i++){
var d=u[i].id;
if(d=="vUi"){
var w=new Array();
w.push("["+c+"]");
c++;
w.push(0);
w.push(1);
w.push(null);
w.push([u[i].innerHTML]);
Z.push(w);
u[i].innerHTML=s.replace(/Z#/g,"Z"+w[0])+u[i].innerHTML;
}else if(d=="v5A")
t.push(encodeURI(u[i].innerText));
}
for(var i=0;i<Z.length;i++)
Z[i].push(t[i]);
u=document.getElementsByTagName("fieldset");
for(var i=0;i<u.length;i++){
if(u[i].className=="a"){
d=u[i].childNodes;
x_(d[d.length-1],0);
}
}
}
if(!Z){
if(window.addEventListener){
window.addEventListener("load",d,false);
document.addEventListener("keydown",k_,false);
}else{window.attachEvent("onload",d);
document.attachEvent("onkeydown",k_);
}};
return{
o:function(c){
c.style.display="none";
c.nextSibling.style.display="inline";
},
b:function(c){
var p=c.parentNode;
p.style.display="none";
p.previousSibling.style.display="inline-block";
},
x:function(c){
x_(c,1);
},
h:function(c,n){
var p=c.parentNode;
for(var i=0;i<p.childNodes.length;i++)
	p.childNodes[i].style.textDecoration="";
var b=p.nextSibling;
for(var i=0;i<b.childNodes.length;i++){
var s=b.childNodes[i].style;
	if(i==n){
		if(s.display=="block")
			s.display="none";
		else{s.display="block";c.style.textDecoration="underline";}
	}else s.display="none";
}
},
l:function(c,u){
c.style.display="none";
var w=W();
try{
var a=document.createElement("audio");
var p=c.parentNode;
if(c.nextSibling)
p.insertBefore(a,c.nextSibling);
else p.appendChild(a);
a.setAttribute("src",u);
a.setAttribute("controls","true");
var s=a.style;
s.width=50;
s.margin="8px 0";
s.transition="width 2s";
setTimeout(function(){s.width=w<300?w:300;},1000);
a.play();
}catch(e){
}
},
v:function(c,f){
c.removeAttribute("onclick");
var s=c.style;
s.cursor="default";
s.outline="1px dotted gray";
var u="http://s3.amazonaws.com/audio.vocabulary.com/1.0/us/"+f+".mp3";
var b=function(){s.cursor="pointer";s.outline="";c.setAttribute("onclick","v0r.v(this,'"+f+"')");};
var t=setTimeout(b,2000);
try{
with(document.createElement("audio")){
setAttribute("src",u);
onloadstart=function(){clearTimeout(t);};
onended=b;
play();
}
}catch(e){
c.style.outline="";
}
},
n:function(c,w){
if(w[2]<w[4].length){
w[2]+=1;
c.parentNode.nextSibling.innerHTML=w[4][w[2]-1];
A(c.previousSibling,"v0r.p(this,Z"+w[0]+")");
}else{
g(c,w);
}
},
p:function(c,w){
if(w[2]>1){
w[2]-=1;
c.parentNode.nextSibling.innerHTML=w[4][w[2]-1];
A(c.nextSibling,"v0r.n(this,Z"+w[0]+")");
}
if(w[2]<=1){
R(c);
}
},
c:function(c,v,d,w){
v=v?v:window.event;
v.cancelBubble=true;
w[1]=0;
w[2]=0;
w[3]=D[d];
w[4]=[];
var n=c.parentNode;
R(n.nextSibling.childNodes[0]);
n.style.display="none";
var p=n.previousSibling;
p.style.visibility="visible";
p.innerText=c.innerText;
g(n.nextSibling.childNodes[1],w);
},
e:function(c,v){
v=v?v:window.event;
v.cancelBubble=true;
c.nextSibling.style.display="block";
c.style.visibility="hidden";
}}}());
