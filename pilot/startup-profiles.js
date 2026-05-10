(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.STARTUP_PROFILES_DATA || {}) : (window.STARTUP_PROFILES_DATA || {});
  const themeSystem = window.THEME_SYSTEM || null;
  const semanticSingle = window.deepRepairData ? window.deepRepairData(window.SEMANTIC_SINGLE_LEVEL_DATA || {}) : (window.SEMANTIC_SINGLE_LEVEL_DATA || {});
  const semanticAssignments = (semanticSingle.recommended && semanticSingle.recommended.assignmentsById) || {};
  const profiles = payload.profiles || [];
  const queue = payload.queue || [];
  const summary = payload.summary || {};
  const reviewCounts = payload.review_counts || [];
  const scopeCounts = payload.scope_counts || [];
  const scopeStatusCounts = payload.scope_status_counts || [];
  const qualityCounts = payload.quality_counts || [];
  const sourceBackedCounts = payload.source_backed_counts || [];

  const generatedAt = document.getElementById("profiles-generated-at");
  const coverage = document.getElementById("profiles-coverage");
  const metrics = document.getElementById("profiles-metrics");
  const sourceBackedTotal = document.getElementById("source-backed-total");
  const sourceBackedInclude = document.getElementById("source-backed-include");
  const searchInput = document.getElementById("profiles-search");
  const scopeFilter = document.getElementById("profiles-scope");
  const statusFilter = document.getElementById("profiles-status");
  const list = document.getElementById("profiles-list");
  const count = document.getElementById("profiles-count");
  const badge = document.getElementById("profile-badge");
  const detail = document.getElementById("profile-detail");
  const queueCount = document.getElementById("profiles-queue-count");
  const queueEl = document.getElementById("profiles-queue");
  const qualityChart = document.getElementById("quality-band-chart");
  const reviewChart = document.getElementById("review-status-chart");
  const scopeChart = document.getElementById("scope-chart");
  const scopeStatusChart = document.getElementById("scope-status-chart");
  const sourceBackedChart = document.getElementById("source-backed-chart");

  const state = {
    selectedId: null,
    search: "",
    scope: "all",
    status: "all"
  };

  function clean(value) {
    if (value === undefined || value === null) return "n/d";
    const text = String(value).trim();
    if (!text || text.toLowerCase() === "nan") return "n/d";
    return text;
  }

  function raw(value) {
    const text = clean(value);
    return text === "n/d" ? "" : text;
  }

  function titleCase(text) {
    return String(text || "")
      .replace(/[_-]+/g, " ")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function themeLabel(value) {
    if (themeSystem) return themeSystem.themeLabel(value);
    return titleCase(clean(value));
  }

  function tagChips(value, className = "muted") {
    const tags = raw(value)
      .split(";")
      .map((tag) => tag.trim())
      .filter(Boolean);
    if (!tags.length) return `<span class="pill muted">Sin tags</span>`;
    return tags.map((tag) => `<span class="pill ${className}">${titleCase(tag)}</span>`).join("");
  }

  function profileTheme(profile) {
    const semantic = semanticAssignments[profile.startup_id];
    return semantic ? semantic.semantic_single_theme : profile.macro_theme;
  }

  function addMetric(label, value) {
    const article = document.createElement("article");
    article.className = "summary-card";
    article.innerHTML = `<span class="label">${label}</span><strong class="value">${value}</strong>`;
    metrics.appendChild(article);
  }

  function percent(part, total) {
    const numerator = Number(part || 0);
    const denominator = Number(total || 0);
    if (!denominator) return "0%";
    return `${Math.round((numerator / denominator) * 100)}%`;
  }

  function renderBarChart(container, rows, keyName, total) {
    container.innerHTML = "";
    [...rows]
      .sort((a, b) => Number(b.count || 0) - Number(a.count || 0))
      .forEach((row) => {
      const countValue = Number(row.count || 0);
      const width = total ? Math.max(2, (countValue / total) * 100) : 0;
      const label = titleCase(row[keyName] || "unknown");

      const item = document.createElement("div");
      item.className = "chart-row";
      item.innerHTML = `
        <div class="chart-label">
          <span>${label}</span>
          <span>${countValue}</span>
        </div>
        <div class="chart-bar">
          <div class="chart-fill" style="width:${width}%"></div>
        </div>
      `;
      container.appendChild(item);
    });
  }

  function matches(profile) {
    const haystack = [
      profile.startup_name,
      profile.startup_summary_v1,
      profile.thesis_scope_note,
      profile.technical_stack,
      profile.industry_destination,
      profileTheme(profile),
      profile.macro_theme,
      profile.scope_reason,
      profile.evidence_excerpt,
      profile.bio_lens_tags,
      profile.domain_tags,
      profile.technology_tags,
      profile.scale_tags
    ].join(" ").toLowerCase();

    if (state.search && !haystack.includes(state.search)) return false;
    if (state.scope !== "all" && clean(profile.scope_decision) !== state.scope) return false;
    if (state.status !== "all" && clean(profile.review_status) !== state.status) return false;
    return true;
  }

  function renderList() {
    const filtered = profiles
      .filter(matches)
      .sort((a, b) => {
        const reviewRank = { reviewed: 3, seeded: 2, taxonomy_stub: 1 };
        const aReview = reviewRank[clean(a.review_status).toLowerCase()] || 0;
        const bReview = reviewRank[clean(b.review_status).toLowerCase()] || 0;
        if (bReview !== aReview) return bReview - aReview;
        const aQuality = Number(a.data_quality_score_10 || 0);
        const bQuality = Number(b.data_quality_score_10 || 0);
        if (bQuality !== aQuality) return bQuality - aQuality;
        return String(a.startup_name || "").localeCompare(String(b.startup_name || ""), "es");
      });
    list.innerHTML = "";
    count.textContent = String(filtered.length);

    filtered.forEach((profile) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "profile-item";
      if (profile.startup_id === state.selectedId) {
        item.classList.add("active");
      }
      item.innerHTML = `
        <div class="item-title">${clean(profile.startup_name)}</div>
        <div class="item-meta">${themeLabel(profileTheme(profile))}</div>
        <div class="item-meta">${clean(profile.startup_summary_v1)}</div>
      `;
      item.addEventListener("click", () => {
        state.selectedId = profile.startup_id;
        renderList();
        renderDetail();
      });
      list.appendChild(item);
    });
  }

  function renderDetail() {
    const profile = profiles.find((item) => item.startup_id === state.selectedId);
    if (!profile) {
      badge.textContent = "Sin seleccion";
      badge.className = "pill muted";
      detail.textContent = "Selecciona una startup para ver su resumen, su calidad, la fuente y la razon de inclusion o exclusion.";
      return;
    }

    badge.textContent = `${titleCase(clean(profile.review_status))} - ${titleCase(clean(profile.scope_decision))} - ${titleCase(clean(profile.scope_status))}`;
    badge.className = clean(profile.scope_decision) === "exclude" ? "pill warning" : "pill";

    const sourceUrl = raw(profile.source_url);
    const sourceBackedStatus = sourceUrl
      ? (clean(profile.review_status) === "reviewed" ? "Source-backed reviewed" : clean(profile.review_status) === "seeded" ? "Source-backed seeded" : "Source-backed minimum")
      : "Missing external source";
    const sourceMarkup = sourceUrl
      ? `<a href="${sourceUrl}" target="_blank" rel="noreferrer">${sourceUrl}</a>`
      : "n/d";

    detail.innerHTML = `
      <div class="detail-stack">
        <div class="item-title">${clean(profile.startup_name)}</div>
        <div class="badge-row">
          <span class="pill">${themeLabel(profileTheme(profile))}</span>
          <span class="pill muted">${sourceBackedStatus}</span>
          <span class="pill muted">${titleCase(clean(profile.quality_band))}</span>
        </div>
        <div class="detail-summary">
          <strong>Etiquetas estrategicas</strong>
          <div class="badge-row">${tagChips(profile.bio_lens_tags)}</div>
          <div class="badge-row">${tagChips(profile.domain_tags, "muted")}</div>
          <div class="badge-row">${tagChips(profile.technology_tags, "muted")}</div>
          <div class="badge-row">${tagChips(profile.scale_tags, "muted")}</div>
        </div>
        <div class="detail-summary">
          <strong>Resumen editorial</strong>
          <p>${clean(profile.startup_summary_v1)}</p>
        </div>
        <div class="detail-grid">
          <div class="detail-box">
            <span>Categoria semantica</span>
            <strong>${themeLabel(profileTheme(profile))}</strong>
          </div>
          <div class="detail-box">
            <span>One liner</span>
            <strong>${clean(profile.business_one_liner)}</strong>
          </div>
          <div class="detail-box">
            <span>Scope</span>
            <strong>${titleCase(clean(profile.scope_decision))} - ${clean(profile.scope_reason)}</strong>
          </div>
          <div class="detail-box">
            <span>Estado del scope</span>
            <strong>${titleCase(clean(profile.scope_status))} - ${titleCase(clean(profile.scope_basis))}</strong>
          </div>
          <div class="detail-box">
            <span>Calidad</span>
            <strong>${clean(profile.data_quality_score_10)} / 10 - ${titleCase(clean(profile.quality_band))}</strong>
          </div>
          <div class="detail-box">
            <span>Estado de evidencia</span>
            <strong>${sourceBackedStatus}</strong>
          </div>
          <div class="detail-box">
            <span>Fuente</span>
            <strong>${clean(profile.source_type)} - ${clean(profile.source_date)}</strong>
          </div>
        </div>
        <div class="detail-row"><strong>Problema:</strong> ${clean(profile.transition_function || profile.problem_addressed)}</div>
        <div class="detail-row"><strong>Enfoque tecnico:</strong> ${clean(profile.technical_stack || profile.technical_approach)}</div>
        <div class="detail-row"><strong>Industria destino:</strong> ${clean(profile.industry_destination)}</div>
        <div class="detail-row"><strong>Materiality signal:</strong> ${titleCase(clean(profile.materiality_signal))}</div>
        <div class="detail-row"><strong>Nota de tesis:</strong> ${clean(profile.thesis_scope_note)}</div>
        <div class="detail-row"><strong>Evidencia:</strong> ${clean(profile.evidence_excerpt)}</div>
        <div class="detail-row"><strong>URL:</strong> ${sourceMarkup}</div>
      </div>
    `;
  }

  function renderQueue() {
    queueEl.innerHTML = "";
    queueCount.textContent = String(queue.length);

    queue.slice(0, 24).forEach((item) => {
      const row = document.createElement("div");
      row.className = "review-item";
      row.innerHTML = `
        <div class="item-title">${clean(item.startup_name)}</div>
        <div class="item-meta">Scope: ${clean(item.scope_decision)} - Prioridad: ${clean(item.research_priority)} - Estado: ${clean(item.review_status)}</div>
        <div class="item-meta">Fuente esperada: ${clean(item.source_type)} - Resumen actual: ${item.has_summary === "True" || item.has_summary === true ? "si" : "no"}</div>
      `;
      queueEl.appendChild(row);
    });
  }

  if (generatedAt) {
    generatedAt.textContent = clean(summary.generated_at);
  }
  if (coverage) {
    coverage.textContent = `${clean(summary.confirmed_scope)} / ${clean(summary.total)} scope confirmado`;
  }
  if (sourceBackedTotal) {
    sourceBackedTotal.textContent = `${clean(summary.confirmed_scope)} / ${clean(summary.total)} scope confirmado (${percent(summary.confirmed_scope, summary.total)})`;
  }
  if (sourceBackedInclude) {
    sourceBackedInclude.textContent = `${clean(summary.include_confirmed_scope)} / ${scopeCounts.find((row) => row.scope_decision === "include")?.count || 0} include confirmado (${percent(summary.include_confirmed_scope, scopeCounts.find((row) => row.scope_decision === "include")?.count || 0)})`;
  }

  addMetric("Startups", clean(summary.total));
  addMetric("Scope confirmado", clean(summary.confirmed_scope));
  addMetric("Scope provisional", clean(summary.provisional_scope));
  addMetric("Include confirmado", clean(summary.include_confirmed_scope));
  addMetric("Include provisional", clean(summary.include_provisional_scope));
  addMetric("% confirmado", percent(summary.confirmed_scope, summary.total));

  renderBarChart(sourceBackedChart, sourceBackedCounts, "label", Number(summary.total || profiles.length));
  renderBarChart(scopeStatusChart, scopeStatusCounts, "scope_status", Number(summary.total || profiles.length));
  renderBarChart(qualityChart, qualityCounts, "quality_band", Number(summary.total || profiles.length));
  renderBarChart(reviewChart, reviewCounts, "review_status", Number(summary.total || profiles.length));
  renderBarChart(scopeChart, scopeCounts, "scope_decision", Number(summary.total || profiles.length));

  searchInput.addEventListener("input", (event) => {
    state.search = event.target.value.trim().toLowerCase();
    renderList();
  });
  scopeFilter.addEventListener("change", (event) => {
    state.scope = event.target.value;
    renderList();
  });
  statusFilter.addEventListener("change", (event) => {
    state.status = event.target.value;
    renderList();
  });

  const firstProfile = profiles.find((profile) => clean(profile.scope_decision) === "include") || profiles[0];
  state.selectedId = firstProfile ? firstProfile.startup_id : null;
  renderList();
  renderDetail();
  renderQueue();
})();
