(function () {
  const pilotData = window.deepRepairData ? window.deepRepairData(window.PILOT_DATA || {}) : (window.PILOT_DATA || {});
  const payload = pilotData.graph;
  const allEntities = pilotData.entities || [];
  const allAliases = pilotData.aliases || [];

  const svg = document.getElementById("graph-svg");
  const detail = document.getElementById("graph-detail");
  const detailBadge = document.getElementById("graph-detail-badge");
  const summary = document.getElementById("graph-summary");
  const runLayoutButton = document.getElementById("run-layout");
  const resetLayoutButton = document.getElementById("reset-layout");

  if (!payload || !svg) {
    if (detail) detail.textContent = "No pude cargar los datos del grafo.";
    return;
  }

  const WIDTH = 1400;
  const HEIGHT = 900;
  const entityById = new Map(allEntities.map((entity) => [entity.entity_id, entity]));
  const aliasesByEntityId = allAliases.reduce((acc, alias) => {
    if (!acc[alias.entity_id]) acc[alias.entity_id] = [];
    acc[alias.entity_id].push(alias.alias);
    return acc;
  }, {});

  const investorNodes = payload.nodes.filter((node) => node.type === "investor");
  const startupNodes = payload.nodes.filter((node) => node.type === "startup");

  const nodeState = new Map();
  const nodeElements = new Map();
  const labelElements = new Map();
  const edgeElements = [];

  function makeSvg(tag, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function edgePath(source, target) {
    const dx = Math.abs(target.x - source.x) * 0.35;
    return `M ${source.x} ${source.y} C ${source.x + dx} ${source.y}, ${target.x - dx} ${target.y}, ${target.x} ${target.y}`;
  }

  function buildInitialPositions() {
    const investorX = 240;
    const startupX = 1120;
    const topPadding = 70;
    const investorGap = Math.max(44, Math.floor(760 / Math.max(1, investorNodes.length)));
    const startupGap = Math.max(22, Math.floor(760 / Math.max(1, startupNodes.length)));

    investorNodes.forEach((node, index) => {
      nodeState.set(node.id, {
        ...node,
        x: investorX,
        y: topPadding + index * investorGap,
        vx: 0,
        vy: 0,
        baseX: investorX,
        baseY: topPadding + index * investorGap
      });
    });

    startupNodes.forEach((node, index) => {
      nodeState.set(node.id, {
        ...node,
        x: startupX,
        y: topPadding + index * startupGap,
        vx: 0,
        vy: 0,
        baseX: startupX,
        baseY: topPadding + index * startupGap
      });
    });
  }

  function renderSummary(mode) {
    summary.innerHTML = [
      `Generado: ${payload.generated_at}`,
      `Descripción: ${payload.description}`,
      `Inversores: ${investorNodes.length}`,
      `Startups: ${startupNodes.length}`,
      `Aristas: ${payload.edges.length}`,
      `Modo: ${mode}`
    ].join("<br>");
  }

  buildInitialPositions();
  renderSummary("bipartita inicial");

  const edgeLayer = makeSvg("g", {});
  const nodeLayer = makeSvg("g", {});
  const labelLayer = makeSvg("g", {});
  svg.append(edgeLayer, nodeLayer, labelLayer);

  payload.edges.forEach((edge) => {
    const path = makeSvg("path", {
      fill: "none",
      stroke: "rgba(110, 98, 83, 0.28)",
      "stroke-width": "1.6"
    });
    path.dataset.source = edge.source;
    path.dataset.target = edge.target;
    edgeLayer.append(path);
    edgeElements.push(path);
  });

  function render() {
    payload.edges.forEach((edge, index) => {
      const source = nodeState.get(edge.source);
      const target = nodeState.get(edge.target);
      if (!source || !target) return;
      edgeElements[index].setAttribute("d", edgePath(source, target));
    });

    payload.nodes.forEach((node) => {
      const state = nodeState.get(node.id);
      const circle = nodeElements.get(node.id);
      const label = labelElements.get(node.id);
      if (!state || !circle || !label) return;

      const radius = node.type === "investor"
        ? Math.max(7, Math.min(16, 7 + Number(node.degree) / 18))
        : Math.max(4, Math.min(11, 4 + Number(node.degree) / 6));

      circle.setAttribute("cx", state.x);
      circle.setAttribute("cy", state.y);
      circle.setAttribute("r", radius);
      label.setAttribute("x", state.type === "investor" ? state.x - radius - 10 : state.x + radius + 10);
      label.setAttribute("y", state.y + 4);
      label.setAttribute("text-anchor", state.type === "investor" ? "end" : "start");
    });
  }

  function renderDetail(nodeId) {
    const entity = entityById.get(nodeId);
    const graphNode = nodeState.get(nodeId);
    if (!entity || !graphNode) {
      detail.textContent = "No encontré detalles para este nodo.";
      return;
    }

    const connected = payload.edges.filter((edge) => edge.source === nodeId || edge.target === nodeId);
    const aliases = aliasesByEntityId[nodeId] || [];

    detailBadge.textContent = graphNode.type;
    detailBadge.className = "pill";

    const counterpartHtml = connected.slice(0, 18).map((edge) => {
      const counterpartId = edge.source === nodeId ? edge.target : edge.source;
      const counterpart = entityById.get(counterpartId);
      return `<div class="edge-item"><div class="item-title">${counterpart ? counterpart.canonical_name : counterpartId}</div><div class="item-meta">${edge.source_file} · confianza ${edge.confidence_score}</div></div>`;
    }).join("");

    detail.innerHTML = `
      <div class="detail-card">
        <h3>${entity.canonical_name}</h3>
        <p class="detail-text">ID: ${entity.entity_id}</p>
        <p class="detail-text">Fuentes: ${entity.source_presence || "sin dato"} · Confianza: ${entity.confidence_score}</p>
        ${entity.quality_flags ? `<p class="detail-text">Flags: ${entity.quality_flags}</p>` : ""}
      </div>
      <div class="detail-card">
        <h4>Aliases</h4>
        ${aliases.length ? aliases.map((alias) => `<div class="alias-item"><div class="item-title">${alias}</div></div>`).join("") : `<p class="detail-text">Sin aliases registrados.</p>`}
      </div>
      <div class="detail-card">
        <h4>Relaciones (${connected.length})</h4>
        ${connected.length ? counterpartHtml : `<p class="detail-text">Sin relaciones en este subgrafo.</p>`}
      </div>
    `;

    edgeElements.forEach((path) => {
      const active = path.dataset.source === nodeId || path.dataset.target === nodeId;
      path.setAttribute("stroke", active ? "rgba(15,118,110,0.58)" : "rgba(110, 98, 83, 0.12)");
      path.setAttribute("stroke-width", active ? "2.8" : "1.2");
    });
  }

  payload.nodes.forEach((node) => {
    const state = nodeState.get(node.id);
    const color = node.type === "investor" ? "#0f766e" : "#9a3412";
    const circle = makeSvg("circle", {
      cx: state.x,
      cy: state.y,
      fill: color,
      stroke: "#fffaf1",
      "stroke-width": "1.5",
      opacity: "0.92"
    });
    circle.style.cursor = "pointer";
    circle.addEventListener("click", () => renderDetail(node.id));

    const label = makeSvg("text", {
      x: state.x,
      y: state.y,
      "font-size": node.type === "investor" ? "13" : "11",
      "font-family": "Georgia, serif",
      fill: "#43362a"
    });
    label.textContent = node.label;

    nodeLayer.append(circle);
    labelLayer.append(label);
    nodeElements.set(node.id, circle);
    labelElements.set(node.id, label);
  });

  function animateToTargets(duration = 700, modeLabel = "force atlas") {
    const start = performance.now();
    const from = new Map();

    nodeState.forEach((state, id) => {
      from.set(id, {
        x: Number(nodeElements.get(id).getAttribute("cx")),
        y: Number(nodeElements.get(id).getAttribute("cy"))
      });
    });

    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);

      nodeState.forEach((state, id) => {
        const source = from.get(id);
        const x = source.x + (state.x - source.x) * eased;
        const y = source.y + (state.y - source.y) * eased;
        const circle = nodeElements.get(id);
        const label = labelElements.get(id);
        const radius = Number(circle.getAttribute("r")) || 8;

        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        label.setAttribute("x", state.type === "investor" ? x - radius - 10 : x + radius + 10);
        label.setAttribute("y", y + 4);
      });

      payload.edges.forEach((edge, index) => {
        const sourceCircle = nodeElements.get(edge.source);
        const targetCircle = nodeElements.get(edge.target);
        edgeElements[index].setAttribute("d", edgePath(
          { x: Number(sourceCircle.getAttribute("cx")), y: Number(sourceCircle.getAttribute("cy")) },
          { x: Number(targetCircle.getAttribute("cx")), y: Number(targetCircle.getAttribute("cy")) }
        ));
      });

      if (t < 1) {
        requestAnimationFrame(tick);
      } else {
        renderSummary(modeLabel);
        render();
      }
    }

    requestAnimationFrame(tick);
  }

  function resetBipartiteLayout() {
    nodeState.forEach((state) => {
      state.x = state.baseX;
      state.y = state.baseY;
      state.vx = 0;
      state.vy = 0;
    });
    animateToTargets(550, "bipartita");
  }

  function runForceAtlasLikeLayout(iterations = 360) {
    const states = Array.from(nodeState.values());
    const centerX = WIDTH / 2;
    const centerY = HEIGHT / 2;
    const repulsion = 70000;
    const attraction = 0.014;
    const gravity = 0.0012;

    states.forEach((state, index) => {
      const angle = (Math.PI * 2 * index) / Math.max(1, states.length);
      const radius = 180 + (index % 7) * 18;
      state.x = centerX + Math.cos(angle) * radius + (Math.random() - 0.5) * 40;
      state.y = centerY + Math.sin(angle) * radius + (Math.random() - 0.5) * 40;
      state.vx = 0;
      state.vy = 0;
    });

    for (let step = 0; step < iterations; step += 1) {
      for (const a of states) {
        a.vx = 0;
        a.vy = 0;
      }

      for (let i = 0; i < states.length; i += 1) {
        for (let j = i + 1; j < states.length; j += 1) {
          const a = states[i];
          const b = states[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist2 = Math.max(120, dx * dx + dy * dy);
          const dist = Math.sqrt(dist2);
          const force = repulsion / dist2;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx += fx;
          a.vy += fy;
          b.vx -= fx;
          b.vy -= fy;
        }
      }

      for (const edge of payload.edges) {
        const source = nodeState.get(edge.source);
        const target = nodeState.get(edge.target);
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const desired = 85;
        const spring = (dist - desired) * attraction;
        const fx = (dx / dist) * spring;
        const fy = (dy / dist) * spring;
        source.vx += fx;
        source.vy += fy;
        target.vx -= fx;
        target.vy -= fy;
      }

      for (const state of states) {
        state.vx += (centerX - state.x) * gravity;
        state.vy += (centerY - state.y) * gravity;
        state.x = clamp(state.x + state.vx, 50, WIDTH - 50);
        state.y = clamp(state.y + state.vy, 30, HEIGHT - 30);
      }
    }

    animateToTargets(850, "force atlas");
  }

  if (runLayoutButton) {
    runLayoutButton.addEventListener("click", () => {
      runLayoutButton.disabled = true;
      runLayoutButton.textContent = "Ordenando...";
      setTimeout(() => {
        runForceAtlasLikeLayout();
        runLayoutButton.disabled = false;
        runLayoutButton.textContent = "Reordenar con Force Atlas";
      }, 10);
    });
  }

  if (resetLayoutButton) {
    resetLayoutButton.addEventListener("click", resetBipartiteLayout);
  }

  render();
  if (payload.nodes.length) renderDetail(payload.nodes[0].id);

  setTimeout(() => {
    runForceAtlasLikeLayout();
  }, 180);
})();
