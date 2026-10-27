var Q=Object.defineProperty;var D=(t,a)=>Q(t,"name",{value:a,configurable:!0});import{a1 as S,a4 as z,b2 as Y,g as tt,s as et,a as at,b as rt,q as nt,p as it,_ as p,l as F,c as st,F as ot,I as lt,N as ct,e as ut,z as pt,G as dt}from"./mermaid.core-Gk6hIeGV.js";import{p as gt}from"./chunk-4BX2VUAB-DMwwOL5k.js";import{p as ft}from"./cynefin-VYW2F7L2-DuO0BV_e.js";import{d as _}from"./arc-BF-A-7wP.js";import{o as ht}from"./ordinal-CzvP-XYS.js";import"./index-DZ9lEWqF.js";import"./init-GRbUuopv.js";function mt(t,a){return a<t?-1:a>t?1:a>=t?0:NaN}D(mt,"descending");function vt(t){return t}D(vt,"identity");function xt(){var t=vt,a=mt,f=null,y=S(0),s=S(z),d=S(0);function o(e){var n,l=(e=Y(e)).length,g,h,v=0,c=new Array(l),i=new Array(l),x=+y.apply(this,arguments),w=Math.min(z,Math.max(-z,s.apply(this,arguments)-x)),m,$=Math.min(Math.abs(w)/l,d.apply(this,arguments)),T=$*(w<0?-1:1),u;for(n=0;n<l;++n)(u=i[c[n]=n]=+t(e[n],n,e))>0&&(v+=u);for(a!=null?c.sort(function(A,C){return a(i[A],i[C])}):f!=null&&c.sort(function(A,C){return f(e[A],e[C])}),n=0,h=v?(w-l*T)/v:0;n<l;++n,x=m)g=c[n],u=i[g],m=x+(u>0?u*h:0)+T,i[g]={data:e[g],index:n,value:u,startAngle:x,endAngle:m,padAngle:$};return i}return D(o,"pie"),o.value=function(e){return arguments.length?(t=typeof e=="function"?e:S(+e),o):t},o.sortValues=function(e){return arguments.length?(a=e,f=null,o):a},o.sort=function(e){return arguments.length?(f=e,a=null,o):f},o.startAngle=function(e){return arguments.length?(y=typeof e=="function"?e:S(+e),o):y},o.endAngle=function(e){return arguments.length?(s=typeof e=="function"?e:S(+e),o):s},o.padAngle=function(e){return arguments.length?(d=typeof e=="function"?e:S(+e),o):d},o}D(xt,"d3pie");var St=dt.pie,W={sections:new Map,showData:!1},b=W.sections,G=W.showData,yt=structuredClone(St),wt=p(()=>structuredClone(yt),"getConfig"),At=p(()=>{b=new Map,G=W.showData,pt()},"clear"),Ct=p(({label:t,value:a})=>{if(a<0)throw new Error(`"${t}" has invalid value: ${a}. Negative values are not allowed in pie charts. All slice values must be >= 0.`);b.has(t)||(b.set(t,a),F.debug(`added new section: ${t}, with value: ${a}`))},"addSection"),Dt=p(()=>b,"getSections"),$t=p(t=>{G=t},"setShowData"),Tt=p(()=>G,"getShowData"),V={getConfig:wt,clear:At,setDiagramTitle:it,getDiagramTitle:nt,setAccTitle:rt,getAccTitle:at,setAccDescription:et,getAccDescription:tt,addSection:Ct,getSections:Dt,setShowData:$t,getShowData:Tt},bt=p((t,a)=>{gt(t,a),a.setShowData(t.showData),t.sections.map(a.addSection)},"populateDb"),kt={parse:p(async t=>{const a=await ft("pie",t);F.debug(a),bt(a,V)},"parse")},Et=p(t=>`
  .pieCircle{
    stroke: ${t.pieStrokeColor};
    stroke-width : ${t.pieStrokeWidth};
    opacity : ${t.pieOpacity};
  }
  .pieOuterCircle{
    stroke: ${t.pieOuterStrokeColor};
    stroke-width: ${t.pieOuterStrokeWidth};
    fill: none;
  }
  .pieTitleText {
    text-anchor: middle;
    font-size: ${t.pieTitleTextSize};
    fill: ${t.pieTitleTextColor};
    font-family: ${t.fontFamily};
  }
  .slice {
    font-family: ${t.fontFamily};
    fill: ${t.pieSectionTextColor};
    font-size:${t.pieSectionTextSize};
    // fill: white;
  }
  .legend text {
    fill: ${t.pieLegendTextColor};
    font-family: ${t.fontFamily};
    font-size: ${t.pieLegendTextSize};
  }
`,"getStyles"),Mt=Et,Rt=p(t=>{const a=[...t.values()].reduce((s,d)=>s+d,0),f=[...t.entries()].map(([s,d])=>({label:s,value:d})).filter(s=>s.value/a*100>=1);return xt().value(s=>s.value).sort(null)(f)},"createPieArcs"),zt=p((t,a,f,y)=>{F.debug(`rendering pie chart
`+t);const s=y.db,d=st(),o=ot(s.getConfig(),d.pie),e=40,n=18,l=4,g=450,h=g,v=lt(a),c=v.append("g");c.attr("transform","translate("+h/2+","+g/2+")");const{themeVariables:i}=d;let[x]=ct(i.pieOuterStrokeWidth);x??=2;const w=o.textPosition,m=Math.min(h,g)/2-e,$=_().innerRadius(0).outerRadius(m),T=_().innerRadius(m*w).outerRadius(m*w);c.append("circle").attr("cx",0).attr("cy",0).attr("r",m+x/2).attr("class","pieOuterCircle");const u=s.getSections(),A=Rt(u),C=[i.pie1,i.pie2,i.pie3,i.pie4,i.pie5,i.pie6,i.pie7,i.pie8,i.pie9,i.pie10,i.pie11,i.pie12];let k=0;u.forEach(r=>{k+=r});const N=A.filter(r=>(r.data.value/k*100).toFixed(0)!=="0"),E=ht(C).domain([...u.keys()]);c.selectAll("mySlices").data(N).enter().append("path").attr("d",$).attr("fill",r=>E(r.data.label)).attr("class","pieCircle"),c.selectAll("mySlices").data(N).enter().append("text").text(r=>(r.data.value/k*100).toFixed(0)+"%").attr("transform",r=>"translate("+T.centroid(r)+")").style("text-anchor","middle").attr("class","slice");const U=c.append("text").text(s.getDiagramTitle()).attr("x",0).attr("y",-400/2).attr("class","pieTitleText"),L=[...u.entries()].map(([r,R])=>({label:r,value:R})),M=c.selectAll(".legend").data(L).enter().append("g").attr("class","legend").attr("transform",(r,R)=>{const P=n+l,H=P*L.length/2,J=12*n,K=R*P-H;return"translate("+J+","+K+")"});M.append("rect").attr("width",n).attr("height",n).style("fill",r=>E(r.label)).style("stroke",r=>E(r.label)),M.append("text").attr("x",n+l).attr("y",n-l).text(r=>s.getShowData()?`${r.label} [${r.value}]`:r.label);const j=Math.max(...M.selectAll("text").nodes().map(r=>r?.getBoundingClientRect().width??0)),q=h+e+n+l+j,B=U.node()?.getBoundingClientRect().width??0,X=h/2-B/2,Z=h/2+B/2,I=Math.min(0,X),O=Math.max(q,Z)-I;v.attr("viewBox",`${I} 0 ${O} ${g}`),ut(v,g,O,o.useMaxWidth)},"draw"),Ft={draw:zt},Vt={parser:kt,db:V,renderer:Ft,styles:Mt};export{Vt as diagram};
//# sourceMappingURL=pieDiagram-4H26LBE5-DWvuZXRh.js.map
