(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.ECOSYSTEM_DATA || { nodes: [], edges: [], summary: {} }) : (window.ECOSYSTEM_DATA || { nodes: [], edges: [], summary: {} });
  const svg = document.getElementById("ecosystem-svg");
  const summary = document.getElementById("ecosystem-summary");
  const coverage = document.getElementById("ecosystem-coverage");
  const detail = document.getElementById("ecosystem-detail");
  const badge = document.getElementById("ecosystem-badge");
  const relayoutButton = document.getElementById("ecosystem-relayout");
  const recenterButton = document.getElementById("ecosystem-recenter");
  const zoomInButton = document.getElementById("ecosystem-zoom-in");
  const zoomOutButton = document.getElementById("ecosystem-zoom-out");
  const resetViewButton = document.getElementById("ecosystem-reset-view");

  const WIDTH = 1700;
  const HEIGHT = 980;
  const COLORS = {
    capital: "#25b66a",
    institution: "#ff7b2c",
    founder: "#d96ad9",
    startup: "#7c83fd"
  };
  const EDGE_COLORS = {
    funded_by: "rgba(37, 182, 106, 0.16)",
    researched_at: "rgba(255, 123, 44, 0.18)",
    studied_at: "rgba(255, 123, 44, 0.18)",
    accelerated_at: "rgba(124, 131, 253, 0.16)",
    collaborates_with: "rgba(124, 131, 253, 0.16)",
    other: "rgba(88, 79, 70, 0.10)"
  };

  const nodes = payload.nodes || [];
  const edges = payload.edges || [];

  const state = new Map();
  const nodeGroups = new Map();
  const circles = new Map();
  const halos = new Map();
  const labels = new Map();
  const paths = [];
  let selectedId = null;
  const viewportState = {
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    dragOriginX: 0,
    dragOriginY: 0
  };

  if (!svg || !nodes.length) {
    if (detail) detail.textContent = "No hay datos para renderizar el ecosistema.";
    return;
  }

  function makeSvg(tag, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function edgeColor(kind) {
    return EDGE_COLORS[kind] || EDGE_COLORS.other;
  }

  function gephiColor(node) {
    if (
      typeof node.gephi_r === "number" &&
      typeof node.gephi_g === "number" &&
      typeof node.gephi_b === "number"
    ) {
      const r = Math.round(node.gephi_r * 255);
      const g = Math.round(node.gephi_g * 255);
      const b = Math.round(node.gephi_b * 255);
      return `rgb(${r}, ${g}, ${b})`;
    }
    return COLORS[node.type] || "#7c83fd";
  }

  function cleanValue(value) {
    if (value === undefined || value === null) return "n/d";
    const text = String(value).trim();
    if (!text || text.toLowerCase() === "nan") return "n/d";
    return text;
  }

  function titleCase(text) {
    return String(text || "")
      .replace(/_/g, " ")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function fontSizeFor(node) {
    if (node.size >= 34) return 36;
    if (node.size >= 24) return 24;
    if (node.size >= 18) return 16;
    if (node.size >= 13) return 12;
    if (selectedId === node.id) return 12;
    return 0;
  }

  function edgePath(a, b) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const mx = (a.x + b.x) / 2;
    const my = (a.y + b.y) / 2;
    const norm = Math.max(1, Math.sqrt(dx * dx + dy * dy));
    const curve = Math.min(42, norm * 0.07);
    const cx = mx - (dy / norm) * curve;
    const cy = my + (dx / norm) * curve;
    return `M ${a.x} ${a.y} Q ${cx} ${cy} ${b.x} ${b.y}`;
  }

  function initialPositions() {
    const rawPositions = nodes.map((node) => ({
      id: node.id,
      x: typeof node.gephi_x === "number" ? node.gephi_x : 0,
      y: typeof node.gephi_y === "number" ? node.gephi_y : 0
    }));
    const minX = Math.min(...rawPositions.map((p) => p.x));
    const maxX = Math.max(...rawPositions.map((p) => p.x));
    const minY = Math.min(...rawPositions.map((p) => p.y));
    const maxY = Math.max(...rawPositions.map((p) => p.y));
    const graphWidth = Math.max(1, maxX - minX);
    const graphHeight = Math.max(1, maxY - minY);
    const padding = 80;
    const scale = Math.min((WIDTH - padding * 2) / graphWidth, (HEIGHT - padding * 2) / graphHeight);
    const offsetX = (WIDTH - graphWidth * scale) / 2;
    const offsetY = (HEIGHT - graphHeight * scale) / 2;

    nodes.forEach((node) => {
      const rawX = typeof node.gephi_x === "number" ? node.gephi_x : 0;
      const rawY = typeof node.gephi_y === "number" ? node.gephi_y : 0;
      const x = offsetX + (rawX - minX) * scale;
      const y = offsetY + (rawY - minY) * scale;
      state.set(node.id, { ...node, x, y, baseX: x, baseY: y, vx: 0, vy: 0 });
    });
  }

  initialPositions();

  const viewport = makeSvg("g", {});
  const edgeLayer = makeSvg("g", {});
  const nodeLayer = makeSvg("g", {});
  viewport.append(edgeLayer, nodeLayer);
  svg.append(viewport);

  edges.forEach((edge) => {
    const path = makeSvg("path", {
      fill: "none",
      stroke: edgeColor(edge.kind),
      "stroke-width": edge.kind === "funded_by" ? "1.35" : "1.05",
      "stroke-linecap": "round"
    });
    path.dataset.source = edge.source;
    path.dataset.target = edge.target;
    path.dataset.kind = edge.kind;
    edgeLayer.append(path);
    paths.push(path);
  });

  nodes.forEach((node) => {
    const s = state.get(node.id);
    const group = makeSvg("g", { transform: `translate(${s.x} ${s.y})` });
    group.style.cursor = "pointer";

    const halo = makeSvg("circle", {
      r: s.size * 1.22,
      fill: gephiColor(s),
      opacity: s.size >= 18 ? "0.12" : "0"
    });

    const circle = makeSvg("circle", {
      r: s.size,
      fill: gephiColor(s),
      stroke: "#ffffff",
      "stroke-width": s.size >= 18 ? "3" : "1.3",
      opacity: s.type === "startup" || s.type === "founder" ? "0.88" : "0.94"
    });

    const label = makeSvg("text", {
      "text-anchor": "middle",
      y: s.size >= 18 ? 10 : 4,
      "font-size": String(fontSizeFor(s)),
      "font-family": "Georgia, serif",
      "font-weight": s.size >= 18 ? "700" : "500",
      fill: "#111111",
      stroke: "rgba(255,255,255,0.92)",
      "stroke-width": s.size >= 18 ? "5" : "3",
      "paint-order": "stroke"
    });
    label.textContent = s.label;
    label.setAttribute("opacity", fontSizeFor(s) > 0 ? "1" : "0");

    group.append(halo, circle, label);
    group.addEventListener("click", () => {
      selectedId = node.id;
      updateVisualState();
      renderDetail(node.id);
    });

    nodeLayer.append(group);
    nodeGroups.set(node.id, group);
    halos.set(node.id, halo);
    circles.set(node.id, circle);
    labels.set(node.id, label);
  });

  function render() {
    edges.forEach((edge, i) => {
      const a = state.get(edge.source);
      const b = state.get(edge.target);
      if (!a || !b) return;
      paths[i].setAttribute("d", edgePath(a, b));
    });

    nodes.forEach((node) => {
      const s = state.get(node.id);
      const group = nodeGroups.get(node.id);
      const label = labels.get(node.id);
      const halo = halos.get(node.id);

      group.setAttribute("transform", `translate(${s.x} ${s.y})`);
      label.setAttribute("font-size", String(fontSizeFor(s)));
      label.setAttribute("opacity", fontSizeFor(s) > 0 ? "1" : "0");
      halo.setAttribute("opacity", s.size >= 18 || selectedId === s.id ? "0.12" : "0");
    });
  }

  function updateViewport() {
    viewport.setAttribute("transform", `translate(${viewportState.offsetX} ${viewportState.offsetY}) scale(${viewportState.scale})`);
  }

  function computeBounds() {
    const values = Array.from(state.values());
    const minX = Math.min(...values.map((n) => n.x - n.size * 1.6));
    const maxX = Math.max(...values.map((n) => n.x + n.size * 1.6));
    const minY = Math.min(...values.map((n) => n.y - n.size * 1.6));
    const maxY = Math.max(...values.map((n) => n.y + n.size * 1.6));
    return { minX, maxX, minY, maxY };
  }

  function fitToGraph() {
    const bounds = computeBounds();
    const graphWidth = Math.max(1, bounds.maxX - bounds.minX);
    const graphHeight = Math.max(1, bounds.maxY - bounds.minY);
    const padding = 70;
    viewportState.scale = Math.min((WIDTH - padding * 2) / graphWidth, (HEIGHT - padding * 2) / graphHeight, 1.65);
    viewportState.offsetX = (WIDTH - graphWidth * viewportState.scale) / 2 - bounds.minX * viewportState.scale;
    viewportState.offsetY = (HEIGHT - graphHeight * viewportState.scale) / 2 - bounds.minY * viewportState.scale;
    updateViewport();
  }

  function zoomAt(factor, clientX, clientY) {
    const rect = svg.getBoundingClientRect();
    const px = ((clientX - rect.left) / rect.width) * WIDTH;
    const py = ((clientY - rect.top) / rect.height) * HEIGHT;
    const nextScale = clamp(viewportState.scale * factor, 0.32, 4.5);
    const worldX = (px - viewportState.offsetX) / viewportState.scale;
    const worldY = (py - viewportState.offsetY) / viewportState.scale;
    viewportState.offsetX = px - worldX * nextScale;
    viewportState.offsetY = py - worldY * nextScale;
    viewportState.scale = nextScale;
    updateViewport();
  }

  function animate(duration = 900) {
    const start = performance.now();
    const from = new Map();

    state.forEach((s, id) => {
      const transform = nodeGroups.get(id).getAttribute("transform").match(/translate\(([-\d.]+) ([-\d.]+)\)/);
      from.set(id, {
        x: Number(transform[1]),
        y: Number(transform[2])
      });
    });

    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);

      state.forEach((s, id) => {
        const f = from.get(id);
        const x = f.x + (s.x - f.x) * eased;
        const y = f.y + (s.y - f.y) * eased;
        nodeGroups.get(id).setAttribute("transform", `translate(${x} ${y})`);
      });

      edges.forEach((edge, i) => {
        const aTransform = nodeGroups.get(edge.source).getAttribute("transform").match(/translate\(([-\d.]+) ([-\d.]+)\)/);
        const bTransform = nodeGroups.get(edge.target).getAttribute("transform").match(/translate\(([-\d.]+) ([-\d.]+)\)/);
        paths[i].setAttribute("d", edgePath(
          { x: Number(aTransform[1]), y: Number(aTransform[2]) },
          { x: Number(bTransform[1]), y: Number(bTransform[2]) }
        ));
      });

      if (t < 1) {
        requestAnimationFrame(frame);
      } else {
        render();
        fitToGraph();
      }
    }

    requestAnimationFrame(frame);
  }

  function runLayout(iterations = 520) {
    const values = Array.from(state.values());
    const centerX = WIDTH / 2;
    const centerY = HEIGHT / 2;

    values.forEach((node, index) => {
      const angle = (Math.PI * 2 * index) / Math.max(1, values.length);
      const radius = 230 + (index % 11) * 18;
      node.x = centerX + Math.cos(angle) * radius + (Math.random() - 0.5) * 45;
      node.y = centerY + Math.sin(angle) * radius * 0.72 + (Math.random() - 0.5) * 45;
      node.vx = 0;
      node.vy = 0;
    });

    for (let step = 0; step < iterations; step += 1) {
      values.forEach((n) => { n.vx = 0; n.vy = 0; });

      for (let i = 0; i < values.length; i += 1) {
        for (let j = i + 1; j < values.length; j += 1) {
          const a = values[i];
          const b = values[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist2 = Math.max(170, dx * dx + dy * dy);
          const dist = Math.sqrt(dist2);
          const force = (18000 + (a.size + b.size) * 420) / dist2;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx += fx;
          a.vy += fy;
          b.vx -= fx;
          b.vy -= fy;
        }
      }

      edges.forEach((edge) => {
        const a = state.get(edge.source);
        const b = state.get(edge.target);
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const desired = edge.kind === "funded_by" ? 84 : 128;
        const spring = (dist - desired) * 0.011;
        const fx = (dx / dist) * spring;
        const fy = (dy / dist) * spring;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      });

      values.forEach((node) => {
        const typeAnchorX = node.type === "capital" ? WIDTH * 0.38 : node.type === "institution" ? WIDTH * 0.54 : node.type === "founder" ? WIDTH * 0.60 : WIDTH * 0.68;
        const typeAnchorY = node.type === "capital" ? HEIGHT * 0.43 : node.type === "institution" ? HEIGHT * 0.52 : node.type === "founder" ? HEIGHT * 0.45 : HEIGHT * 0.54;
        node.vx += (typeAnchorX - node.x) * 0.00045;
        node.vy += (typeAnchorY - node.y) * 0.00045;
        node.vx += (centerX - node.x) * 0.00035;
        node.vy += (centerY - node.y) * 0.00035;
        node.x = clamp(node.x + node.vx, 55, WIDTH - 55);
        node.y = clamp(node.y + node.vy, 40, HEIGHT - 40);
      });
    }

    animate();
  }

  function recenter() {
    state.forEach((node) => {
      node.x = node.baseX;
      node.y = node.baseY;
    });
    animate(650);
  }

  function updateVisualState() {
    const activeEdges = new Set();
    if (selectedId) {
      edges.forEach((edge, index) => {
        if (edge.source === selectedId || edge.target === selectedId) {
          activeEdges.add(index);
        }
      });
    }

    edges.forEach((edge, index) => {
      const path = paths[index];
      if (!selectedId) {
        path.setAttribute("opacity", edge.kind === "funded_by" ? "0.58" : "0.4");
        path.setAttribute("stroke-width", edge.kind === "funded_by" ? "1.35" : "1.05");
      } else {
        const active = activeEdges.has(index);
        path.setAttribute("opacity", active ? "0.92" : "0.08");
        path.setAttribute("stroke-width", active ? "2.3" : "0.8");
      }
    });

    nodes.forEach((node) => {
      const circle = circles.get(node.id);
      const halo = halos.get(node.id);
      const label = labels.get(node.id);
      const connected = !selectedId || edges.some((edge) => (edge.source === selectedId && edge.target === node.id) || (edge.target === selectedId && edge.source === node.id));
      const active = selectedId === node.id;

      circle.setAttribute("opacity", !selectedId ? (node.type === "startup" || node.type === "founder" ? "0.88" : "0.94") : (active || connected ? "0.97" : "0.18"));
      circle.setAttribute("stroke-width", active ? "3.5" : (node.size >= 18 ? "2.5" : "1.2"));
      halo.setAttribute("opacity", active || node.size >= 22 ? "0.13" : "0");

      const shouldShowLabel = fontSizeFor(node) > 0 || active || connected;
      label.setAttribute("opacity", shouldShowLabel ? "1" : "0");
    });
  }

  function renderDetail(id) {
    const node = state.get(id);
    const neighborhood = edges.filter((edge) => edge.source === id || edge.target === id);
    const neighbors = neighborhood.map((edge) => {
      const other = state.get(edge.source === id ? edge.target : edge.source);
      return other ? `${other.label} · ${edge.kind}` : null;
    }).filter(Boolean);

    badge.textContent = node.type;
    badge.className = "pill";
    detail.innerHTML = `
      <div class="detail-card">
        <h3>${node.label}</h3>
        <p class="detail-text">Tipo: ${node.type}</p>
        <p class="detail-text">Conexiones: ${neighborhood.length}</p>
        <p class="detail-text">Grado: ${node.degree || neighborhood.length}</p>
        <p class="detail-text">Fuentes: ${node.sources || "n/d"}</p>
        <p class="detail-text">Match con Gephi rico: ${node.structured_match ? "si" : "no"}</p>
        <p class="detail-text">Tipo Gephi: ${cleanValue(node.structured_type)}</p>
        <p class="detail-text">Pais Gephi: ${cleanValue(node.structured_country)}</p>
        <p class="detail-text">Sector Gephi: ${cleanValue(node.structured_sector)}</p>
        ${node.type === "startup" ? `<p class="detail-text">Scope decision: ${titleCase(cleanValue(node.scope_decision || "review"))}</p>` : ""}
        ${node.type === "startup" ? `<p class="detail-text">Scope reason: ${titleCase(cleanValue(node.scope_reason))}</p>` : ""}
        ${node.type === "startup" ? `<p class="detail-text">Macro theme: ${titleCase(cleanValue(node.macro_theme))}</p>` : ""}
      </div>
      <div class="detail-card">
        <h4>Vecindad</h4>
        ${neighbors.slice(0, 14).map((name) => `<div class="alias-item"><div class="item-title">${name}</div></div>`).join("")}
      </div>
    `;
    updateVisualState();
  }

  function renderSummary() {
    const counts = nodes.reduce((acc, node) => {
      acc[node.type] = (acc[node.type] || 0) + 1;
      return acc;
    }, {});
    const sourced = nodes.reduce((acc, node) => {
      String(node.sources || "").split("|").filter(Boolean).forEach((part) => {
        acc[part] = (acc[part] || 0) + 1;
      });
      return acc;
    }, {});

    const coverageStats = payload.coverage || {};
    const summaryStats = payload.summary || {};
    summary.innerHTML = [
      `Nodos totales: ${nodes.length}`,
      `Capital: ${counts.capital || 0}`,
      `Universidades / instituciones: ${counts.institution || 0}`,
      `Founders: ${counts.founder || 0}`,
      `Startups: ${counts.startup || 0}`,
      `Recorte thesis-first compartido con startup themes`,
      `Startups core: ${summaryStats.scope_include_startups || 0}`,
      `Startups review: ${summaryStats.scope_review_startups || 0}`,
      `Startups excluidas fuera de tesis: ${summaryStats.excluded_scope_startups || 0}`,
      `Aristas: ${edges.length}`,
      `Modo: layout Gephi ajustado a viewport`,
      `Controles: rueda, arrastre, +, -, reset`,
      `Fuentes: full_gephi ${sourced.full_gephi || 0}`,
      `Provenance rows: ${summaryStats.provenance_rows || 0}`,
      `Matches con Gephi rico: ${coverageStats.structured_matches_total || 0}`
    ].join("<br>");
  }

  function renderCoverage() {
    if (!coverage) return;

    const coverageStats = payload.coverage || {};
    const unmatchedPreview = coverageStats.unmatched_preview || [];
    const typeCounts = coverageStats.structured_type_counts || [];
    const topTypes = typeCounts
      .slice()
      .sort((a, b) => (b.count || 0) - (a.count || 0))
      .slice(0, 5)
      .map((row) => `${row.type}: ${row.count}`)
      .join("<br>");

    coverage.innerHTML = `
      Extraidos del .gephi rico: ${coverageStats.structured_nodes_total || 0}<br>
      Nodos conectados hoy en el sitio: ${coverageStats.connected_nodes_total || 0}<br>
      Nodos conectados con match estructurado: ${coverageStats.structured_matches_total || 0}<br>
      Nodos del .gephi aun no conectados: ${coverageStats.structured_unmatched_total || 0}<br><br>
      Tipos mas frecuentes en la extraccion:<br>
      ${topTypes || "n/d"}<br><br>
      Muestra de nodos aun fuera de la red conectada:<br>
      ${unmatchedPreview.slice(0, 8).map((row) => `${row.label} · ${cleanValue(row.type)} · ${cleanValue(row.country)}`).join("<br>")}
    `;
  }

  relayoutButton.addEventListener("click", runLayout);
  recenterButton.addEventListener("click", recenter);
  if (zoomInButton) {
    zoomInButton.addEventListener("click", () => {
      const rect = svg.getBoundingClientRect();
      zoomAt(1.18, rect.left + rect.width / 2, rect.top + rect.height / 2);
    });
  }
  if (zoomOutButton) {
    zoomOutButton.addEventListener("click", () => {
      const rect = svg.getBoundingClientRect();
      zoomAt(0.85, rect.left + rect.width / 2, rect.top + rect.height / 2);
    });
  }
  if (resetViewButton) {
    resetViewButton.addEventListener("click", fitToGraph);
  }

  svg.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoomAt(event.deltaY < 0 ? 1.12 : 0.9, event.clientX, event.clientY);
  }, { passive: false });

  svg.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    viewportState.isDragging = true;
    viewportState.dragStartX = event.clientX;
    viewportState.dragStartY = event.clientY;
    viewportState.dragOriginX = viewportState.offsetX;
    viewportState.dragOriginY = viewportState.offsetY;
    svg.style.cursor = "grabbing";
  });

  window.addEventListener("pointermove", (event) => {
    if (!viewportState.isDragging) return;
    viewportState.offsetX = viewportState.dragOriginX + (event.clientX - viewportState.dragStartX);
    viewportState.offsetY = viewportState.dragOriginY + (event.clientY - viewportState.dragStartY);
    updateViewport();
  });

  window.addEventListener("pointerup", () => {
    viewportState.isDragging = false;
    svg.style.cursor = "default";
  });

  render();
  fitToGraph();
  renderSummary();
  renderCoverage();
  const defaultNode = nodes.slice().sort((a, b) => (b.degree || 0) - (a.degree || 0))[0];
  selectedId = defaultNode ? defaultNode.id : null;
  if (selectedId && state.has(selectedId)) {
    renderDetail(selectedId);
  } else {
    updateVisualState();
  }
})();
