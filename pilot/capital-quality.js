(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.CAPITAL_QUALITY_DATA || {}) : (window.CAPITAL_QUALITY_DATA || {});
  const summary = payload.summary || {};

  const metricsEl = document.getElementById("capital-quality-metrics");
  const generatedAtEl = document.getElementById("capital-quality-generated-at");
  const readinessEl = document.getElementById("capital-readiness");
  const progressEl = document.getElementById("capital-progress");
  const strategyEl = document.getElementById("capital-strategy");
  const structureEl = document.getElementById("capital-structure");
  const themeCoverageEl = document.getElementById("theme-coverage");
  const countryCoverageEl = document.getElementById("country-coverage");
  const fundQualityEl = document.getElementById("fund-quality");
  const fundRiskEl = document.getElementById("fund-risk");
  const evidenceLadderEl = document.getElementById("evidence-ladder");
  const gapQueueEl = document.getElementById("gap-queue");
  const gapQueueTotalEl = document.getElementById("gap-queue-total");
  const edgeQueueEl = document.getElementById("edge-upgrade-queue");
  const edgeQueueTotalEl = document.getElementById("edge-queue-total");
  const fundSpecificEvidenceQueueEl = document.getElementById("fund-specific-evidence-queue");
  const readinessMeterEl = document.getElementById("capital-readiness-meter");
  const nextActionTitleEl = document.getElementById("capital-next-action-title");
  const nextActionsEl = document.getElementById("capital-next-actions");
  const mainContinentEl = document.getElementById("capital-main-continent");
  const floatingIslandsEl = document.getElementById("capital-floating-islands");
  const componentsEl = document.getElementById("capital-components");
  const evidenceTrackEl = document.getElementById("evidence-ladder-track");

  function clean(value) {
    if (value === undefined || value === null) return "n/d";
    const text = String(value).trim();
    if (!text || text.toLowerCase() === "nan") return "n/d";
    return text;
  }

  function number(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toLocaleString("en-US") : clean(value);
  }

  function pctTone(pct) {
    const value = Number(pct || 0);
    if (value < 45) return "warm";
    if (value < 75) return "muted";
    return "good";
  }

  function titleCase(value) {
    return String(value || "")
      .replace(/[_-]/g, " ")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function renderMetric(label, value, note) {
    if (!metricsEl) return;
    const item = document.createElement("article");
    item.className = "summary-card";
    item.innerHTML = `
      <span class="label">${label}</span>
      <strong class="value">${value}</strong>
      <span class="row-sub">${note || ""}</span>
    `;
    metricsEl.appendChild(item);
  }

  function renderFocusActions() {
    if (!nextActionsEl) return;
    const fundQueue = payload.fund_specific_evidence_queue || [];
    const gapQueue = payload.gap_queue || [];
    const edgeQueue = payload.edge_upgrade_queue || [];
    const topFund = fundQueue[0];
    const topGap = gapQueue[0];
    const topEdge = edgeQueue[0];
    const actions = [
      topFund ? {
        title: `Auditar ${clean(topFund.fund_name)}`,
        note: `${number(topFund.portfolio_include)} startups BIO, ${clean(topFund.specific_edge_pct)}% evidencia especifica.`,
        score: number(topFund.priority_score)
      } : null,
      topGap ? {
        title: `Buscar capital para ${clean(topGap.startup_name)}`,
        note: `${titleCase(clean(topGap.theme))} · ${clean(topGap.country)} · pool ${number(topGap.candidate_fund_pool)}.`,
        score: number(topGap.priority_score)
      } : null,
      topEdge ? {
        title: `Subir edge ${clean(topEdge.fund_name)} -> ${clean(topEdge.startup_name)}`,
        note: `Nivel ${clean(topEdge.evidence_level)} · ${clean(topEdge.evidence_label)} · conf ${clean(topEdge.confidence)}.`,
        score: number(topEdge.priority_score)
      } : null
    ].filter(Boolean);
    if (nextActionTitleEl) {
      nextActionTitleEl.textContent = actions[0]?.title || "Sin prioridades pendientes";
    }
    nextActionsEl.innerHTML = actions.map((action, index) => `
      <article class="focus-item">
        <span class="focus-rank">${index + 1}</span>
        <div>
          <strong>${action.title}</strong>
          <div class="row-sub">${action.note}</div>
        </div>
        <span class="pill">P ${action.score}</span>
      </article>
    `).join("");
  }

  function renderProgress(row) {
    if (!progressEl) return;
    const pct = Number(row.pct || 0);
    const item = document.createElement("article");
    item.className = "progress-row";
    item.innerHTML = `
      <div class="row-top">
        <span>${clean(row.dimension)}</span>
        <span>${number(row.ready)} / ${number(row.total)} - ${pct}%</span>
      </div>
      <div class="bar-track"><div class="bar-fill ${pctTone(pct)}" style="width:${Math.max(2, pct)}%"></div></div>
      <div class="row-sub">${clean(row.note)}</div>
    `;
    progressEl.appendChild(item);
  }

  function renderBar(container, label, value, max, note, tone = "default") {
    if (!container) return;
    const pct = max > 0 ? Math.round((Number(value || 0) / max) * 100) : 0;
    const item = document.createElement("article");
    item.className = "capital-row";
    item.innerHTML = `
      <div class="row-top">
        <span>${label}</span>
        <span>${number(value)}</span>
      </div>
      <div class="bar-track"><div class="bar-fill ${tone}" style="width:${Math.max(2, pct)}%"></div></div>
      <div class="row-sub">${note || ""}</div>
    `;
    container.appendChild(item);
  }

  function renderEvidenceLevel(row) {
    if (!evidenceLadderEl) return;
    const level = Number(row.level || 0);
    const tone = level < 2 ? "low" : level < 3 ? "mid" : "high";
    const item = document.createElement("article");
    item.className = `evidence-level ${tone}`;
    item.innerHTML = `
      <span class="evidence-number">${level}</span>
      <div>
        <strong>${clean(row.label)}</strong>
        <div class="row-sub">${clean(row.next_action)}</div>
      </div>
      <div class="row-sub">${number(row.edges)} edges - ${clean(row.pct)}%</div>
    `;
    evidenceLadderEl.appendChild(item);
  }

  function renderEvidenceTrack() {
    if (!evidenceTrackEl) return;
    evidenceTrackEl.innerHTML = "";
    (payload.evidence_ladder || []).forEach((row) => {
      const level = Number(row.level || 0);
      const tone = level < 2 ? "warm" : level < 3 ? "muted" : "good";
      const item = document.createElement("article");
      item.className = "ladder-segment";
      item.innerHTML = `
        <div class="row-top"><span>N${level}</span><span>${clean(row.pct)}%</span></div>
        <strong>${number(row.edges)}</strong>
        <div class="bar-track"><span class="bar-fill ${tone}" style="width:${Math.max(2, Number(row.pct || 0))}%"></span></div>
        <div class="row-sub">${clean(row.label)}</div>
      `;
      evidenceTrackEl.appendChild(item);
    });
  }

  function renderComponents() {
    if (!componentsEl) return;
    const rows = payload.capital_components || [];
    componentsEl.innerHTML = rows.slice(0, 6).map((row, index) => {
      const title = index === 0 ? "Continente principal" : `Isla ${index}`;
      const names = clean(row.fund_names) || "sin fondo";
      const startups = clean(row.startup_names) || "sin startups";
      return `
        <article class="component-card">
          <div class="row-top"><span>${title}</span><span>${number(row.nodes)} nodos</span></div>
          <strong>${number(row.funds)} fondos · ${number(row.startups)} startups</strong>
          <div class="row-sub"><b>Fondos:</b> ${names}</div>
          <div class="row-sub"><b>Startups:</b> ${startups}</div>
        </article>
      `;
    }).join("");
  }

  function renderQueue(container, rows, kind) {
    if (!container) return;
    container.innerHTML = "";
    rows.slice(0, 30).forEach((row) => {
      const item = document.createElement("article");
      item.className = "queue-item";
      if (kind === "gap") {
        item.innerHTML = `
          <div>
            <strong>${clean(row.startup_name)}</strong>
            <div class="row-sub">${titleCase(clean(row.theme))} - ${clean(row.country)}</div>
          </div>
          <div class="row-sub">${clean(row.suggested_action)} ${clean(row.summary).slice(0, 160)}</div>
          <div class="badge-row">
            <span class="pill warning">Gap</span>
            <span class="pill muted">Pool ${number(row.candidate_fund_pool)}</span>
            <span class="pill">P ${number(row.priority_score)}</span>
          </div>
        `;
      } else {
        item.innerHTML = `
          <div>
            <strong>${clean(row.fund_name)} -> ${clean(row.startup_name)}</strong>
            <div class="row-sub">${titleCase(clean(row.theme))} - ${clean(row.country)}</div>
          </div>
          <div class="row-sub">${clean(row.suggested_action)} Nivel ${clean(row.evidence_level)}: ${clean(row.evidence_label)} - ${clean(row.relation_type)}</div>
          <div class="badge-row">
            <span class="pill warning">L${clean(row.evidence_level)}</span>
            <span class="pill muted">${clean(row.evidence_tier)}</span>
            <span class="pill muted">conf ${clean(row.confidence)}</span>
            <span class="pill">P ${number(row.priority_score)}</span>
          </div>
        `;
      }
      container.appendChild(item);
    });
  }

  if (generatedAtEl) generatedAtEl.textContent = clean(summary.generated_at);
  if (readinessEl) readinessEl.textContent = `${clean(summary.capital_readiness_pct)}%`;
  if (readinessMeterEl) readinessMeterEl.style.width = `${Math.max(2, Math.min(100, Number(summary.capital_readiness_pct || 0)))}%`;
  if (mainContinentEl) mainContinentEl.textContent = `${clean(summary.main_continent_share_pct)}%`;
  if (floatingIslandsEl) floatingIslandsEl.textContent = number(summary.floating_components);
  renderFocusActions();

  renderMetric("Cobertura BIO", `${clean(summary.capital_coverage_pct)}%`, `${number(summary.include_with_capital)} con capital - ${number(summary.include_without_capital)} gaps`);
  renderMetric("Edges publicos", `${clean(summary.public_edge_pct)}%`, `${number(summary.public_investment_edges)} de ${number(summary.investment_edges)} aristas BIO`);
  renderMetric("Edges especificos", `${clean(summary.specific_edge_pct)}%`, `${number(summary.specific_investment_edges)} relaciones startup-fondo`);
  renderMetric("Confianza alta", `${clean(summary.high_confidence_edge_pct)}%`, `${number(summary.high_confidence_edges)} aristas >= 0.90`);
  renderMetric("Fondos activos", `${clean(summary.active_fund_pct)}%`, `${number(summary.active_funds)} fondos con cartera BIO`);
  renderMetric("Coinversion", `${clean(summary.co_investable_pct)}%`, `${number(summary.co_investable_startups)} startups con 2+ fondos`);
  renderMetric("Continente principal", `${clean(summary.main_continent_share_pct)}%`, `${number(summary.largest_component_nodes)} nodos - ${number(summary.floating_components)} islas`);

  (payload.progress || []).forEach(renderProgress);

  const structureRows = [
    ["Cobertura", `${clean(summary.capital_coverage_pct)}%`, "Cuanto del universo BIO tiene al menos una relacion de capital."],
    ["Auditabilidad", `${clean(summary.public_edge_pct)}%`, "Cuantas aristas tienen URL publica y no solo fuente canonica interna."],
    ["Especificidad", `${clean(summary.specific_edge_pct)}%`, "Cuantas aristas tienen evidencia startup-fondo, no solo una URL de fondo."],
    ["Estructura", `${clean(summary.co_investable_pct)}%`, "Cuanto permite leer sindicatos, comunidades y relacion fondo-fondo."],
    ["Continente", `${clean(summary.main_continent_share_pct)}%`, "Que parte del grafo BIO + fondos vive en la mayor componente conectada."],
    ["Concentracion", `${clean(summary.top_fund_share_pct)}%`, "Share del top hub sobre aristas BIO; si sube demasiado, el grafo explica poco."],
    ["Allocators", number(summary.allocator_edges), "Aristas LP/fund-of-funds que explican flujo institucional de capital."]
  ];
  structureRows.forEach(([label, value, note]) => renderBar(structureEl, label, value, 100, note, pctTone(Number(String(value).replace("%", "")))));

  renderComponents();
  renderEvidenceTrack();
  (payload.evidence_ladder || []).forEach(renderEvidenceLevel);

  if (strategyEl) {
    (payload.strategy || []).forEach((row) => {
      const item = document.createElement("article");
      item.className = "strategy-card";
      item.innerHTML = `<strong>${clean(row.step)}</strong><div class="row-sub">${clean(row.description)}</div>`;
      strategyEl.appendChild(item);
    });
  }

  const themeRows = payload.theme_coverage || [];
  const maxThemeGap = Math.max(...themeRows.map((row) => Number(row.gaps || 0)), 1);
  themeRows.slice(0, 10).forEach((row) => {
    renderBar(themeCoverageEl, titleCase(clean(row.theme)), Number(row.gaps || 0), maxThemeGap, `${number(row.mapped)}/${number(row.startups)} mapeadas - ${clean(row.coverage_pct)}% cobertura - ${clean(row.public_edge_pct)}% edges publicos`, "warm");
  });

  const countryRows = payload.country_coverage || [];
  const maxCountryGap = Math.max(...countryRows.map((row) => Number(row.gaps || 0)), 1);
  countryRows.slice(0, 10).forEach((row) => {
    renderBar(countryCoverageEl, clean(row.country), Number(row.gaps || 0), maxCountryGap, `${number(row.mapped)}/${number(row.startups)} mapeadas - ${clean(row.coverage_pct)}% cobertura`, "warm");
  });

  const fundQuality = payload.fund_quality || [];
  fundQuality.slice(0, 12).forEach((row) => {
    renderBar(fundQualityEl, clean(row.fund_name), Number(row.quality_score || 0), 100, `${number(row.portfolio_include)} startups - ${clean(row.source_coverage_pct)}% URL - ${clean(row.specific_edge_pct)}% especifica`, "default");
  });

  const fundRisk = payload.fund_risk || [];
  fundRisk.slice(0, 12).forEach((row) => {
    renderBar(fundRiskEl, clean(row.fund_name), Math.max(1, 100 - Number(row.specific_edge_pct || 0)), 100, `${number(row.portfolio_include)} startups - ${clean(row.source_coverage_pct)}% URL - ${clean(row.specific_edge_pct)}% especifica`, "warm");
  });

  if (gapQueueTotalEl) gapQueueTotalEl.textContent = `${number((payload.gap_queue || []).length)} casos`;
  if (edgeQueueTotalEl) edgeQueueTotalEl.textContent = `${number((payload.edge_upgrade_queue || []).length)} casos`;
  renderQueue(gapQueueEl, payload.gap_queue || [], "gap");
  renderQueue(edgeQueueEl, payload.edge_upgrade_queue || [], "edge");

  if (fundSpecificEvidenceQueueEl) {
    (payload.fund_specific_evidence_queue || []).slice(0, 18).forEach((row) => {
      const item = document.createElement("article");
      item.className = "queue-item";
      item.innerHTML = `
        <div>
          <strong>${clean(row.fund_name)}</strong>
          <div class="row-sub">${number(row.portfolio_include)} startups BIO en cartera</div>
        </div>
        <div class="row-sub">${clean(row.suggested_action)}</div>
        <div class="badge-row">
          <span class="pill warning">${clean(row.specific_edge_pct)}% especifica</span>
          <span class="pill muted">${clean(row.source_coverage_pct)}% URL</span>
          <span class="pill">P ${number(row.priority_score)}</span>
        </div>
      `;
      fundSpecificEvidenceQueueEl.appendChild(item);
    });
  }
})();
