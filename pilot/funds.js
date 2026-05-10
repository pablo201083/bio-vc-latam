(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.FUND_ANALYTICS_DATA || {}) : (window.FUND_ANALYTICS_DATA || {});
  const themeSystem = window.THEME_SYSTEM || null;
  const summary = payload.summary || {};
  const funds = payload.funds || [];
  const topOverlaps = payload.top_overlaps || [];
  const themeTotals = payload.theme_totals || [];
  const capitalAllocators = payload.capital_allocators || [];
  const actorTypeTotals = payload.actor_type_totals || [];

  const generatedAt = document.getElementById("funds-generated-at");
  const summaryMetrics = document.getElementById("fund-summary-metrics");
  const fundCount = document.getElementById("fund-count");
  const fundList = document.getElementById("fund-list");
  const fundSearch = document.getElementById("fund-search");
  const typeFilter = document.getElementById("fund-type-filter");
  const roleFilter = document.getElementById("fund-role-filter");
  const actorTypeMix = document.getElementById("actor-type-mix");
  const globalThemeMix = document.getElementById("global-theme-mix");
  const capitalAllocatorList = document.getElementById("capital-allocator-list");
  const fundDetailBadge = document.getElementById("fund-detail-badge");
  const fundDetail = document.getElementById("fund-detail");
  const fundKpis = document.getElementById("fund-kpis");
  const fundInsights = document.getElementById("fund-insights");
  const fundOverlaps = document.getElementById("fund-overlaps");
  const fundTopStartups = document.getElementById("fund-top-startups");

  if (!funds.length) return;

  const state = {
    selectedInvestorId: funds[0].investor_id,
    search: "",
    actorType: "all",
    bioRole: "all"
  };

  const roleLabels = {
    anchor_bio_platform: "Anchor BIO platform",
    diversified_bio_investor: "Diversified BIO investor",
    specialized_bio_investor: "Specialized BIO investor",
    emerging_bio_signal: "Emerging BIO signal",
    peripheral_or_discovery_signal: "Peripheral/discovery signal",
    capital_context_only: "Capital context only"
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

  function normalize(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function themeLabel(theme) {
    return themeSystem ? themeSystem.themeLabel(theme) : titleCase(clean(theme));
  }

  function themeColor(theme) {
    return themeSystem ? themeSystem.themeColor(theme) : "#90a4ae";
  }

  function roleLabel(role) {
    return roleLabels[role] || titleCase(role || "n/d");
  }

  function metricCard(label, value, note) {
    const article = document.createElement("article");
    article.className = "summary-card";
    article.innerHTML = `
      <span class="label">${label}</span>
      <strong class="value">${value}</strong>
      <div class="item-meta">${note}</div>
    `;
    return article;
  }

  function money(value) {
    const amount = Number(value || 0);
    if (!amount) return "monto n/d";
    if (amount >= 1000000) return `US$${Math.round(amount / 1000000)}M`;
    return `US$${Math.round(amount / 1000)}k`;
  }

  function selectedFund() {
    return funds.find((fund) => fund.investor_id === state.selectedInvestorId) || filteredFunds()[0] || funds[0];
  }

  function filteredFunds() {
    const q = normalize(state.search);
    return funds.filter((fund) => {
      const haystack = normalize([
        fund.investor_name,
        fund.actor_label,
        fund.actor_type,
        fund.bio_role,
        fund.dominant_theme,
        ...(fund.country_mix || []).map((row) => row.country)
      ].join(" "));
      if (q && !haystack.includes(q)) return false;
      if (state.actorType !== "all" && fund.actor_type !== state.actorType) return false;
      if (state.bioRole !== "all" && fund.bio_role !== state.bioRole) return false;
      return true;
    });
  }

  function renderSummary() {
    generatedAt.textContent = clean(summary.generated_at);
    summaryMetrics.innerHTML = "";
    [
      metricCard("Actores en tracker", funds.length, `${clean(summary.mapped_funds_total)} con cartera conectada`),
      metricCard("VC / investors", clean(summary.vc_or_investor_total), "Fondos e inversores financieros"),
      metricCard("Builders / aceleradoras", clean(summary.builders_total), "Company builders, aceleradoras e investigacion aplicada"),
      metricCard("Anchor BIO platforms", clean(summary.anchor_bio_platforms), "Actores con mayor cartera BIO confirmada"),
      metricCard("Cobertura fuente", `${clean(summary.average_source_coverage_pct)}%`, "Promedio de source_url en carteras"),
      metricCard("LPs / FoF", clean(summary.capital_allocators_total), `${clean(summary.allocator_edges_total)} relaciones institucionales`),
      metricCard("Top actor BIO", clean(summary.top_fund_by_confirmed), "Mayor cartera include confirmada")
    ].forEach((card) => summaryMetrics.appendChild(card));
  }

  function populateFilters() {
    const types = [...new Map(funds.map((fund) => [fund.actor_type, fund.actor_label])).entries()]
      .sort((a, b) => a[1].localeCompare(b[1], "es"));
    typeFilter.innerHTML = '<option value="all">Todos los tipos</option>' +
      types.map(([value, label]) => `<option value="${value}">${label}</option>`).join("");

    const roles = Array.from(new Set(funds.map((fund) => fund.bio_role).filter(Boolean)))
      .sort((a, b) => roleLabel(a).localeCompare(roleLabel(b), "es"));
    roleFilter.innerHTML = '<option value="all">Todos los roles BIO</option>' +
      roles.map((role) => `<option value="${role}">${roleLabel(role)}</option>`).join("");
  }

  function renderFundList() {
    const rows = filteredFunds();
    fundList.innerHTML = "";
    fundCount.textContent = String(rows.length);

    rows.forEach((fund) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = `fund-row${fund.investor_id === state.selectedInvestorId ? " active" : ""}`;
      const dominant = raw(fund.dominant_theme) ? themeLabel(fund.dominant_theme) : "Sin tesis dominante";
      row.innerHTML = `
        <div class="fund-row-top">
          <div class="item-title">${clean(fund.investor_name)}</div>
          <span class="pill">${fund.include_confirmed_count}</span>
        </div>
        <div class="item-meta">${clean(fund.actor_label)} · ${roleLabel(fund.bio_role)}</div>
        <div class="item-meta">${fund.portfolio_size} startups · ${fund.source_coverage_pct}% con fuente · ${fund.unique_themes} themes</div>
        <div class="fund-row-meta">
          <span class="pill muted">${dominant}</span>
          <span class="pill muted">HHI ${clean(fund.theme_concentration_hhi)}</span>
        </div>
      `;
      row.addEventListener("click", () => {
        state.selectedInvestorId = fund.investor_id;
        renderFundList();
        renderFundDetail();
      });
      fundList.appendChild(row);
    });
    if (!rows.length) {
      fundList.innerHTML = `<div class="item-meta">No hay actores con esos filtros.</div>`;
    }
  }

  function renderBar(container, label, count, max, color = "#0f766e", note = "") {
    const width = max ? Math.max(2, (Number(count || 0) / max) * 100) : 0;
    const node = document.createElement("div");
    node.className = "bar-row";
    node.innerHTML = `
      <div class="bar-head">
        <span>${label}</span>
        <strong>${count}</strong>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${width}%; background:${color}"></div>
      </div>
      ${note ? `<div class="item-meta">${note}</div>` : ""}
    `;
    container.appendChild(node);
  }

  function renderThemeBars(container, rows, total) {
    container.innerHTML = "";
    rows.forEach((row) => renderBar(container, themeLabel(row.theme), Number(row.count || 0), total, themeColor(row.theme)));
  }

  function renderGlobalPanels() {
    actorTypeMix.innerHTML = "";
    const maxActor = Math.max(...actorTypeTotals.map((row) => Number(row.include_confirmed_count || row.count || 0)), 1);
    actorTypeTotals.forEach((row) => {
      renderBar(actorTypeMix, clean(row.actor_label), Number(row.include_confirmed_count || row.count || 0), maxActor, "#0f766e", `${row.count} actores`);
    });

    const totalThemes = themeTotals.reduce((sum, row) => sum + Number(row.count || 0), 0);
    renderThemeBars(globalThemeMix, themeTotals, totalThemes);
  }

  function renderCapitalAllocators() {
    capitalAllocatorList.innerHTML = "";
    if (!capitalAllocators.length) {
      capitalAllocatorList.innerHTML = `<div class="item-meta">Todavia no hay LPs o fondos de fondos cargados.</div>`;
      return;
    }
    capitalAllocators.forEach((allocator) => {
      const edges = allocator.fund_edges || [];
      const node = document.createElement("div");
      node.className = "table-item";
      node.innerHTML = `
        <div class="table-topline">
          <div>
            <div class="item-title">${clean(allocator.allocator_name)}</div>
            <div class="table-sub">${titleCase(clean(allocator.allocator_type))}</div>
          </div>
          <span class="pill">${allocator.fund_count} fondos</span>
        </div>
        <div class="item-meta">${money(allocator.disclosed_amount_usd)} divulgado</div>
        <div class="chip-row">
          ${edges.slice(0, 5).map((edge) => `<span class="pill muted">${clean(edge.target_fund_name)} · ${clean(edge.year)}</span>`).join("")}
        </div>
      `;
      capitalAllocatorList.appendChild(node);
    });
  }

  function renderFundDetail() {
    const fund = selectedFund();
    fundDetailBadge.textContent = `${fund.actor_label} · ${fund.include_confirmed_count} BIO confirmadas`;
    fundDetail.innerHTML = `
      <div class="detail-grid-2">
        <div class="detail-box">
          <span>Clasificacion de capital</span>
          <strong>${clean(fund.actor_label)}</strong>
        </div>
        <div class="detail-box">
          <span>Rol BIO</span>
          <strong>${roleLabel(fund.bio_role)}</strong>
        </div>
        <div class="detail-box">
          <span>Tesis dominante</span>
          <strong>${raw(fund.dominant_theme) ? themeLabel(fund.dominant_theme) : "Sin dominancia clara"}</strong>
        </div>
        <div class="detail-box">
          <span>Cobertura con fuente</span>
          <strong>${fund.source_backed_count} / ${fund.portfolio_size} · ${fund.source_coverage_pct}%</strong>
        </div>
      </div>
      <div class="chip-row" style="margin-top:12px;">
        ${(fund.country_mix || []).slice(0, 8).map((row) => `<span class="pill muted">${clean(row.country)} · ${row.count}</span>`).join("") || `<span class="pill muted">pais n/d</span>`}
      </div>
    `;

    fundKpis.innerHTML = "";
    [
      metricCard("Portfolio mapeado", fund.portfolio_size, "Startups conectadas al actor"),
      metricCard("BIO confirmadas", fund.include_confirmed_count, "Include + scope confirmado"),
      metricCard("Fuera de tesis", fund.exclude_count, "Edges conectados a excludes"),
      metricCard("Diversidad tematica", fund.unique_themes, `HHI ${clean(fund.theme_concentration_hhi)}`)
    ].forEach((card) => fundKpis.appendChild(card));

    fundInsights.innerHTML = "";
    [
      metricCard("Calidad promedio", clean(fund.average_quality), "Score de datos de startups conectadas"),
      metricCard("Fuente cartera", `${clean(fund.source_coverage_pct)}%`, "Con source_url en el master"),
      metricCard("Edge count", clean(fund.edge_count), `${clean(fund.source_presence)} como origen`)
    ].forEach((card) => fundInsights.appendChild(card));

    const existing = document.getElementById("selected-fund-theme-panel");
    if (existing) existing.remove();
    const themePanel = document.createElement("section");
    themePanel.className = "panel";
    themePanel.id = "selected-fund-theme-panel";
    themePanel.innerHTML = `
      <div class="panel-head">
        <h2>Mix tematico del actor</h2>
        <span class="pill muted">${fund.include_confirmed_count} startups</span>
      </div>
      <div id="selected-fund-theme-mix" class="theme-stack"></div>
    `;
    fundKpis.parentElement.insertBefore(themePanel, fundInsights.nextSibling);
    renderThemeBars(document.getElementById("selected-fund-theme-mix"), fund.theme_mix || [], fund.include_confirmed_count || 1);

    renderOverlaps(fund);
    renderStartups(fund);
  }

  function renderOverlaps(fund) {
    fundOverlaps.innerHTML = "";
    const related = topOverlaps
      .filter((row) => row.left_investor_id === fund.investor_id || row.right_investor_id === fund.investor_id)
      .slice(0, 8);
    if (!related.length) {
      fundOverlaps.innerHTML = `<div class="item-meta">Todavia no hay suficiente solapamiento mapeado para mostrar comparables fuertes.</div>`;
      return;
    }
    related.forEach((row) => {
      const counterpart = row.left_investor_id === fund.investor_id ? row.right_investor_name : row.left_investor_name;
      const card = document.createElement("div");
      card.className = "table-item";
      card.innerHTML = `
        <div class="table-topline">
          <div class="item-title">${counterpart}</div>
          <span class="pill">${row.shared_count} compartidas</span>
        </div>
        <div class="table-sub">Jaccard ${row.jaccard}. ${row.shared_startups.map((item) => item.startup_name).slice(0, 5).join(", ")}</div>
      `;
      fundOverlaps.appendChild(card);
    });
  }

  function renderStartups(fund) {
    fundTopStartups.innerHTML = "";
    const rows = (fund.startups || [])
      .slice()
      .sort((a, b) => {
        const aInclude = a.scope_decision === "include" && a.scope_status === "confirmed" ? 1 : 0;
        const bInclude = b.scope_decision === "include" && b.scope_status === "confirmed" ? 1 : 0;
        if (bInclude !== aInclude) return bInclude - aInclude;
        return Number(b.data_quality_score_10 || 0) - Number(a.data_quality_score_10 || 0);
      })
      .slice(0, 24);

    rows.forEach((startup) => {
      const node = document.createElement("div");
      node.className = "table-item";
      const theme = startup.semantic_single_theme || startup.macro_theme;
      node.innerHTML = `
        <div class="table-topline">
          <div class="item-title">${clean(startup.startup_name)}</div>
          <span class="pill ${startup.scope_decision === "include" ? "" : "warning"}">${titleCase(clean(startup.scope_decision))}</span>
        </div>
        <div class="table-sub">${clean(startup.structured_country)} · ${themeLabel(theme)} · calidad ${clean(startup.data_quality_score_10)} · ${clean(startup.review_status)}</div>
      `;
      fundTopStartups.appendChild(node);
    });
  }

  function bindEvents() {
    fundSearch.addEventListener("input", () => {
      state.search = fundSearch.value;
      renderFundList();
    });
    typeFilter.addEventListener("change", () => {
      state.actorType = typeFilter.value;
      renderFundList();
    });
    roleFilter.addEventListener("change", () => {
      state.bioRole = roleFilter.value;
      renderFundList();
    });
  }

  renderSummary();
  populateFilters();
  bindEvents();
  renderFundList();
  renderGlobalPanels();
  renderCapitalAllocators();
  renderFundDetail();
})();
