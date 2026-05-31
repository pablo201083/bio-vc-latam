import sys, re
path = r'C:\Users\Pablo A\Desktop\Exploración Semantica y Grafo\pilot\startup-themes.html'
with open(path, encoding='utf-8') as f:
    content = f.read()

# ── Replace cluster rows section ───────────────────────────────────────
# Find the section by markers
START = '  // ── Cluster rows: leaf node + label + stage composition bar + count ──'
END   = '  // ── Funding stage mini-legend (bottom of SVG) ─────────────────────'

i1 = content.find(START)
i2 = content.find(END)
if i1 == -1 or i2 == -1:
    print('FAIL: markers not found', i1, i2)
    sys.exit(1)

new_rows = '''  // ── Cluster rows: ecológico — label + strip de etapa + tokens + count ──
  const MAX_CLUSTER_SIZE=Math.max(...clusters.map(c=>c.startups.length));
  const STAGE_ORDER_BAR=['pre-seed','seed','accelerator','series-a','series-b','series-c','series-c+','growth'];
  const STAGE_LBL={"pre-seed":"Pre-seed","seed":"Seed","accelerator":"Aceleradora",
    "series-a":"Serie A","series-b":"Serie B","series-c":"Serie C","series-c+":"Serie C+","growth":"Growth"};

  clusters.forEach(c=>{
    // Nodo hoja
    el("circle",{cx:X_CLUST,cy:c.y,r:"3",fill:c.color,opacity:"0.90",
      stroke:"rgba(255,255,255,.72)","stroke-width":"0.9"},layerNodes);

    // Label del sub-cluster
    const lblG=el("g",{"data-theme":c.theme},layerLabels);
    const maxLblChars=Math.floor(SUB_W/5.0);
    const lblTxt=c.label.length>maxLblChars?c.label.slice(0,maxLblChars-1)+"…":c.label;
    el("text",{x:X_SUB,y:c.y,"dominant-baseline":"central",
      "font-size":"9.5","font-weight":"600",fill:c.color,opacity:"0.88",
      "font-family":"DM Sans,sans-serif","pointer-events":"none"},lblG).textContent=lblTxt;

    // Grupo de datos (strip + tokens)
    const dataG=el("g",{"data-theme":c.theme},layerDots);
    const stageCounts={};
    c.startups.forEach(s=>{
      const st=s.funding_stage||'unknown';
      stageCounts[st]=(stageCounts[st]||0)+1;
    });
    const total=c.startups.length;

    // ── Strip de etapa: 4px, ancho proporcional al tamaño del cluster ──
    const strip_w=Math.max(4,(total/MAX_CLUSTER_SIZE)*STRIP_W);
    const stripY=c.y-2;
    el("rect",{x:X_STRIP,y:stripY,width:STRIP_W,height:4,
      fill:"rgba(0,0,0,0.06)",rx:"2"},dataG);
    let bx=X_STRIP;
    STAGE_ORDER_BAR.forEach(stage=>{
      if(!stageCounts[stage])return;
      const segW=(stageCounts[stage]/total)*strip_w;
      el("rect",{x:bx,y:stripY,width:Math.max(segW,0.5),height:4,
        fill:STAGE_COL[stage]||"#ccc",opacity:"0.92",rx:"1.5"},dataG);
      bx+=segW;
    });

    // ── Tokens representativos (2 palabras clave del one_liner) ──
    const toks=clusterTokens(c.startups,2);
    if(toks.length){
      el("text",{x:X_STRIP,y:c.y+6,"dominant-baseline":"central",
        "font-size":"7","fill":c.color,opacity:"0.50",
        "font-family":"DM Sans,sans-serif","pointer-events":"none"},dataG)
        .textContent=toks.join(" · ");
    }

    // ── Count: prominente, columna fija ──
    el("text",{x:X_COUNT,y:c.y,"dominant-baseline":"central","text-anchor":"middle",
      "font-size":"11","font-weight":"800",fill:c.color,opacity:"0.62",
      "font-family":"DM Sans,sans-serif","pointer-events":"none"},lblG)
      .textContent=total;

    // Tooltip
    dataG.style.cursor="default";
    dataG.addEventListener("mousemove",e=>{
      e.stopPropagation();
      const rect=svg.parentElement.getBoundingClientRect();
      const px=e.clientX-rect.left, py=e.clientY-rect.top;
      const toLeft=px>rect.width*0.55;
      tt.style.left=toLeft?"":(px+14)+"px";
      tt.style.right=toLeft?(rect.width-px+14)+"px":"";
      tt.style.top=(py-12)+"px";
      const breakdown=STAGE_ORDER_BAR
        .filter(st=>stageCounts[st])
        .map(st=>'<span style="color:'+( STAGE_COL[st]||'#aaa' )+'">'+( STAGE_LBL[st]||st )+' '+stageCounts[st]+'</span>')
        .join(" · ");
      tt.innerHTML='<div class="a-tt-name">'+c.label+'</div>'+
        '<div class="a-tt-theme" style="color:'+c.color+'">'+( SHORT_THEME[c.theme]||c.theme )+'</div>'+
        '<div class="a-tt-body">'+total+' startups · '+breakdown+'</div>';
      tt.classList.add("vis");
    });
    dataG.addEventListener("mouseleave",()=>tt.classList.remove("vis"));
  });

  '''

content = content[:i1] + new_rows + content[i2:]
print('rows: OK')

# ── Update legend: X_BARS → X_STRIP ─────────────────────────────────
content = content.replace('  let lx=X_BARS;\n  el("text",{x:lx', '  let lx=X_STRIP;\n  el("text",{x:lx')
print('legend: OK' if 'let lx=X_STRIP' in content else 'legend: FAIL')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done.')
