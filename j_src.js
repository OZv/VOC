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
x=null;
Z=null;
M=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
D=[null,"F","A","N","B","S","M","T"];
function m(c){
with(c.parentNode){
style.display="none";
nextSibling.style.display="block";
}
}
function h(c){
with(c.parentNode){
previousSibling.style.display="block";
style.display="none";
}
}
function g(c,w){
R(c);
x.onload=function(){
if(x.readyState==4&&x.status==200&&x.responseText){
var h=r(x.responseText);
if(h){
with(c.parentNode.nextSibling){
	innerHTML=h;
	w[4].push(h);
}A(c,"n(this,Z"+w[0]+")");
if(w[4].length>1)A(c.previousSibling.previousSibling,"p(this,Z"+w[0]+")");
w[2]+=1;
w[1]+=5;
}
}
};
var f='';
with(c.parentNode.parentNode.previousSibling){
if(nodeName=='INPUT')
	f="&filter="+value;
}
var d=w[3]?'&domain='+w[3]:'';
var u="http://corpus.vocabulary.com/api/1.0/examples.json?query="+w[5]+"&maxResults=5&startOffset="+w[1]+d+f;
if(x instanceof XMLHttpRequest)
x.open("GET",u,true);
else x.open("GET",u);
x.send();
}
function n(c,w){
with(c.parentNode.nextSibling){
if(w[2]<w[4].length){
w[2]+=1;
innerHTML=w[4][w[2]-1];
A(c.previousSibling.previousSibling,"p(this,Z"+w[0]+")");
}else{
g(c,w);
}
}
}
function p(c,w){
with(c.parentNode.nextSibling){
if(w[2]>1){
w[2]-=1;
innerHTML=w[4][w[2]-1];
A(c.nextSibling.nextSibling,"n(this,Z"+w[0]+")");
}
if(w[2]<=1){
R(c);
}
}
}
function c(c,v,d,w){
v=v?v:window.event;
v.cancelBubble=true;
w[1]=0;
w[2]=0;
w[3]=D[d];
w[4]=[];
with(c.parentNode){
R(nextSibling.childNodes[0]);
style.display="none";
with(previousSibling){
	style.visibility="visible";
	innerText=c.innerText;
}
g(nextSibling.childNodes[2],w);
}
}
function e(c,v){
v=v?v:window.event;
v.cancelBubble=true;
with(c){
	nextSibling.style.display="block";
	style.visibility="hidden";
}
}
function r(s){
var j=eval("("+s+")");
var h='';
var a=j.result.sentences;
for(var i=0;i<a.length;i++){
with(a[i]){
var f=offsets;
s=sentence;
s=s.substr(0,f[0])+'<b>'+s.substr(f[0],f[1]-f[0])+'</b>'+s.substr(f[1]);
with(volume){
var t=('datePublished'in volume)?datePublished:dateAdded;
var y=t.substr(0,4);
var n=corpus.id;
if(n=='LIT'||n=='GUT')
n=author+', <i>'+title+'</i>';
else{
n=corpus.name;
with(t)
	y=M[parseInt(substr(5,2))-1]+' '+substr(8,2)+', '+y;
}
}
}
h+='<div class=n>'+s+'</div><div class="g r">'+n+'('+y+')</div>';
}
return h;
}
function R(c){
c.removeAttribute("onclick");
with(c.style){
	color="gray";
	cursor="default";
}
}
function A(c,f){
c.setAttribute("onclick",f);
with(c.style){
	color="";
	cursor="pointer";
}
}
function l(c,f){
R(c);
c.style.outline="1px dotted gray";
var u="http://s3.amazonaws.com/audio.vocabulary.com/1.0/us/"+f+".mp3";
var b=function(){c.style.outline="";A(c,"l(this,'"+f+"')");};
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
}
function W(){
var w=window.innerWidth||document.documentElement.clientWidth||document.body.clientWidth;
return parseInt(w*0.8);
}
function L(c,u){
c.style.display="none";
var w=W();
try{
var a=document.createElement("audio");
c.parentNode.appendChild(a);
with(a){
setAttribute("src",u);
setAttribute("controls","true");
with(style){
width=50;
margin="8px 0";
transition="width 2s";
setTimeout(function(){width=w<300?w:300;},1000);
}
play();
}
}catch(e){
}
}
function z(){
var g=document.getElementsByTagName('img');
var a=document.getElementsByTagName('audio');
var w=W();
for(var i=0;i<g.length;i++)
with(g[i])
if(width>w)
width=w;
for(var i=0;i<a.length;i++)
with(a[i].style)
if(parseInt(width)>w)
width=w;
}
function k(){
if(x){
var l=document.getElementsByTagName('span');
var m=document.getElementsByTagName('div');
for(var i=0;i<l.length;i++){
if(l[i].id=='I9l')
l[i].style.visibility="visible";
}
for(var i=0;i<m.length;i++){
if(m[i].id=='mIq')
m[i].style.display="none";
}
}
}
function d(){
if(Z)
return;
Z=new Array();
z();
if(!window.ActiveXObject&&window.addEventListener)
window.addEventListener("resize",z,false);
if(window.XMLHttpRequest)
x=new XMLHttpRequest();
if(!x||!("withCredentials"in x)){
if(window.XDomainRequest)
x=new XDomainRequest();
else x=null;
}
if(x){
if(window.addEventListener)
document.addEventListener('click',k,false);
else document.attachEvent('onclick',k);
var s='';
var a=["All Sources","Fiction","Arts/Culture","News","Business","Sports","Science/Medicine","Technology"];
for(var i=0;i<a.length;i++)
	s+='<span onclick="c(this,event,'+i+',Z#)"class=f>'+a[i]+'</span>';
s='<span id="I9l"onclick="e(this,event)"class="p k">All Sources</span><div id="mIq"class=f>'+s+'</div><span class="p q"><a href="javascript:void(0);"style="color:gray"class=q>&lt;Prev</a><span class=j>|</span><a href="javascript:void(0);"onclick="n(this,Z#)"class=t>Next&gt;</a></span>';
var u=document.getElementsByTagName('div');
var c=0;
var t=[];
for(var i=0;i<u.length;i++){
var d=u[i].id;
if(d=='vUi'){
var w=new Array();
w.push('['+c+']');
c++;
w.push(0);
w.push(1);
w.push(null);
w.push([u[i].innerHTML]);
Z.push(w);
u[i].innerHTML=s.replace(/Z#/g,"Z"+w[0])+u[i].innerHTML;
}else if(d=='v5A')
t.push(encodeURI(u[i].innerText));
}
for(var i=0;i<Z.length;i++)
Z[i].push(t[i]);
}else{
var m=document.getElementsByTagName('img');
for(var i=0;i<m.length;i++)
if(m[i].onclick)
m[i].style.display="none";
}
}
if(!Z){
if(window.addEventListener)
window.addEventListener('load',d,false);
else window.attachEvent('onload',d);
};
