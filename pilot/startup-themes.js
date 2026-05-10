(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.ECOSYSTEM_DATA || { nodes: [] }) : (window.ECOSYSTEM_DATA || { nodes: [] });
  const svg = document.getElementById("startup-themes-svg");
  const themeList = document.getElementById("theme-list");
  const themeSelect = document.getElementById("theme-select");
  const startupSearchInput = document.getElementById("startup-search");
  const startupSearchResults = document.getElementById("startup-search-results");
  const countrySelect = document.getElementById("country-select");
  const investorSelect = document.getElementById("investor-select");
  const clearHighlightsButton = document.getElementById("clear-highlights");
  const startupCount = document.getElementById("startup-count");
  const detail = document.getElementById("startup-detail");
  const hoverCard = document.getElementById("startup-hover-card");
  const zoomInButton = document.getElementById("themes-zoom-in");
  const zoomOutButton = document.getElementById("themes-zoom-out");
  const resetButton = document.getElementById("themes-reset");
  const toggleConfirmedButton = document.getElementById("toggle-confirmed");
  const toggleProvisionalButton = document.getElementById("toggle-provisional");
  const toggleResidualButton = document.getElementById("toggle-residual");
  const toggleLabelsButton = document.getElementById("toggle-labels");
  const clusterViewSelect = document.getElementById("cluster-view-select");
  const semanticProfileSelect = document.getElementById("semantic-profile-select");
  const semanticKSelect = document.getElementById("semantic-k-select");
  const clusterModePill = document.getElementById("cluster-mode-pill");
  const themeIntro = document.getElementById("theme-intro");
  const themesNote = document.getElementById("themes-note");
  const taxonomyPayload = window.deepRepairData ? window.deepRepairData(window.STARTUP_TAXONOMY_DATA || { summary: {}, theme_counts: [], assignmentsById: {} }) : (window.STARTUP_TAXONOMY_DATA || { summary: {}, theme_counts: [], assignmentsById: {} });
  const profilesPayload = window.deepRepairData ? window.deepRepairData(window.STARTUP_PROFILES_DATA || { summary: {}, profiles: [] }) : (window.STARTUP_PROFILES_DATA || { summary: {}, profiles: [] });
  const semanticSinglePayload = window.deepRepairData ? window.deepRepairData(window.SEMANTIC_SINGLE_LEVEL_DATA || { recommended: { assignmentsById: {} } }) : (window.SEMANTIC_SINGLE_LEVEL_DATA || { recommended: { assignmentsById: {} } });
  const themeSystem = window.THEME_SYSTEM || null;

  const WIDTH = 1700;
  const HEIGHT = 980;

  const taxonomyAssignments = taxonomyPayload.assignmentsById || {};
  const semanticCandidates = semanticSinglePayload.candidates || [];
  const semanticWeightProfiles = semanticSinglePayload.weight_profiles || [];
  const sharedTaxonomyStateKey = "bioVcLatam.activeSemanticTaxonomy";
  const recommendedSemanticProfile = semanticSinglePayload.summary?.recommended_profile || "balanced";
  const defaultExplorationProfile = semanticCandidates.some((candidate) => candidate.feature_profile === recommendedSemanticProfile)
    ? recommendedSemanticProfile
    : (semanticCandidates[0]?.feature_profile || "balanced");
  const recommendedK = Number(semanticSinglePayload.summary?.recommended_k || 10);
  const preferredSemanticK = semanticCandidates.some((candidate) => candidate.feature_profile === defaultExplorationProfile && Number(candidate.k) === recommendedK)
    ? recommendedK
    : Number(semanticCandidates.find((candidate) => candidate.feature_profile === defaultExplorationProfile)?.k || recommendedK);
  function readSharedTaxonomyState() {
    try {
      return JSON.parse(window.localStorage.getItem(sharedTaxonomyStateKey) || "{}");
    } catch (_) {
      return {};
    }
  }
  function semanticCandidateExists(profile, k) {
    return semanticCandidates.some((candidate) => candidate.feature_profile === profile && Number(candidate.k) === Number(k));
  }
  const storedTaxonomyState = readSharedTaxonomyState();
  const initialSemanticProfile = semanticCandidateExists(storedTaxonomyState.semanticProfile, storedTaxonomyState.semanticK)
    ? storedTaxonomyState.semanticProfile
    : defaultExplorationProfile;
  const initialSemanticK = semanticCandidateExists(initialSemanticProfile, storedTaxonomyState.semanticK)
    ? Number(storedTaxonomyState.semanticK)
    : preferredSemanticK;
  const rawSemanticAssignments = (semanticSinglePayload.recommended && semanticSinglePayload.recommended.assignmentsById) || {};
  const semanticAssignments = Object.keys(rawSemanticAssignments).reduce((map, key) => {
    const value = rawSemanticAssignments[key];
    map[key] = Array.isArray(value) ? value[0] : value;
    return map;
  }, {});
  const profilesById = (profilesPayload.profiles || []).reduce((map, profile) => {
    map[profile.startup_id] = profile;
    return map;
  }, {});

  const ecosystemStartups = (payload.nodes || []).filter((node) => node.type === "startup");
  const ecosystemCapital = (payload.nodes || []).filter((node) => node.type === "capital" || node.canonical_type === "investor");
  const startupNodeById = new Map(ecosystemStartups.map((node) => [node.id, node]));
  const startupNodeByLabel = new Map(
    ecosystemStartups.map((node) => [normalizeEntityKey(node.label || node.structured_label || node.id), node]).filter(([key]) => key)
  );
  const capitalById = new Map(ecosystemCapital.map((node) => [node.id, node]));
  Object.keys(semanticAssignments).forEach((startupId) => {
    if (startupNodeById.has(startupId)) return;
    const semantic = semanticAssignments[startupId] || {};
    const taxonomy = taxonomyAssignments[startupId] || {};
    const profile = profilesById[startupId] || {};
    const matchedByLabel = startupNodeByLabel.get(
      normalizeEntityKey(semantic.startup_name || taxonomy.startup_name || profile.startup_name || startupId)
    );
    if (matchedByLabel) {
      startupNodeById.set(startupId, {
        ...matchedByLabel,
        id: startupId,
        label: semantic.startup_name || taxonomy.startup_name || profile.startup_name || matchedByLabel.label || startupId,
        structured_country: taxonomy.structured_country || matchedByLabel.structured_country || "",
        structured_sector: taxonomy.structured_sector || matchedByLabel.structured_sector || "",
        synthetic_from_master: false,
        matched_from_label: true
      });
      return;
    }
    startupNodeById.set(startupId, {
      id: startupId,
      label: semantic.startup_name || taxonomy.startup_name || profile.startup_name || startupId,
      type: "startup",
      size: 6,
      degree: 0,
      confidence_score: taxonomy.confidence || semantic.semantic_beta_confidence || "",
      sources: profile.source_url || semantic.source_url || "",
      quality_flags: "",
      canonical_type: "Startup",
      structured_match: false,
      structured_type: "Startup",
      structured_country: taxonomy.structured_country || "",
      structured_sector: taxonomy.structured_sector || "",
      structured_label: "",
      structured_slug: "",
      structured_raw_attrs: "",
      synthetic_from_master: true
    });
  });

  const rawStartups = Array.from(startupNodeById.values());
  if (!svg || !rawStartups.length) {
    return;
  }

  function cleanTheme(value) {
    if (themeSystem) return themeSystem.normalizeThemeKey(value);
    const text = String(value || "").trim();
    if (!text || text.toLowerCase() === "nan" || text === "Digital Economy" || text === "Other / Unclassified") {
      return "peripheral or underclassified ventures";
    }
    return text;
  }

  function cleanValue(value) {
    const text = String(value || "").trim();
    if (!text || text.toLowerCase() === "nan") return "n/d";
    return text;
  }

  function normalizeEntityKey(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "");
  }

  function normalizeSearchText(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function prettyTheme(theme) {
    if (themeSystem) return themeSystem.themeLabel(theme);
    const raw = String(theme || "").trim();
    return raw.replace(/-/g, " ").replace(/\s+/g, " ").trim();
  }

  function prettySemanticTheme(theme) {
    const raw = String(theme || "").trim();
    if (!raw) return "needs review";
    return raw.replace(/-/g, " ").replace(/\s+/g, " ").trim();
  }

  function themeSortScore(theme) {
    return themeSystem ? themeSystem.themeSortScore(theme) : 0;
  }

  function titleCase(text) {
    return String(text || "")
      .split(" ")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function splitTokens(value) {
    return String(value || "")
      .split(/[;,|]/)
      .map((token) => token.trim())
      .filter(Boolean)
      .slice(0, 7);
  }

  function splitRepresentativeNames(value, limit = 5) {
    return String(value || "")
      .split(/[;|]/)
      .map((name) => name.trim())
      .filter(Boolean)
      .slice(0, limit);
  }

  function representativeNamesForMembers(members, limit = 5) {
    return members
      .slice()
      .sort((a, b) => {
        const weightDiff = (parseNumeric(b.visual_weight) || 0) - (parseNumeric(a.visual_weight) || 0);
        if (weightDiff !== 0) return weightDiff;
        const sizeDiff = Number(b.size || 0) - Number(a.size || 0);
        if (sizeDiff !== 0) return sizeDiff;
        const degreeDiff = Number(b.degree || 0) - Number(a.degree || 0);
        if (degreeDiff !== 0) return degreeDiff;
        return String(a.label || a.id).localeCompare(String(b.label || b.id), "es");
      })
      .slice(0, limit)
      .map((node) => node.label || node.id);
  }

  function semanticClusterPolicy(profileId, k, clusterId, fallbackLabel) {
    const key = `${profileId}::${Number(k)}::${clusterId}`;
    const policies = {
      "technology_heavy::7::k7_cluster_1": {
        label: "clinical diagnostics and bioinstrumentation",
        description: "Diagnostics, detection, bioinstrumentation and clinical devices for health or biological analysis.",
        anchor: /diagnostics|medtech|medicaldevices|clinicaldevices|biopsy|detection|imaging|corneal|respiratory|tumor|coagulation|genomics|molecular|cancer/i
      },
      "technology_heavy::7::k7_cluster_2": {
        label: "regenerative bio and bioactive platforms",
        description: "Regenerative biology, tissue engineering and bioactive products across health, food, cosmetics or biomaterials.",
        anchor: /regenerative|tissue|cells|bioactive|stem|wound|biomaterials|scaffolds|culture|healthspan|ingredients|cosmetics|microencapsulation/i
      },
      "technology_heavy::7::k7_cluster_3": {
        label: "agri intelligence and crop systems",
        description: "Agronomic intelligence, crop decisioning, biological application and data systems for agriculture.",
        anchor: /agtech|agronomic|crop|growers|farm|field|geospatial|drone|irrigation|seeds|plant|biologicals|pollination|livestock|soil/i
      },
      "technology_heavy::7::k7_cluster_4": {
        label: "traceable agri-food and circular supply chains",
        description: "Traceability, producer infrastructure and circular supply-chain coordination for agri-food and material flows.",
        anchor: /traceability|marketplace|supply|chain|producer|growers|grains|tokenization|recycling|logistics|passport|verification|sustainability|vertical|farming/i
      },
      "technology_heavy::7::k7_cluster_5": {
        label: "bio-process and resource optimization",
        description: "Optimization platforms for bioprocesses, pollination, energy, cold chains, logistics or resource-intensive operating systems.",
        anchor: /optimization|bioprocess|microalgae|pollination|microbiome|energy|forecasting|cold|refrigeration|logistics|freight|yield|grid|plant|fungi|glycobiology/i
      },
      "technology_heavy::7::k7_cluster_6": {
        label: "biobased chemistry and molecular materials",
        description: "Biobased chemistry, biomaterials, molecular manufacturing and circular material substitution.",
        anchor: /chemistry|biomaterials|biosynthesis|molecule|microbiology|biomineralization|pigments|textile|biopolymer|proteins|insects|formulations|polymer/i
      },
      "technology_heavy::7::k7_cluster_7": {
        label: "food ingredients and fermentation platforms",
        description: "Food ingredients, fermentation, proteins, functional formulations and biofactory-enabled food systems.",
        anchor: /ingredients|proteins|fermentation|precisionfermentation|enzymes|plant|dairy|bacteria|yeast|foodtech|formulation|nutraceutical|encapsulation|biopolymer|compostable/i
      }
    };
    const policy = policies[key];
    if (policy) return { ...policy, status: "curated" };
    return {
      label: fallbackLabel || "needs review",
      description: "",
      anchor: null,
      status: "auto"
    };
  }

  function nodeClusterFit(node, topTokens, policy) {
    const semantic = node.semanticViewAssignment || {};
    const text = [
      node.label,
      node.profile?.startup_summary_v1,
      node.profile?.business_one_liner,
      node.taxonomy?.market_label,
      node.taxonomy?.technical_stack,
      node.taxonomy?.transition_function,
      semantic.technology_features,
      semantic.industry_features
    ].join(" ").toLowerCase();
    const overlap = topTokens.filter((token) => token && text.includes(String(token).toLowerCase()));
    const margin = parseNumeric(semantic.margin);
    const policyFit = !policy.anchor || policy.anchor.test(text);
    const flags = [];
    if (margin !== null && margin < 4) flags.push("low_margin");
    if (topTokens.length && overlap.length < 1) flags.push("weak_token_overlap");
    if (!policyFit) flags.push("weak_policy_fit");
    return {
      fit: flags.length === 0 ? "good" : policyFit && !flags.includes("low_margin") ? "watch" : "review",
      flags,
      overlapCount: overlap.length,
      policyFit
    };
  }

  function parseNumeric(value) {
    const parsed = Number(String(value || "").replace(",", "."));
    return Number.isFinite(parsed) ? parsed : null;
  }

  function startupRadius(node, mode) {
    const baseSize = Number.isFinite(node.size) ? node.size : 5;
    const networkSignal = Math.max(0, Math.min(1, (baseSize - 4) / 5));
    const degree = Number(node.degree || 0);
    const degreeSignal = degree > 1 ? Math.min(1, Math.log2(degree + 1) / 3.2) : 0;
    const semanticSignal = parseNumeric(node.visual_weight) ?? 0;
    const blendedSignal = Math.max(
      0,
      Math.min(1, networkSignal * 0.5 + degreeSignal * 0.25 + semanticSignal * 0.85)
    );
    const sizeSignal = 4.2 + blendedSignal * 9.6;

    if (mode === "selected") {
      return Math.max(7.2, Math.min(22.5, sizeSignal * 1.24));
    }
    if (mode === "hovered") {
      return Math.max(6.2, Math.min(19.6, sizeSignal * 1.1));
    }
    return Math.max(4.8, Math.min(17.8, sizeSignal));
  }

  function getThemeAnchor(index, total) {
    if (themeSystem && typeof themeSystem.themePosition === "function") {
      return null;
    }
    const centerX = WIDTH / 2;
    const centerY = HEIGHT / 2;
    if (index === 0) {
      return { x: centerX + 70, y: centerY + 30 };
    }
    const ring = Math.floor((index - 1) / 6) + 1;
    const positionInRing = (index - 1) % 6;
    const itemsInRing = Math.min(6 + (ring - 1) * 4, Math.max(6, total - (ring - 1) * 6));
    const angle = ((Math.PI * 2) / itemsInRing) * positionInRing - Math.PI / 2 + ring * 0.16;
    const radius = 210 + ring * 150;
    return {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius * 0.78
    };
  }

  function semanticThemeAnchor(theme, index, total) {
    const centerX = WIDTH / 2;
    const centerY = HEIGHT / 2;
    const radius = Math.min(WIDTH, HEIGHT) * 0.145;
    const angle = ((Math.PI * 2) / Math.max(1, total)) * index - Math.PI / 2;
    return {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius * 0.8
    };
  }

  const enrichedStartups = rawStartups.map((node) => {
    const taxonomy = taxonomyAssignments[node.id] || null;
    const profile = profilesById[node.id] || null;
    const semantic = semanticAssignments[node.id] || null;
    const semanticTheme = semantic ? cleanTheme(semantic.semantic_single_theme) : null;
    const taxonomyTheme = taxonomy ? cleanTheme(taxonomy.macro_theme || taxonomy.emergent_theme) : null;
    const resolvedTheme = semanticTheme || taxonomyTheme || "uncertain source-backed edge cases";
    const resolvedSubtheme = semanticTheme || cleanTheme(taxonomy ? taxonomy.emergent_theme : "uncertain source-backed edge cases");
    const scopeStatus = cleanValue(
      (profile && profile.scope_status) ||
      node.scope_status ||
      (taxonomy ? taxonomy.scope_status : "")
    ).toLowerCase();
    const visualStatus = semanticTheme && scopeStatus === "confirmed" && resolvedTheme !== "uncertain source-backed edge cases"
      ? "confirmed"
      : scopeStatus === "provisional"
        ? "provisional"
        : "residual";
    return {
      ...node,
      taxonomy,
      profile,
      semantic,
      adoptedTheme: resolvedTheme,
      adoptedSubtheme: resolvedSubtheme,
      adoptedSemanticClusterId: semantic && semantic.semantic_single_cluster_id ? semantic.semantic_single_cluster_id : `legacy_${resolvedTheme.replace(/[^a-z0-9]+/gi, "_").toLowerCase()}`,
      layoutClusterId: semantic && semantic.semantic_single_cluster_id ? semantic.semantic_single_cluster_id : `legacy_${resolvedTheme.replace(/[^a-z0-9]+/gi, "_").toLowerCase()}`,
      semanticClusterId: semantic && semantic.semantic_single_cluster_id ? semantic.semantic_single_cluster_id : `legacy_${resolvedTheme.replace(/[^a-z0-9]+/gi, "_").toLowerCase()}`,
      theme: resolvedTheme,
      subtheme: resolvedSubtheme,
      scopeStatus,
      visualStatus,
      themeSource: semantic ? "semantic_single_level" : taxonomy ? cleanValue(taxonomy.taxonomy_source) : "legacy_sector",
      gephi_x: Number(node.gephi_x || 0),
      gephi_y: Number(node.gephi_y || 0),
      size: Number(node.size || 5),
      degree: Number(node.degree || 0)
    };
  });

  function startupDedupScore(node) {
    let score = 0;
    if (node.taxonomy) score += 100;
    if (node.semantic) score += 60;
    if (node.profile && node.profile.source_url) score += 40;
    if (node.profile && node.profile.review_status === "reviewed") score += 20;
    if (node.label && /\s/.test(node.label)) score += 4;
    score += Math.min(12, Number(node.degree || 0));
    score += Math.min(8, Number(node.size || 0));
    return score;
  }

  const duplicateAudit = [];
  const dedupedMap = new Map();
  enrichedStartups.forEach((node) => {
    const key = normalizeEntityKey(node.label || node.structured_label || node.id);
    if (!key) return;

    if (!dedupedMap.has(key)) {
      dedupedMap.set(key, node);
      return;
    }

    const existing = dedupedMap.get(key);
    const existingScore = startupDedupScore(existing);
    const candidateScore = startupDedupScore(node);
    if (candidateScore > existingScore) {
      duplicateAudit.push({
        normalized_key: key,
        kept_id: node.id,
        kept_label: node.label,
        dropped_id: existing.id,
        dropped_label: existing.label
      });
      dedupedMap.set(key, node);
    } else {
      duplicateAudit.push({
        normalized_key: key,
        kept_id: existing.id,
        kept_label: existing.label,
        dropped_id: node.id,
        dropped_label: node.label
      });
    }
  });

  const allStartups = Array.from(dedupedMap.values());
  window.STARTUP_THEME_DUPLICATE_AUDIT = duplicateAudit;

  // This adopted map must stay strict: only include + confirmed + source-backed startups
  // that made it into the semantic single-level layer.
  const startups = allStartups.filter((node) =>
    node.semantic &&
    node.taxonomy &&
    node.taxonomy.scope_decision === "include" &&
    node.scopeStatus === "confirmed"
  );

  const startupById = new Map(startups.map((node) => [node.id, node]));
  const startupByNormalizedLabel = new Map(
    startups.map((node) => [normalizeEntityKey(node.label || node.structured_label || node.id), node]).filter(([key]) => key)
  );
  const startupSearchIndex = startups
    .map((node) => ({
      node,
      name: node.label || node.structured_label || node.id,
      key: normalizeSearchText(`${node.label || ""} ${node.structured_label || ""} ${node.id || ""}`)
    }))
    .sort((a, b) => a.name.localeCompare(b.name, "es"));
  const investorPortfolioMap = buildInvestorPortfolioMap();
  const startupInvestorsById = buildStartupInvestorsById();

  let themeGroups = [];
  let themeColors = new Map();
  let activeClusterMeta = new Map();

  function semanticNormalizeText(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/entra en tesis.*$/g, " ")
      .replace(/official site describes|official site presents|official site states|linkedin company profile describes|linkedin company profile states that|gridx describes|f6s profile describes/gi, " ")
      .replace(/[^a-z0-9\s-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function semanticTokenSet(node) {
    const text = semanticNormalizeText([
      node.semantic?.startup_summary_v1,
      node.profile?.startup_summary_v1,
      node.profile?.business_one_liner,
      node.semantic?.evidence_excerpt,
      node.taxonomy?.technical_stack,
      node.taxonomy?.industry_destination
    ].filter(Boolean).join(" "));
    const stop = new Set([
      "startup","startups","company","empresa","platform","plataforma","technology","solution","solutions",
      "biotech","biology","bio","life","health","food","agriculture","official","site","describes","presents",
      "states","with","from","into","para","con","por","una","uno","their","this","that","using","used","based",
      "mediante","editorial","text","texto","auditado","fuente","sources","source","evidence","resumen",
      "datos","data","high","scale","sistemas","systems","mercado","markets","market","desarrollo","develops",
      "desarrolla","servicios","products","productos","process","processes","tecnologia","tecnologias",
      "latam","brazil","brasil","argentina","mexico","chile","colombia","peru","uruguay"
    ]);
    return new Set(
      text
        .split(" ")
        .filter((token) => token.length >= 4 && !stop.has(token))
    );
  }

  function topTokensForMembers(members, limit = 6) {
    const counts = new Map();
    members.forEach((node) => {
      semanticTokenSet(node).forEach((token) => {
        counts.set(token, (counts.get(token) || 0) + 1);
      });
    });
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "es"))
      .slice(0, limit)
      .map(([token]) => token);
  }

  function semanticCandidateKey(profile, k) {
    return `${profile || ""}::${Number(k) || ""}`;
  }

  const semanticCandidatesByKey = new Map(
    semanticCandidates.map((candidate) => [semanticCandidateKey(candidate.feature_profile, candidate.k), candidate])
  );

  function currentSemanticCandidate() {
    const profile = semanticProfileSelect?.value || recommendedSemanticProfile;
    const k = Number(semanticKSelect?.value || preferredSemanticK);
    return semanticCandidatesByKey.get(semanticCandidateKey(profile, k)) ||
      semanticCandidates.find((candidate) => candidate.feature_profile === profile) ||
      semanticCandidates[0] ||
      null;
  }

  function assignmentMapForCandidate(candidate) {
    const assignments = new Map();
    if (!candidate) return assignments;
    (candidate.clusters || []).forEach((cluster) => {
      (cluster.members || []).forEach((member) => {
        assignments.set(member.startup_id, {
          ...member,
          cluster_id: cluster.cluster_id,
          cluster_label: cluster.label,
          cluster_description: cluster.description,
          cluster_top_tokens: cluster.top_tokens,
          cluster_size: cluster.size,
          cluster_avg_margin: cluster.avg_margin,
          cluster_low_confidence_count: cluster.low_confidence_count,
          feature_profile: candidate.feature_profile,
          feature_profile_label: candidate.feature_profile_label,
          k: candidate.k
        });
      });
    });
    return assignments;
  }

  function colorForTheme(theme, index) {
    if (themeSystem && state.clusterMode === "adopted") return themeSystem.themeColor(theme);
    const palette = [
      "#ff7043", "#d66aa2", "#b64050", "#09a7b7", "#235a7c", "#7d58c7",
      "#83bf4c", "#2fa89f", "#f08a24", "#8fa5ad", "#c65f97", "#4f8cc9"
    ];
    return palette[index % palette.length];
  }

  function resolveStartupFromEdgeValue(value) {
    const raw = String(value || "").trim();
    if (!raw) return null;
    return startupById.get(raw) ||
      startupByNormalizedLabel.get(normalizeEntityKey(raw)) ||
      startupByNormalizedLabel.get(normalizeEntityKey(raw.replace(/-/g, " "))) ||
      null;
  }

  function buildInvestorPortfolioMap() {
    const portfolio = new Map();
    (payload.edges || []).forEach((edge) => {
      const sourceCapital = capitalById.get(edge.source);
      const targetCapital = capitalById.get(edge.target);
      const sourceStartup = resolveStartupFromEdgeValue(edge.source);
      const targetStartup = resolveStartupFromEdgeValue(edge.target);
      let investor = null;
      let startup = null;
      if (sourceCapital && targetStartup) {
        investor = sourceCapital;
        startup = targetStartup;
      } else if (targetCapital && sourceStartup) {
        investor = targetCapital;
        startup = sourceStartup;
      }
      if (!investor || !startup) return;
      if (!portfolio.has(investor.id)) {
        portfolio.set(investor.id, {
          id: investor.id,
          label: investor.label || investor.structured_label || investor.id,
          startups: new Set()
        });
      }
      portfolio.get(investor.id).startups.add(startup.id);
    });
    return portfolio;
  }

  function buildStartupInvestorsById() {
    const map = new Map();
    investorPortfolioMap.forEach((portfolio, investorId) => {
      portfolio.startups.forEach((startupId) => {
        if (!map.has(startupId)) map.set(startupId, []);
        map.get(startupId).push(portfolio.label || investorId);
      });
    });
    map.forEach((labels) => labels.sort((a, b) => a.localeCompare(b, "es")));
    return map;
  }

  function semanticFacetSet(node) {
    const facets = new Set();
    const taxonomyText = semanticNormalizeText([
      node.taxonomy?.market_label,
      node.taxonomy?.industry_destination,
      node.taxonomy?.transition_function,
      node.taxonomy?.output_class,
      node.taxonomy?.technical_stack,
      node.theme
    ].filter(Boolean).join(" "));

    function addFacet(label, patterns) {
      if (patterns.some((pattern) => taxonomyText.includes(pattern))) {
        facets.add(label);
      }
    }

    addFacet("human_health", ["clinical", "medical", "diagnostic", "therapeut", "regenerative", "health", "drug", "pharma", "patient"]);
    addFacet("ag_systems", ["crop", "agric", "agri", "pollination", "livestock", "farm", "soil", "seed"]);
    addFacet("food_systems", ["food", "ingredient", "nutrition", "beverage", "dairy", "protein"]);
    addFacet("bioindustrial", ["industrial", "bioprocess", "enzyme", "fermentation", "molecular", "manufacturing", "bioindustrial"]);
    addFacet("climate_resource", ["carbon", "resource", "climate", "water", "energy", "remediation", "circular", "recovery", "waste"]);
    addFacet("monitor_trace", ["trace", "monitor", "intelligence", "analytics", "mrv", "market", "token", "sensor"]);
    addFacet("intervention", ["intervention", "therapeut", "diagnostic", "input", "delivery", "device"]);
    addFacet("platform", ["platform", "software", "model", "screening", "discovery", "simulation"]);

    return facets;
  }

  function jaccardSimilarity(setA, setB) {
    if (!setA.size || !setB.size) return 0;
    let intersection = 0;
    const smaller = setA.size <= setB.size ? setA : setB;
    const larger = setA.size <= setB.size ? setB : setA;
    smaller.forEach((token) => {
      if (larger.has(token)) intersection += 1;
    });
    const union = setA.size + setB.size - intersection;
    return union ? intersection / union : 0;
  }

  function compositeSimilarity(textA, textB, facetA, facetB) {
    const textSim = jaccardSimilarity(textA, textB);
    const facetSim = jaccardSimilarity(facetA, facetB);
    const healthBonus = facetA.has("human_health") && facetB.has("human_health") ? 0.14 : 0;
    const agBonus = facetA.has("ag_systems") && facetB.has("ag_systems") ? 0.08 : 0;
    const industrialBonus = facetA.has("bioindustrial") && facetB.has("bioindustrial") ? 0.08 : 0;
    const climateBonus = facetA.has("climate_resource") && facetB.has("climate_resource") ? 0.08 : 0;
    return Math.min(1, textSim * 0.62 + facetSim * 0.38 + healthBonus + agBonus + industrialBonus + climateBonus);
  }

  function average(values) {
    if (!values.length) return 0;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  }

  function seededUnit(value) {
    let hash = 2166136261;
    const text = String(value || "");
    for (let i = 0; i < text.length; i += 1) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return ((hash >>> 0) % 100000) / 100000;
  }

  function computeSemanticLayout(nodes) {
    const semanticNodes = nodes.filter((node) => node.semantic && node.visualStatus === "confirmed");
    const layoutNodes = semanticNodes.length ? semanticNodes : nodes;
    const tokensById = new Map(layoutNodes.map((node) => [node.id, semanticTokenSet(node)]));
    const facetsById = new Map(layoutNodes.map((node) => [node.id, semanticFacetSet(node)]));
    const sims = new Map();
    const positions = new Map();
    function layoutClusterKey(node) {
      if (state.clusterMode === "semantic") {
        return node.semanticClusterId || `semantic_${node.theme || node.id}`;
      }
      return node.layoutClusterId || node.adoptedSemanticClusterId || node.semanticClusterId || `legacy_${node.adoptedTheme || node.theme}`;
    }
    const clusterGroups = Array.from(
      layoutNodes.reduce((map, node) => {
        const key = layoutClusterKey(node);
        if (!map.has(key)) map.set(key, []);
        map.get(key).push(node);
        return map;
      }, new Map())
    ).map(([clusterId, members]) => ({ clusterId, members }));
    const clusterPositions = new Map();
    const clusterSims = new Map();

    for (let i = 0; i < layoutNodes.length; i += 1) {
      for (let j = i + 1; j < layoutNodes.length; j += 1) {
        const a = layoutNodes[i];
        const b = layoutNodes[j];
        const sim = compositeSimilarity(
          tokensById.get(a.id),
          tokensById.get(b.id),
          facetsById.get(a.id),
          facetsById.get(b.id)
        );
        sims.set(`${a.id}::${b.id}`, sim);
      }
    }

    clusterGroups.forEach((group, index) => {
      const representativeTheme = group.members[0]?.theme || "needs review";
      const anchor = semanticThemeAnchor(representativeTheme, index, clusterGroups.length);
      const jitterX = (seededUnit(`${group.clusterId}::cx`) - 0.5) * 28;
      const jitterY = (seededUnit(`${group.clusterId}::cy`) - 0.5) * 28;
      clusterPositions.set(group.clusterId, {
        x: anchor.x + jitterX,
        y: anchor.y + jitterY
      });
    });

    for (let i = 0; i < clusterGroups.length; i += 1) {
      for (let j = i + 1; j < clusterGroups.length; j += 1) {
        const a = clusterGroups[i];
        const b = clusterGroups[j];
        const pairwise = [];
        a.members.forEach((left) => {
          b.members.forEach((right) => {
            const key = left.id < right.id ? `${left.id}::${right.id}` : `${right.id}::${left.id}`;
            pairwise.push(sims.get(key) || 0);
          });
        });
        clusterSims.set(`${a.clusterId}::${b.clusterId}`, average(pairwise));
      }
    }

    const clusterSimValues = Array.from(clusterSims.values()).filter((value) => Number.isFinite(value));
    const minClusterSim = clusterSimValues.length ? Math.min(...clusterSimValues) : 0;
    const maxClusterSim = clusterSimValues.length ? Math.max(...clusterSimValues) : 1;
    function normalizedClusterSim(value) {
      if (!Number.isFinite(value)) return 0.5;
      if (maxClusterSim - minClusterSim < 0.0001) return 0.5;
      return (value - minClusterSim) / (maxClusterSim - minClusterSim);
    }

    for (let iter = 0; iter < 180; iter += 1) {
      const forces = new Map(clusterGroups.map((group) => [group.clusterId, { x: 0, y: 0 }]));
      const center = { x: WIDTH / 2, y: HEIGHT / 2 };
      for (let i = 0; i < clusterGroups.length; i += 1) {
        for (let j = i + 1; j < clusterGroups.length; j += 1) {
          const a = clusterGroups[i];
          const b = clusterGroups[j];
          const pa = clusterPositions.get(a.clusterId);
          const pb = clusterPositions.get(b.clusterId);
          const dx = pb.x - pa.x;
          const dy = pb.y - pa.y;
          const dist = Math.max(20, Math.sqrt(dx * dx + dy * dy));
          const ux = dx / dist;
          const uy = dy / dist;
          const sim = clusterSims.get(`${a.clusterId}::${b.clusterId}`) || 0;
          const simNorm = normalizedClusterSim(sim);
          const target = 720 - simNorm * 250;
          const attraction = (dist - target) * (0.0125 + simNorm * 0.0145);
          const repulsion = 90000 / (dist * dist);
          const fx = ux * (attraction - repulsion);
          const fy = uy * (attraction - repulsion);
          forces.get(a.clusterId).x += fx;
          forces.get(a.clusterId).y += fy;
          forces.get(b.clusterId).x -= fx;
          forces.get(b.clusterId).y -= fy;
        }
      }
      clusterGroups.forEach((group) => {
        const pos = clusterPositions.get(group.clusterId);
        const force = forces.get(group.clusterId);
        force.x += (center.x - pos.x) * 0.00004;
        force.y += (center.y - pos.y) * 0.00004;
        pos.x += Math.max(-16, Math.min(16, force.x));
        pos.y += Math.max(-16, Math.min(16, force.y));
      });
    }

    clusterGroups.forEach((group) => {
      const centroid = clusterPositions.get(group.clusterId);
      const spreadBoost = Math.min(2.35, 0.96 + Math.sqrt(group.members.length) / 7.2);
      group.members.forEach((node, index) => {
        const ux = seededUnit(`${node.id}::x`);
        const uy = seededUnit(`${node.id}::y`);
        positions.set(node.id, {
          x: centroid.x + (ux - 0.5) * 13.5 * spreadBoost + ((index % 4) - 1.5) * 0.98 * spreadBoost,
          y: centroid.y + (uy - 0.5) * 13.5 * spreadBoost + ((Math.floor(index / 4) % 4) - 1.5) * 0.98 * spreadBoost
        });
      });
    });

    const neighborsById = new Map();
    layoutNodes.forEach((node) => {
      const neighborPairs = layoutNodes
        .filter((other) => other.id !== node.id)
        .map((other) => {
          const key = node.id < other.id ? `${node.id}::${other.id}` : `${other.id}::${node.id}`;
          return { id: other.id, sim: sims.get(key) || 0 };
        })
        .filter((entry) => entry.sim > 0)
        .sort((a, b) => b.sim - a.sim)
        .slice(0, 5);
      neighborsById.set(node.id, neighborPairs);
    });

    layoutNodes.forEach((node) => {
      const neighborPairs = neighborsById.get(node.id) || [];
      const semanticDensity = average(neighborPairs.slice(0, 3).map((entry) => entry.sim));
      const degree = Number(node.degree || 0);
      const degreeSignal = degree > 1 ? Math.min(1, Math.log2(degree + 1) / 3.2) : 0;
      node.visual_weight = Math.max(0, Math.min(1, semanticDensity * 0.8 + degreeSignal * 0.2));
    });

    for (let iter = 0; iter < 140; iter += 1) {
      const forces = new Map(layoutNodes.map((node) => [node.id, { x: 0, y: 0 }]));
      const center = { x: WIDTH / 2, y: HEIGHT / 2 };
      const seen = new Set();

      layoutNodes.forEach((node) => {
        const pos = positions.get(node.id);
        const nodeClusterCenter = clusterPositions.get(layoutClusterKey(node));
        if (nodeClusterCenter) {
          forces.get(node.id).x += (nodeClusterCenter.x - pos.x) * 0.19;
          forces.get(node.id).y += (nodeClusterCenter.y - pos.y) * 0.19;
        }
        (neighborsById.get(node.id) || []).forEach((neighbor) => {
          const pairKey = node.id < neighbor.id ? `${node.id}::${neighbor.id}` : `${neighbor.id}::${node.id}`;
          if (seen.has(pairKey)) return;
          seen.add(pairKey);
          const other = positions.get(neighbor.id);
          const dx = other.x - pos.x;
          const dy = other.y - pos.y;
          const dist = Math.max(8, Math.sqrt(dx * dx + dy * dy));
          const ux = dx / dist;
          const uy = dy / dist;
          const target = 13 + (1 - neighbor.sim) * 16;
          const attraction = (dist - target) * 0.13;
          const fx = ux * attraction;
          const fy = uy * attraction;
          forces.get(node.id).x += fx;
          forces.get(node.id).y += fy;
          forces.get(neighbor.id).x -= fx;
          forces.get(neighbor.id).y -= fy;
        });
      });

      for (let i = 0; i < layoutNodes.length; i += 1) {
        for (let j = i + 1; j < layoutNodes.length; j += 1) {
          const a = layoutNodes[i];
          const b = layoutNodes[j];
          const pa = positions.get(a.id);
          const pb = positions.get(b.id);
          const dx = pb.x - pa.x;
          const dy = pb.y - pa.y;
          const dist = Math.max(8, Math.sqrt(dx * dx + dy * dy));
          const ux = dx / dist;
          const uy = dy / dist;
          const sameCluster = layoutClusterKey(a) === layoutClusterKey(b);
          const repulsion = sameCluster ? 270 / (dist * dist) : 9200 / (dist * dist);
          const fx = ux * (-repulsion);
          const fy = uy * (-repulsion);
          forces.get(a.id).x += fx;
          forces.get(a.id).y += fy;
          forces.get(b.id).x -= fx;
          forces.get(b.id).y -= fy;
        }
      }

      layoutNodes.forEach((node) => {
        const pos = positions.get(node.id);
        const force = forces.get(node.id);
        force.x += (center.x - pos.x) * 0.00003;
        force.y += (center.y - pos.y) * 0.00003;
        pos.x += Math.max(-5, Math.min(5, force.x));
        pos.y += Math.max(-5, Math.min(5, force.y));
      });
    }

    const xs = Array.from(positions.values()).map((pos) => pos.x);
    const ys = Array.from(positions.values()).map((pos) => pos.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const width = Math.max(1, maxX - minX);
    const height = Math.max(1, maxY - minY);
    const scale = Math.min((WIDTH - 240) / width, (HEIGHT - 200) / height);
    const semanticPositionMap = new Map();
    layoutNodes.forEach((node) => {
      const pos = positions.get(node.id);
      semanticPositionMap.set(node.id, {
        x: 120 + (pos.x - minX) * scale,
        y: 96 + (pos.y - minY) * scale
      });
    });

    const fallbackNodes = nodes.filter((node) => !semanticPositionMap.has(node.id));
    fallbackNodes.forEach((node, index) => {
      const ux = seededUnit(`${node.id}::fx`);
      const uy = seededUnit(`${node.id}::fy`);
      semanticPositionMap.set(node.id, {
        x: 150 + ux * (WIDTH - 300) + ((index % 3) - 1) * 8,
        y: 120 + uy * (HEIGHT - 240) + ((Math.floor(index / 3) % 3) - 1) * 8
      });
    });

    relaxOverlappingNodes(semanticPositionMap, nodes);

    return semanticPositionMap;
  }

  let semanticPositionMap = new Map();
  let transitionFromPositionMap = null;

  function relaxOverlappingNodes(positionMap, nodes) {
    const activeNodes = nodes.filter((node) => positionMap.has(node.id));
    const radii = new Map(activeNodes.map((node) => [node.id, startupRadius(node, "default") + 2.4]));
    for (let iter = 0; iter < 42; iter += 1) {
      let moved = false;
      for (let i = 0; i < activeNodes.length; i += 1) {
        for (let j = i + 1; j < activeNodes.length; j += 1) {
          const a = activeNodes[i];
          const b = activeNodes[j];
          const pa = positionMap.get(a.id);
          const pb = positionMap.get(b.id);
          const dx = pb.x - pa.x;
          const dy = pb.y - pa.y;
          const dist = Math.max(0.1, Math.sqrt(dx * dx + dy * dy));
          const minDist = (radii.get(a.id) || 6) + (radii.get(b.id) || 6);
          if (dist >= minDist) continue;
          const push = (minDist - dist) * 0.5;
          const ux = dx / dist;
          const uy = dy / dist;
          pa.x = Math.max(42, Math.min(WIDTH - 42, pa.x - ux * push));
          pa.y = Math.max(42, Math.min(HEIGHT - 42, pa.y - uy * push));
          pb.x = Math.max(42, Math.min(WIDTH - 42, pb.x + ux * push));
          pb.y = Math.max(42, Math.min(HEIGHT - 42, pb.y + uy * push));
          moved = true;
        }
      }
      if (!moved) break;
    }
  }

  const viewport = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const circleLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const labelLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  viewport.append(edgeLayer, circleLayer, labelLayer);
  svg.append(viewport);

  const state = {
    selectedTheme: "all",
    activeThemes: new Set(),
    activeCountry: "all",
    activeInvestor: "all",
    activeSearchStartupId: null,
    selectedNodeId: null,
    hoveredNodeId: null,
    showLabels: true,
    clusterMode: storedTaxonomyState.clusterMode === "adopted" ? "adopted" : "semantic",
    semanticProfile: initialSemanticProfile,
    semanticK: initialSemanticK,
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    dragOriginX: 0,
    dragOriginY: 0,
    visibleStatuses: new Set(["confirmed"])
  };

  function writeSharedTaxonomyState() {
    try {
      window.localStorage.setItem(sharedTaxonomyStateKey, JSON.stringify({
        clusterMode: state.clusterMode,
        semanticProfile: state.semanticProfile,
        semanticK: state.semanticK,
        updatedAt: new Date().toISOString()
      }));
    } catch (_) {
      // Local file contexts can occasionally block storage; the map still works without cross-page sync.
    }
  }

  function makeSvg(tag, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  function isNodeVisible(node) {
    return state.visibleStatuses.has(node.visualStatus);
  }

  function isThemeHighlighted(theme) {
    return state.activeThemes.size === 0 || state.activeThemes.has(theme);
  }

  function hasActiveHighlightFilters() {
    return state.activeThemes.size > 0 || state.activeCountry !== "all" || state.activeInvestor !== "all" || !!state.activeSearchStartupId;
  }

  function nodeMatchesHighlight(node) {
    const themeMatch = state.activeThemes.size === 0 || state.activeThemes.has(node.theme);
    const countryMatch = state.activeCountry === "all" || cleanValue(node.structured_country) === state.activeCountry;
    const investorMatch = state.activeInvestor === "all" || (investorPortfolioMap.get(state.activeInvestor)?.startups.has(node.id));
    const searchMatch = !state.activeSearchStartupId || node.id === state.activeSearchStartupId;
    return themeMatch && countryMatch && investorMatch && searchMatch;
  }

  function groupMatchesHighlight(group) {
    return !hasActiveHighlightFilters() || group.members.some(nodeMatchesHighlight);
  }

  function themeLabel(theme) {
    return state.clusterMode === "semantic" ? titleCase(prettySemanticTheme(theme)) : prettyTheme(theme);
  }

  function rebuildThemeGroups() {
    themeGroups = Array.from(
      startups.reduce((map, node) => {
        if (!map.has(node.theme)) map.set(node.theme, []);
        map.get(node.theme).push(node);
        return map;
      }, new Map())
    )
      .map(([theme, members]) => ({ theme, members }))
      .sort((a, b) => {
        const countDiff = b.members.length - a.members.length;
        if (countDiff !== 0) return countDiff;
        if (state.clusterMode === "adopted") {
          const scoreDiff = themeSortScore(a.theme) - themeSortScore(b.theme);
          if (scoreDiff !== 0) return scoreDiff;
        }
        return themeLabel(a.theme).localeCompare(themeLabel(b.theme), "es");
      });

    themeColors = new Map(themeGroups.map((group, index) => [group.theme, colorForTheme(group.theme, index)]));
  }

  function applyActiveClusterView({ recomputeLayout = true } = {}) {
    activeClusterMeta = new Map();
    if (state.clusterMode === "semantic") {
      const candidate = currentSemanticCandidate();
      const assignments = assignmentMapForCandidate(candidate);
      startups.forEach((node) => {
        const assignment = assignments.get(node.id);
        if (assignment) {
          const policy = semanticClusterPolicy(candidate?.feature_profile, candidate?.k, assignment.cluster_id, assignment.cluster_label);
          node.semanticViewAssignment = assignment;
          node.semanticViewPolicy = policy;
          node.theme = policy.label || assignment.cluster_label || "needs review";
          node.subtheme = policy.label || assignment.cluster_label || node.adoptedSubtheme;
          node.semanticClusterId = assignment.cluster_id || node.adoptedSemanticClusterId;
          return;
        }
        node.semanticViewAssignment = null;
        node.semanticViewPolicy = null;
        node.semanticViewFit = null;
        node.theme = "needs review";
        node.subtheme = node.adoptedSubtheme;
        node.semanticClusterId = `semantic_missing_${node.id}`;
      });
      (candidate?.clusters || []).forEach((cluster) => {
        const clusterMembers = (cluster.members || [])
          .map((member) => startups.find((node) => node.id === member.startup_id))
          .filter(Boolean);
        const visibleTokens = topTokensForMembers(clusterMembers, 6);
        const representatives = splitRepresentativeNames(cluster.representatives, 5);
        const policy = semanticClusterPolicy(candidate?.feature_profile, candidate?.k, cluster.cluster_id, cluster.label);
        const displayLabel = policy.label || cluster.label;
        const topTokens = visibleTokens.length ? visibleTokens : splitTokens(cluster.top_tokens);
        const fitSummary = clusterMembers.reduce((summary, node) => {
          const fit = nodeClusterFit(node, topTokens, policy);
          node.semanticViewFit = fit;
          summary[fit.fit] = (summary[fit.fit] || 0) + 1;
          return summary;
        }, { good: 0, watch: 0, review: 0 });
        const credibilityScore = Math.max(0, Math.round(100 - (((fitSummary.review || 0) * 7 + (fitSummary.watch || 0) * 2.5 + Number(cluster.low_confidence_count || 0) * 3) / Math.max(1, clusterMembers.length)) * 10));
        activeClusterMeta.set(displayLabel, {
          description: policy.description || cluster.description || "Cluster semantico calculado desde texto auditado y features tecnologicas/industriales.",
          tokens: visibleTokens.length ? visibleTokens : splitTokens(cluster.top_tokens),
          representatives: representatives.length ? representatives : representativeNamesForMembers(clusterMembers, 5),
          avgMargin: cluster.avg_margin,
          lowConfidenceCount: cluster.low_confidence_count,
          fitReviewCount: fitSummary.review || 0,
          fitWatchCount: fitSummary.watch || 0,
          credibilityScore,
          namingStatus: policy.status,
          score: candidate.metrics?.explainability_score,
          featureProfileLabel: candidate.feature_profile_label,
          k: candidate.k
        });
      });
    } else {
      startups.forEach((node) => {
        node.semanticViewAssignment = null;
        node.theme = node.adoptedTheme;
        node.subtheme = node.adoptedSubtheme;
        node.semanticClusterId = node.adoptedSemanticClusterId;
      });
      startups.reduce((map, node) => {
        if (!map.has(node.theme)) map.set(node.theme, []);
        map.get(node.theme).push(node);
        return map;
      }, new Map()).forEach((members, theme) => {
        const themeMeta = themeSystem ? themeSystem.themeMeta(theme) : null;
        activeClusterMeta.set(theme, {
          description: themeMeta?.description || "Categoria operativa adoptada para lectura thesis-first del universo BIO.",
          tokens: topTokensForMembers(members, 6),
          representatives: representativeNamesForMembers(members, 5),
          gridx: themeMeta?.gridx,
          antom: themeMeta?.antom
        });
      });
    }
    rebuildThemeGroups();
    if (recomputeLayout || !semanticPositionMap.size) semanticPositionMap = computeSemanticLayout(startups);
  }

  function visibleThemes() {
    const filtered = themeGroups
      .map((group) => {
        const members = group.members.filter(isNodeVisible).map((node) => ({
          ...node,
          plotX: semanticPositionMap.get(node.id)?.x || WIDTH / 2,
          plotY: semanticPositionMap.get(node.id)?.y || HEIGHT / 2,
          clusterRadius: Math.max(18, Math.min(48, 16 + Math.sqrt(group.members.length) * 4))
        }));
        const clusters = Array.from(
          members.reduce((map, node) => {
            const key = node.semanticClusterId || `legacy_${group.theme}`;
            if (!map.has(key)) map.set(key, []);
            map.get(key).push(node);
            return map;
          }, new Map())
        ).map(([clusterId, clusterMembers]) => {
          const cx = clusterMembers.reduce((sum, node) => sum + node.plotX, 0) / clusterMembers.length;
          const cy = clusterMembers.reduce((sum, node) => sum + node.plotY, 0) / clusterMembers.length;
          const radius = Math.max(
            16,
            ...clusterMembers.map((node) => Math.hypot(node.plotX - cx, node.plotY - cy) + 10)
          );
          return {
            clusterId,
            members: clusterMembers,
            nodes: clusterMembers,
            anchor: { x: cx, y: cy },
            radius
          };
        });
        if (!members.length) return null;
        const anchor = {
          x: members.reduce((sum, node) => sum + node.plotX, 0) / members.length,
          y: members.reduce((sum, node) => sum + node.plotY, 0) / members.length
        };
        const macroRadius = Math.max(
          46,
          ...members.map((node) => Math.hypot(node.plotX - anchor.x, node.plotY - anchor.y) + 16)
        );
        return {
          ...group,
          color: themeColors.get(group.theme),
          members,
          nodes: members,
          clusters,
          anchor,
          macroRadius
        };
      })
      .filter(Boolean);

    return filtered;
  }

  function updateViewport() {
    viewport.setAttribute("transform", `translate(${state.offsetX} ${state.offsetY}) scale(${state.scale})`);
  }

  function currentVisibleBounds() {
    const groups = visibleThemes();
    const points = [];
    groups.forEach((group) => {
      group.members.forEach((node) => {
        points.push({ x: node.plotX, y: node.plotY });
      });
    });
    if (!points.length) {
      return { minX: 120, minY: 100, maxX: WIDTH - 120, maxY: HEIGHT - 100 };
    }
    return {
      minX: Math.min(...points.map((p) => p.x)),
      minY: Math.min(...points.map((p) => p.y)),
      maxX: Math.max(...points.map((p) => p.x)),
      maxY: Math.max(...points.map((p) => p.y))
    };
  }

  function clearSelection() {
    state.selectedNodeId = null;
    state.hoveredNodeId = null;
    hideHoverCard();
    setSelectedNode(null);
    draw();
  }

  function hideHoverCard() {
    if (!hoverCard) return;
    hoverCard.classList.remove("visible");
  }

  function moveHoverCard(clientX, clientY) {
    if (!hoverCard) return;
    const wrap = hoverCard.parentElement;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const cardWidth = hoverCard.offsetWidth || 320;
    const cardHeight = hoverCard.offsetHeight || 180;
    let left = clientX - rect.left + 18;
    let top = clientY - rect.top + 18;
    if (left + cardWidth > rect.width - 12) left = clientX - rect.left - cardWidth - 18;
    if (top + cardHeight > rect.height - 12) top = clientY - rect.top - cardHeight - 18;
    left = Math.max(12, left);
    top = Math.max(12, top);
    hoverCard.style.left = `${left}px`;
    hoverCard.style.top = `${top}px`;
  }

  function showHoverCard(node, color, clientX, clientY) {
    if (!hoverCard || !node) return;
    const semantic = node.semantic;
    const profile = node.profile;
    const taxonomy = node.taxonomy;
    const summary = cleanValue(profile?.business_one_liner || profile?.startup_summary_v1 || semantic?.startup_summary_v1);
    const investorLabels = startupInvestorsById.get(node.id) || [];
    hoverCard.innerHTML = `
      <div class="hover-title">${node.label}</div>
      <div class="hover-chip-row">
        <span class="hover-chip"><span class="hover-chip-dot" style="background:${color}"></span>${themeLabel(node.theme)}</span>
        <span class="hover-chip">${cleanValue(node.structured_country)}</span>
        ${profile ? `<span class="hover-chip">${titleCase(cleanValue(profile.quality_band))}</span>` : ""}
        ${profile ? `<span class="hover-chip">${titleCase(cleanValue(profile.review_status))}</span>` : ""}
        ${investorLabels.slice(0, 2).map((label) => `<span class="hover-chip">${label}</span>`).join("")}
      </div>
      <div class="hover-summary">${summary}</div>
      <div class="hover-meta">
        <div class="hover-meta-item">
          <div class="hover-meta-label">Fuente</div>
          <div class="hover-meta-value">${profile?.source_type ? cleanValue(profile.source_type) : "n/d"}</div>
        </div>
        <div class="hover-meta-item">
          <div class="hover-meta-label">Calidad</div>
          <div class="hover-meta-value">${profile ? `${cleanValue(profile.data_quality_score_10)}/10` : "n/d"}</div>
        </div>
        <div class="hover-meta-item">
          <div class="hover-meta-label">Transition function</div>
          <div class="hover-meta-value">${taxonomy ? titleCase(cleanValue(taxonomy.transition_function)) : "n/d"}</div>
        </div>
        <div class="hover-meta-item">
          <div class="hover-meta-label">Industry destination</div>
          <div class="hover-meta-value">${taxonomy ? titleCase(cleanValue(taxonomy.industry_destination)) : "n/d"}</div>
        </div>
      </div>
    `;
    moveHoverCard(clientX, clientY);
    hoverCard.classList.add("visible");
  }

  function clusterLabelPlacements(groups) {
    const placements = [];
    groups
      .map((group) => ({
        group,
        width: Math.max(168, themeLabel(group.theme).length * 8.1 + 28),
        x: group.anchor.x,
        y: group.anchor.y - 34
      }))
      .sort((a, b) => a.y - b.y)
      .forEach((entry) => {
        let x = entry.x;
        let y = entry.y;
        const height = 28;
        let moved = true;
        let tries = 0;
        while (moved && tries < 18) {
          moved = false;
          tries += 1;
          for (const placed of placements) {
            const overlapX = Math.abs(x - placed.x) < (entry.width + placed.width) / 2 + 12;
            const overlapY = Math.abs(y - placed.y) < height + 10;
            if (overlapX && overlapY) {
              y = placed.y + height + 12;
              moved = true;
            }
          }
        }
        placements.push({
          theme: entry.group.theme,
          x,
          y,
          width: entry.width
        });
      });
    return new Map(placements.map((placement) => [placement.theme, placement]));
  }

  function setSelectedNode(node) {
    state.selectedNodeId = node ? node.id : null;
    if (!node) {
      const activeThemeKey = state.activeThemes.size === 1 ? Array.from(state.activeThemes)[0] : null;
      const activeThemeMeta = activeThemeKey ? activeClusterMeta.get(activeThemeKey) : null;
      const visible = startups.filter(isNodeVisible);
      const audited = visible.filter((startup) => startup.profile && startup.profile.source_url).length;
      const visibleCategoryLabel = state.clusterMode === "semantic" ? `Exploracion k=${state.semanticK}` : "Base operativa guardada";
      detail.innerHTML = `
        <div class="item-title">${activeThemeKey ? themeLabel(activeThemeKey) : "Detalle"}</div>
        <div class="detail-grid">
          <div class="item-meta">Haz click en una startup para ver su ficha. Puedes arrastrar el mapa, usar zoom y limpiar la seleccion cuando quieras.</div>
          <div class="detail-actions">
            <button type="button" class="detail-action-btn" data-action="clear-selection">Limpiar seleccion</button>
            <button type="button" class="detail-action-btn" data-action="show-all">Mostrar todas las categorias</button>
          </div>
          <div class="detail-stat-grid">
            <div class="detail-stat">
              <div class="detail-stat-label">Cobertura auditada</div>
              <div class="detail-stat-value">${audited} / ${visible.length}</div>
            </div>
            <div class="detail-stat">
              <div class="detail-stat-label">Categoria visible</div>
              <div class="detail-stat-value">${visibleCategoryLabel}</div>
            </div>
          </div>
        </div>
        ${activeThemeMeta ? `
          <div class="item-meta"><strong>Descripcion:</strong> ${activeThemeMeta.description}</div>
          ${activeThemeMeta.tokens?.length ? `<div class="item-meta"><strong>Tokens distintivos:</strong> ${activeThemeMeta.tokens.join(", ")}</div>` : ""}
          ${activeThemeMeta.gridx ? `<div class="item-meta"><strong>Match GRIDX:</strong> ${activeThemeMeta.gridx}</div>` : ""}
          ${activeThemeMeta.antom ? `<div class="item-meta"><strong>Lente Antom:</strong> ${activeThemeMeta.antom}</div>` : ""}
        ` : ""}
      `;
      return;
    }

    const taxonomy = node.taxonomy;
    const profile = node.profile;
    const semantic = node.semantic;
    const sourceUrl = profile ? cleanValue(profile.source_url) : "n/d";
    const hasAuditedSource = profile && profile.source_url;
    const qualityLabel = profile ? `${cleanValue(profile.data_quality_score_10)} / 10 - ${titleCase(cleanValue(profile.quality_band))}` : `n/d`;
    const themeMeta = activeClusterMeta.get(node.theme) || (themeSystem ? themeSystem.themeMeta(node.theme) : null);
    const evidenceLabel = profile ? cleanValue(profile.evidence_excerpt) : "n/d";
    const investorLabels = startupInvestorsById.get(node.id) || [];
    const fit = node.semanticViewFit;
    const fitLabel = fit ? `${titleCase(fit.fit)}${fit.flags.length ? ` (${fit.flags.join(", ")})` : ""}` : "";
    const sourceLabel = hasAuditedSource
      ? `<a href="${profile.source_url}" target="_blank" rel="noreferrer" style="color:inherit;">${profile.source_url}</a>`
      : "Todavia sin URL auditable vinculada";
    detail.innerHTML = `
      <div class="item-title">${node.label}</div>
      <div class="detail-actions">
        <button type="button" class="detail-action-btn" data-action="clear-selection">Deseleccionar</button>
        <button type="button" class="detail-action-btn" data-action="filter-theme" data-theme="${node.theme}">Ver solo esta categoria</button>
      </div>
      <div class="detail-chip-row">
        <span class="detail-chip">${themeLabel(node.theme)}</span>
        ${taxonomy ? `<span class="detail-chip">${cleanValue(taxonomy.scope_decision || taxonomy.thesis_fit)}</span>` : ""}
        ${profile ? `<span class="detail-chip">${titleCase(cleanValue(profile.review_status))}</span>` : ""}
        ${profile ? `<span class="detail-chip">${titleCase(cleanValue(profile.quality_band))}</span>` : ""}
        <span class="detail-chip">${cleanValue(node.structured_country)}</span>
        ${investorLabels.slice(0, 3).map((label) => `<span class="detail-chip">${label}</span>`).join("")}
      </div>
      <div class="detail-stat-grid">
        <div class="detail-stat">
          <div class="detail-stat-label">Estado visual</div>
          <div class="detail-stat-value">${titleCase(node.visualStatus)}</div>
        </div>
        <div class="detail-stat">
          <div class="detail-stat-label">Categoria semantica</div>
          <div class="detail-stat-value">${node.semanticViewAssignment ? `${themeLabel(node.theme)} (${cleanValue(node.semanticViewAssignment.confidence)})` : semantic ? `${prettyTheme(semantic.semantic_single_theme)} (${cleanValue(semantic.semantic_single_confidence)})` : "n/d"}</div>
        </div>
        <div class="detail-stat">
          <div class="detail-stat-label">Calidad</div>
          <div class="detail-stat-value">${qualityLabel}</div>
        </div>
        <div class="detail-stat">
          <div class="detail-stat-label">${state.clusterMode === "semantic" ? "Cluster dinamico" : "Categoria operativa"}</div>
          <div class="detail-stat-value">${cleanValue(node.semanticClusterId)}</div>
        </div>
      </div>
      ${profile ? `<div class="item-meta"><strong>Resumen:</strong> ${cleanValue(profile.startup_summary_v1)}</div>` : ""}
      ${profile ? `<div class="item-meta"><strong>One-liner:</strong> ${cleanValue(profile.business_one_liner)}</div>` : ""}
      ${profile ? `<div class="item-meta"><strong>Por que entra o sale:</strong> ${cleanValue(profile.thesis_scope_note)}</div>` : ""}
      <div class="item-meta"><strong>Fuente:</strong> ${sourceLabel}</div>
      ${fitLabel ? `<div class="item-meta"><strong>Fit dentro del cluster:</strong> ${fitLabel}</div>` : ""}
      ${investorLabels.length ? `<div class="item-meta"><strong>Fondos vinculados:</strong> ${investorLabels.join(", ")}</div>` : ""}
      <div class="item-meta"><strong>Evidencia:</strong> ${evidenceLabel}</div>
      ${themeMeta ? `<div class="item-meta"><strong>Lectura del theme:</strong> ${themeMeta.description}</div>` : ""}
      ${taxonomy ? `
        <div class="item-meta"><strong>Subtheme:</strong> ${prettyTheme(cleanValue(node.subtheme))}</div>
        <div class="item-meta"><strong>Market label:</strong> ${titleCase(cleanValue(taxonomy.market_label))}</div>
        <div class="item-meta"><strong>Transition function:</strong> ${titleCase(cleanValue(taxonomy.transition_function))}</div>
        <div class="item-meta"><strong>Technical stack:</strong> ${titleCase(cleanValue(taxonomy.technical_stack))}</div>
        <div class="item-meta"><strong>Output class:</strong> ${titleCase(cleanValue(taxonomy.output_class))}</div>
        <div class="item-meta"><strong>Feedstock:</strong> ${titleCase(cleanValue(taxonomy.feedstock))}</div>
        <div class="item-meta"><strong>Industry destination:</strong> ${titleCase(cleanValue(taxonomy.industry_destination))}</div>
        <div class="item-meta"><strong>Market interface:</strong> ${titleCase(cleanValue(taxonomy.market_interface))}</div>
        <div class="item-meta"><strong>Match GRIDX:</strong> ${themeMeta ? themeMeta.gridx : "n/d"}</div>
        <div class="item-meta"><strong>Lente Antom:</strong> ${themeMeta ? themeMeta.antom : "n/d"}</div>
        <div class="item-meta"><strong>Current TRL:</strong> ${cleanValue(taxonomy.trl_current_status) === "pending_research" ? "Pending current research" : cleanValue(taxonomy.trl_current)}</div>
        <div class="item-meta"><strong>Estado editorial:</strong> ${profile ? titleCase(cleanValue(profile.review_status)) : "n/d"}</div>
        <div class="item-meta"><strong>Tipo de fuente:</strong> ${profile ? cleanValue(profile.source_type) : cleanValue(taxonomy.evidence_source)}</div>
        <div class="item-meta"><strong>Metodo de asignacion:</strong> ${titleCase(cleanValue(taxonomy.assignment_method))}</div>
        <div class="item-meta"><strong>Confianza taxonomica:</strong> ${cleanValue(taxonomy.confidence)}</div>
        <div class="item-meta"><strong>Scope reason:</strong> ${titleCase(cleanValue(taxonomy.scope_reason))}</div>
        ${cleanValue(node.structured_sector) !== "Digital Economy" ? `<div class="item-meta"><strong>Structured sector:</strong> ${prettyTheme(cleanValue(node.structured_sector))}</div>` : ""}
        <div class="item-meta"><strong>Origen visual:</strong> ${cleanValue(node.origin)}</div>
        <div class="item-meta"><strong>Valuation tier:</strong> ${cleanValue(node.valuation_tier)}</div>
        <div class="item-meta"><strong>PageRank:</strong> ${cleanValue(node.pagerank)}</div>
        <div class="item-meta"><strong>Degree:</strong> ${node.degree}</div>
      ` : `
        ${cleanValue(node.structured_sector) !== "Digital Economy" ? `<div class="item-meta"><strong>Legacy sector:</strong> ${prettyTheme(cleanValue(node.structured_sector))}</div>` : ""}
      `}
    `;
  }

  function renderThemeList() {
    const visibleStartupSet = startups.filter(isNodeVisible);
    const activeCandidate = state.clusterMode === "semantic" ? currentSemanticCandidate() : null;
    const reviewedVisible = visibleStartupSet.filter((node) => node.profile?.review_status === "reviewed").length;
    const seededVisible = visibleStartupSet.filter((node) => node.profile?.review_status === "seeded").length;
    startupCount.textContent = `${visibleStartupSet.length.toLocaleString("en-US")} startups confirmadas`;
    themeList.innerHTML = "";
    themeSelect.innerHTML = '<option value="all">All startup themes</option>';
    if (clusterModePill) {
      clusterModePill.textContent = state.clusterMode === "semantic" ? `Exploracion dinamica ${activeCandidate?.feature_profile_label || state.semanticProfile} / k=${state.semanticK}` : "Base operativa congelada k=7";
    }
    if (themeIntro) {
      themeIntro.innerHTML = state.clusterMode === "semantic"
        ? `Estas tarjetas muestran una <strong>exploracion semantica</strong>: perfil <strong>${activeCandidate?.feature_profile_label || state.semanticProfile}</strong>, <strong>k=${state.semanticK}</strong>, color, tamano, descripcion y empresas tipo. Universo visible: <strong>${visibleStartupSet.length}</strong> confirmadas (<strong>${reviewedVisible}</strong> reviewed, <strong>${seededVisible}</strong> seeded pendiente). Cambiar k recalcula categorias y posicion visual.`
        : `Cada tarjeta resume la <strong>base operativa congelada k=7</strong>: 7 categorias adoptadas sobre include + confirmed + source-backed, con empresas tipo para leer rapido el contenido. El selector k solo aplica cuando estas en exploracion semantica dinamica. Universo visible: <strong>${visibleStartupSet.length}</strong> confirmadas = <strong>${reviewedVisible}</strong> reviewed + <strong>${seededVisible}</strong> seeded pendientes.`;
    }
    if (themesNote) {
      themesNote.innerHTML = state.clusterMode === "semantic"
        ? `Vista dinamica: <strong>${activeCandidate?.feature_profile_label || "perfil semantico"}</strong>, <strong>k=${state.semanticK}</strong>, score de explicabilidad ${activeCandidate?.metrics?.explainability_score ?? "n/d"}. Esta capa puede tener 5, 6, 7, 8, 9, 10, 11 o 12 categorias segun el selector. Al cambiar k, cada punto migra suavemente hacia su nuevo lugar.`
        : `Esta pantalla muestra la <strong>base operativa congelada k=7</strong>: 7 categorias adoptadas del universo BIO confirmado. El selector k no modifica esta base; sirve para auditar cortes alternativos en la exploracion semantica.`;
    }
    const visibleThemeEntries = visibleThemes();
    visibleThemeEntries.forEach((group) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "theme-row";
      const highlighted = groupMatchesHighlight(group);
      if (highlighted && hasActiveHighlightFilters()) {
        row.classList.add("active");
      } else if (hasActiveHighlightFilters()) {
        row.style.opacity = "0.48";
      }
      const pct = Math.round((group.members.length / Math.max(1, visibleStartupSet.length)) * 100);
      const sourced = group.members.filter((node) => node.profile && node.profile.source_url).length;
      const themeMeta = activeClusterMeta.get(group.theme) || (themeSystem ? themeSystem.themeMeta(group.theme) : null);
      const representatives = themeMeta?.representatives || representativeNamesForMembers(group.members, 5);
      const reviewCount = Number(themeMeta?.fitReviewCount || 0);
      const watchCount = Number(themeMeta?.fitWatchCount || 0);
      const credibilityScore = themeMeta?.credibilityScore;
      row.innerHTML = `
        <div class="theme-row-top">
          <span class="theme-dot" style="background:${themeColors.get(group.theme)}"></span>
          <span class="theme-name">${themeLabel(group.theme)}</span>
          <span class="theme-count">${group.members.length}</span>
          <span class="theme-pct">${pct}%</span>
        </div>
        ${themeMeta?.description ? `<div class="theme-description">${themeMeta.description}</div>` : ""}
        ${representatives.length ? `<div class="theme-company-line"><span class="theme-company-label">Empresas tipo:</span> ${representatives.join(" · ")}</div>` : ""}
        ${state.clusterMode === "semantic" && credibilityScore !== undefined ? `<div class="theme-quality-line"><span class="theme-quality-pill${reviewCount ? " warn" : ""}">Credibilidad ${credibilityScore}/100</span><span>${reviewCount} revisar · ${watchCount} observar</span></div>` : ""}
        <div class="theme-bar">
          <div class="theme-bar-fill" style="width:${pct}%; background:${themeColors.get(group.theme)}"></div>
        </div>
      `;
      row.title = `${group.members.length} startups confirmadas en esta categoria. ${sourced}/${group.members.length} ya tienen URL fuente. ${themeMeta ? themeMeta.description : ""}${state.clusterMode === "semantic" ? ` Credibilidad: ${credibilityScore}/100. Revisar: ${reviewCount}. Observar: ${watchCount}.` : ""}`;
      row.addEventListener("click", () => {
        if (state.activeThemes.has(group.theme)) {
          state.activeThemes.delete(group.theme);
        } else {
          state.activeThemes.add(group.theme);
        }
        themeSelect.value = state.activeThemes.size === 1 ? Array.from(state.activeThemes)[0] : "all";
        renderThemeList();
        draw();
        setSelectedNode(state.selectedNodeId ? startups.find((node) => node.id === state.selectedNodeId) : null);
      });
      themeList.appendChild(row);

      const option = document.createElement("option");
      option.value = group.theme;
      option.textContent = `${themeLabel(group.theme)} (${group.members.length})`;
      themeSelect.appendChild(option);
    });

    const note = document.createElement("div");
    note.className = "item-meta";
    note.style.marginTop = "12px";
    const sourcedVisible = visibleStartupSet.filter((node) => node.profile && node.profile.source_url).length;
    const highlightedVisible = visibleStartupSet.filter(nodeMatchesHighlight).length;
    const highlightText = hasActiveHighlightFilters() ? ` Iluminadas: ${highlightedVisible}.` : "";
    note.textContent = `${visibleStartupSet.length} startups confirmadas visibles: ${reviewedVisible} reviewed + ${seededVisible} seeded pendientes. Categorias visibles: ${visibleThemeEntries.length}. Con URL fuente: ${sourcedVisible}.${highlightText} ${state.clusterMode === "semantic" ? `Exploracion: ${activeCandidate?.feature_profile_label || state.semanticProfile}, k=${state.semanticK}.` : "Modo: base operativa guardada."}`;
    themeList.appendChild(note);
    themeSelect.value = state.activeThemes.size === 1 ? Array.from(state.activeThemes)[0] : "all";
  }

  function draw() {
    edgeLayer.innerHTML = "";
    circleLayer.innerHTML = "";
    labelLayer.innerHTML = "";
    const transitionMap = transitionFromPositionMap;
    const visibleGroups = visibleThemes();
    const labelPlacements = clusterLabelPlacements(visibleGroups);

    visibleGroups.forEach((group) => {
      const emphasized = groupMatchesHighlight(group);
      const displayColor = emphasized ? group.color : "#c9c1b6";
      if (state.showLabels) {
        const labelText = themeLabel(group.theme);
        const placement = labelPlacements.get(group.theme) || {
          x: group.anchor.x,
          y: group.anchor.y - 26,
          width: Math.max(160, labelText.length * 8.4 + 24)
        };
        const labelWidth = placement.width;
        const labelX = placement.x - labelWidth / 2;
        const labelY = placement.y;
        const labelBg = makeSvg("rect", {
          x: labelX,
          y: labelY - 18,
          width: labelWidth,
          height: 28,
          rx: 14,
          fill: emphasized ? "rgba(255,250,241,0.92)" : "rgba(246,241,234,0.72)",
          stroke: displayColor,
          "stroke-width": "1"
        });
        labelBg.style.pointerEvents = "none";
        const label = makeSvg("text", {
          x: placement.x,
          y: labelY,
          "text-anchor": "middle",
          "font-family": "Georgia, serif",
          "font-size": "13",
          "font-weight": "700",
          fill: displayColor
        });
        label.style.pointerEvents = "none";
        label.textContent = labelText;
        labelLayer.appendChild(labelBg);
        labelLayer.appendChild(label);
      }

      group.clusters.forEach((cluster) => {
        cluster.nodes.forEach((node) => {
          const selected = state.selectedNodeId === node.id;
          const hovered = state.hoveredNodeId === node.id;
          const nodeEmphasized = !hasActiveHighlightFilters() || nodeMatchesHighlight(node) || selected || hovered;
          const previousPosition = transitionMap?.get(node.id);
          const shouldAnimate = previousPosition &&
            (Math.abs(previousPosition.x - node.plotX) > 1 || Math.abs(previousPosition.y - node.plotY) > 1);
          const radius = selected
            ? startupRadius(node, "selected")
            : hovered
              ? startupRadius(node, "hovered")
              : startupRadius(node, "default");
          const dot = makeSvg("circle", {
            cx: shouldAnimate ? previousPosition.x : node.plotX,
            cy: shouldAnimate ? previousPosition.y : node.plotY,
            r: radius,
            fill: nodeEmphasized ? group.color : "#cfc8bd",
            stroke: selected ? "#111111" : hovered ? "rgba(17,17,17,0.78)" : node.taxonomy ? "#ffffff" : "rgba(17,17,17,0.45)",
            "stroke-width": selected ? "1.8" : hovered ? "1.2" : node.taxonomy ? "0.8" : "0.9",
            opacity: selected ? "0.98" : nodeEmphasized ? (node.taxonomy ? "0.94" : "0.72") : "0.18"
          });
          dot.style.cursor = "pointer";
          if (shouldAnimate) {
            dot.style.transition = "cx 620ms cubic-bezier(0.22, 1, 0.36, 1), cy 620ms cubic-bezier(0.22, 1, 0.36, 1), fill 260ms ease, opacity 220ms ease";
            requestAnimationFrame(() => {
              dot.setAttribute("cx", node.plotX);
              dot.setAttribute("cy", node.plotY);
            });
          }
          dot.addEventListener("click", (event) => {
            event.stopPropagation();
            if (state.selectedNodeId === node.id) {
              clearSelection();
              return;
            }
            state.hoveredNodeId = null;
            setSelectedNode(node);
            draw();
          });
          dot.addEventListener("mouseenter", () => {
            state.hoveredNodeId = node.id;
          });
          dot.addEventListener("mouseleave", () => {
            state.hoveredNodeId = null;
            hideHoverCard();
          });
          dot.addEventListener("mousemove", (event) => {
            state.hoveredNodeId = node.id;
            showHoverCard(node, group.color, event.clientX, event.clientY);
          });
          circleLayer.appendChild(dot);
        });
      });
    });
    transitionFromPositionMap = null;
  }

  function zoomAt(factor, clientX, clientY) {
    const rect = svg.getBoundingClientRect();
    const px = ((clientX - rect.left) / rect.width) * WIDTH;
    const py = ((clientY - rect.top) / rect.height) * HEIGHT;
    const nextScale = Math.max(0.55, Math.min(3.5, state.scale * factor));
    const worldX = (px - state.offsetX) / state.scale;
    const worldY = (py - state.offsetY) / state.scale;
    state.offsetX = px - worldX * nextScale;
    state.offsetY = py - worldY * nextScale;
    state.scale = nextScale;
    updateViewport();
  }

  function resetView() {
    const bounds = currentVisibleBounds();
    const padX = 92;
    const padY = 72;
    const graphWidth = Math.max(1, bounds.maxX - bounds.minX);
    const graphHeight = Math.max(1, bounds.maxY - bounds.minY);
    const fitScale = Math.min((WIDTH - padX * 2) / graphWidth, (HEIGHT - padY * 2) / graphHeight, 2.32);
    state.scale = Math.max(1.42, fitScale);
    const cx = (bounds.minX + bounds.maxX) / 2;
    const cy = (bounds.minY + bounds.maxY) / 2;
    state.offsetX = WIDTH / 2 - cx * state.scale;
    state.offsetY = HEIGHT / 2 - cy * state.scale;
    updateViewport();
  }

  function populateSemanticControls() {
    if (clusterViewSelect) clusterViewSelect.value = state.clusterMode;
    if (semanticProfileSelect) {
      const profileIds = Array.from(new Set(semanticCandidates.map((candidate) => candidate.feature_profile)));
      const profiles = profileIds.map((id) =>
        semanticWeightProfiles.find((profile) => profile.id === id) || {
          id,
          label: titleCase(id.replace(/_/g, " "))
        }
      );
      semanticProfileSelect.innerHTML = profiles
        .map((profile) => `<option value="${profile.id}">${profile.label}</option>`)
        .join("");
      semanticProfileSelect.value = state.semanticProfile;
      semanticProfileSelect.disabled = state.clusterMode !== "semantic";
    }
    if (semanticKSelect) {
      const ks = Array.from(new Set(
        semanticCandidates
          .filter((candidate) => candidate.feature_profile === state.semanticProfile)
          .map((candidate) => Number(candidate.k))
          .filter((k) => Number.isFinite(k))
      )).sort((a, b) => a - b);
      if (!ks.includes(Number(state.semanticK))) {
        state.semanticK = ks.includes(preferredSemanticK) ? preferredSemanticK : (ks[0] || state.semanticK);
      }
      semanticKSelect.innerHTML = ks.map((k) => `<option value="${k}">k=${k}</option>`).join("");
      semanticKSelect.value = String(state.semanticK);
      semanticKSelect.disabled = state.clusterMode !== "semantic";
    }
  }

  function populateHighlightControls() {
    if (countrySelect) {
      const countries = Array.from(new Set(
        startups
          .map((node) => cleanValue(node.structured_country))
          .filter((country) => country && country !== "n/d" && country.toLowerCase() !== "nan")
      )).sort((a, b) => a.localeCompare(b, "es"));
      countrySelect.innerHTML = '<option value="all">Todos los paises</option>' +
        countries.map((country) => `<option value="${country}">${country}</option>`).join("");
      countrySelect.value = countries.includes(state.activeCountry) ? state.activeCountry : "all";
      state.activeCountry = countrySelect.value;
    }
    if (investorSelect) {
      const investors = Array.from(investorPortfolioMap.values())
        .map((portfolio) => ({
          id: portfolio.id,
          label: portfolio.label,
          count: Array.from(portfolio.startups).filter((startupId) => startupById.has(startupId)).length
        }))
        .filter((item) => item.count > 0)
        .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "es"));
      investorSelect.innerHTML = '<option value="all">Todos los fondos</option>' +
        investors.map((item) => `<option value="${item.id}">${item.label} (${item.count})</option>`).join("");
      const ids = new Set(investors.map((item) => item.id));
      investorSelect.value = ids.has(state.activeInvestor) ? state.activeInvestor : "all";
      state.activeInvestor = investorSelect.value;
    }
  }

  function refreshClusterView({ reset = true } = {}) {
    const previousPositions = new Map(semanticPositionMap);
    writeSharedTaxonomyState();
    populateSemanticControls();
    populateHighlightControls();
    state.activeThemes = new Set();
    state.activeSearchStartupId = null;
    if (startupSearchInput) startupSearchInput.value = "";
    hideStartupSearchResults();
    state.hoveredNodeId = null;
    state.selectedNodeId = null;
    hideHoverCard();
    applyActiveClusterView({ recomputeLayout: true });
    transitionFromPositionMap = previousPositions.size ? previousPositions : null;
    renderThemeList();
    draw();
    setSelectedNode(null);
    if (reset) resetView();
  }

  function hideStartupSearchResults() {
    if (!startupSearchResults) return;
    startupSearchResults.classList.remove("open");
    startupSearchResults.innerHTML = "";
  }

  function selectStartupFromSearch(node) {
    if (!node) return;
    state.activeSearchStartupId = node.id;
    state.selectedNodeId = node.id;
    if (startupSearchInput) startupSearchInput.value = node.label || node.structured_label || node.id;
    hideStartupSearchResults();
    renderThemeList();
    draw();
    setSelectedNode(node);
  }

  function renderStartupSearchResults() {
    if (!startupSearchInput || !startupSearchResults) return;
    const query = normalizeSearchText(startupSearchInput.value);
    startupSearchResults.innerHTML = "";
    if (query.length < 2) {
      hideStartupSearchResults();
      if (!query) state.activeSearchStartupId = null;
      return;
    }
    const matches = startupSearchIndex
      .filter((item) => item.key.includes(query))
      .sort((a, b) => {
        const aStarts = a.key.startsWith(query) ? 0 : 1;
        const bStarts = b.key.startsWith(query) ? 0 : 1;
        if (aStarts !== bStarts) return aStarts - bStarts;
        return a.name.localeCompare(b.name, "es");
      })
      .slice(0, 12);
    if (!matches.length) {
      startupSearchResults.innerHTML = '<div class="item-meta" style="padding:8px 10px;">Sin resultados</div>';
      startupSearchResults.classList.add("open");
      return;
    }
    matches.forEach((item, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `startup-search-result${index === 0 ? " active" : ""}`;
      button.innerHTML = `<strong>${item.name}</strong><small>${themeLabel(item.node.theme)} · ${cleanValue(item.node.structured_country)}</small>`;
      button.addEventListener("click", () => selectStartupFromSearch(item.node));
      startupSearchResults.appendChild(button);
    });
    startupSearchResults.classList.add("open");
  }

  themeSelect.addEventListener("change", () => {
    const value = themeSelect.value;
    state.activeThemes = value === "all" ? new Set() : new Set([value]);
    renderThemeList();
    draw();
    setSelectedNode(state.selectedNodeId ? startups.find((node) => node.id === state.selectedNodeId) : null);
  });

  if (countrySelect) {
    countrySelect.addEventListener("change", () => {
      state.activeCountry = countrySelect.value || "all";
      renderThemeList();
      draw();
      setSelectedNode(state.selectedNodeId ? startups.find((node) => node.id === state.selectedNodeId) : null);
    });
  }

  if (investorSelect) {
    investorSelect.addEventListener("change", () => {
      state.activeInvestor = investorSelect.value || "all";
      renderThemeList();
      draw();
      setSelectedNode(state.selectedNodeId ? startups.find((node) => node.id === state.selectedNodeId) : null);
    });
  }

  if (startupSearchInput) {
    startupSearchInput.addEventListener("input", () => {
      if (!startupSearchInput.value.trim()) {
        state.activeSearchStartupId = null;
        hideStartupSearchResults();
        renderThemeList();
        draw();
        setSelectedNode(state.selectedNodeId ? startups.find((node) => node.id === state.selectedNodeId) : null);
        return;
      }
      renderStartupSearchResults();
    });
    startupSearchInput.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        startupSearchInput.value = "";
        state.activeSearchStartupId = null;
        hideStartupSearchResults();
        renderThemeList();
        draw();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        const first = startupSearchResults?.querySelector(".startup-search-result");
        if (first) first.click();
      }
    });
    startupSearchInput.addEventListener("focus", renderStartupSearchResults);
  }

  document.addEventListener("click", (event) => {
    if (!startupSearchInput || !startupSearchResults) return;
    if (event.target === startupSearchInput || startupSearchResults.contains(event.target)) return;
    hideStartupSearchResults();
  });

  if (clearHighlightsButton) {
    clearHighlightsButton.addEventListener("click", () => {
      state.activeThemes = new Set();
      state.activeCountry = "all";
      state.activeInvestor = "all";
      state.activeSearchStartupId = null;
      if (themeSelect) themeSelect.value = "all";
      if (countrySelect) countrySelect.value = "all";
      if (investorSelect) investorSelect.value = "all";
      if (startupSearchInput) startupSearchInput.value = "";
      renderThemeList();
      draw();
      setSelectedNode(state.selectedNodeId ? startups.find((node) => node.id === state.selectedNodeId) : null);
    });
  }

  if (clusterViewSelect) {
    clusterViewSelect.addEventListener("change", () => {
      state.clusterMode = clusterViewSelect.value === "semantic" ? "semantic" : "adopted";
      refreshClusterView({ reset: true });
    });
  }

  if (semanticProfileSelect) {
    semanticProfileSelect.addEventListener("change", () => {
      state.semanticProfile = semanticProfileSelect.value || recommendedSemanticProfile;
      refreshClusterView({ reset: false });
    });
  }

  if (semanticKSelect) {
    semanticKSelect.addEventListener("change", () => {
      state.semanticK = Number(semanticKSelect.value || preferredSemanticK);
      refreshClusterView({ reset: false });
    });
  }

  function syncStatusButtons() {
    const pairs = [
      [toggleConfirmedButton, "confirmed"],
      [toggleProvisionalButton, "provisional"],
      [toggleResidualButton, "residual"]
    ];
    pairs.forEach(([button, key]) => {
      if (!button) return;
      button.classList.toggle("active", state.visibleStatuses.has(key));
    });
    if (toggleLabelsButton) {
      toggleLabelsButton.classList.toggle("active", state.showLabels);
      toggleLabelsButton.classList.toggle("muted", !state.showLabels);
      toggleLabelsButton.textContent = state.showLabels ? "Labels on" : "Labels off";
    }
  }

  function toggleStatus(key) {
    if (state.visibleStatuses.has(key)) {
      if (state.visibleStatuses.size === 1) return;
      state.visibleStatuses.delete(key);
    } else {
      state.visibleStatuses.add(key);
    }
    if (state.selectedNodeId) {
      const active = startups.find((node) => node.id === state.selectedNodeId);
      if (!active || !isNodeVisible(active)) {
        state.selectedNodeId = null;
      }
    }
    state.hoveredNodeId = null;
    syncStatusButtons();
    renderThemeList();
    draw();
    setSelectedNode(state.selectedNodeId ? startups.find((node) => node.id === state.selectedNodeId) : null);
    resetView();
  }

  svg.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoomAt(event.deltaY < 0 ? 1.12 : 0.9, event.clientX, event.clientY);
  }, { passive: false });

  svg.addEventListener("pointerdown", (event) => {
    state.isDragging = true;
    state.dragStartX = event.clientX;
    state.dragStartY = event.clientY;
    state.dragOriginX = state.offsetX;
    state.dragOriginY = state.offsetY;
    svg.style.cursor = "grabbing";
  });

  window.addEventListener("pointermove", (event) => {
    if (!state.isDragging) return;
    state.offsetX = state.dragOriginX + (event.clientX - state.dragStartX);
    state.offsetY = state.dragOriginY + (event.clientY - state.dragStartY);
    updateViewport();
  });

  window.addEventListener("pointerup", () => {
    state.isDragging = false;
    svg.style.cursor = "default";
  });
  svg.addEventListener("pointerleave", hideHoverCard);

  svg.addEventListener("click", () => {
    clearSelection();
  });

  zoomInButton.addEventListener("click", () => {
    const rect = svg.getBoundingClientRect();
    zoomAt(1.15, rect.left + rect.width / 2, rect.top + rect.height / 2);
  });
  zoomOutButton.addEventListener("click", () => {
    const rect = svg.getBoundingClientRect();
    zoomAt(0.87, rect.left + rect.width / 2, rect.top + rect.height / 2);
  });
  resetButton.addEventListener("click", resetView);
  if (toggleConfirmedButton) toggleConfirmedButton.addEventListener("click", () => toggleStatus("confirmed"));
  if (toggleProvisionalButton) toggleProvisionalButton.addEventListener("click", () => toggleStatus("provisional"));
  if (toggleResidualButton) toggleResidualButton.addEventListener("click", () => toggleStatus("residual"));
  detail.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const action = button.getAttribute("data-action");
    if (action === "clear-selection") {
      clearSelection();
      return;
    }
    if (action === "show-all") {
      state.activeThemes = new Set();
      state.activeCountry = "all";
      state.activeInvestor = "all";
      state.activeSearchStartupId = null;
      themeSelect.value = "all";
      if (countrySelect) countrySelect.value = "all";
      if (investorSelect) investorSelect.value = "all";
      if (startupSearchInput) startupSearchInput.value = "";
      renderThemeList();
      draw();
      setSelectedNode(null);
      return;
    }
    if (action === "filter-theme") {
      const theme = button.getAttribute("data-theme");
      if (!theme) return;
      state.activeThemes = new Set([theme]);
      themeSelect.value = theme;
      renderThemeList();
      draw();
      setSelectedNode(state.selectedNodeId ? startups.find((node) => node.id === state.selectedNodeId) : null);
    }
  });
  if (toggleLabelsButton) {
    toggleLabelsButton.addEventListener("click", () => {
      state.showLabels = !state.showLabels;
      syncStatusButtons();
      draw();
    });
  }

  syncStatusButtons();
  writeSharedTaxonomyState();
  populateSemanticControls();
  populateHighlightControls();
  applyActiveClusterView({ recomputeLayout: true });
  renderThemeList();
  draw();
  setSelectedNode(null);
  resetView();
})();


