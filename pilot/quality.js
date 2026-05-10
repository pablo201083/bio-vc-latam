(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.QUALITY_DASHBOARD_DATA || {}) : (window.QUALITY_DASHBOARD_DATA || {});
  const summary = payload.summary || {};

  const metrics = document.getElementById("quality-metrics");
  const overallReadiness = document.getElementById("overall-readiness");
  const curationProgress = document.getElementById("curation-progress");
  const curationWorkstreams = document.getElementById("curation-workstreams");
  const statusStrip = document.getElementById("quality-status-strip");
  const readinessDimensions = document.getElementById("readiness-dimensions");
  const bands = document.getElementById("quality-bands");
  const scope = document.getElementById("scope-counts");
  const flags = document.getElementById("top-flags");
  const sourceTrust = document.getElementById("source-trust");
  const validationList = document.getElementById("validation-list");
  const validationTotal = document.getElementById("validation-total");
  const semanticThemes = document.getElementById("semantic-themes");
  const bioLensTags = document.getElementById("bio-lens-tags");
  const domainTags = document.getElementById("domain-tags");
  const bestQuality = document.getElementById("best-quality");
  const reviewQueue = document.getElementById("review-queue");
  const generatedAt = document.getElementById("quality-generated-at");
  const universe = document.getElementById("quality-universe");
  const reviewTotal = document.getElementById("review-total");

  function clean(value) {
    if (value === undefined || value === null) return "n/d";
    const text = String(value).trim();
    if (!text || text.toLowerCase() === "nan") return "n/d";
    return text;
  }

  function titleCase(text) {
    return String(text || "")
      .replace(/[_-]/g, " ")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function toNumber(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  }

  function pctTone(pct) {
    if (pct < 65) return "warm";
    if (pct < 85) return "muted";
    return "default";
  }

  function renderMetric(label, value, note = "") {
    if (!metrics) return;
    const article = document.createElement("article");
    article.className = "summary-card";
    article.innerHTML = `
      <span class="label">${label}</span>
      <strong class="value">${value}</strong>
      ${note ? `<span class="table-sub">${note}</span>` : ""}
    `;
    metrics.appendChild(article);
  }

  function renderStatus(label, value, note) {
    if (!statusStrip) return;
    const item = document.createElement("article");
    item.className = "status-chip";
    item.innerHTML = `
      <span>${label}</span>
      <strong>${value}</strong>
      <div class="table-sub">${note}</div>
    `;
    statusStrip.appendChild(item);
  }

  function renderBar(container, label, count, max, tone = "default") {
    if (!container) return;
    const row = document.createElement("div");
    row.className = "bar-row";
    const pct = max > 0 ? Math.round((count / max) * 100) : 0;
    row.innerHTML = `
      <div class="bar-head">
        <span>${label}</span>
        <span>${count}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill ${tone}" style="width:${Math.max(2, pct)}%"></div>
      </div>
    `;
    container.appendChild(row);
  }

  function renderProgressRow(container, row) {
    if (!container) return;
    const pct = toNumber(row.pct);
    const item = document.createElement("article");
    item.className = "progress-row";
    item.innerHTML = `
      <div class="progress-title">
        <span>${clean(row.dimension)}</span>
        <span>${clean(row.ready)} / ${clean(row.total)} · ${pct}%</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill ${pctTone(pct)}" style="width:${Math.max(2, pct)}%"></div>
      </div>
      <div class="progress-note">${clean(row.note)}</div>
    `;
    container.appendChild(item);
  }

  function renderWorkstream(row) {
    if (!curationWorkstreams) return;
    const item = document.createElement("article");
    item.className = "workstream-card";
    item.innerHTML = `
      <div class="table-sub">${titleCase(clean(row.workstream))}</div>
      <strong>${clean(row.count)}</strong>
      <div>${clean(row.purpose)}</div>
      <div class="table-sub">${clean(row.output)}</div>
    `;
    curationWorkstreams.appendChild(item);
  }

  function renderTableItem(container, title, right, subtitle, chips) {
    if (!container) return;
    const item = document.createElement("div");
    item.className = "table-item";
    item.innerHTML = `
      <div class="table-topline">
        <div class="item-title">${title}</div>
        <div class="pill muted">${right}</div>
      </div>
      <div class="table-sub">${subtitle}</div>
      <div class="badge-row">${chips.join("")}</div>
    `;
    container.appendChild(item);
  }

  function renderQueueItem(row) {
    if (!reviewQueue) return;
    const item = document.createElement("article");
    item.className = "queue-item";
    const confidence = clean(row.semantic_confidence || row.semantic_single_confidence);
    const quality = clean(row.quality_band || row.data_quality_score_10);
    item.innerHTML = `
      <div>
        <strong>${clean(row.startup_name)}</strong>
        <div class="queue-meta">${titleCase(clean(row.current_theme || row.semantic_single_theme))}</div>
      </div>
      <div class="queue-meta">${clean(row.suggested_action || row.missing_signals || row.curation_reasons)}</div>
      <div class="badge-row">
        <span class="pill warning">${titleCase(confidence)}</span>
        <span class="pill muted">${titleCase(quality)}</span>
        <span class="pill muted">${titleCase(clean(row.source_type))}</span>
      </div>
    `;
    reviewQueue.appendChild(item);
  }

  if (generatedAt) generatedAt.textContent = clean(summary.generated_at);
  if (universe) universe.textContent = `${clean(summary.include)} include · ${clean(summary.exclude)} exclude`;
  if (overallReadiness) overallReadiness.textContent = `${clean(summary.overall_readiness_pct)}%`;

  renderMetric("Include BIO", clean(summary.include), `${clean(summary.exclude)} fuera del universo`);
  renderMetric("Reviewed", `${clean(summary.include_reviewed_pct)}%`, `${clean(summary.include_seeded)} seeded restantes`);
  renderMetric("Alta calidad", `${clean(summary.include_high_quality_pct)}%`, `${clean(summary.include_high_quality)} include high`);
  renderMetric("Semantica estable", `${clean(summary.semantic_high_confidence_pct)}%`, `${clean(summary.semantic_low_confidence)} low confidence`);
  renderMetric("Frontera revisada", `${clean(summary.exclude_reviewed_pct)}%`, `${clean(summary.exclude_reviewed)} excludes reviewed`);

  renderStatus("Score promedio", clean(summary.avg_quality_score), "Promedio 0-10 de toda la base");
  renderStatus("Fuente include", `${clean(summary.include_source_url_coverage_pct)}%`, "URL externa en universo BIO");
  renderStatus("Fragile total", clean(summary.fragile_quality), "Casos aun debiles en toda la base");
  renderStatus("Pipeline", `${clean(summary.validation_errors)} errores`, `${clean(summary.validation_warnings)} warnings`);

  (payload.curation_progress || []).forEach((row) => renderProgressRow(curationProgress, row));
  (payload.curation_workstreams || []).forEach(renderWorkstream);

  (payload.readiness_dimensions || []).forEach((row) => {
    if (!readinessDimensions) return;
    const card = document.createElement("article");
    card.className = "readiness-card";
    const pct = toNumber(row.pct);
    card.innerHTML = `
      <div class="bar-head">
        <span>${clean(row.dimension)}</span>
        <span>${clean(row.ready)} / ${clean(row.total)}</span>
      </div>
      <strong>${pct}%</strong>
      <div class="bar-track">
        <div class="bar-fill ${pctTone(pct)}" style="width:${Math.max(2, pct)}%"></div>
      </div>
      <div class="table-sub">${clean(row.note)}</div>
    `;
    readinessDimensions.appendChild(card);
  });

  const qualityBands = payload.quality_bands || [];
  const maxBand = Math.max(...qualityBands.map((row) => Number(row.count || 0)), 1);
  qualityBands.forEach((row) => {
    const tone = row.band === "poor" || row.band === "fragile" ? "warm" : (row.band === "medium" ? "muted" : "default");
    renderBar(bands, titleCase(row.band), Number(row.count || 0), maxBand, tone);
  });

  const scopeCounts = payload.scope_counts || [];
  const maxScope = Math.max(...scopeCounts.map((row) => Number(row.count || 0)), 1);
  scopeCounts.forEach((row) => {
    const tone = row.scope === "exclude" ? "warm" : (row.scope === "review" ? "muted" : "default");
    renderBar(scope, titleCase(row.scope), Number(row.count || 0), maxScope, tone);
  });

  const topFlags = payload.top_flags || [];
  const maxFlag = Math.max(...topFlags.map((row) => Number(row.count || 0)), 1);
  topFlags.forEach((row) => renderBar(flags, titleCase(row.flag), Number(row.count || 0), maxFlag, "warm"));

  const sourceTrustRows = payload.source_trust || [];
  const maxTrust = Math.max(...sourceTrustRows.map((row) => Number(row.include_count || 0)), 1);
  sourceTrustRows.forEach((row) => {
    const tone = Number(row.trust_tier || 0) > 2 ? "warm" : "default";
    renderBar(sourceTrust, `Tier ${clean(row.trust_tier)} · ${clean(row.source_count)} fuentes`, Number(row.include_count || 0), maxTrust, tone);
  });

  const validationRows = payload.validation || [];
  const actionable = validationRows.filter((row) => row.status !== "pass");
  if (validationTotal) validationTotal.textContent = String(actionable.length);
  (actionable.length ? actionable : validationRows.slice(0, 4)).forEach((row) => {
    const tone = row.status === "fail" ? "warning" : "muted";
    renderTableItem(
      validationList,
      clean(row.check_id),
      clean(row.status),
      `${clean(row.message)} (${clean(row.count)})`,
      [`<span class="pill ${tone}">${clean(row.severity)}</span>`]
    );
  });

  const semanticCategories = payload.semantic_categories || [];
  const maxTheme = Math.max(...semanticCategories.map((row) => Number(row.count || 0)), 1);
  semanticCategories.forEach((row) => renderBar(semanticThemes, titleCase(clean(row.theme)), Number(row.count || 0), maxTheme, "default"));

  const strategicTags = payload.strategic_tag_counts || {};
  const bioLensRows = strategicTags.bio_lens || [];
  const maxBioLens = Math.max(...bioLensRows.map((row) => Number(row.count || 0)), 1);
  bioLensRows.forEach((row) => renderBar(bioLensTags, titleCase(clean(row.tag)), Number(row.count || 0), maxBioLens, "default"));

  const domainRows = strategicTags.domain || [];
  const maxDomain = Math.max(...domainRows.map((row) => Number(row.count || 0)), 1);
  domainRows.forEach((row) => renderBar(domainTags, titleCase(clean(row.tag)), Number(row.count || 0), maxDomain, "muted"));

  (payload.best_quality || []).forEach((row) => {
    renderTableItem(
      bestQuality,
      clean(row.startup_name),
      `Score ${clean(row.data_quality_score_10)}`,
      `${titleCase(clean(row.semantic_single_theme))} · ${titleCase(clean(row.scope_decision))}`,
      [
        `<span class="pill">${titleCase(clean(row.scope_decision))}</span>`,
        `<span class="pill muted">${titleCase(clean(row.semantic_single_theme))}</span>`
      ]
    );
  });

  const reviews = (payload.curation_queue && payload.curation_queue.length) ? payload.curation_queue : (payload.review_queue || []);
  if (reviewTotal) reviewTotal.textContent = String(reviews.length);
  reviews.forEach(renderQueueItem);
})();
