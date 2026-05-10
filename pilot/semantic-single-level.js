(function () {
  const payload = window.deepRepairData ? window.deepRepairData(window.SEMANTIC_SINGLE_LEVEL_DATA || {}) : (window.SEMANTIC_SINGLE_LEVEL_DATA || {});
  const candidateList = document.getElementById("candidate-list");
  const detailBody = document.getElementById("detail-body");
  const detailTitle = document.getElementById("detail-title");
  const detailPill = document.getElementById("detail-pill");
  const metricsEl = document.getElementById("single-metrics");
  const universeEl = document.getElementById("single-universe");
  const recommendedEl = document.getElementById("single-recommended");
  const countEl = document.getElementById("candidate-count");
  const decisionMap = document.getElementById("k-decision-map");
  const profileSelect = document.getElementById("feature-profile-select");
  const profileNote = document.getElementById("feature-profile-note");

  const candidates = payload.candidates || [];
  const recommended = payload.recommended || {};
  if (!candidateList || !detailBody || !candidates.length) return;

  let selectedProfile = payload.summary?.recommended_profile || "balanced";
  let selectedK = payload.summary?.recommended_k || recommended.k || candidates.find((item) => item.feature_profile === selectedProfile)?.k || candidates[0].k;

  function getCandidate(k) {
    return candidates.find((candidate) => candidate.feature_profile === selectedProfile && Number(candidate.k) === Number(k))
      || candidates.find((candidate) => candidate.feature_profile === selectedProfile)
      || candidates[0];
  }

  function getProfileCandidates() {
    return candidates.filter((candidate) => candidate.feature_profile === selectedProfile);
  }

  function getProfiles() {
    const fromPayload = payload.weight_profiles || [];
    if (fromPayload.length) return fromPayload;
    const seen = new Set();
    return candidates.filter((candidate) => {
      if (seen.has(candidate.feature_profile)) return false;
      seen.add(candidate.feature_profile);
      return true;
    }).map((candidate) => ({
      id: candidate.feature_profile,
      label: candidate.feature_profile_label || candidate.feature_profile,
      description: candidate.feature_profile_description || ""
    }));
  }

  function clean(value) {
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

  function numberValue(value) {
    const parsed = Number(String(value ?? "").replace(",", "."));
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function pctWidth(value) {
    return Math.max(0, Math.min(100, numberValue(value)));
  }

  function selectedIsScoreWinner() {
    return selectedProfile === (payload.summary?.recommended_profile || "balanced") && Number(selectedK) === Number(payload.summary?.recommended_k);
  }

  function candidateRank(candidate) {
    const sorted = [...getProfileCandidates()].sort((a, b) => {
      const scoreDiff = numberValue(b.metrics?.explainability_score) - numberValue(a.metrics?.explainability_score);
      if (scoreDiff !== 0) return scoreDiff;
      return Number(a.k) - Number(b.k);
    });
    return sorted.findIndex((item) => Number(item.k) === Number(candidate.k)) + 1;
  }

  function tradeoffText(metrics) {
    const low = numberValue(metrics.low_confidence_share);
    const largest = numberValue(metrics.largest_cluster_share);
    const labels = numberValue(metrics.unique_labels);
    const k = numberValue(metrics.k);
    const parts = [];
    if (low <= 12) parts.push("baja ambiguedad");
    if (low > 18) parts.push("muchos casos dudosos");
    if (largest > 28) parts.push("un cluster domina demasiado");
    if (largest <= 22) parts.push("tamanos bastante balanceados");
    if (labels < k) parts.push("algunas etiquetas se repiten o colapsan");
    if (labels === k) parts.push("cada cluster logra nombre propio");
    return parts.join(", ") || "corte intermedio";
  }

  function clusterQuality(cluster, universeSize) {
    const avgMargin = Number(cluster.avg_margin || 0);
    const lowCount = Number(cluster.low_confidence_count || 0);
    const size = Number(cluster.startup_count || cluster.size || 0);
    const purity = Math.max(0, 100 - (size ? (lowCount / size) * 100 : 0));
    const share = universeSize ? (size / universeSize) * 100 : 0;
    const score = Math.max(0, Math.min(100, avgMargin * 1.7 + purity * 0.55 + Math.min(share, 18)));
    const label = score >= 80 ? "Muy solido" : score >= 65 ? "Solido" : score >= 50 ? "Prometedor" : "Fragil";
    return {
      score: Math.round(score),
      purity: Math.round(purity),
      share: share.toFixed(1),
      label
    };
  }

  function renderMetrics() {
    const summary = payload.summary || {};
    universeEl.textContent = `${summary.startups || 0} include confirmed`;
    recommendedEl.textContent = `${summary.recommended_profile || "balanced"} / k=${summary.recommended_k || "?"}`;
    countEl.textContent = `${getProfileCandidates().length} corridas`;

    const selected = getCandidate(selectedK);
    const metrics = selected.metrics || {};
    const cards = [
      { label: "k seleccionado", value: `k=${selected.k}` },
      { label: "Perfil", value: selected.feature_profile_label || selected.feature_profile || selectedProfile },
      { label: "Ranking", value: `#${candidateRank(selected)}` },
      { label: "Explainability", value: metrics.explainability_score || 0 },
      { label: "Low confidence", value: `${metrics.low_confidence_share || 0}%` },
      { label: "Pesos T/Tec/Ind", value: `${selected.weights?.text || "?"}/${selected.weights?.technology || "?"}/${selected.weights?.industry || "?"}` }
    ];
    metricsEl.innerHTML = cards.map((card) => `
      <div class="kpi-card">
        <div class="kpi-label">${card.label}</div>
        <div class="kpi-value">${card.value}</div>
      </div>
    `).join("");
  }

  function renderDecisionMap() {
    if (!decisionMap) return;
    decisionMap.innerHTML = "";
    getProfileCandidates().forEach((candidate) => {
      const metrics = candidate.metrics || {};
      const isActive = Number(candidate.k) === Number(selectedK);
      const button = document.createElement("button");
      button.type = "button";
      button.className = `decision-node${isActive ? " active" : ""}`;
      button.innerHTML = `
        <div class="candidate-top">
          <strong>k=${candidate.k}</strong>
          <span class="pill ${candidate.feature_profile === payload.summary?.recommended_profile && Number(candidate.k) === Number(payload.summary?.recommended_k) ? "" : "muted"}">${candidate.feature_profile === payload.summary?.recommended_profile && Number(candidate.k) === Number(payload.summary?.recommended_k) ? "mejor score" : `#${candidateRank(candidate)}`}</span>
        </div>
        <div class="decision-axis">
          <div class="decision-axis-label"><span>Explicabilidad</span><strong>${metrics.explainability_score || 0}</strong></div>
          <div class="bar-track"><div class="bar-fill" style="width:${pctWidth(metrics.explainability_score)}%"></div></div>
        </div>
        <div class="decision-axis">
          <div class="decision-axis-label"><span>Low confidence</span><strong>${metrics.low_confidence_share || 0}%</strong></div>
          <div class="bar-track"><div class="bar-fill" style="width:${100 - pctWidth(metrics.low_confidence_share)}%"></div></div>
        </div>
        <div class="candidate-sub">${tradeoffText({ ...metrics, k: candidate.k })}</div>
      `;
      button.addEventListener("click", () => {
        selectedK = candidate.k;
        renderMetrics();
        renderDecisionMap();
        renderCandidates();
        renderDetail();
      });
      decisionMap.appendChild(button);
    });
  }

  function renderCandidates() {
    candidateList.innerHTML = "";
    getProfileCandidates().forEach((candidate) => {
      const metrics = candidate.metrics || {};
      const item = document.createElement("div");
      item.className = `candidate-item${Number(candidate.k) === Number(selectedK) ? " active" : ""}`;
      item.innerHTML = `
        <button class="candidate-button" type="button">
          <div class="candidate-top">
            <strong>k=${candidate.k}</strong>
            <span class="pill ${candidate.feature_profile === payload.summary?.recommended_profile && Number(candidate.k) === Number(payload.summary?.recommended_k) ? "" : "muted"}">${candidate.feature_profile === payload.summary?.recommended_profile && Number(candidate.k) === Number(payload.summary?.recommended_k) ? "mejor score" : `rank #${candidateRank(candidate)}`}</span>
          </div>
          <div class="candidate-sub">${tradeoffText({ ...metrics, k: candidate.k })}. Margin ${metrics.avg_margin || 0}, low confidence ${metrics.low_confidence_share || 0}%.</div>
          <div class="bar-track">
            <div class="bar-fill" style="width:${Math.max(0, Math.min(100, Number(metrics.explainability_score || 0)))}%"></div>
          </div>
          <div class="pill-row">
            <span class="theme-pill">${metrics.unique_labels || 0} labels</span>
            <span class="theme-pill">compression ${metrics.label_compression || 0}</span>
            <span class="theme-pill">largest ${metrics.largest_cluster_share || 0}%</span>
            <span class="theme-pill">weights ${candidate.weights?.text || "?"}/${candidate.weights?.technology || "?"}/${candidate.weights?.industry || "?"}</span>
          </div>
        </button>
      `;
      item.querySelector("button").addEventListener("click", () => {
        selectedK = candidate.k;
        renderMetrics();
        renderCandidates();
        renderDetail();
      });
      candidateList.appendChild(item);
    });
  }

  function renderDetail() {
    const selected = getCandidate(selectedK);
    const metrics = selected.metrics || {};
    const isScoreWinner = selectedIsScoreWinner();
    const clusters = (selected.clusters || [])
      .slice()
      .sort((a, b) => Number(b.startup_count || b.size || 0) - Number(a.startup_count || a.size || 0));
    detailTitle.textContent = isScoreWinner ? `Corte con mejor score` : `Corte candidato k=${selected.k}`;
    detailPill.textContent = isScoreWinner ? `k=${selected.k} mejor score` : `k=${selected.k} exploratorio`;

    detailBody.innerHTML = `
      <div class="tradeoff-grid">
        <div class="tradeoff-card">
          <strong>Lectura rapida</strong>
          <div class="candidate-sub">${tradeoffText({ ...metrics, k: selected.k })}.</div>
        </div>
        <div class="tradeoff-card">
          <strong>Compresion</strong>
          <div class="candidate-sub">${metrics.unique_labels || 0} nombres para ${selected.k} clusters. Ratio ${metrics.label_compression || 0}x.</div>
        </div>
        <div class="tradeoff-card">
          <strong>Riesgo principal</strong>
          <div class="candidate-sub">${Number(metrics.largest_cluster_share || 0) > 28 ? "Un cluster esta absorbiendo demasiado universo." : "No hay una megacategoria obvia."}</div>
        </div>
        <div class="tradeoff-card">
          <strong>Uso recomendado</strong>
          <div class="candidate-sub">${isScoreWinner ? "Mejor punto automatico por score; revisar si comprime demasiado." : "Sirve para auditar si conviene ganar granularidad aunque baje el score."}</div>
        </div>
        <div class="tradeoff-card">
          <strong>Feature mix</strong>
          <div class="candidate-sub">Texto ${selected.weights?.text || "?"}, tecnologia ${selected.weights?.technology || "?"}, industria ${selected.weights?.industry || "?"}. ${selected.feature_profile_description || ""}</div>
        </div>
      </div>
      <div class="mini-grid">
        <div class="mini-stat">
          <div class="mini-label">Explainability</div>
          <div class="mini-value">${metrics.explainability_score || 0}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-label">Balance (size cv)</div>
          <div class="mini-value">${metrics.size_cv || 0}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-label">Largest cluster share</div>
          <div class="mini-value">${metrics.largest_cluster_share || 0}%</div>
        </div>
      </div>
      <div class="mini-grid" style="margin-top:14px;">
        <div class="mini-stat">
          <div class="mini-label">Avg within</div>
          <div class="mini-value">${metrics.avg_within || 0}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-label">Avg margin</div>
          <div class="mini-value">${metrics.avg_margin || 0}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-label">Low confidence share</div>
          <div class="mini-value">${metrics.low_confidence_share || 0}%</div>
        </div>
      </div>
      <div class="detail-header">
        <h2>Clusters generados para k=${selected.k}</h2>
        <span class="pill muted">${clusters.length} clusters</span>
      </div>
      <div class="cluster-list">
        ${clusters.map((cluster) => `
          ${(() => {
            const rawMembers = Array.isArray(cluster.members) && cluster.members.length
              ? cluster.members
              : (recommended.assignments || []).filter((item) => clean(item.semantic_single_cluster_id) === clean(cluster.cluster_id));
            const members = rawMembers
              .sort((a, b) => {
                const visualDiff = Number(b.score || b.semantic_single_score || b.visual_weight || 0) - Number(a.score || a.semantic_single_score || a.visual_weight || 0);
                if (visualDiff !== 0) return visualDiff;
                return String(a.startup_name || "").localeCompare(String(b.startup_name || ""), "es");
              });
            const quality = clusterQuality(cluster, Number(payload.summary?.startups || 0));
            const tokens = clean(cluster.top_tokens).split(";").map((token) => token.trim()).filter(Boolean);
            const representatives = clean(cluster.representatives).split(";").map((name) => name.trim()).filter(Boolean);
            const clusterName = clean(cluster.cluster_label || cluster.label);
            const clusterSize = Number(cluster.startup_count || cluster.size || 0);
            const clusterLow = Number(cluster.low_confidence_count || 0);
            return `
          <div class="cluster-item">
            <div class="cluster-top">
              <strong>${clusterName}</strong>
              <span>${clusterSize} startups</span>
            </div>
            <div class="cluster-sub">${cluster.description || ""}</div>
            <div class="quality-track">
              <div class="quality-fill" style="width:${quality.score}%"></div>
            </div>
            <div class="cluster-quality-grid">
              <div class="cluster-kpi">
                <div class="mini-label">Calidad del cluster</div>
                <div class="mini-value">${quality.score}/100</div>
                <div class="cluster-sub">${quality.label}</div>
              </div>
              <div class="cluster-kpi">
                <div class="mini-label">Pureza</div>
                <div class="mini-value">${quality.purity}%</div>
                <div class="cluster-sub">${clusterLow} low confidence</div>
              </div>
              <div class="cluster-kpi">
                <div class="mini-label">Peso en el universo</div>
                <div class="mini-value">${quality.share}%</div>
                <div class="cluster-sub">${clusterSize} de ${payload.summary?.startups || 0}</div>
              </div>
              <div class="cluster-kpi">
                <div class="mini-label">Separacion media</div>
                <div class="mini-value">${cluster.avg_margin || 0}</div>
                <div class="cluster-sub">${titleCase(clean(cluster.dominant_macro))}</div>
              </div>
            </div>
            <div class="cluster-columns">
              <div class="content-block">
                <div class="cluster-section-title">Tokens distintivos</div>
                <div class="token-cloud">
                  ${tokens.map((token) => `<span class="token-chip">${token}</span>`).join("") || `<span class="token-chip">n/d</span>`}
                </div>
                <div class="cluster-section-title" style="margin-top:14px;">Startups representativas</div>
                <div class="startup-chip-list">
                  ${representatives.map((name) => `<span class="startup-chip">${name}</span>`).join("") || `<span class="startup-chip">n/d</span>`}
                </div>
              </div>
              <div class="content-block">
                <div class="cluster-section-title">Componentes del cluster</div>
                <div class="startup-chip-list">
                  ${members.length
                    ? members.map((item) => `<span class="startup-chip" title="score ${clean(item.score || item.semantic_single_score)} · margen ${clean(item.margin || item.semantic_single_margin)} · ${clean(item.confidence || item.semantic_single_confidence)}">${clean(item.startup_name)}</span>`).join("")
                    : `<span class="startup-chip">n/d</span>`}
                </div>
              </div>
            </div>
          </div>
            `;
          })()}
        `).join("")}
      </div>
    `;
  }

  function renderProfileControls() {
    if (!profileSelect) return;
    const profiles = getProfiles();
    const active = profiles.find((profile) => profile.id === selectedProfile) || profiles[0];
    profileSelect.innerHTML = profiles.map((profile) => `
      <option value="${profile.id}" ${profile.id === selectedProfile ? "selected" : ""}>${profile.label || profile.id}</option>
    `).join("");
    if (profileNote) profileNote.textContent = active?.description || "";
  }

  if (profileSelect) {
    profileSelect.addEventListener("change", () => {
      selectedProfile = profileSelect.value;
      const best = getProfileCandidates().slice().sort((a, b) => {
        const scoreDiff = numberValue(b.metrics?.explainability_score) - numberValue(a.metrics?.explainability_score);
        if (scoreDiff !== 0) return scoreDiff;
        return Number(a.k) - Number(b.k);
      })[0];
      selectedK = best?.k || selectedK;
      renderProfileControls();
      renderMetrics();
      renderDecisionMap();
      renderCandidates();
      renderDetail();
    });
  }

  renderProfileControls();
  renderMetrics();
  renderDecisionMap();
  renderCandidates();
  renderDetail();
})();
