var I=Object.defineProperty;var $=(e,t)=>I(e,"name",{value:t,configurable:!0});import{s as R,g as F,q as _,p as D,a as E,b as z,_ as l,I as G,z as P,F as C,D as w,G as W,l as B,K as V,e as H}from"./mermaid.core-Gk6hIeGV.js";import{p as j}from"./chunk-4BX2VUAB-DMwwOL5k.js";import{p as q}from"./cynefin-VYW2F7L2-DuO0BV_e.js";import"./index-DZ9lEWqF.js";var m={showLegend:!0,ticks:5,max:null,min:0,graticule:"circle"},b={axes:[],curves:[],options:m},x=structuredClone(b),K=W.radar,N=l(()=>C({...K,...w().radar}),"getConfig"),M=l(()=>x.axes,"getAxes"),U=l(()=>x.curves,"getCurves"),X=l(()=>x.options,"getOptions"),Y=l(e=>{x.axes=e.map(t=>({name:t.name,label:t.label??t.name}))},"setAxes"),Z=l(e=>{x.curves=e.map(t=>({name:t.name,label:t.label??t.name,entries:J(t.entries)}))},"setCurves"),J=l(e=>{if(e[0].axis==null)return e.map(a=>a.value);const t=M();if(t.length===0)throw new Error("Axes must be populated before curves for reference entries");return t.map(a=>{const r=e.find(s=>s.axis?.$refText===a.name);if(r===void 0)throw new Error("Missing entry for axis "+a.label);return r.value})},"computeCurveEntries"),Q=l(e=>{const t=e.reduce((a,r)=>(a[r.name]=r,a),{});x.options={showLegend:t.showLegend?.value??m.showLegend,ticks:t.ticks?.value??m.ticks,max:t.max?.value??m.max,min:t.min?.value??m.min,graticule:t.graticule?.value??m.graticule}},"setOptions"),tt=l(()=>{P(),x=structuredClone(b)},"clear"),f={getAxes:M,getCurves:U,getOptions:X,setAxes:Y,setCurves:Z,setOptions:Q,getConfig:N,clear:tt,setAccTitle:z,getAccTitle:E,setDiagramTitle:D,getDiagramTitle:_,getAccDescription:F,setAccDescription:R},et=l(e=>{j(e,f);const{axes:t,curves:a,options:r}=e;f.setAxes(t),f.setCurves(a),f.setOptions(r)},"populate"),at={parse:l(async e=>{const t=await q("radar",e);B.debug(t),et(t)},"parse")},rt=l((e,t,a,r)=>{const s=r.db,o=s.getAxes(),i=s.getCurves(),n=s.getOptions(),c=s.getConfig(),d=s.getDiagramTitle(),p=G(t),u=st(p,c),g=n.max??Math.max(...i.map(y=>Math.max(...y.entries))),h=n.min,v=Math.min(c.width,c.height)/2;nt(u,o,v,n.ticks,n.graticule),ot(u,o,v,c),A(u,o,i,h,g,n.graticule,c),S(u,i,n.showLegend,c),u.append("text").attr("class","radarTitle").text(d).attr("x",0).attr("y",-c.height/2-c.marginTop)},"draw"),st=l((e,t)=>{const a=t.width+t.marginLeft+t.marginRight,r=t.height+t.marginTop+t.marginBottom,s={x:t.marginLeft+t.width/2,y:t.marginTop+t.height/2};return H(e,r,a,t.useMaxWidth??!0),e.attr("viewBox",`0 0 ${a} ${r}`),e.append("g").attr("transform",`translate(${s.x}, ${s.y})`)},"drawFrame"),nt=l((e,t,a,r,s)=>{if(s==="circle")for(let o=0;o<r;o++){const i=a*(o+1)/r;e.append("circle").attr("r",i).attr("class","radarGraticule")}else if(s==="polygon"){const o=t.length;for(let i=0;i<r;i++){const n=a*(i+1)/r,c=t.map((d,p)=>{const u=2*p*Math.PI/o-Math.PI/2,g=n*Math.cos(u),h=n*Math.sin(u);return`${g},${h}`}).join(" ");e.append("polygon").attr("points",c).attr("class","radarGraticule")}}},"drawGraticule"),ot=l((e,t,a,r)=>{const s=t.length;for(let o=0;o<s;o++){const i=t[o].label,n=2*o*Math.PI/s-Math.PI/2;e.append("line").attr("x1",0).attr("y1",0).attr("x2",a*r.axisScaleFactor*Math.cos(n)).attr("y2",a*r.axisScaleFactor*Math.sin(n)).attr("class","radarAxisLine"),e.append("text").text(i).attr("x",a*r.axisLabelFactor*Math.cos(n)).attr("y",a*r.axisLabelFactor*Math.sin(n)).attr("class","radarAxisLabel")}},"drawAxes");function A(e,t,a,r,s,o,i){const n=t.length,c=Math.min(i.width,i.height)/2;a.forEach((d,p)=>{if(d.entries.length!==n)return;const u=d.entries.map((g,h)=>{const v=2*Math.PI*h/n-Math.PI/2,y=L(g,r,s,c),O=y*Math.cos(v),k=y*Math.sin(v);return{x:O,y:k}});o==="circle"?e.append("path").attr("d",T(u,i.curveTension)).attr("class",`radarCurve-${p}`):o==="polygon"&&e.append("polygon").attr("points",u.map(g=>`${g.x},${g.y}`).join(" ")).attr("class",`radarCurve-${p}`)})}$(A,"drawCurves");l(A,"drawCurves");function L(e,t,a,r){const s=Math.min(Math.max(e,t),a);return r*(s-t)/(a-t)}$(L,"relativeRadius");l(L,"relativeRadius");function T(e,t){const a=e.length;let r=`M${e[0].x},${e[0].y}`;for(let s=0;s<a;s++){const o=e[(s-1+a)%a],i=e[s],n=e[(s+1)%a],c=e[(s+2)%a],d={x:i.x+(n.x-o.x)*t,y:i.y+(n.y-o.y)*t},p={x:n.x-(c.x-i.x)*t,y:n.y-(c.y-i.y)*t};r+=` C${d.x},${d.y} ${p.x},${p.y} ${n.x},${n.y}`}return`${r} Z`}$(T,"closedRoundCurve");l(T,"closedRoundCurve");function S(e,t,a,r){if(!a)return;const s=(r.width/2+r.marginRight)*3/4,o=-(r.height/2+r.marginTop)*3/4,i=20;t.forEach((n,c)=>{const d=e.append("g").attr("transform",`translate(${s}, ${o+c*i})`);d.append("rect").attr("width",12).attr("height",12).attr("class",`radarLegendBox-${c}`),d.append("text").attr("x",16).attr("y",0).attr("class","radarLegendText").text(n.label)})}$(S,"drawLegend");l(S,"drawLegend");var it={draw:rt},lt=l((e,t)=>{let a="";for(let r=0;r<e.THEME_COLOR_LIMIT;r++){const s=e[`cScale${r}`];a+=`
		.radarCurve-${r} {
			color: ${s};
			fill: ${s};
			fill-opacity: ${t.curveOpacity};
			stroke: ${s};
			stroke-width: ${t.curveStrokeWidth};
		}
		.radarLegendBox-${r} {
			fill: ${s};
			fill-opacity: ${t.curveOpacity};
			stroke: ${s};
		}
		`}return a},"genIndexStyles"),ct=l(e=>{const t=V(),a=w(),r=C(t,a.themeVariables),s=C(r.radar,e);return{themeVariables:r,radarOptions:s}},"buildRadarStyleOptions"),dt=l(({radar:e}={})=>{const{themeVariables:t,radarOptions:a}=ct(e);return`
	.radarTitle {
		font-size: ${t.fontSize};
		color: ${t.titleColor};
		dominant-baseline: hanging;
		text-anchor: middle;
	}
	.radarAxisLine {
		stroke: ${a.axisColor};
		stroke-width: ${a.axisStrokeWidth};
	}
	.radarAxisLabel {
		dominant-baseline: middle;
		text-anchor: middle;
		font-size: ${a.axisLabelFontSize}px;
		color: ${a.axisColor};
	}
	.radarGraticule {
		fill: ${a.graticuleColor};
		fill-opacity: ${a.graticuleOpacity};
		stroke: ${a.graticuleColor};
		stroke-width: ${a.graticuleStrokeWidth};
	}
	.radarLegendText {
		text-anchor: start;
		font-size: ${a.legendFontSize}px;
		dominant-baseline: hanging;
	}
	${lt(t,a)}
	`},"styles"),ht={parser:at,db:f,renderer:it,styles:dt};export{ht as diagram};
//# sourceMappingURL=diagram-2AECGRRQ-BNJY2Qrj.js.map
