function u(c,n){
with(c.parentNode){
	var b=nextSibling;
	var i=parseInt(b.value);
	if(i==n)return;
	b.value=n;
	with(childNodes[i].style){
		color="";
		border="1px solid gray";
		boxShadow="";
		backgroundColor="";
	}
	b=b.nextSibling.nextSibling;
	v_(b.childNodes[n],b.nextSibling);
}
with(c.style){
	color="#369";
	border="1px solid #369";
	boxShadow="-1px -1px 3px #A9BCF5 inset";
	backgroundColor="#CEE3F6";
}
}
function d(w){
var n=parseInt(w/90)+1;
return n*90-w;
}
function v_(p,l){
l.innerHTML=p.innerHTML;
var n=document.createElement("span");
n.style.visibility="hidden";
l.appendChild(n);
var h="";
var w=0;
for(var i=0;i<l.childNodes.length-1;i++)
with(l.childNodes[i]){
	if(typeof(offsetWidth)=="undefined"){
	n.innerText=nodeValue;
	w=n.offsetWidth;
	h+="<span style=\"margin-right:"+d(w)+"px\"class=w>"+nodeValue+" </span>";
	}else if(offsetWidth){
	innerText+=" ";
	w=offsetWidth;
	with(style){
		marginRight=d(w)+"px";
		whiteSpace="nowrap";
	}
	h+="<span>"+outerHTML+" </span>";
	}
}
n.innerText="";
l.innerHTML=h;
}
function w(){
var v=document.getElementsByTagName("div");
for(var i=0;i<v.length;i++)
with(v[i]){
	if(id=="Z1w"){
	var n=parseInt(previousSibling.previousSibling.previousSibling.value);
	v_(previousSibling.childNodes[n],v[i]);
	}
}
}
F=0;
function i(){
if(!F){
F=1;
w();
if(!window.ActiveXObject&&window.addEventListener)
window.addEventListener("resize",w,false);
}
}
if(window.addEventListener)window.addEventListener("load",i,false);
else window.attachEvent("onload",i);
