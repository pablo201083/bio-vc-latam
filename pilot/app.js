function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function normalizeText(value) {
  return (value || "").toLowerCase();
}

async function loadPayload() {
  if (window.PILOT_DATA?.dashboard && window.PILOT_DATA?.entities) {
    const embedded = window.deepRepairData ? window.deepRepairData(window.PILOT_DATA) : window.PILOT_DATA;
    return {
      dashboard: embedded.dashboard,
      entities: embedded.entities || [],
      aliases: embedded.aliases || [],
      edges: embedded.investment_edges || [],
      reviewQueue: embedded.review_queue || []
    };
  }

  async function loadJson(path) {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`No pude cargar ${path}`);
    }
    return response.json();
  }

  const [dashboard, entities, aliases, edges, reviewQueue] = await Promise.all([
    loadJson("./data/dashboard.json"),
    loadJson("./data/entities.json"),
    loadJson("./data/aliases.json"),
    loadJson("./data/investment_edges.json"),
    loadJson("./data/review_queue.json")
  ]);

  const payload = { dashboard, entities, aliases, edges, reviewQueue };
  return window.deepRepairData ? window.deepRepairData(payload) : payload;
}

loadPayload().then(({ dashboard, entities, aliases, edges, reviewQueue }) => {
  const state = {
    dashboard,
    entities,
    aliases,
    edges,
    reviewQueue,
    selectedEntityId: null
  };

  const entityById = new Map(entities.map((entity) => [entity.entity_id, entity]));
  const aliasesByEntityId = aliases.reduce((acc, alias) => {
    if (!acc[alias.entity_id]) acc[alias.entity_id] = [];
    acc[alias.entity_id].push(alias);
    return acc;
  }, {});

  const edgesByEntityId = {};
  for (const edge of edges) {
    if (!edgesByEntityId[edge.investor_id]) edgesByEntityId[edge.investor_id] = [];
    if (!edgesByEntityId[edge.startup_id]) edgesByEntityId[edge.startup_id] = [];
    edgesByEntityId[edge.investor_id].push(edge);
    edgesByEntityId[edge.startup_id].push(edge);
  }

  const summaryGrid = document.getElementById("summary-grid");
  const generatedAt = document.getElementById("generated-at");
  const entityList = document.getElementById("entity-list");
  const entityCount = document.getElementById("entity-count");
  const entityDetail = document.getElementById("entity-detail");
  const detailBadge = document.getElementById("detail-badge");
  const reviewCount = document.getElementById("review-count");
  const reviewList = document.getElementById("review-queue");
  const topInvestors = document.getElementById("top-investors");
  const topStartups = document.getElementById("top-startups");

  const searchInput = document.getElementById("search-input");
  const typeFilter = document.getElementById("type-filter");
  const sourceFilter = document.getElementById("source-filter");

  generatedAt.textContent = dashboard.generated_at;

  const summaryItems = [
    ["Entidades", dashboard.summary.entities_total],
    ["Startups", dashboard.summary.startups_total],
    ["Inversores", dashboard.summary.investors_total],
    ["Aristas de inversion", dashboard.summary.investment_edges_total],
    ["Aliases", dashboard.summary.aliases_total],
    ["Revision", dashboard.summary.review_queue_total]
  ];

  for (const [label, value] of summaryItems) {
    const card = el("article", "summary-card");
    card.append(el("span", "label", label));
    card.append(el("strong", "value", String(value)));
    summaryGrid.append(card);
  }

  function filterEntities() {
    const search = normalizeText(searchInput.value);
    const type = typeFilter.value;
    const source = sourceFilter.value;

    return entities.filter((entity) => {
      const typeOk = type === "all" || entity.entity_type === type;
      const sourcePresence = entity.source_presence || "";
      const sourceOk =
        source === "all" ||
        (source === "nodes_csv" && sourcePresence === "nodes_csv") ||
        (source === "graphml" && sourcePresence === "graphml") ||
        (source === "both" && sourcePresence.includes("nodes_csv") && sourcePresence.includes("graphml"));

      const aliasText = (aliasesByEntityId[entity.entity_id] || []).map((alias) => alias.alias).join(" ");
      const searchTarget = normalizeText([
        entity.canonical_name,
        entity.entity_id,
        entity.source_presence,
        entity.quality_flags,
        aliasText
      ].join(" "));
      const searchOk = !search || searchTarget.includes(search);

      return typeOk && sourceOk && searchOk;
    });
  }

  function renderEntityList() {
    const filtered = filterEntities();
    entityCount.textContent = String(filtered.length);
    entityList.innerHTML = "";

    for (const entity of filtered.slice(0, 120)) {
      const card = el("button", "entity-item");
      card.type = "button";
      if (entity.entity_id === state.selectedEntityId) {
        card.classList.add("active");
      }
      card.append(el("div", "item-title", entity.canonical_name));
      card.append(el("div", "item-meta", `${entity.entity_type} · ${entity.source_presence || "sin fuente"}`));
      if (entity.quality_flags) {
        card.append(el("div", "item-meta", `flags: ${entity.quality_flags}`));
      }
      card.addEventListener("click", () => {
        state.selectedEntityId = entity.entity_id;
        renderEntityList();
        renderEntityDetail();
      });
      entityList.append(card);
    }
  }

  function renderEntityDetail() {
    entityDetail.innerHTML = "";
    if (!state.selectedEntityId) {
      detailBadge.textContent = "Sin seleccion";
      detailBadge.className = "pill muted";
      entityDetail.className = "detail-empty";
      entityDetail.textContent = "Selecciona una entidad para ver perfil, aliases y relaciones.";
      return;
    }

    const entity = entityById.get(state.selectedEntityId);
    const entityAliases = aliasesByEntityId[state.selectedEntityId] || [];
    const relatedEdges = edgesByEntityId[state.selectedEntityId] || [];

    detailBadge.textContent = entity.entity_type;
    detailBadge.className = "pill";
    entityDetail.className = "";

    const wrap = el("div", "detail-grid");

    const header = el("section", "detail-card");
    header.append(el("h3", "", entity.canonical_name));
    header.append(el("p", "detail-text", `ID: ${entity.entity_id}`));
    header.append(el("p", "detail-text", `Fuentes: ${entity.source_presence || "sin dato"} · Confianza: ${entity.confidence_score}`));
    if (entity.quality_flags) {
      header.append(el("p", "detail-text", `Flags: ${entity.quality_flags}`));
    }
    wrap.append(header);

    const statCard = el("section", "detail-card");
    statCard.append(el("h4", "", "Senales rapidas"));
    const statGrid = el("div", "detail-stat-grid");
    const relationshipLabel = entity.entity_type === "investor" ? "Inversiones detectadas" : "Inversores detectados";
    const stats = [
      ["Relaciones", relatedEdges.length],
      ["Aliases", entityAliases.length],
      [relationshipLabel, relatedEdges.length]
    ];
    for (const [label, value] of stats) {
      const stat = el("div", "detail-stat");
      stat.append(el("div", "detail-stat-label", label));
      stat.append(el("div", "detail-stat-value", String(value)));
      statGrid.append(stat);
    }
    statCard.append(statGrid);
    wrap.append(statCard);

    const aliasCard = el("section", "detail-card");
    aliasCard.append(el("h4", "", "Aliases y variantes"));
    if (!entityAliases.length) {
      aliasCard.append(el("p", "detail-text", "No hay aliases registrados para esta entidad."));
    } else {
      for (const alias of entityAliases) {
        const row = el("div", "alias-item");
        row.append(el("div", "item-title", alias.alias));
        row.append(el("div", "item-meta", `${alias.alias_type} · origen: ${alias.source_entity_id}`));
        aliasCard.append(row);
      }
    }
    wrap.append(aliasCard);

    const edgeCard = el("section", "detail-card");
    edgeCard.append(el("h4", "", "Relaciones de inversion"));
    if (!relatedEdges.length) {
      edgeCard.append(el("p", "detail-text", "No hay relaciones de inversion registradas todavia."));
    } else {
      const slice = relatedEdges.slice(0, 24);
      for (const edge of slice) {
        const counterpartId = entity.entity_type === "investor" ? edge.startup_id : edge.investor_id;
        const counterpart = entityById.get(counterpartId);
        const row = el("div", "edge-item");
        row.append(el("div", "item-title", counterpart ? counterpart.canonical_name : counterpartId));
        row.append(el("div", "item-meta", `${edge.source_file} · ${edge.direction_status} · confianza ${edge.confidence_score}`));
        edgeCard.append(row);
      }
    }
    wrap.append(edgeCard);

    entityDetail.append(wrap);
  }

  function renderRankList(container, items, valueLabel) {
    container.innerHTML = "";
    for (const item of items) {
      const row = el("div", "rank-item");
      row.append(el("div", "item-title", item.canonical_name));
      row.append(el("div", "item-meta", `${valueLabel}: ${item.investment_count || item.investor_count} · fuentes: ${item.source_presence}`));
      container.append(row);
    }
  }

  function renderReviewQueue() {
    reviewList.innerHTML = "";
    reviewCount.textContent = String(reviewQueue.length);
    for (const item of reviewQueue) {
      const row = el("div", "review-item");
      row.append(el("div", "item-title", `${item.canonical_name} ↔ ${item.alias_name}`));
      row.append(el("div", "item-meta", `${item.review_type} · confianza ${item.merge_confidence}`));
      row.append(el("div", "item-meta", item.notes));
      reviewList.append(row);
    }
  }

  searchInput.addEventListener("input", renderEntityList);
  typeFilter.addEventListener("change", renderEntityList);
  sourceFilter.addEventListener("change", renderEntityList);

  renderRankList(topInvestors, dashboard.top_investors, "inversiones");
  renderRankList(topStartups, dashboard.top_startups, "inversores");
  renderReviewQueue();
  state.selectedEntityId = entities[0]?.entity_id || null;
  renderEntityList();
  renderEntityDetail();
}).catch((error) => {
  document.body.innerHTML = `<pre style="padding:24px;font-family:monospace">${error.message}</pre>`;
});
