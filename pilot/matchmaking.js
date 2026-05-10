(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.MATCHMAKING_DATA || {}) : (window.MATCHMAKING_DATA || {});
  const themeSystem = window.THEME_SYSTEM || null;
  const startupRows = payload.startup_recommendations || [];
  const fundRows = payload.fund_recommendations || [];
  const summary = payload.summary || {};

  const generated = document.getElementById("match-generated");
  const summaryGrid = document.getElementById("match-summary");
  const modeButtons = Array.from(document.querySelectorAll(".mode-button"));
  const modeExplainer = document.getElementById("mode-explainer");
  const candidateTitle = document.getElementById("candidate-title");
  const candidateCount = document.getElementById("candidate-count");
  const candidateList = document.getElementById("candidate-list");
  const searchInput = document.getElementById("match-search");
  const themeFilter = document.getElementById("theme-filter");
  const profileKicker = document.getElementById("profile-kicker");
  const profileName = document.getElementById("profile-name");
  const profileBadge = document.getElementById("profile-badge");
  const profileDescription = document.getElementById("profile-description");
  const profileMeta = document.getElementById("profile-meta");
  const recommendationHeading = document.getElementById("recommendation-heading");
  const recommendationCount = document.getElementById("recommendation-count");
  const recommendationList = document.getElementById("recommendation-list");

  const state = {
    mode: "startup",
    selectedId: startupRows[0] ? startupRows[0].startup_id : "",
    search: "",
    theme: "all"
  };

  function clean(value) {
    if (value === undefined || value === null) return "";
    const text = String(value).trim();
    if (!text || text.toLowerCase() === "nan") return "";
    return text;
  }

  function display(value, fallback = "n/d") {
    return clean(value) || fallback;
  }

  function normalize(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function titleCase(text) {
    return String(text || "")
      .replace(/[_-]+/g, " ")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function themeLabel(theme) {
    return themeSystem ? themeSystem.themeLabel(theme) : titleCase(theme);
  }

  function themeColor(theme) {
    return themeSystem ? themeSystem.themeColor(theme) : "#0f766e";
  }

  function roleLabel(role) {
    const labels = {
      anchor_bio_platform: "Anchor BIO platform",
      diversified_bio_investor: "Diversified BIO investor",
      specialized_bio_investor: "Specialized BIO investor",
      emerging_bio_signal: "Emerging BIO signal",
      peripheral_or_discovery_signal: "Peripheral/discovery signal",
      capital_context_only: "Capital context only"
    };
    return labels[role] || titleCase(role || "");
  }

  function scoreLabel(label) {
    const labels = {
      very_high: "Muy alto",
      high: "Alto",
      medium: "Medio",
      exploratory: "Exploratorio"
    };
    return labels[label] || titleCase(label || "score");
  }

  function metricCard(label, value, note) {
    const card = document.createElement("article");
    card.className = "summary-card";
    card.innerHTML = `
      <span class="label">${label}</span>
      <strong class="value">${value}</strong>
      <div class="item-meta">${note}</div>
    `;
    return card;
  }

  function renderSummary() {
    generated.textContent = display(summary.generated_at, "n/d");
    summaryGrid.innerHTML = "";
    [
      metricCard("Startups elegibles", display(summary.eligible_startups, 0), "include + confirmed"),
      metricCard("Con fondos sugeridos", display(summary.startups_with_recommendations, 0), "startup -> fondo"),
      metricCard("Fondos elegibles", display(summary.eligible_funds, 0), "con cartera BIO mapeada"),
      metricCard("Con dealflow sugerido", display(summary.funds_with_recommendations, 0), "fondo -> startup")
    ].forEach((card) => summaryGrid.appendChild(card));
  }

  function rowsForMode() {
    return state.mode === "startup" ? startupRows : fundRows;
  }

  function idFor(row) {
    return state.mode === "startup" ? row.startup_id : row.investor_id;
  }

  function nameFor(row) {
    return state.mode === "startup" ? row.startup_name : row.investor_name;
  }

  function selectedRow() {
    return rowsForMode().find((row) => idFor(row) === state.selectedId) || rowsForMode()[0] || null;
  }

  function activeThemes() {
    const set = new Set();
    rowsForMode().forEach((row) => {
      const theme = clean(state.mode === "startup" ? row.theme : row.dominant_theme);
      if (theme) set.add(theme);
    });
    return Array.from(set).sort((a, b) => themeLabel(a).localeCompare(themeLabel(b), "es"));
  }

  function populateThemeFilter() {
    const previous = state.theme;
    const themes = activeThemes();
    themeFilter.innerHTML = '<option value="all">Todos los themes</option>' +
      themes.map((theme) => `<option value="${theme}">${themeLabel(theme)}</option>`).join("");
    state.theme = previous === "all" || themes.includes(previous) ? previous : "all";
    themeFilter.value = state.theme;
  }

  function filteredRows() {
    const q = normalize(state.search);
    return rowsForMode().filter((row) => {
      const theme = clean(state.mode === "startup" ? row.theme : row.dominant_theme);
      if (state.theme !== "all" && theme !== state.theme) return false;
      const haystack = normalize([
        nameFor(row),
        row.country,
        row.theme,
        row.dominant_theme,
        row.actor_label,
        row.bio_role,
        row.one_liner,
        ...(row.recommendations || []).slice(0, 4).map((rec) => state.mode === "startup" ? rec.investor_name : rec.startup_name)
      ].join(" "));
      return !q || haystack.includes(q);
    }).sort((a, b) => {
      const topA = Number((a.recommendations || [])[0]?.score || 0);
      const topB = Number((b.recommendations || [])[0]?.score || 0);
      return topB - topA || nameFor(a).localeCompare(nameFor(b), "es");
    });
  }

  function renderCandidateList() {
    const rows = filteredRows();
    candidateList.innerHTML = "";
    candidateCount.textContent = String(rows.length);
    candidateTitle.textContent = state.mode === "startup" ? "Startups" : "Fondos";

    rows.forEach((row) => {
      const id = idFor(row);
      const button = document.createElement("button");
      button.type = "button";
      button.className = `candidate-row${id === state.selectedId ? " active" : ""}`;
      const theme = clean(state.mode === "startup" ? row.theme : row.dominant_theme);
      const count = (row.recommendations || []).length;
      const color = themeColor(theme);
      button.innerHTML = `
        <div class="candidate-top">
          <span class="candidate-title">${display(nameFor(row))}</span>
          <span class="pill">${count}</span>
        </div>
        <div class="item-meta">${state.mode === "startup" ? display(row.country) : roleLabel(row.bio_role)}</div>
        <div class="profile-meta">
          <span class="pill muted" style="border-color:${color}; color:${color}">${themeLabel(theme)}</span>
          ${state.mode === "startup" ? `<span class="pill muted">Q ${display(row.quality_score, "n/d")}/10</span>` : `<span class="pill muted">${display(row.include_confirmed_count, 0)} include</span>`}
        </div>
      `;
      button.addEventListener("click", () => {
        state.selectedId = id;
        render();
      });
      candidateList.appendChild(button);
    });

    if (!rows.length) {
      candidateList.innerHTML = `<div class="match-empty">No hay resultados para esos filtros.</div>`;
    }
  }

  function pill(text, extra = "muted", style = "") {
    return `<span class="pill ${extra}" ${style ? `style="${style}"` : ""}>${text}</span>`;
  }

  function renderProfile(row) {
    if (!row) {
      profileName.textContent = "Sin datos";
      profileDescription.textContent = "No hay entidades para mostrar.";
      profileMeta.innerHTML = "";
      return;
    }
    const startupMode = state.mode === "startup";
    const theme = clean(startupMode ? row.theme : row.dominant_theme);
    const color = themeColor(theme);
    profileKicker.textContent = startupMode ? "Startup buscando fondos" : "Fondo buscando dealflow";
    profileName.textContent = display(nameFor(row));
    profileBadge.textContent = startupMode ? "Startup advisor" : "Fund advisor";
    profileDescription.textContent = startupMode
      ? (clean(row.one_liner) || "Priorizamos fondos por afinidad tematica, pais, tags BIO, profundidad de cartera y evidencia.")
      : `${display(row.actor_label)}. Priorizamos startups parecidas a su cartera y oportunidades adyacentes dentro del universo BIO confirmado.`;

    profileMeta.innerHTML = startupMode
      ? [
          pill(themeLabel(theme), "muted", `border-color:${color}; color:${color}`),
          pill(display(row.country, "pais n/d")),
          pill(`Calidad ${display(row.quality_score, "n/d")}/10`),
          pill(`${(row.current_investors || []).length} inversores actuales`),
          row.source_url ? `<a class="pill" href="${row.source_url}" target="_blank" rel="noreferrer">Fuente</a>` : pill("Sin URL fuente", "warning")
        ].join("")
      : [
          pill(themeLabel(theme), "muted", `border-color:${color}; color:${color}`),
          pill(roleLabel(row.bio_role)),
          pill(`${display(row.include_confirmed_count, 0)} include confirmadas`),
          pill(`${display(row.source_coverage_pct, 0)}% fuente`)
        ].join("");
    document.querySelectorAll(".advisor-note.dynamic").forEach((node) => node.remove());
    profileMeta.insertAdjacentHTML("afterend", `
      <div class="advisor-note dynamic">
        ${startupMode
          ? "Lectura sugerida: prioriza fondos con score alto y comparables concretos; si un fondo aparece por pais pero sin comparables, tratarlo como acercamiento exploratorio."
          : "Lectura sugerida: las primeras startups son extensiones naturales de cartera; las de score medio suelen ser adyacencias utiles para discovery, no leads cerrados."}
      </div>
    `);
  }

  function renderRecommendationCard(rec) {
    const startupMode = state.mode === "startup";
    const title = startupMode ? rec.investor_name : rec.startup_name;
    const subtitle = startupMode
      ? `${display(rec.actor_label)} &middot; ${roleLabel(rec.bio_role)}`
      : `${display(rec.country)} &middot; ${themeLabel(rec.theme)} &middot; Q ${display(rec.quality_score, "n/d")}/10`;
    const peers = startupMode ? (rec.comparable_startups || []) : (rec.comparable_portfolio || []);
    const peerTitle = startupMode ? "Comparables en cartera" : "Parecidas en cartera";

    const card = document.createElement("article");
    card.className = "recommendation-card";
    const score = Math.max(0, Math.min(100, Number(rec.score || 0)));
    card.innerHTML = `
      <div class="recommendation-top">
        <div>
          <div class="recommendation-title">${display(title)}</div>
          <div class="item-meta">${subtitle}</div>
        </div>
        <div class="score-badge">${display(rec.score, 0)}<span>${scoreLabel(rec.score_label)}</span></div>
      </div>
      <div class="score-track"><div class="score-fill" style="width:${score}%"></div></div>
      <div class="profile-meta">
        ${pill(scoreLabel(rec.score_label), `score-${rec.score_label || "medium"}`)}
        ${startupMode ? pill(`${display(rec.include_confirmed_count, 0)} BIO en cartera`) : pill(`Fuente ${rec.source_url ? "si" : "pendiente"}`)}
        ${startupMode ? pill(`${display(rec.source_coverage_pct, 0)}% fuente`) : ""}
      </div>
      <div class="reason-list">
        ${(rec.reasons || []).map((reason) => `
          <div class="reason-line">
            <span>${display(reason.text)}</span>
            <span class="reason-weight">
              ${display(reason.weight, 0)}
              <span class="reason-weight-bar" style="width:${Math.max(8, Math.min(46, Number(reason.weight || 0) * 1.4))}px"></span>
            </span>
          </div>
        `).join("")}
      </div>
      <div>
        <div class="item-meta">${peerTitle}</div>
        <div class="peer-stack">
          ${peers.length ? peers.map((peer) => pill(display(peer.startup_name))).join("") : pill("Sin comparables directos", "muted")}
        </div>
      </div>
      ${!startupMode && rec.source_url ? `<a class="item-meta" href="${rec.source_url}" target="_blank" rel="noreferrer">Abrir fuente de startup</a>` : ""}
    `;
    return card;
  }

  function renderRecommendations(row) {
    const recs = row ? (row.recommendations || []) : [];
    recommendationHeading.textContent = state.mode === "startup" ? "Fondos recomendados" : "Startups recomendadas";
    recommendationCount.textContent = String(recs.length);
    recommendationList.innerHTML = "";
    if (!recs.length) {
      recommendationList.innerHTML = `<div class="match-empty">Todavia no hay recomendaciones con suficiente score. Esto suele indicar falta de edges, fuente o tags comparables.</div>`;
      return;
    }
    recs.forEach((rec) => recommendationList.appendChild(renderRecommendationCard(rec)));
  }

  function setMode(mode) {
    state.mode = mode;
    state.search = "";
    state.theme = "all";
    state.selectedId = rowsForMode()[0] ? idFor(rowsForMode()[0]) : "";
    searchInput.value = "";
    modeButtons.forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
    modeExplainer.textContent = mode === "startup"
      ? "Busca una startup y prioriza fondos por fit tematico, pais, tags BIO, profundidad de cartera y calidad de evidencia."
      : "Busca un fondo y prioriza startups no invertidas por similitud con cartera, gaps tematicos, pais y calidad de datos.";
    populateThemeFilter();
    render();
  }

  function render() {
    const row = selectedRow();
    renderCandidateList();
    renderProfile(row);
    renderRecommendations(row);
  }

  function init() {
    renderSummary();
    populateThemeFilter();
    render();

    modeButtons.forEach((button) => {
      button.addEventListener("click", () => setMode(button.dataset.mode));
    });
    searchInput.addEventListener("input", (event) => {
      state.search = event.target.value;
      const rows = filteredRows();
      if (rows.length && !rows.some((row) => idFor(row) === state.selectedId)) {
        state.selectedId = idFor(rows[0]);
      }
      render();
    });
    themeFilter.addEventListener("change", (event) => {
      state.theme = event.target.value;
      const rows = filteredRows();
      state.selectedId = rows[0] ? idFor(rows[0]) : "";
      render();
    });
  }

  init();
})();
