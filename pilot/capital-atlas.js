(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.CAPITAL_ATLAS_DATA || { nodes: [], edges: [], summary: {} }) : (window.CAPITAL_ATLAS_DATA || { nodes: [], edges: [], summary: {} });
  const semanticSinglePayload = window.deepRepairData ? window.deepRepairData(window.SEMANTIC_SINGLE_LEVEL_DATA || { summary: {}, candidates: [] }) : (window.SEMANTIC_SINGLE_LEVEL_DATA || { summary: {}, candidates: [] });
  const themeSystem = window.THEME_SYSTEM || null;

  const svg = document.getElementById("capital-atlas-svg");
  const modeSelect = document.getElementById("atlas-mode");
  const themeSelect = document.getElementById("atlas-theme");
  const countrySelect = document.getElementById("atlas-country");
  const confidenceSelect = document.getElementById("atlas-confidence");
  const sourceTierSelect = document.getElementById("atlas-source-tier");
  const searchInput = document.getElementById("atlas-search");
  const searchResults = document.getElementById("atlas-search-results");
  const runLayoutButton = document.getElementById("atlas-run-layout");
  const resetButton = document.getElementById("atlas-reset");
  const labelsButton = document.getElementById("atlas-labels");
  const universeButton = document.getElementById("atlas-universe");
  const backboneButton = document.getElementById("atlas-backbone");
  const clearButton = document.getElementById("atlas-clear");
  const zoomInButton = document.getElementById("atlas-zoom-in");
  const zoomOutButton = document.getElementById("atlas-zoom-out");
  const resetViewButton = document.getElementById("atlas-reset-view");
  const summaryEl = document.getElementById("atlas-summary");
  const rankingEl = document.getElementById("atlas-ranking");
  const themeMixEl = document.getElementById("atlas-theme-mix");
  const detailEl = document.getElementById("atlas-detail");
  const badgeEl = document.getElementById("atlas-detail-badge");
  const noteEl = document.getElementById("atlas-note");
  const tooltipEl = document.getElementById("atlas-tooltip");

  const WIDTH = 1900;
  const HEIGHT = 900;
  const LAYOUT_MARGIN = 190;
  const FUND_COLOR = "#0f766e";
  const ALLOCATOR_COLOR = "#b7791f";
  const STARTUP_FALLBACK = "#7c83fd";
  // Paleta canónica de bio-themes — idéntica a startup-themes.html
  const THEME_PAL = {
    "Therapeutics":                           "#7033BC",
    "Diagnostics & Health Access":            "#1A6DB5",
    "Food Systems & Alt Proteins":            "#C25A2A",
    "Bioinputs & Crop Resilience":            "#2A7A42",
    "Nature & Ecosystem Tech":               "#127A6E",
    "Farm Intelligence":                      "#2E4E8C",
    "Biomaterials & Circular Economy":        "#8B6D14",
    "Biomanufacturing & Fermentation Economy":"#6B8C3A",
  };
  const SHARED_TAXONOMY_STATE_KEY = "bioVcLatam.activeSemanticTaxonomy";
  const DYNAMIC_THEME_PALETTE = [
    "#ff7043", "#d66aa2", "#b64050", "#09a7b7", "#235a7c", "#7d58c7",
    "#83bf4c", "#2fa89f", "#f08a24", "#8fa5ad", "#c65f97", "#4f8cc9"
  ];
  const EDGE_COLORS = {
    direct_investment: "rgba(10, 104, 96, 0.58)",
    portfolio_investment: "rgba(31, 78, 108, 0.5)",
    portfolio_or_acceleration: "rgba(96, 92, 180, 0.42)",
    investment_or_membership: "rgba(92, 82, 70, 0.34)",
    co_investment: "rgba(10, 104, 96, 0.5)",
    lp_commitment_to_vc_fund: "rgba(183, 121, 31, 0.58)",
    lp_partner_in_vc_fund: "rgba(183, 121, 31, 0.48)",
    equity_investment_to_growth_fund: "rgba(183, 121, 31, 0.58)"
  };

  if (!svg || !payload.nodes?.length) return;

  const allNodesById = new Map((payload.nodes || []).map((node) => [node.id, node]));
  const rawEdges = payload.edges || [];
  let activeNodes = [];
  let activeEdges = [];
  let positions = new Map();
  let selectedId = null;
  let selectedEdgeId = null;
  let hoverId = null;
  let hoverEdgeId = null;
  let showLabels = true;
  let showUniverseContext = false;
  let backboneOnly = false;
  let hiddenByBackbone = 0;
  let transform = { x: 0, y: 0, k: 1 };
  let activeTaxonomyState = readSharedTaxonomyState();
  let dynamicAssignmentById = new Map();
  let dynamicAssignmentByLabel = new Map();
  let dynamicThemeColorByKey = new Map();
  let isDragging = false;
  let didDrag = false;
  let dragStart = { x: 0, y: 0, ox: 0, oy: 0 };

  const viewport = makeSvg("g", {});
  const edgeLayer = makeSvg("g", {});
  const nodeLayer = makeSvg("g", {});
  const labelLayer = makeSvg("g", {});
  viewport.append(edgeLayer, nodeLayer, labelLayer);
  svg.append(viewport);

  function makeSvg(tag, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  function closestInteractive(target) {
    return target?.closest?.("[data-node-id], [data-edge-id]");
  }

  function clean(value) {
    const text = String(value ?? "").trim();
    return !text || text.toLowerCase() === "nan" ? "" : text;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function titleCase(value) {
    return String(value || "")
      .replace(/_/g, " ")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function normalize(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function seeded(id, salt) {
    let hash = 2166136261;
    const text = `${id}::${salt}`;
    for (let i = 0; i < text.length; i += 1) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return ((hash >>> 0) % 10000) / 10000;
  }

  function readSharedTaxonomyState() {
    const fallbackProfile = semanticSinglePayload.summary?.recommended_profile || "balanced";
    const fallbackK = Number(semanticSinglePayload.summary?.recommended_k || 10);
    try {
      const stored = JSON.parse(window.localStorage.getItem(SHARED_TAXONOMY_STATE_KEY) || "{}");
      return {
        clusterMode: stored.clusterMode === "adopted" ? "adopted" : "semantic",
        semanticProfile: stored.semanticProfile || fallbackProfile,
        semanticK: Number(stored.semanticK || fallbackK)
      };
    } catch (_) {
      return { clusterMode: "semantic", semanticProfile: fallbackProfile, semanticK: fallbackK };
    }
  }

  function semanticCandidateKey(profile, k) {
    return `${profile || ""}::${Number(k) || ""}`;
  }

  const semanticCandidates = semanticSinglePayload.candidates || [];
  const semanticCandidatesByKey = new Map(
    semanticCandidates.map((candidate) => [semanticCandidateKey(candidate.feature_profile, candidate.k), candidate])
  );

  function currentSemanticCandidate() {
    if (activeTaxonomyState.clusterMode !== "semantic") return null;
    const profile = activeTaxonomyState.semanticProfile || semanticSinglePayload.summary?.recommended_profile || "balanced";
    const k = Number(activeTaxonomyState.semanticK || semanticSinglePayload.summary?.recommended_k || 10);
    return semanticCandidatesByKey.get(semanticCandidateKey(profile, k)) ||
      semanticCandidates.find((candidate) => candidate.feature_profile === profile) ||
      semanticCandidates[0] ||
      null;
  }

  function rebuildDynamicAssignments() {
    dynamicAssignmentById = new Map();
    dynamicAssignmentByLabel = new Map();
    dynamicThemeColorByKey = new Map();
    const candidate = currentSemanticCandidate();
    if (!candidate) return;
    (candidate.clusters || []).forEach((cluster, index) => {
      const key = clean(cluster.label) || cluster.cluster_id || `cluster_${index + 1}`;
      dynamicThemeColorByKey.set(key, DYNAMIC_THEME_PALETTE[index % DYNAMIC_THEME_PALETTE.length]);
      (cluster.members || []).forEach((member) => {
        const assignment = {
          ...member,
          cluster_id: cluster.cluster_id,
          cluster_label: key,
          cluster_description: cluster.description,
          cluster_top_tokens: cluster.top_tokens,
          feature_profile: candidate.feature_profile,
          feature_profile_label: candidate.feature_profile_label,
          k: candidate.k
        };
        if (member.startup_id) dynamicAssignmentById.set(member.startup_id, assignment);
        const labelKey = normalize(member.startup_name || member.label || "");
        if (labelKey && !dynamicAssignmentByLabel.has(labelKey)) dynamicAssignmentByLabel.set(labelKey, assignment);
      });
    });
  }

  function dynamicAssignmentForNode(node) {
    if (!node || node.type !== "startup" || activeTaxonomyState.clusterMode !== "semantic") return null;
    return dynamicAssignmentById.get(node.id) ||
      dynamicAssignmentByLabel.get(normalize(node.label)) ||
      dynamicAssignmentByLabel.get(normalize((node.label || "").replace(/-/g, " "))) ||
      null;
  }

  function themeKey(node) {
    const dynamic = dynamicAssignmentForNode(node);
    if (dynamic) return dynamic.cluster_label;
    return clean(node.theme) || "needs review";
  }

  function themeLabel(theme) {
    if (dynamicThemeColorByKey.has(theme)) return titleCase(theme || "Unclassified");
    if (themeSystem) return themeSystem.themeLabel(theme);
    return titleCase(theme || "Unclassified");
  }

  function nodeColor(node) {
    if (node.type === "fund") return FUND_COLOR;
    if (node.type === "allocator") return ALLOCATOR_COLOR;
    const key = themeKey(node);
    if (dynamicThemeColorByKey.has(key)) return dynamicThemeColorByKey.get(key);
    if (THEME_PAL[key]) return THEME_PAL[key];
    if (themeSystem) return themeSystem.themeColor(key);
    return STARTUP_FALLBACK;
  }

  function themeColor(theme) {
    if (dynamicThemeColorByKey.has(theme)) return dynamicThemeColorByKey.get(theme);
    if (THEME_PAL[theme]) return THEME_PAL[theme];
    if (themeSystem) return themeSystem.themeColor(theme);
    return STARTUP_FALLBACK;
  }

  function activeTaxonomyLabel() {
    const candidate = currentSemanticCandidate();
    if (!candidate) return "base operativa guardada";
    return `${candidate.feature_profile_label || activeTaxonomyState.semanticProfile} / k=${candidate.k}`;
  }

  function edgeColor(edge) {
    return EDGE_COLORS[edge.type] || "rgba(92,82,70,0.16)";
  }

  function edgeWeight(edge) {
    if (edge.type === "co_investment") return Math.max(1.4, Math.min(6.5, Number(edge.shared_count || 1) * 0.85));
    return Math.max(1.15, Math.min(4.4, Number(edge.weight || 1.4) * 1.18));
  }

  function edgeLabel(edge) {
    const labels = {
      direct_investment: "Inversion directa",
      portfolio_investment: "Portfolio",
      portfolio_or_acceleration: "Portfolio / aceleracion",
      investment_or_membership: "Inversion o membresia",
      co_investment: "Co-investment",
      lp_commitment_to_vc_fund: "LP commitment",
      lp_partner_in_vc_fund: "LP partner",
      equity_investment_to_growth_fund: "Growth fund investment"
    };
    return labels[edge.type] || titleCase(edge.type);
  }

  function nodeWeight(node) {
    const base = Number(node.visible_weighted_degree ?? node.weighted_degree ?? node.visible_degree ?? node.degree ?? 0);
    if (node.type !== "startup") return base;
    return base + Number(node.visible_public_edges || 0) * 0.75 + Number(node.visible_specific_edges || 0) * 1.2;
  }

  function startupCapitalSignal(node) {
    if (node.type !== "startup") return nodeWeight(node);
    const capitalDegree = Number(node.visible_capital_degree ?? node.visible_degree ?? node.degree ?? 0);
    const publicEdges = Number(node.visible_public_edges || 0);
    const specificEdges = Number(node.visible_specific_edges || 0);
    const announcementEdges = Number(node.visible_announcement_edges || 0);
    return capitalDegree + publicEdges * 0.85 + specificEdges * 1.25 + announcementEdges * 1.6;
  }

  function hasActiveFilters() {
    return themeSelect.value !== "all" ||
      countrySelect.value !== "all" ||
      sourceTierSelect.value !== "all" ||
      Number(confidenceSelect.value || 0.75) > 0;
  }

  function edgePassesHighlightFilters(edge) {
    const minConfidence = Number(confidenceSelect?.value || 0);
    if (Number(edge.confidence || 0) < minConfidence) return false;
    if (sourceTierSelect?.value === "public_url" && edge.evidence_tier !== "public_url" && edge.type !== "co_investment") return false;
    const source = allNodesById.get(edge.source);
    const target = allNodesById.get(edge.target);
    const startup = source?.type === "startup" ? source : target?.type === "startup" ? target : null;
    if (startup) {
      if (themeSelect.value !== "all" && themeKey(startup) !== themeSelect.value) return false;
      if (countrySelect.value !== "all" && clean(startup.country) !== countrySelect.value) return false;
    } else if (themeSelect.value !== "all" || countrySelect.value !== "all") {
      const endpoints = new Set([edge.source, edge.target]);
      return activeEdges.some((candidate) => {
        if (!endpoints.has(candidate.source) && !endpoints.has(candidate.target)) return false;
        const candidateSource = allNodesById.get(candidate.source);
        const candidateTarget = allNodesById.get(candidate.target);
        const candidateStartup = candidateSource?.type === "startup" ? candidateSource : candidateTarget?.type === "startup" ? candidateTarget : null;
        if (!candidateStartup) return false;
        if (themeSelect.value !== "all" && themeKey(candidateStartup) !== themeSelect.value) return false;
        if (countrySelect.value !== "all" && clean(candidateStartup.country) !== countrySelect.value) return false;
        return true;
      });
    }
    return true;
  }

  function nodePassesHighlightFilters(node) {
    if (!hasActiveFilters()) return true;
    if (!node) return false;
    if (node.type === "startup") {
      if (themeSelect.value !== "all" && themeKey(node) !== themeSelect.value) return false;
      if (countrySelect.value !== "all" && clean(node.country) !== countrySelect.value) return false;
      if (sourceTierSelect.value === "public_url" && Number(node.visible_degree || 0) === 0 && !clean(node.source_url)) return false;
      if (Number(confidenceSelect.value || 0) <= 0 && sourceTierSelect.value === "all") return true;
    }
    return activeEdges.some((edge) => (edge.source === node.id || edge.target === node.id) && edgePassesHighlightFilters(edge));
  }

  function nodeRadius(node) {
    const weight = nodeWeight(node);
    if (modeSelect?.value === "coverage_gaps" && node.type === "startup") return 7 + seeded(node.id, "gap-size") * 4.2;
    if (node.type === "startup") {
      const signal = startupCapitalSignal(node);
      if (signal <= 0) return 2.8;
      return Math.max(5.4, Math.min(29, 4.8 + Math.sqrt(signal) * 4.2 + Math.min(5.6, Number(node.visible_capital_degree || 0) * 0.82)));
    }
    if (node.type === "allocator") return Math.max(17, Math.min(38, 15 + Math.sqrt(weight + 1) * 4.8));
    if (node.type === "fund") return Math.max(16, Math.min(54, 12 + Math.sqrt(weight + 1) * 5.6));
    return Math.max(7.4, Math.min(28, 5.6 + Math.sqrt(weight + 1) * 4.25));
  }

  function layoutStats() {
    const coreCount = layoutNodesForCapital().length || activeNodes.length || 1;
    const connectedStartups = activeNodes.filter((node) => node.type === "startup" && Number(node.visible_degree || 0) > 0).length;
    const funds = activeNodes.filter((node) => node.type === "fund").length;
    const density = activeEdges.length / Math.max(1, coreCount);
    const scale = Math.max(0.88, Math.min(1.38, Math.sqrt(coreCount / 260)));
    return {
      coreCount,
      connectedStartups,
      funds,
      density,
      scale,
      repulsion: 9200 + coreCount * 24 + Math.max(0, funds - 10) * 110 + Math.max(0, density - 1.1) * 640,
      edgeLength: Math.max(92, Math.min(158, 104 + Math.sqrt(connectedStartups) * 2.1 - Math.max(0, density - 1.1) * 5))
    };
  }

  function isContextStartup(node) {
    if (modeSelect?.value === "coverage_gaps") return false;
    return node?.type === "startup" && Number(node.visible_degree || 0) === 0;
  }

  function edgeAllowedByFilters(edge) {
    const source = allNodesById.get(edge.source);
    const target = allNodesById.get(edge.target);
    const hiddenFlags = "capital_core_hidden_exclude_only|capital_core_sidecar_broad_low_priority";
    if (new RegExp(hiddenFlags).test(String(source?.quality_flags || ""))) return false;
    if (new RegExp(hiddenFlags).test(String(target?.quality_flags || ""))) return false;
    const startup = source?.type === "startup" ? source : target?.type === "startup" ? target : null;
    if (startup) {
      if (modeSelect.value === "capital_core" && startup.scope_decision !== "include") return false;
    }
    return true;
  }

  function startupAllowedByContext(node) {
    if (!node || node.type !== "startup") return false;
    if (node.scope_decision !== "include") return false;
    return true;
  }

  function investmentEdges() {
    return rawEdges.filter((edge) =>
      edge.type !== "lp_commitment_to_vc_fund" &&
      edge.type !== "lp_partner_in_vc_fund" &&
      edge.type !== "equity_investment_to_growth_fund" &&
      allNodesById.get(edge.source)?.type === "fund" &&
      allNodesById.get(edge.target)?.type === "startup" &&
      edgeAllowedByFilters(edge)
    );
  }

  function allocatorEdges() {
    return rawEdges.filter((edge) =>
      (
        allNodesById.get(edge.source)?.type === "allocator" ||
        String(edge.type || "").includes("fund_of_funds")
      ) &&
      allNodesById.get(edge.target)?.type === "fund"
    );
  }

  function buildCoInvestmentGraph(baseEdges) {
    const byStartup = new Map();
    baseEdges.forEach((edge) => {
      if (!byStartup.has(edge.target)) byStartup.set(edge.target, []);
      byStartup.get(edge.target).push(edge.source);
    });
    const pairMap = new Map();
    byStartup.forEach((funds, startupId) => {
      const unique = Array.from(new Set(funds)).sort();
      for (let i = 0; i < unique.length; i += 1) {
        for (let j = i + 1; j < unique.length; j += 1) {
          const key = `${unique[i]}--${unique[j]}`;
          if (!pairMap.has(key)) {
            pairMap.set(key, { source: unique[i], target: unique[j], startups: [] });
          }
          pairMap.get(key).startups.push(startupId);
        }
      }
    });
    return Array.from(pairMap.values())
      .filter((item) => item.startups.length >= 1)
      .map((item, index) => ({
        id: `co-${index}`,
        source: item.source,
        target: item.target,
        type: "co_investment",
        confidence: 1,
        shared_count: item.startups.length,
        shared_startups: item.startups,
        weight: Math.min(4.8, 1 + Math.log2(item.startups.length + 1))
      }));
  }

  function buildActiveGraph() {
    const mode = modeSelect.value;
    let edges = investmentEdges();
    if (mode === "coverage_gaps") {
      activeEdges = [];
    } else if (mode === "co_investment") {
      activeEdges = buildCoInvestmentGraph(edges);
    } else if (mode === "allocator_layer") {
      const alloc = allocatorEdges();
      const targetFunds = new Set(alloc.map((edge) => edge.target));
      const portfolioEdges = edges.filter((edge) => targetFunds.has(edge.source));
      activeEdges = alloc.concat(portfolioEdges);
    } else if (mode === "full_network") {
      activeEdges = edges.concat(allocatorEdges());
    } else {
      activeEdges = edges;
    }

    hiddenByBackbone = 0;
    if (backboneOnly && mode !== "co_investment") {
      const degree = new Map();
      activeEdges.forEach((edge) => {
        degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
        degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
      });
      const keepStartup = (startupId) => {
        const node = allNodesById.get(startupId);
        if (!node || node.type !== "startup") return true;
        if ((degree.get(startupId) || 0) >= 2) return true;
        return activeEdges.some((edge) =>
          edge.target === startupId &&
          edge.evidence_tier === "public_url"
        );
      };
      const before = new Set(activeEdges.flatMap((edge) => [edge.source, edge.target]));
      activeEdges = activeEdges.filter((edge) => keepStartup(edge.source) && keepStartup(edge.target));
      const after = new Set(activeEdges.flatMap((edge) => [edge.source, edge.target]));
      hiddenByBackbone = Array.from(before).filter((id) => !after.has(id) && allNodesById.get(id)?.type === "startup").length;
    }

    const nodeIds = new Set();
    if (mode === "coverage_gaps") {
      payload.nodes
        .filter((node) => startupAllowedByContext(node) && String(node.capital_status || "") === "no_capital_edge")
        .forEach((node) => nodeIds.add(node.id));
    } else {
      activeEdges.forEach((edge) => {
        nodeIds.add(edge.source);
        nodeIds.add(edge.target);
      });
    }
    if (showUniverseContext && mode !== "co_investment" && mode !== "coverage_gaps") {
      payload.nodes
        .filter(startupAllowedByContext)
        .forEach((node) => nodeIds.add(node.id));
    }
    activeNodes = Array.from(nodeIds)
      .map((id) => allNodesById.get(id))
      .filter(Boolean)
      .map((node) => ({ ...node, visible_degree: 0, visible_weighted_degree: 0, visible_public_edges: 0, visible_specific_edges: 0, visible_announcement_edges: 0, visible_capital_degree: 0 }));
    const activeById = new Map(activeNodes.map((node) => [node.id, node]));
    activeEdges.forEach((edge) => {
      const weight = edgeWeight(edge);
      const source = activeById.get(edge.source);
      const target = activeById.get(edge.target);
      const edgeTouchesStartup = source?.type === "startup" || target?.type === "startup";
      const edgeTouchesFund = source?.type === "fund" || target?.type === "fund";
      const isCapitalStartupEdge = edgeTouchesStartup && edgeTouchesFund && edge.type !== "co_investment";
      if (activeById.has(edge.source)) {
        activeById.get(edge.source).visible_degree += 1;
        activeById.get(edge.source).visible_weighted_degree += weight;
        if (edge.evidence_tier === "public_url") activeById.get(edge.source).visible_public_edges += 1;
        if (Number(edge.capital_evidence_level || 0) >= 3) activeById.get(edge.source).visible_specific_edges += 1;
        if (Number(edge.capital_evidence_level || 0) >= 4) activeById.get(edge.source).visible_announcement_edges += 1;
        if (isCapitalStartupEdge && activeById.get(edge.source).type === "startup") activeById.get(edge.source).visible_capital_degree += 1;
      }
      if (activeById.has(edge.target)) {
        activeById.get(edge.target).visible_degree += 1;
        activeById.get(edge.target).visible_weighted_degree += weight;
        if (edge.evidence_tier === "public_url") activeById.get(edge.target).visible_public_edges += 1;
        if (Number(edge.capital_evidence_level || 0) >= 3) activeById.get(edge.target).visible_specific_edges += 1;
        if (Number(edge.capital_evidence_level || 0) >= 4) activeById.get(edge.target).visible_announcement_edges += 1;
        if (isCapitalStartupEdge && activeById.get(edge.target).type === "startup") activeById.get(edge.target).visible_capital_degree += 1;
      }
    });
  }

  function populateFilters() {
    const startupNodes = (payload.nodes || []).filter((node) => node.type === "startup" && node.scope_decision === "include");
    const themes = Array.from(new Set(startupNodes.map(themeKey).filter(Boolean)))
      .sort((a, b) => themeLabel(a).localeCompare(themeLabel(b), "es"));
    const countries = Array.from(new Set(startupNodes.map((node) => clean(node.country)).filter(Boolean)))
      .sort((a, b) => a.localeCompare(b, "es"));
    themeSelect.innerHTML = '<option value="all">Todas las categorias</option>' +
      themes.map((theme) => `<option value="${escapeHtml(theme)}">${escapeHtml(themeLabel(theme))}</option>`).join("");
    countrySelect.innerHTML = '<option value="all">Todos los paises</option>' +
      countries.map((country) => `<option value="${escapeHtml(country)}">${escapeHtml(country)}</option>`).join("");
  }

  function initializePositions() {
    positions = new Map();
    const mode = modeSelect.value;
    if (mode === "coverage_gaps") {
      initializeGapPositions();
      return;
    }
    const centerX = WIDTH / 2;
    const centerY = HEIGHT / 2;
    const fundNodes = activeNodes
      .filter((node) => node.type === "fund")
      .sort((a, b) => Number(b.visible_degree || 0) - Number(a.visible_degree || 0) || a.label.localeCompare(b.label, "es"));
    const fundRank = new Map(fundNodes.map((node, index) => [node.id, index]));
    const startupFundLinks = new Map();
    activeEdges.forEach((edge) => {
      const source = allNodesById.get(edge.source);
      const target = allNodesById.get(edge.target);
      if (source?.type === "fund" && target?.type === "startup") {
        if (!startupFundLinks.has(target.id)) startupFundLinks.set(target.id, []);
        startupFundLinks.get(target.id).push(source.id);
      }
    });

    fundNodes.forEach((node, index) => {
      const angle = index * Math.PI * (3 - Math.sqrt(5)) - Math.PI / 8;
      const ring = index < 5 ? 70 + index * 38 : 214 + ((index - 5) % 8) * 15;
      const pos = {
        x: centerX + Math.cos(angle) * ring * 1.18,
        y: centerY + Math.sin(angle) * ring * 0.64,
        vx: 0,
        vy: 0,
        index
      };
      positions.set(node.id, pos);
    });

    activeNodes
      .filter((node) => node.type !== "fund")
      .forEach((node, index) => {
      const angle = Math.PI * 2 * seeded(node.id, mode);
      const linkedFunds = startupFundLinks.get(node.id) || [];
      const anchorPositions = linkedFunds.map((id) => positions.get(id)).filter(Boolean);
      const anchor = anchorPositions.length
        ? {
            x: anchorPositions.reduce((sum, pos) => sum + pos.x, 0) / anchorPositions.length,
            y: anchorPositions.reduce((sum, pos) => sum + pos.y, 0) / anchorPositions.length
          }
        : { x: centerX, y: centerY };
      const bestRank = Math.min(...linkedFunds.map((id) => fundRank.get(id) ?? 99), 99);
      const baseRing = node.type === "allocator" ? 258 : bestRank < 5 ? 90 : 155;
      const jitter = node.type === "allocator" ? 42 : 30 + 58 * seeded(node.id, "jitter");
      const pos = {
        x: anchor.x + Math.cos(angle) * (baseRing + jitter) * (node.type === "allocator" ? 1.28 : 1),
        y: (node.type === "allocator" ? HEIGHT * 0.34 : anchor.y) + Math.sin(angle) * (baseRing * 0.66 + jitter * 0.45),
        vx: 0,
        vy: 0,
        index
      };
      positions.set(node.id, {
        x: pos.x,
        y: pos.y,
        vx: pos.vx,
        vy: pos.vy,
        index
      });
    });
  }

  function initializeGapPositions() {
    const gapNodes = activeNodes.filter((node) => node.type === "startup");
    const groups = Array.from(
      gapNodes.reduce((map, node) => {
        const key = themeKey(node);
        if (!map.has(key)) map.set(key, []);
        map.get(key).push(node);
        return map;
      }, new Map())
    ).sort((a, b) => b[1].length - a[1].length || themeLabel(a[0]).localeCompare(themeLabel(b[0]), "es"));
    const centerX = WIDTH / 2;
    const centerY = HEIGHT / 2;
    const golden = Math.PI * (3 - Math.sqrt(5));
    groups.forEach(([theme, members], groupIndex) => {
      const angle = (groupIndex / Math.max(1, groups.length)) * Math.PI * 2 - Math.PI / 2;
      const ring = groups.length <= 1 ? 0 : 235 + Math.floor(groupIndex / 7) * 70;
      const anchorX = centerX + Math.cos(angle) * ring * 1.45;
      const anchorY = centerY + Math.sin(angle) * ring * 0.76;
      members
        .slice()
        .sort((a, b) => a.label.localeCompare(b.label, "es"))
        .forEach((node, index) => {
          const localAngle = index * golden + seeded(node.id, "gap-angle") * 0.42;
          const localRing = 16 + Math.sqrt(index + 1) * 16 + seeded(node.id, "gap-ring") * 10;
          positions.set(node.id, {
            x: anchorX + Math.cos(localAngle) * localRing,
            y: anchorY + Math.sin(localAngle) * localRing * 0.78,
            vx: 0,
            vy: 0,
            index
          });
        });
    });
  }

  function layoutNodesForCapital() {
    return activeNodes.filter((node) => !isContextStartup(node));
  }

  function positionContextNodes() {
    const contextNodes = activeNodes.filter(isContextStartup);
    if (!contextNodes.length) return;
    const coreNodes = layoutNodesForCapital();
    const corePositions = coreNodes.map((node) => positions.get(node.id)).filter(Boolean);
    const centerX = corePositions.length ? corePositions.reduce((sum, pos) => sum + pos.x, 0) / corePositions.length : WIDTH / 2;
    const centerY = corePositions.length ? corePositions.reduce((sum, pos) => sum + pos.y, 0) / corePositions.length : HEIGHT / 2;
    const themes = Array.from(new Set(contextNodes.map(themeKey))).sort((a, b) => themeLabel(a).localeCompare(themeLabel(b), "es"));
    const themeIndex = new Map(themes.map((theme, index) => [theme, index]));
    const golden = Math.PI * (3 - Math.sqrt(5));
    const byThemeSeen = new Map();

    const connectedRadius = corePositions.length
      ? Math.max(...corePositions.map((pos) => Math.hypot(pos.x - centerX, pos.y - centerY)))
      : 240;

    contextNodes
      .slice()
      .sort((a, b) => themeKey(a).localeCompare(themeKey(b), "es") || a.label.localeCompare(b.label, "es"))
      .forEach((node) => {
        const key = themeKey(node);
        const indexInTheme = byThemeSeen.get(key) || 0;
        byThemeSeen.set(key, indexInTheme + 1);
        const themeAngle = ((themeIndex.get(key) || 0) / Math.max(1, themes.length)) * Math.PI * 2 - Math.PI / 2;
        const localAngle = themeAngle + (indexInTheme * golden) * 0.28 + (seeded(node.id, "context-angle") - 0.5) * 0.34;
        const ring = Math.max(connectedRadius + 105, 315) + (indexInTheme % 7) * 8 + seeded(node.id, "context-ring") * 42;
        const sideBias = 1 + (seeded(key, "theme-side") - 0.5) * 0.18;
        positions.set(node.id, {
          x: centerX + Math.cos(localAngle) * ring * sideBias,
          y: centerY + Math.sin(localAngle) * ring * 0.58,
          vx: 0,
          vy: 0
        });
      });
  }

  function runForceAtlas(iterations = 520) {
    if (!activeNodes.length) return;
    if (modeSelect.value === "coverage_gaps") {
      initializeGapPositions();
      preventOverlap(28);
      return;
    }
    const values = layoutNodesForCapital().map((node) => ({ node, pos: positions.get(node.id) })).filter((item) => item.pos);
    const centerX = WIDTH / 2;
    const centerY = HEIGHT / 2;
    const stats = layoutStats();
    const visibleFundsByStartup = buildVisibleFundIndex();
    for (let step = 0; step < iterations; step += 1) {
      values.forEach((item) => { item.pos.vx = 0; item.pos.vy = 0; });
      for (let i = 0; i < values.length; i += 1) {
        for (let j = i + 1; j < values.length; j += 1) {
          const a = values[i];
          const b = values[j];
          const dx = a.pos.x - b.pos.x;
          const dy = a.pos.y - b.pos.y;
          const dist2 = Math.max(120, dx * dx + dy * dy);
          const dist = Math.sqrt(dist2);
          const ra = nodeRadius(a.node);
          const rb = nodeRadius(b.node);
          const sameTypeDamp = a.node.type === b.node.type && a.node.type === "startup" ? 0.82 : 1;
          const hubBoost = a.node.type === "fund" || b.node.type === "fund" ? 1.15 : 1;
          const coPortfolioDamp = a.node.type === "startup" && b.node.type === "startup" && shareVisibleFund(a.node.id, b.node.id, visibleFundsByStartup) ? 0.58 : 1;
          const force = (stats.repulsion + (ra + rb) * 390) * sameTypeDamp * hubBoost * coPortfolioDamp / dist2;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.pos.vx += fx;
          a.pos.vy += fy;
          b.pos.vx -= fx;
          b.pos.vy -= fy;
        }
      }
      activeEdges.forEach((edge) => {
        const a = positions.get(edge.source);
        const b = positions.get(edge.target);
        if (!a || !b) return;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const desired = edge.type === "co_investment"
          ? 112 + Math.min(40, stats.funds * 1.1)
          : edge.source.startsWith("idb") || edge.type.includes("lp")
            ? 132
            : stats.edgeLength;
        const evidenceBoost = edge.evidence_tier === "public_url" ? 1.16 : 0.86;
        const spring = (dist - desired) * 0.0135 * edgeWeight(edge) * evidenceBoost;
        const fx = (dx / dist) * spring;
        const fy = (dy / dist) * spring;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      });
      values.forEach(({ node, pos }) => {
        const typePull = node.type === "allocator" ? { x: centerX, y: HEIGHT * 0.34 } : node.type === "fund" ? { x: centerX * 0.99, y: centerY } : { x: centerX * 1.01, y: centerY * 1.01 };
        const typeStrength = node.type === "fund" ? 0.00052 : 0.0003;
        pos.vx += (typePull.x - pos.x) * typeStrength;
        pos.vy += (typePull.y - pos.y) * typeStrength;
        const dxCenter = centerX - pos.x;
        const dyCenter = centerY - pos.y;
        const distCenter = Math.sqrt(dxCenter * dxCenter + dyCenter * dyCenter);
        const gravity = 0.000072 + Math.max(0, distCenter - 780) * 0.00000062;
        pos.vx += dxCenter * gravity;
        pos.vy += dyCenter * gravity;
        const speed = step < 120 ? 8.6 : 5.2;
        pos.x += Math.max(-speed, Math.min(speed, pos.vx));
        pos.y += Math.max(-speed, Math.min(speed, pos.vy));
      });
      if (step % 18 === 0) preventOverlap();
    }
    preventOverlap(24);
    positionPeripheralLeaves();
    preventOverlap(12);
    positionContextNodes();
  }

  function positionPeripheralLeaves() {
    const nodesById = new Map(activeNodes.map((node) => [node.id, node]));
    const leavesByFund = new Map();
    activeEdges.forEach((edge) => {
      const source = nodesById.get(edge.source);
      const target = nodesById.get(edge.target);
      if (!source || !target || source.type !== "fund" || target.type !== "startup") return;
      if (Number(target.visible_degree || 0) !== 1) return;
      if (Number(source.visible_degree || 0) > 36) return;
      if (!leavesByFund.has(source.id)) leavesByFund.set(source.id, []);
      leavesByFund.get(source.id).push(target);
    });

    const golden = Math.PI * (3 - Math.sqrt(5));
    leavesByFund.forEach((leaves, fundId) => {
      const fund = nodesById.get(fundId);
      const center = positions.get(fundId);
      if (!fund || !center || leaves.length < 3) return;
      const start = seeded(fundId, "leaf-fan") * Math.PI * 2;
      leaves
        .slice()
        .sort((a, b) => a.label.localeCompare(b.label, "es"))
        .forEach((leaf, index) => {
          const pos = positions.get(leaf.id);
          if (!pos) return;
          const angle = start + index * golden;
          const ring = nodeRadius(fund) + 72 + Math.floor(index / 11) * 34 + seeded(leaf.id, "leaf-ring") * 18;
          pos.x += (center.x + Math.cos(angle) * ring - pos.x) * 0.78;
          pos.y += (center.y + Math.sin(angle) * ring * 0.82 - pos.y) * 0.78;
        });
    });
  }

  function buildVisibleFundIndex() {
    const index = new Map();
    activeEdges.forEach((edge) => {
      if (allNodesById.get(edge.source)?.type !== "fund") return;
      if (allNodesById.get(edge.target)?.type !== "startup") return;
      if (!index.has(edge.target)) index.set(edge.target, new Set());
      index.get(edge.target).add(edge.source);
    });
    return index;
  }

  function shareVisibleFund(leftId, rightId, visibleFundsByStartup) {
    const leftFunds = visibleFundsByStartup.get(leftId);
    const rightFunds = visibleFundsByStartup.get(rightId);
    if (!leftFunds || !rightFunds) return false;
    for (const fund of leftFunds) {
      if (rightFunds.has(fund)) return true;
    }
    return false;
  }

  function preventOverlap(iterations = 12) {
    const overlapNodes = layoutNodesForCapital();
    for (let iter = 0; iter < iterations; iter += 1) {
      for (let i = 0; i < overlapNodes.length; i += 1) {
        for (let j = i + 1; j < overlapNodes.length; j += 1) {
          const a = overlapNodes[i];
          const b = overlapNodes[j];
          const pa = positions.get(a.id);
          const pb = positions.get(b.id);
          if (!pa || !pb) continue;
          const dx = pb.x - pa.x;
          const dy = pb.y - pa.y;
          const dist = Math.max(0.1, Math.sqrt(dx * dx + dy * dy));
          const minDist = nodeRadius(a) + nodeRadius(b) + 4;
          if (dist >= minDist) continue;
          const push = (minDist - dist) * 0.52;
          const ux = dx / dist;
          const uy = dy / dist;
          pa.x -= ux * push;
          pa.y -= uy * push;
          pb.x += ux * push;
          pb.y += uy * push;
        }
      }
    }
  }

  function edgePath(edge) {
    const a = positions.get(edge.source);
    const b = positions.get(edge.target);
    if (!a || !b) return "";
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
    const mx = (a.x + b.x) / 2;
    const my = (a.y + b.y) / 2;
    const curve = Math.min(58, dist * 0.08);
    const cx = mx - (dy / dist) * curve;
    const cy = my + (dx / dist) * curve;
    return `M ${a.x} ${a.y} Q ${cx} ${cy} ${b.x} ${b.y}`;
  }

  function focusEdge() {
    if (selectedEdgeId) return activeEdges.find((edge) => edge.id === selectedEdgeId) || null;
    if (selectedId) return null;
    return activeEdges.find((edge) => edge.id === hoverEdgeId) || null;
  }

  function connectedToSelected(id) {
    const edgeFocus = focusEdge();
    if (edgeFocus) return id === edgeFocus.source || id === edgeFocus.target;
    const focusId = selectedId || hoverId;
    if (focusId) {
      return id === focusId || activeEdges.some((edge) =>
        (edge.source === focusId && edge.target === id) ||
        (edge.target === focusId && edge.source === id)
      );
    }
    return nodePassesHighlightFilters(activeNodes.find((node) => node.id === id) || allNodesById.get(id));
  }

  function focusedEdgeSet() {
    const edgeFocus = focusEdge();
    const focusId = selectedId || hoverId;
    const set = new Set();
    if (edgeFocus) {
      activeEdges.forEach((edge, index) => {
        if (edge.id === edgeFocus.id) set.add(index);
      });
      return set;
    }
    if (!focusId) return set;
    activeEdges.forEach((edge, index) => {
      if (edge.source === focusId || edge.target === focusId) set.add(index);
    });
    return set;
  }

  function renderTooltip(node) {
    if (!tooltipEl) return;
    if (!node) {
      tooltipEl.classList.remove("visible");
      tooltipEl.innerHTML = "";
      return;
    }
    const connected = activeEdges.filter((edge) => edge.source === node.id || edge.target === node.id);
    const publicEdges = connected.filter((edge) => edge.evidence_tier === "public_url" || edge.type === "co_investment").length;
    const theme = node.type === "startup" ? themeLabel(themeKey(node)) : clean(node.investor_subtype) || titleCase(node.type);
    tooltipEl.innerHTML = `
      <div class="tooltip-kicker">${escapeHtml(titleCase(node.type))}</div>
      <div class="tooltip-title">${escapeHtml(node.label)}</div>
      <div class="tooltip-meta">${escapeHtml(theme)}${node.country ? ` · ${escapeHtml(node.country)}` : ""}${node.summary ? ` · ${escapeHtml(node.summary).slice(0, 150)}${node.summary.length > 150 ? "..." : ""}` : ""}</div>
      <div class="tooltip-stats">
        <div class="tooltip-stat"><span>Weighted degree</span><strong>${nodeWeight(node).toFixed(1)}</strong></div>
        ${node.type === "startup" ? `<div class="tooltip-stat"><span>Diametro</span><strong>${startupCapitalSignal(node).toFixed(1)}</strong></div>` : ""}
        <div class="tooltip-stat"><span>Edges</span><strong>${connected.length}</strong></div>
        <div class="tooltip-stat"><span>Publicas</span><strong>${publicEdges}</strong></div>
      </div>
    `;
    tooltipEl.classList.add("visible");
  }

  function moveTooltip(clientX, clientY) {
    if (!tooltipEl) return;
    const wrap = tooltipEl.parentElement;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const cardWidth = tooltipEl.offsetWidth || 360;
    const cardHeight = tooltipEl.offsetHeight || 190;
    let left = clientX - rect.left + 18;
    let top = clientY - rect.top + 18;
    if (left + cardWidth > rect.width - 12) left = clientX - rect.left - cardWidth - 18;
    if (top + cardHeight > rect.height - 12) top = clientY - rect.top - cardHeight - 18;
    tooltipEl.style.left = `${Math.max(12, left)}px`;
    tooltipEl.style.top = `${Math.max(12, top)}px`;
  }

  function hideTooltip() {
    if (!tooltipEl) return;
    tooltipEl.classList.remove("visible");
    tooltipEl.innerHTML = "";
  }

  function renderNodeTooltip(node, event) {
    if (!tooltipEl || !node) return;
    const connected = activeEdges.filter((edge) => edge.source === node.id || edge.target === node.id);
    const publicEdges = connected.filter((edge) => edge.evidence_tier === "public_url" || edge.type === "co_investment").length;
    const theme = node.type === "startup" ? themeLabel(themeKey(node)) : clean(node.investor_subtype) || titleCase(node.type);
    const topNeighbors = connected
      .slice()
      .sort((a, b) => edgeWeight(b) - edgeWeight(a))
      .slice(0, 3)
      .map((edge) => allNodesById.get(edge.source === node.id ? edge.target : edge.source)?.label)
      .filter(Boolean);
    tooltipEl.innerHTML = `
      <div class="tooltip-kicker">${escapeHtml(titleCase(node.type))}</div>
      <div class="tooltip-title">${escapeHtml(node.label)}</div>
      <div class="tooltip-chip-row">
        <span class="tooltip-chip"><span class="tooltip-chip-dot" style="background:${nodeColor(node)}"></span>${escapeHtml(theme)}</span>
        ${node.country ? `<span class="tooltip-chip">${escapeHtml(node.country)}</span>` : ""}
        ${node.scope_decision ? `<span class="tooltip-chip">${escapeHtml(node.scope_decision)}</span>` : ""}
      </div>
      ${node.summary ? `<div class="tooltip-meta">${escapeHtml(node.summary).slice(0, 185)}${node.summary.length > 185 ? "..." : ""}</div>` : ""}
      <div class="tooltip-stats">
        <div class="tooltip-stat"><span>Weighted degree</span><strong>${nodeWeight(node).toFixed(1)}</strong></div>
        ${node.type === "startup" ? `<div class="tooltip-stat"><span>Diametro</span><strong>${startupCapitalSignal(node).toFixed(1)}</strong></div>` : ""}
        <div class="tooltip-stat"><span>Edges</span><strong>${connected.length}</strong></div>
        <div class="tooltip-stat"><span>Publicas</span><strong>${publicEdges}</strong></div>
      </div>
      ${topNeighbors.length ? `<div class="tooltip-meta"><strong>Conecta con:</strong> ${escapeHtml(topNeighbors.join(", "))}</div>` : ""}
      <div class="tooltip-meta">Click para fijar este vecindario.</div>
    `;
    moveTooltip(event.clientX, event.clientY);
    tooltipEl.classList.add("visible");
  }

  function renderEdgeTooltip(edge, event) {
    if (!tooltipEl || !edge) return;
    const source = allNodesById.get(edge.source);
    const target = allNodesById.get(edge.target);
    tooltipEl.innerHTML = `
      <div class="tooltip-kicker">Relacion de capital</div>
      <div class="tooltip-title">${escapeHtml(source?.label || edge.source)} -> ${escapeHtml(target?.label || edge.target)}</div>
      <div class="tooltip-chip-row">
        <span class="tooltip-chip">${escapeHtml(edgeLabel(edge))}</span>
        <span class="tooltip-chip">conf ${escapeHtml(edge.confidence ?? "n/d")}</span>
        <span class="tooltip-chip">${escapeHtml(edge.evidence_tier || "canonical")}</span>
      </div>
      ${edge.evidence ? `<div class="tooltip-meta">${escapeHtml(edge.evidence).slice(0, 210)}${edge.evidence.length > 210 ? "..." : ""}</div>` : ""}
      <div class="tooltip-stats">
        <div class="tooltip-stat"><span>Peso visual</span><strong>${edgeWeight(edge).toFixed(1)}</strong></div>
        <div class="tooltip-stat"><span>Tipo</span><strong>${edge.type === "co_investment" ? "co" : "edge"}</strong></div>
        <div class="tooltip-stat"><span>Fuente</span><strong>${edge.source_url ? "URL" : "canon"}</strong></div>
      </div>
      <div class="tooltip-meta">Click para fijar esta relacion.</div>
    `;
    moveTooltip(event.clientX, event.clientY);
    tooltipEl.classList.add("visible");
  }

  function renderGapThemeLabels() {
    if (modeSelect.value !== "coverage_gaps" || !showLabels) return;
    const groups = Array.from(
      activeNodes
        .filter((node) => node.type === "startup")
        .reduce((map, node) => {
          const key = themeKey(node);
          const pos = positions.get(node.id);
          if (!pos) return map;
          if (!map.has(key)) map.set(key, []);
          map.get(key).push({ node, pos });
          return map;
        }, new Map())
    );
    groups.forEach(([theme, items]) => {
      if (!items.length) return;
      const x = items.reduce((sum, item) => sum + item.pos.x, 0) / items.length;
      const y = items.reduce((sum, item) => sum + item.pos.y, 0) / items.length;
      const label = makeSvg("text", {
        x,
        y: y - 36,
        "text-anchor": "middle",
        "font-size": "15",
        "font-family": "Georgia, serif",
        "font-weight": "900",
        fill: themeColor(theme),
        stroke: "rgba(255,252,246,0.98)",
        "stroke-width": "5",
        "paint-order": "stroke",
        "pointer-events": "none"
      });
      label.textContent = `${themeLabel(theme)} · ${items.length}`;
      labelLayer.append(label);
    });
  }

  function renderGraph() {
    edgeLayer.innerHTML = "";
    nodeLayer.innerHTML = "";
    labelLayer.innerHTML = "";
    const activeEdgeSet = focusedEdgeSet();
    const hasFocus = Boolean(selectedId || hoverId || selectedEdgeId || hoverEdgeId);

    activeEdges.forEach((edge, index) => {
      const filterActive = edgePassesHighlightFilters(edge);
      const active = hasFocus ? activeEdgeSet.has(index) : filterActive;
      const isSelectedFocusEdge = Boolean(selectedId || selectedEdgeId) && active;
      const path = makeSvg("path", {
        d: edgePath(edge),
        fill: "none",
        stroke: edgeColor(edge),
        "stroke-width": String(active ? edgeWeight(edge) * (isSelectedFocusEdge ? 1.34 : 1) : 0.64),
        opacity: active ? (isSelectedFocusEdge ? "0.96" : (edge.evidence_tier === "public_url" || edge.type === "co_investment" ? "0.82" : "0.52")) : "0.045",
        "stroke-dasharray": edge.evidence_tier === "public_url" || edge.type === "co_investment" ? "" : "4 5",
        "stroke-linecap": "round"
      });
      path.style.cursor = "pointer";
      path.dataset.edgeId = edge.id;
      path.addEventListener("mouseenter", (event) => {
        hoverEdgeId = edge.id;
        renderEdgeTooltip(edge, event);
      });
      path.addEventListener("mousemove", (event) => renderEdgeTooltip(edge, event));
      path.addEventListener("mouseleave", () => {
        hoverEdgeId = null;
        hideTooltip();
      });
      path.addEventListener("click", (event) => {
        event.stopPropagation();
        selectedId = null;
        hoverId = null;
        hoverEdgeId = null;
        hideTooltip();
        selectedEdgeId = selectedEdgeId === edge.id ? null : edge.id;
        renderGraph();
        renderDetail(null);
      });
      const title = makeSvg("title", {});
      title.textContent = `${titleCase(edge.type)} | conf ${edge.confidence ?? "n/d"} | ${edge.evidence_tier || "derived"}`;
      path.append(title);
      edgeLayer.append(path);
    });

    activeNodes
      .slice()
      .sort((a, b) => nodeRadius(a) - nodeRadius(b))
      .forEach((node) => {
        const pos = positions.get(node.id);
        if (!pos) return;
        const active = connectedToSelected(node.id);
        const selected = selectedId === node.id;
        const hovered = hoverId === node.id;
        const radius = nodeRadius(node);
        const isContextStartup = node.type === "startup" && Number(node.visible_degree || 0) === 0;
        const filterDimmed = hasActiveFilters() && !nodePassesHighlightFilters(node) && !hasFocus;
        const selectedNeighbor = hasFocus && active && !selected && !hovered;
        const group = makeSvg("g", { transform: `translate(${pos.x} ${pos.y})` });
        group.style.cursor = "pointer";
        group.dataset.nodeId = node.id;
        const halo = makeSvg("circle", {
          r: radius * (selected ? 2.55 : selectedNeighbor ? 2.02 : 1.72),
          fill: nodeColor(node),
          opacity: selected ? "0.34" : hovered ? "0.24" : selectedNeighbor ? "0.18" : filterDimmed ? "0" : node.type === "fund" && nodeWeight(node) >= 14 ? "0.14" : "0"
        });
        const shape = node.type === "allocator"
          ? makeSvg("polygon", {
              points: `0,${-radius} ${radius},0 0,${radius} ${-radius},0`,
              fill: nodeColor(node),
              stroke: selected || hovered ? "#111" : selectedNeighbor ? "#3d3227" : "#fffaf1",
              "stroke-width": selected || hovered ? "3.8" : selectedNeighbor ? "2.6" : "1.7",
              opacity: active ? "0.97" : "0.08"
            })
          : makeSvg("circle", {
              r: radius,
              fill: nodeColor(node),
              stroke: selected || hovered ? "#111" : selectedNeighbor ? "#3d3227" : "#fffaf1",
              "stroke-width": selected || hovered ? "3.8" : selectedNeighbor ? "2.5" : isContextStartup ? "0.8" : node.type === "fund" ? "2.4" : "1.4",
              opacity: selected ? "1" : isContextStartup ? (active ? "0.18" : "0.035") : active ? "0.96" : "0.075"
            });
        const title = makeSvg("title", {});
        title.textContent = `${node.label} | weighted degree ${nodeWeight(node).toFixed(1)} | capital signal ${startupCapitalSignal(node).toFixed(1)} | edges ${node.visible_degree || 0}`;
        shape.append(title);
        group.append(halo, shape);
        group.addEventListener("mouseenter", (event) => {
          hoverId = node.id;
          renderNodeTooltip(node, event);
        });
        group.addEventListener("mousemove", (event) => renderNodeTooltip(node, event));
        group.addEventListener("mouseleave", () => {
          hoverId = null;
          hideTooltip();
        });
        group.addEventListener("click", (event) => {
          event.stopPropagation();
          selectedEdgeId = null;
          hoverId = null;
          hoverEdgeId = null;
          hideTooltip();
          selectedId = selectedId === node.id ? null : node.id;
          renderGraph();
          renderDetail(selectedId);
        });
        nodeLayer.append(group);

        const shouldLabel = showLabels && (selected || hovered || selectedNeighbor || active && (node.type !== "startup" || nodeWeight(node) >= 3.2) || nodeWeight(node) >= 10);
        if (shouldLabel) {
          const label = makeSvg("text", {
            x: pos.x + (node.type === "startup" ? radius + 8 : 0),
            y: pos.y + (node.type === "startup" ? 4 : -radius - 10),
            "text-anchor": node.type === "startup" ? "start" : "middle",
            "font-size": node.type === "startup" ? (selected || hovered ? "16" : "13.2") : (selected || hovered ? "19" : "16.8"),
            "font-family": "Georgia, serif",
            "font-weight": node.type === "startup" ? "800" : "900",
            fill: node.type === "startup" ? "#352d26" : "#0d0d0d",
            stroke: "rgba(255,252,246,0.98)",
            "stroke-width": selected || hovered ? "6.2" : "5.4",
            "paint-order": "stroke",
            "pointer-events": "none",
            opacity: active ? "1" : "0.14"
          });
          label.textContent = node.label;
          labelLayer.append(label);
        }
      });
    renderGapThemeLabels();
  }

  function fitToGraph() {
    if (!activeNodes.length) return;
    const fitNodes = layoutNodesForCapital().length ? layoutNodesForCapital() : activeNodes;
    const xs = fitNodes.map((node) => positions.get(node.id)?.x || WIDTH / 2);
    const ys = fitNodes.map((node) => positions.get(node.id)?.y || HEIGHT / 2);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const graphWidth = Math.max(1, maxX - minX);
    const graphHeight = Math.max(1, maxY - minY);
    const paddingX = 56;
    const paddingY = 54;
    transform.k = Math.min((WIDTH - paddingX * 2) / graphWidth, (HEIGHT - paddingY * 2) / graphHeight, 1.72);
    transform.x = WIDTH / 2 - ((minX + maxX) / 2) * transform.k;
    transform.y = HEIGHT / 2 - ((minY + maxY) / 2) * transform.k;
    updateViewport();
  }

  function updateViewport() {
    viewport.setAttribute("transform", `translate(${transform.x} ${transform.y}) scale(${transform.k})`);
  }

  function renderSummary() {
    const funds = activeNodes.filter((node) => node.type === "fund").length;
    const startups = activeNodes.filter((node) => node.type === "startup").length;
    const mappedStartups = activeNodes.filter((node) => node.type === "startup" && Number(node.visible_degree || 0) > 0).length;
    const contextStartups = activeNodes.filter((node) => node.type === "startup" && Number(node.visible_degree || 0) === 0).length;
    const allocators = activeNodes.filter((node) => node.type === "allocator").length;
    const audited = activeEdges.filter((edge) => edge.evidence_tier === "public_url" || edge.type === "co_investment").length;
    const highlightedEdges = activeEdges.filter(edgePassesHighlightFilters).length;
    const highlightedNodes = activeNodes.filter(nodePassesHighlightFilters).length;
    const weightedStartupNodes = activeNodes.filter((node) => node.type === "startup" && startupCapitalSignal(node) > 0);
    const maxStartupSignal = weightedStartupNodes.length ? Math.max(...weightedStartupNodes.map(startupCapitalSignal)) : 0;
    const includeUniverse = (payload.nodes || []).filter((node) => node.type === "startup" && node.scope_decision === "include");
    const includeMapped = includeUniverse.filter((node) => String(node.capital_status || "") === "capital_mapped").length;
    const coveragePct = includeUniverse.length ? Math.round((includeMapped / includeUniverse.length) * 100) : 0;
    const publicPct = activeEdges.length ? Math.round((audited / activeEdges.length) * 100) : 0;
    summaryEl.innerHTML = [
      ["Cobertura BIO", `${coveragePct}%`],
      ["Edges publicos", `${publicPct}%`],
      ["Fondos", funds],
      ["Startups", startups],
      ["Con capital", mappedStartups],
      ["Sin edge", contextStartups]
    ].map(([label, value]) => `
      <div class="stat-card">
        <div class="stat-label">${label}</div>
        <div class="stat-value">${typeof value === "number" ? Number(value).toLocaleString("en-US") : escapeHtml(value)}</div>
      </div>
    `).join("");
  }

  function fundRecommendationsForStartup(startup, limit = 7) {
    if (!startup || startup.type !== "startup") return [];
    const targetTheme = themeKey(startup);
    const targetCountry = clean(startup.country);
    const scores = new Map();
    rawEdges.forEach((edge) => {
      if (allNodesById.get(edge.source)?.type !== "fund") return;
      const peer = allNodesById.get(edge.target);
      if (!peer || peer.type !== "startup" || peer.id === startup.id) return;
      if (peer.scope_decision !== "include") return;
      const sameTheme = themeKey(peer) === targetTheme;
      const sameCountry = targetCountry && clean(peer.country) === targetCountry;
      if (!sameTheme && !sameCountry) return;
      const current = scores.get(edge.source) || {
        fund: allNodesById.get(edge.source),
        score: 0,
        sameTheme: 0,
        sameCountry: 0,
        publicEdges: 0,
        examples: new Set()
      };
      current.score += (sameTheme ? 4 : 0) + (sameCountry ? 1.2 : 0) + Number(edge.confidence || 0) + (edge.evidence_tier === "public_url" ? 1.3 : 0);
      if (sameTheme) current.sameTheme += 1;
      if (sameCountry) current.sameCountry += 1;
      if (edge.evidence_tier === "public_url") current.publicEdges += 1;
      if (current.examples.size < 4) current.examples.add(peer.label);
      scores.set(edge.source, current);
    });
    return Array.from(scores.values())
      .filter((item) => item.fund)
      .sort((a, b) => b.score - a.score || b.sameTheme - a.sameTheme || String(a.fund.label).localeCompare(String(b.fund.label), "es"))
      .slice(0, limit)
      .map((item) => ({
        ...item,
        examples: Array.from(item.examples)
      }));
  }

  function renderGapPriorities() {
    const rows = Array.from(
      activeNodes
        .filter((node) => node.type === "startup")
        .reduce((map, node) => {
          const key = themeKey(node);
          if (!map.has(key)) map.set(key, { theme: key, count: 0, countries: new Map(), examples: [] });
          const row = map.get(key);
          row.count += 1;
          const country = clean(node.country) || "s/pais";
          row.countries.set(country, (row.countries.get(country) || 0) + 1);
          if (row.examples.length < 4) row.examples.push(node.label);
          return map;
        }, new Map())
    )
      .sort((a, b) => b.count - a.count || themeLabel(a.theme).localeCompare(themeLabel(b.theme), "es"))
      .slice(0, 12);
    rankingEl.innerHTML = rows.length ? rows.map((row) => {
      const countries = Array.from(row.countries.entries())
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "es"))
        .slice(0, 3)
        .map(([country, count]) => `${country} ${count}`)
        .join(" · ");
      return `
        <button class="ranking-row" type="button" data-gap-theme="${escapeHtml(row.theme)}">
          <div class="ranking-top"><span>${escapeHtml(themeLabel(row.theme))}</span><span>${row.count}</span></div>
          <div class="ranking-meta">${escapeHtml(countries || "sin pais")} &middot; ${escapeHtml(row.examples.join(", "))}</div>
        </button>
      `;
    }).join("") : '<div class="detail-muted">No hay vacios visibles con estos filtros.</div>';
    rankingEl.querySelectorAll("[data-gap-theme]").forEach((button) => {
      button.addEventListener("click", () => {
        themeSelect.value = button.dataset.gapTheme || "all";
        rebuild({ rerun: true });
      });
    });
  }

  function renderRanking() {
    if (modeSelect.value === "coverage_gaps") {
      renderGapPriorities();
      return;
    }
    const rows = activeNodes
      .filter((node) => node.type === "fund" || node.type === "allocator")
      .sort((a, b) => nodeWeight(b) - nodeWeight(a) || Number(b.visible_degree || 0) - Number(a.visible_degree || 0) || a.label.localeCompare(b.label, "es"))
      .slice(0, 12);
    rankingEl.innerHTML = rows.map((node) => `
      <button class="ranking-row${selectedId === node.id ? " active" : ""}" type="button" data-node-id="${escapeHtml(node.id)}">
        <div class="ranking-top"><span>${escapeHtml(node.label)}</span><span>${nodeWeight(node).toFixed(1)}</span></div>
        <div class="ranking-meta">${node.type === "allocator" ? "Capital institucional / allocator" : "Fondo / inversor"} &middot; ${node.visible_degree || 0} edges &middot; ${escapeHtml(clean(node.source_presence) || "sin fuente")}</div>
      </button>
    `).join("");
    rankingEl.querySelectorAll("[data-node-id]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedEdgeId = null;
        selectedId = button.dataset.nodeId;
        renderGraph();
        renderDetail(selectedId);
      });
    });
  }

  function renderThemeMix() {
    if (!themeMixEl) return;
    const counts = new Map();
    const mapped = new Map();
    activeNodes
      .filter((node) => node.type === "startup")
      .forEach((node) => {
        const key = themeKey(node);
        counts.set(key, (counts.get(key) || 0) + 1);
        if (Number(node.visible_degree || 0) > 0) mapped.set(key, (mapped.get(key) || 0) + 1);
      });
    const rows = Array.from(counts.entries())
      .sort((a, b) => ((b[1] - (mapped.get(b[0]) || 0)) - (a[1] - (mapped.get(a[0]) || 0))) || b[1] - a[1] || themeLabel(a[0]).localeCompare(themeLabel(b[0]), "es"))
      .slice(0, 9);
    const max = Math.max(1, ...rows.map(([, count]) => count));
    themeMixEl.innerHTML = rows.length ? rows.map(([theme, count]) => {
      const mappedCount = mapped.get(theme) || 0;
      const gapCount = Math.max(0, count - mappedCount);
      const barWidth = Math.round((count / max) * 100);
      const mappedWidth = count ? Math.round((mappedCount / count) * barWidth) : 0;
      const gapWidth = Math.max(0, barWidth - mappedWidth);
      return `
        <div class="theme-mix-row">
          <div class="theme-mix-top"><span>${escapeHtml(themeLabel(theme))}</span><span>${mappedCount}/${count}</span></div>
          <div class="theme-mix-bar">
            <div class="theme-mix-fill mapped" style="width:${mappedWidth}%;background:${themeColor(theme)}"></div>
            <div class="theme-mix-fill gap" style="width:${gapWidth}%"></div>
          </div>
          <div class="theme-mix-foot">${gapCount} sin capital mapeado visible</div>
        </div>
      `;
    }).join("") : '<div class="detail-muted">No hay startups visibles con estos filtros.</div>';
  }

  function renderEdgeDetail(edge) {
    const source = allNodesById.get(edge.source);
    const target = allNodesById.get(edge.target);
    badgeEl.textContent = "Relacion";
    badgeEl.className = "pill";
    detailEl.innerHTML = `
      <div class="detail-chip-row">
        <span class="detail-chip">${escapeHtml(edgeLabel(edge))}</span>
        <span class="detail-chip">conf ${escapeHtml(edge.confidence ?? "n/d")}</span>
        <span class="detail-chip">${escapeHtml(edge.evidence_tier || "canonical")}</span>
      </div>
      <div>
        <h3 style="margin:10px 0 6px;">${escapeHtml(source?.label || edge.source)} -> ${escapeHtml(target?.label || edge.target)}</h3>
        <div class="detail-muted">Relacion fijada. Click en un nodo para abrir su vecindario completo.</div>
      </div>
      <div class="detail-metric-grid">
        <div class="detail-metric"><span>Peso visual</span><strong>${edgeWeight(edge).toFixed(1)}</strong></div>
        <div class="detail-metric"><span>Confianza</span><strong>${edge.confidence ?? "n/d"}</strong></div>
        <div class="detail-metric"><span>Fuente</span><strong>${edge.source_url ? "URL" : "canonica"}</strong></div>
      </div>
      ${edge.evidence ? `<div class="detail-muted">${escapeHtml(edge.evidence)}</div>` : ""}
      ${edge.source_url ? `<div class="detail-muted"><a href="${escapeHtml(edge.source_url)}" target="_blank" rel="noreferrer">Abrir fuente publica</a></div>` : ""}
      <div class="edge-list">
        ${[source, target].filter(Boolean).map((node) => `
          <button class="edge-item" type="button" data-node-id="${escapeHtml(node.id)}">
            <div class="ranking-top"><span>${escapeHtml(node.label)}</span><span>${escapeHtml(titleCase(node.type))}</span></div>
            <div class="ranking-meta">weighted degree ${nodeWeight(activeNodes.find((item) => item.id === node.id) || node).toFixed(1)}</div>
          </button>
        `).join("")}
      </div>
    `;
    detailEl.querySelectorAll("[data-node-id]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedEdgeId = null;
        selectedId = button.dataset.nodeId;
        renderGraph();
        renderDetail(selectedId);
      });
    });
  }

  function pct(part, total) {
    return total ? `${Math.round((part / total) * 100)}%` : "n/d";
  }

  function hostname(url) {
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch (_error) {
      return clean(url);
    }
  }

  function connectionQualityLabel(publicEdges, totalEdges) {
    if (!totalEdges) return "sin conexiones visibles";
    const share = publicEdges / totalEdges;
    if (share >= 0.72) return "relaciones bien documentadas";
    if (share >= 0.35) return "documentacion parcial";
    return "documentacion limitada";
  }

  function connectionRowsForNode(id) {
    return activeEdges
      .filter((edge) => edge.source === id || edge.target === id)
      .map((edge) => {
        const otherId = edge.source === id ? edge.target : edge.source;
        const other = allNodesById.get(otherId);
        return { edge, other };
      })
      .filter((item) => item.other)
      .sort((a, b) =>
        edgeWeight(b.edge) - edgeWeight(a.edge) ||
        Number(b.edge.confidence || 0) - Number(a.edge.confidence || 0) ||
        String(a.other.label).localeCompare(String(b.other.label), "es")
      );
  }

  function evidenceBadge(edge) {
    if (edge.evidence_tier === "public_url") return "URL publica";
    if (edge.type === "co_investment") return "co-investment";
    if (Number(edge.capital_evidence_level || 0) >= 4) return "anuncio";
    if (Number(edge.capital_evidence_level || 0) >= 3) return "especifica";
    return edge.evidence_tier || "canonica";
  }

  function mixForConnections(neighbors, propertyGetter, limit = 5) {
    const counts = new Map();
    neighbors.forEach(({ other }) => {
      const value = clean(propertyGetter(other));
      if (!value) return;
      counts.set(value, (counts.get(value) || 0) + 1);
    });
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0]), "es"))
      .slice(0, limit);
  }

  function firstSentence(text, max = 230) {
    const value = clean(text).replace(/\s+/g, " ");
    if (!value) return "";
    const sentence = value.match(/^(.+?[.!?])\s/)?.[1] || value;
    return sentence.length > max ? `${sentence.slice(0, max - 1).trim()}...` : sentence;
  }

  function investorSubtypeLabel(value) {
    const subtype = clean(value);
    if (!subtype || subtype === "vc_or_investor") return "Fondo / inversor";
    if (subtype === "fund_of_funds") return "Fund of funds";
    if (subtype.includes("development")) return "Banco de desarrollo / LP";
    if (subtype.includes("environmental")) return "Capital ambiental institucional";
    if (subtype.includes("financial")) return "Institucion financiera / LP";
    return titleCase(subtype.replace(/_/g, " "));
  }

  function organizationTypeLabel(node) {
    if (node.type === "startup") return "Startup BIO LATAM";
    if (node.type === "allocator") return "Allocator / LP";
    return investorSubtypeLabel(node.investor_subtype);
  }

  function organizationDescription(node, neighbors) {
    if (node.summary) return firstSentence(node.summary);
    if (node.type === "startup") {
      const theme = themeLabel(themeKey(node));
      return `${node.label} aparece como startup ${theme}${node.country ? ` basada en ${node.country}` : ""}. Todavia necesita una descripcion externa mas fuerte para que el mapa la explique mejor.`;
    }
    const startupNeighbors = neighbors.filter(({ other }) => other.type === "startup");
    const themeRows = mixForConnections(startupNeighbors, (startup) => themeKey(startup), 2);
    const topThemes = themeRows.map(([theme, count]) => `${themeLabel(theme)} (${count})`).join(", ");
    return `${node.label} aparece como ${investorSubtypeLabel(node.investor_subtype).toLowerCase()} dentro de la red de capital BIO LATAM${topThemes ? `, con cartera visible concentrada en ${topThemes}` : ""}.`;
  }

  function ecosystemRole(node, neighbors) {
    const connectedFunds = neighbors.filter(({ other }) => other.type === "fund" || other.type === "allocator").length;
    const connectedStartups = neighbors.filter(({ other }) => other.type === "startup").length;
    if (node.type === "startup") {
      const theme = themeLabel(themeKey(node));
      if (connectedFunds) {
        return `Muestra una oportunidad o caso operativo dentro de ${theme}. Su valor en el mapa es ver que tipo de capital ya se acerca a esta solucion y que fondos comparten tesis o vecindad con ella.`;
      }
      return `Muestra una oportunidad dentro de ${theme}, pero todavia no tiene capital visible en esta red. Para el usuario funciona como pista de relevamiento: validar inversores, rondas o si realmente debe quedar como caso aislado.`;
    }
    const startupNeighbors = neighbors.filter(({ other }) => other.type === "startup");
    const themeRows = mixForConnections(startupNeighbors, (startup) => themeKey(startup), 3);
    const topThemes = themeRows.map(([theme, count]) => `${themeLabel(theme)} (${count})`).join(", ");
    if (!connectedStartups) {
      return "Aparece como actor de capital, pero todavia no tiene una cartera BIO visible en esta vista.";
    }
    return `Canaliza capital hacia ${connectedStartups} startup${connectedStartups === 1 ? "" : "s"} BIO visible${connectedStartups === 1 ? "" : "s"}${topThemes ? `, principalmente en ${topThemes}` : ""}.`;
  }

  function renderOrganizationHeader(node, neighbors, subtitle) {
    const description = organizationDescription(node, neighbors);
    return `
      <div class="detail-title-card organization-card">
        <div class="organization-kicker">${escapeHtml(organizationTypeLabel(node))}</div>
        <h3>${escapeHtml(node.label)}</h3>
        <div class="detail-subtitle">${escapeHtml(subtitle)}</div>
        <p>${escapeHtml(description)}</p>
      </div>
      <div class="org-insight-grid">
        <div class="org-insight-card">
          <span>Por que importa</span>
          <strong>${escapeHtml(ecosystemRole(node, neighbors))}</strong>
        </div>
      </div>
    `;
  }

  function renderMiniBars(rows, { colorFor = () => "#0f766e", total = null } = {}) {
    const max = Math.max(1, ...rows.map(([, count]) => count));
    const denominator = total || rows.reduce((sum, [, value]) => sum + value, 0);
    return rows.map(([label, count]) => {
      const width = Math.max(8, Math.round((count / max) * 100));
      return `
        <div class="detail-bar-row">
          <div class="detail-bar-top"><span>${escapeHtml(themeLabel(label) || label)}</span><strong>${count}</strong></div>
          <div class="detail-bar-track"><span style="width:${width}%;background:${escapeHtml(colorFor(label))}"></span></div>
          <div class="detail-bar-foot">${pct(count, denominator)} del foco visible</div>
        </div>
      `;
    }).join("");
  }

  function renderConnectionList(neighbors, currentNode, limit = 14) {
    const rows = neighbors.slice(0, limit);
    if (!rows.length) return '<div class="detail-empty">Sin conexiones visibles con los filtros actuales.</div>';
    return rows.map(({ edge, other }) => {
      const otherTheme = other.type === "startup" ? themeLabel(themeKey(other)) : clean(other.investor_subtype) || titleCase(other.type);
      const sourceText = edge.source_url ? hostname(edge.source_url) : clean(edge.source_presence) || evidenceBadge(edge);
      const relevance = [
        `${edgeWeight(edge).toFixed(1)} peso`,
        `conf ${edge.confidence ?? "n/d"}`,
        evidenceBadge(edge),
        edge.shared_count ? `${edge.shared_count} compartidas` : "",
        currentNode.type === "fund" && other.type === "startup" ? themeLabel(themeKey(other)) : "",
        currentNode.type === "startup" && other.type === "fund" ? clean(other.investor_subtype) || "fondo" : ""
      ].filter(Boolean).join(" · ");
      return `
        <button class="edge-item connection-card" type="button" data-node-id="${escapeHtml(other.id)}">
          <div class="ranking-top"><span>${escapeHtml(other.label)}</span><span>${escapeHtml(edgeLabel(edge))}</span></div>
          <div class="ranking-meta">${escapeHtml(otherTheme)}${other.country ? ` · ${escapeHtml(other.country)}` : ""}</div>
          <div class="connection-evidence">${escapeHtml(relevance)}</div>
          ${sourceText ? `<div class="connection-source">${escapeHtml(sourceText)}</div>` : ""}
        </button>
      `;
    }).join("");
  }

  function fundPortfolioInsight(node, neighbors) {
    if (node.type !== "fund" && node.type !== "allocator") return "";
    const startupNeighbors = neighbors.filter(({ other }) => other.type === "startup");
    const themeRows = mixForConnections(startupNeighbors, (startup) => themeKey(startup), 5);
    const countryRows = mixForConnections(startupNeighbors, (startup) => startup.country, 4);
    return `
      <section class="detail-block">
        <h3>Perfil de cartera visible</h3>
        <div class="detail-muted">Composicion de startups conectadas dentro de los filtros actuales.</div>
        <div class="detail-bars">${themeRows.length ? renderMiniBars(themeRows, { colorFor: themeColor, total: startupNeighbors.length }) : '<div class="detail-empty">Sin startups visibles.</div>'}</div>
        ${countryRows.length ? `<div class="detail-country-line">${countryRows.map(([country, count]) => `<span>${escapeHtml(country)} ${count}</span>`).join("")}</div>` : ""}
      </section>
    `;
  }

  function startupCapitalInsight(node, neighbors, recommendationHtml) {
    if (node.type !== "startup") return "";
    const fundNeighbors = neighbors.filter(({ other }) => other.type === "fund" || other.type === "allocator");
    const fundLine = fundNeighbors.length
      ? `${fundNeighbors.length} fondo${fundNeighbors.length === 1 ? "" : "s"} conectado${fundNeighbors.length === 1 ? "" : "s"}: ${fundNeighbors.slice(0, 5).map(({ other }) => other.label).join(", ")}`
      : "Sin fondos visibles conectados: priorizar busqueda de aristas o validar si debe quedar como contexto.";
    return `
      <section class="detail-block">
        <h3>Lectura para startup</h3>
        <div class="detail-callout">
          <strong>${escapeHtml(themeLabel(themeKey(node)))}</strong>
          <span>${escapeHtml(fundLine)}</span>
        </div>
        ${recommendationHtml ? `
          <h3>Fondos candidatos para investigar</h3>
          <div class="detail-muted">Heuristica por cartera similar, pais, confianza y fuente publica.</div>
          <div class="edge-list compact">${recommendationHtml}</div>
        ` : ""}
      </section>
    `;
  }

  function renderNodeInspector(id) {
    const node = activeNodes.find((item) => item.id === id) || allNodesById.get(id);
    if (!node) return;
    const connected = activeEdges.filter((edge) => edge.source === id || edge.target === id);
    const neighbors = connectionRowsForNode(id);
    const publicEdges = connected.filter((edge) => edge.evidence_tier === "public_url" || edge.type === "co_investment").length;
    const avgConfidence = connected.length
      ? connected.reduce((sum, edge) => sum + Number(edge.confidence || 0), 0) / connected.length
      : 0;
    const recommendations = node.type === "startup" && Number(node.visible_degree || 0) === 0
      ? fundRecommendationsForStartup(node)
      : [];
    const recommendationHtml = recommendations.map((item) => `
      <button class="edge-item connection-card" type="button" data-node-id="${escapeHtml(item.fund.id)}">
        <div class="ranking-top"><span>${escapeHtml(item.fund.label)}</span><span>${item.score.toFixed(1)}</span></div>
        <div class="ranking-meta">${item.sameTheme} cartera misma categoria · ${item.sameCountry} mismo pais · ${item.publicEdges} URL publica</div>
        ${item.examples.length ? `<div class="connection-source">${escapeHtml(item.examples.join(", "))}</div>` : ""}
      </button>
    `).join("");
    badgeEl.textContent = titleCase(node.type);
    badgeEl.className = "pill";
    const publicShare = pct(publicEdges, connected.length);
    const visibleSpecific = Number(node.visible_specific_edges || 0);
    const visibleAnnouncements = Number(node.visible_announcement_edges || 0);
    const sourceLine = node.source_url ? ` Fuente principal: <a href="${escapeHtml(node.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(hostname(node.source_url))}</a>.` : "";
    const subtitle = node.type === "startup"
      ? `${themeLabel(themeKey(node))}${node.country ? ` · ${node.country}` : ""}`
      : `${investorSubtypeLabel(node.investor_subtype)} · ${connected.length} conexiones visibles`;
    detailEl.innerHTML = `
      ${renderOrganizationHeader(node, neighbors, subtitle)}
      <div class="detail-metric-grid">
        <div class="detail-metric primary"><span>Relevancia red</span><strong>${nodeWeight(node).toFixed(1)}</strong></div>
        <div class="detail-metric"><span>Conexiones</span><strong>${connected.length}</strong></div>
        <div class="detail-metric"><span>Evidencia URL</span><strong>${publicShare}</strong></div>
        <div class="detail-metric"><span>Conf. media</span><strong>${avgConfidence ? avgConfidence.toFixed(2) : "n/d"}</strong></div>
        ${node.type === "startup" ? `<div class="detail-metric"><span>Senal startup</span><strong>${startupCapitalSignal(node).toFixed(1)}</strong></div>` : ""}
        <div class="detail-metric"><span>Specific/anuncio</span><strong>${visibleSpecific}/${visibleAnnouncements}</strong></div>
      </div>
      <div class="detail-callout">
        <strong>${escapeHtml(connectionQualityLabel(publicEdges, connected.length))}</strong>
        <span>${publicEdges} de ${connected.length} conexiones visibles tienen fuente publica.${sourceLine}</span>
      </div>
      ${fundPortfolioInsight(node, neighbors)}
      ${startupCapitalInsight(node, neighbors, recommendationHtml)}
      <section class="detail-block">
        <h3>Conexiones clave</h3>
        <div class="detail-muted">Ordenadas por peso visual, confianza y calidad de evidencia. Click en una conexion para pivotear el inspector.</div>
        <div class="edge-list">${renderConnectionList(neighbors, node)}</div>
      </section>
    `;
    detailEl.querySelectorAll("[data-node-id]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedEdgeId = null;
        selectedId = button.dataset.nodeId;
        renderGraph();
        renderDetail(selectedId);
      });
    });
  }

  function renderDetail(id) {
    if (selectedEdgeId) {
      const edge = activeEdges.find((item) => item.id === selectedEdgeId);
      if (edge) {
        renderEdgeDetail(edge);
        return;
      }
    }
    if (!id) {
      badgeEl.textContent = "Sin seleccion";
      badgeEl.className = "pill muted";
      detailEl.innerHTML = `
        <div class="detail-title-card">
          <h3>Selecciona un nodo</h3>
          <div class="detail-subtitle">Fondo, startup o relacion</div>
          <p>El inspector va a mostrar rol en la red, evidencia, conexiones principales, cartera visible o fondos candidatos segun lo que selecciones.</p>
        </div>
        <div class="detail-callout">
          <strong>Lectura sugerida</strong>
          <span>Click en un fondo para ver su perfil de cartera. Click en una startup para ver fondos conectados, calidad de evidencia y vecindad relevante.</span>
        </div>
      `;
      return;
    }
    renderNodeInspector(id);
    return;
    const connected = activeEdges.filter((edge) => edge.source === id || edge.target === id);
    const publicEdges = connected.filter((edge) => edge.evidence_tier === "public_url" || edge.type === "co_investment").length;
    const avgConfidence = connected.length
      ? connected.reduce((sum, edge) => sum + Number(edge.confidence || 0), 0) / connected.length
      : 0;
    const neighbors = connected.map((edge) => {
      const otherId = edge.source === id ? edge.target : edge.source;
      const other = allNodesById.get(otherId);
      return { edge, other };
    }).filter((item) => item.other);
    badgeEl.textContent = titleCase(node.type);
    badgeEl.className = "pill";
    const chips = [
      node.type,
      node.country,
      node.scope_decision,
      node.type === "startup" && Number(node.visible_degree || 0) === 0 ? "sin capital mapeado" : "",
      node.type === "startup" ? themeLabel(themeKey(node)) : node.investor_subtype
    ].filter(Boolean);
    const neighborHtml = neighbors
      .sort((a, b) => Number(b.edge.confidence || 0) - Number(a.edge.confidence || 0))
      .slice(0, 24)
      .map(({ edge, other }) => `
        <button class="edge-item" type="button" data-node-id="${escapeHtml(other.id)}">
          <div class="ranking-top"><span>${escapeHtml(other.label)}</span><span>${escapeHtml(edgeLabel(edge))}</span></div>
          <div class="ranking-meta">conf ${edge.confidence ?? "n/d"}${edge.shared_count ? ` &middot; ${edge.shared_count} startups compartidas` : ""}${edge.source_url ? ` &middot; ${escapeHtml(edge.source_url)}` : ""}</div>
        </button>
      `).join("");
    const recommendations = node.type === "startup" && Number(node.visible_degree || 0) === 0
      ? fundRecommendationsForStartup(node)
      : [];
    const recommendationHtml = recommendations.map((item) => `
      <div class="edge-item">
        <div class="ranking-top"><span>${escapeHtml(item.fund.label)}</span><span>${item.score.toFixed(1)}</span></div>
        <div class="ranking-meta">${item.sameTheme} cartera misma categoria · ${item.sameCountry} mismo pais · ${item.publicEdges} URL publica${item.examples.length ? ` · ${escapeHtml(item.examples.join(", "))}` : ""}</div>
      </div>
    `).join("");
    detailEl.innerHTML = `
      <div class="detail-chip-row">${chips.map((chip) => `<span class="detail-chip">${escapeHtml(chip)}</span>`).join("")}</div>
      <div>
        <h3 style="margin:10px 0 6px;">${escapeHtml(node.label)}</h3>
        <div class="detail-muted">El tamano del nodo usa weighted degree: suma del peso/evidencia de sus aristas visibles.${node.type === "startup" && Number(node.visible_degree || 0) === 0 ? " Aparece como contexto del universo BIO sin capital mapeado." : ""}</div>
      </div>
      <div class="detail-metric-grid">
        <div class="detail-metric"><span>Weighted degree</span><strong>${nodeWeight(node).toFixed(1)}</strong></div>
        ${node.type === "startup" ? `<div class="detail-metric"><span>Diametro startup</span><strong>${startupCapitalSignal(node).toFixed(1)}</strong></div>` : ""}
        <div class="detail-metric"><span>Edges visibles</span><strong>${connected.length}</strong></div>
        <div class="detail-metric"><span>Conf. media</span><strong>${avgConfidence ? avgConfidence.toFixed(2) : "n/d"}</strong></div>
      </div>
      <div class="detail-muted">Fuentes publicas visibles: <strong>${publicEdges}</strong> &middot; Especificas: <strong>${node.visible_specific_edges || 0}</strong> &middot; Anuncios: <strong>${node.visible_announcement_edges || 0}</strong> &middot; Conexiones base: ${node.degree || 0}</div>
      ${node.summary ? `<div class="detail-muted">${escapeHtml(node.summary)}</div>` : ""}
      ${recommendations.length ? `
        <div>
          <h3 style="margin:12px 0 6px;">Fondos candidatos para buscar arista</h3>
          <div class="detail-muted">Ranking heuristico por cartera similar: misma categoria semantica, mismo pais, confianza y fuente publica.</div>
        </div>
        <div class="edge-list">${recommendationHtml}</div>
      ` : ""}
      <div class="edge-list">${neighborHtml || '<div class="detail-muted">Sin conexiones visibles con los filtros actuales.</div>'}</div>
    `;
    detailEl.querySelectorAll("[data-node-id]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedEdgeId = null;
        selectedId = button.dataset.nodeId;
        renderGraph();
        renderDetail(selectedId);
      });
    });
  }

  function updateNote() {
    const mode = modeSelect.value;
    const layer = activeTaxonomyState.clusterMode === "semantic"
      ? `taxonomia semantica activa de Themes (${activeTaxonomyLabel()})`
      : "base operativa guardada";
      const copy = {
      capital_core: `Capital Core muestra la red de inversion sobre el universo BIO include usando la ${layer}. Los colores, filtros y cobertura por categoria siguen el selector activo en Themes para mantener una sola lectura visual.`,
      coverage_gaps: `Vacios de capital agrupa startups BIO include sin edge de capital mapeado usando la ${layer}. Sirve para priorizar busqueda de fondos, fuentes y relaciones faltantes por categoria.`,
      co_investment: "Co-investment proyecta la red fondo-fondo: dos fondos se acercan si comparten startups. Es ideal para ver sindicatos y vecindades de capital.",
      allocator_layer: `Allocator Layer suma capital institucional, LPs y fund-of-funds, manteniendo la ${layer} para colorear las startups del universo BIO.`,
      full_network: `Full Network es el default exploratorio: muestra todo el grafo disponible y colorea startups con la ${layer}. Los filtros no recortan el espacio; iluminan themes, paises o calidad mientras el resto queda como contexto tenue.`
    };
    noteEl.textContent = copy[mode] || copy.capital_core;
  }

  function syncLayerButtons() {
    labelsButton?.classList.toggle("active", showLabels);
    universeButton?.classList.toggle("active", showUniverseContext);
    backboneButton?.classList.toggle("active", backboneOnly);
    if (labelsButton) labelsButton.textContent = showLabels ? "Labels" : "Labels off";
    if (universeButton) universeButton.textContent = showUniverseContext ? "Universo BIO" : "Solo red";
    if (backboneButton) backboneButton.textContent = backboneOnly ? "Backbone" : "Full nodes";
  }

  function taxonomyStateSignature(state = activeTaxonomyState) {
    return `${state.clusterMode || "semantic"}::${state.semanticProfile || ""}::${Number(state.semanticK || 0)}`;
  }

  function syncSharedTaxonomyState({ force = false } = {}) {
    const next = readSharedTaxonomyState();
    if (!force && taxonomyStateSignature(next) === taxonomyStateSignature()) return false;
    activeTaxonomyState = next;
    rebuildDynamicAssignments();
    if (themeSelect) themeSelect.value = "all";
    populateFilters();
    rebuild({ rerun: true });
    return true;
  }

  function rebuild({ rerun = true } = {}) {
    selectedId = null;
    selectedEdgeId = null;
    hoverId = null;
    hoverEdgeId = null;
    hideTooltip();
    buildActiveGraph();
    initializePositions();
    if (rerun) runForceAtlas(modeSelect.value === "co_investment" ? 620 : 520);
    if (!rerun) positionContextNodes();
    renderGraph();
    renderSummary();
    renderRanking();
    renderThemeMix();
    renderDetail(null);
    updateNote();
    syncLayerButtons();
    fitToGraph();
  }

  function normalizeSearchIndex() {
    return activeNodes
      .map((node) => ({
        node,
        key: normalize(`${node.label} ${node.id} ${node.type} ${node.country || ""} ${themeLabel(themeKey(node))}`)
      }))
      .sort((a, b) => a.node.label.localeCompare(b.node.label, "es"));
  }

  function hideSearchResults() {
    searchResults.classList.remove("open");
    searchResults.innerHTML = "";
  }

  function renderSearchResults() {
    const query = normalize(searchInput.value);
    searchResults.innerHTML = "";
    if (query.length < 2) {
      hideSearchResults();
      return;
    }
    const matches = normalizeSearchIndex()
      .filter((item) => item.key.includes(query))
      .slice(0, 12);
    if (!matches.length) {
      searchResults.innerHTML = '<div class="detail-muted" style="padding:8px 10px;">Sin resultados visibles</div>';
      searchResults.classList.add("open");
      return;
    }
    matches.forEach(({ node }) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "atlas-search-result";
      button.innerHTML = `<strong>${escapeHtml(node.label)}</strong><small>${escapeHtml(titleCase(node.type))}${node.type === "startup" ? ` &middot; ${escapeHtml(themeLabel(themeKey(node)))}` : ""}</small>`;
      button.addEventListener("click", () => {
        selectedEdgeId = null;
        selectedId = node.id;
        searchInput.value = node.label;
        hideSearchResults();
        renderGraph();
        renderDetail(selectedId);
      });
      searchResults.appendChild(button);
    });
    searchResults.classList.add("open");
  }

  function zoomAt(factor, clientX, clientY) {
    const rect = svg.getBoundingClientRect();
    const px = ((clientX - rect.left) / rect.width) * WIDTH;
    const py = ((clientY - rect.top) / rect.height) * HEIGHT;
    const next = Math.max(0.25, Math.min(4.5, transform.k * factor));
    const worldX = (px - transform.x) / transform.k;
    const worldY = (py - transform.y) / transform.k;
    transform.x = px - worldX * next;
    transform.y = py - worldY * next;
    transform.k = next;
    updateViewport();
  }

  modeSelect.addEventListener("change", () => rebuild({ rerun: true }));
  [themeSelect, countrySelect, confidenceSelect, sourceTierSelect].forEach((control) => {
    control.addEventListener("change", () => {
      selectedId = null;
      selectedEdgeId = null;
      hoverId = null;
      hoverEdgeId = null;
      hideTooltip();
      renderGraph();
      renderSummary();
      renderDetail(null);
    });
  });
  runLayoutButton.addEventListener("click", () => {
    runForceAtlas(620);
    renderGraph();
    fitToGraph();
  });
  resetButton.addEventListener("click", () => rebuild({ rerun: true }));
  clearButton.addEventListener("click", () => {
    selectedId = null;
    selectedEdgeId = null;
    hoverId = null;
    hoverEdgeId = null;
    searchInput.value = "";
    themeSelect.value = "all";
    countrySelect.value = "all";
    confidenceSelect.value = "0";
    sourceTierSelect.value = "all";
    hideSearchResults();
    hideTooltip();
    renderGraph();
    renderSummary();
    renderDetail(null);
  });
  labelsButton.addEventListener("click", () => {
    showLabels = !showLabels;
    labelsButton.classList.toggle("active", showLabels);
    labelsButton.textContent = showLabels ? "Labels" : "Labels off";
    renderGraph();
  });
  universeButton.addEventListener("click", () => {
    showUniverseContext = !showUniverseContext;
    universeButton.classList.toggle("active", showUniverseContext);
    universeButton.textContent = showUniverseContext ? "Universo BIO" : "Solo red";
    rebuild({ rerun: true });
  });
  backboneButton.addEventListener("click", () => {
    backboneOnly = !backboneOnly;
    backboneButton.classList.toggle("active", backboneOnly);
    backboneButton.textContent = backboneOnly ? "Backbone" : "Full nodes";
    rebuild({ rerun: true });
  });
  searchInput.addEventListener("input", renderSearchResults);
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      searchInput.value = "";
      selectedId = null;
      selectedEdgeId = null;
      hoverId = null;
      hoverEdgeId = null;
      hideSearchResults();
      hideTooltip();
      renderGraph();
      renderDetail(null);
    }
  });
  document.addEventListener("click", (event) => {
    if (event.target === searchInput || searchResults.contains(event.target)) return;
    hideSearchResults();
  });
  svg.addEventListener("click", () => {
    if (didDrag) {
      didDrag = false;
      return;
    }
    selectedId = null;
    selectedEdgeId = null;
    hoverId = null;
    hoverEdgeId = null;
    hideTooltip();
    renderGraph();
    renderDetail(null);
  });
  svg.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoomAt(event.deltaY < 0 ? 1.11 : 0.91, event.clientX, event.clientY);
  }, { passive: false });
  svg.addEventListener("pointerdown", (event) => {
    if (closestInteractive(event.target)) return;
    isDragging = true;
    didDrag = false;
    dragStart = { x: event.clientX, y: event.clientY, ox: transform.x, oy: transform.y };
    svg.setPointerCapture(event.pointerId);
  });
  svg.addEventListener("pointermove", (event) => {
    if (!isDragging) return;
    const rect = svg.getBoundingClientRect();
    if (Math.hypot(event.clientX - dragStart.x, event.clientY - dragStart.y) > 3) didDrag = true;
    transform.x = dragStart.ox + ((event.clientX - dragStart.x) / rect.width) * WIDTH;
    transform.y = dragStart.oy + ((event.clientY - dragStart.y) / rect.height) * HEIGHT;
    updateViewport();
  });
  svg.addEventListener("pointerup", (event) => {
    isDragging = false;
    if (svg.hasPointerCapture?.(event.pointerId)) svg.releasePointerCapture(event.pointerId);
  });
  zoomInButton.addEventListener("click", () => zoomAt(1.18, window.innerWidth / 2, window.innerHeight / 2));
  zoomOutButton.addEventListener("click", () => zoomAt(0.84, window.innerWidth / 2, window.innerHeight / 2));
  resetViewButton.addEventListener("click", fitToGraph);
  window.addEventListener("storage", (event) => {
    if (event.key === SHARED_TAXONOMY_STATE_KEY) syncSharedTaxonomyState();
  });
  window.addEventListener("focus", () => syncSharedTaxonomyState());

  rebuildDynamicAssignments();
  populateFilters();
  rebuild({ rerun: true });
})();
