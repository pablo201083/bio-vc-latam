(function () {
  const data = window.deepRepairData ? window.deepRepairData(window.SEMANTIC_TAXONOMY_BETA_DATA) : window.SEMANTIC_TAXONOMY_BETA_DATA;
  if (!data) return;

  const fmt = new Intl.NumberFormat('es-AR');

  const els = {
    generatedAt: document.getElementById('beta-generated-at'),
    universe: document.getElementById('beta-universe'),
    metrics: document.getElementById('beta-metrics'),
    themeListCount: document.getElementById('theme-list-count'),
    themeList: document.getElementById('theme-list'),
    microclusterCount: document.getElementById('microcluster-list-count'),
    microclusterList: document.getElementById('microcluster-list'),
    confidenceList: document.getElementById('confidence-list'),
    uncertainCount: document.getElementById('uncertain-count'),
    uncertainList: document.getElementById('uncertain-list'),
    detailBadge: document.getElementById('detail-badge'),
    themeDetail: document.getElementById('theme-detail')
  };

  const summary = data.summary || {};
  const rawThemeCoverage = data.theme_coverage || [];
  const microclusterCounts = data.microcluster_counts || [];
  const confidenceCounts = data.confidence_counts || [];
  const uncertainAssignments = data.uncertain_assignments || [];

  const themeCoverage = [...rawThemeCoverage].sort((a, b) => {
    const countDelta = Number(b.startup_count || 0) - Number(a.startup_count || 0);
    if (countDelta !== 0) return countDelta;
    const qualityDelta = Number(b.cluster_quality_score || 0) - Number(a.cluster_quality_score || 0);
    if (qualityDelta !== 0) return qualityDelta;
    return String(a.theme || '').localeCompare(String(b.theme || ''), 'es');
  });

  let selectedTheme = themeCoverage[0]?.theme || null;

  function humanDate(value) {
    if (!value) return 'N/D';
    return value.replace('T', ' ');
  }

  function percent(part, total) {
    if (!total) return 0;
    return (Number(part || 0) / Number(total || 0)) * 100;
  }

  function round1(value) {
    return Math.round(Number(value || 0) * 10) / 10;
  }

  function metricCard(label, value, note) {
    const article = document.createElement('article');
    article.className = 'panel';
    article.innerHTML = `
      <div class="meta-label">${label}</div>
      <div style="font-size:2rem;font-weight:700;margin-top:8px">${value}</div>
      <div class="item-sub">${note}</div>
    `;
    return article;
  }

  function themeSignalLabel(signal) {
    if (signal === 'strong') return 'Fuerte';
    if (signal === 'promising') return 'Prometedor';
    return 'Ruidoso';
  }

  function deriveThemeStats(theme) {
    const startupCount = Number(theme.startup_count || 0);
    const lowConfidenceCount = Number(theme.low_confidence_count || 0);
    const confirmedUniverse = Number(summary.confirmed_include_total || 0);
    const certaintyPct = round1(percent(startupCount - lowConfidenceCount, startupCount));
    const ambiguityPct = round1(percent(lowConfidenceCount, startupCount));
    const universePct = round1(percent(startupCount, confirmedUniverse));
    const signalBonus = theme.explanatory_signal === 'strong'
      ? 25
      : theme.explanatory_signal === 'promising'
        ? 12
        : 0;
    const qualityScore = Math.min(100, Math.round((certaintyPct * 0.75) + signalBonus));

    let qualityLabel = 'Cluster muy inestable';
    if (qualityScore >= 80) {
      qualityLabel = 'Cluster fuerte';
    } else if (qualityScore >= 60) {
      qualityLabel = 'Cluster usable';
    } else if (qualityScore >= 40) {
      qualityLabel = 'Cluster fragil';
    }

    let nextAction = 'Necesita mas confirmacion externa y probablemente un split editorial antes de usarlo como categoria estable.';
    if (theme.explanatory_signal === 'strong') {
      nextAction = 'Ya explica una familia bastante clara. Conviene sumar mas casos confirmados y abrir subthemes internos.';
    } else if (theme.explanatory_signal === 'promising') {
      nextAction = 'Tiene forma, pero todavia necesita bajar ambiguedad y confirmar mejor el borde del cluster.';
    }

    return {
      startupCount,
      lowConfidenceCount,
      certaintyPct,
      ambiguityPct,
      universePct,
      qualityScore,
      qualityLabel,
      nextAction
    };
  }

  function splitPills(value) {
    return String(value || '')
      .split(';')
      .join(',')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function renderMetrics() {
    els.generatedAt.textContent = humanDate(summary.generated_at);
    els.universe.textContent = `${fmt.format(summary.confirmed_include_total || 0)} confirmadas`;
    els.metrics.innerHTML = '';

    const cards = [
      metricCard('Startups totales', fmt.format(summary.startups_total || 0), 'Base total actual'),
      metricCard('Include confirmadas', fmt.format(summary.confirmed_include_total || 0), `${summary.confirmed_include_coverage_pct || 0}% del universo include`),
      metricCard('Microclusters', fmt.format(summary.microclusters_total || 0), 'Unidades analiticas puras'),
      metricCard('Macrothemes', fmt.format(summary.macrothemes_total || 0), 'Sintesis editorial actual'),
      metricCard('Compresion', `${summary.global_compression_ratio || 0}x`, 'Microclusters por macrotheme'),
      metricCard('Asignaciones low confidence', fmt.format(summary.low_confidence_assignments || 0), 'Donde la beta todavia duda'),
      metricCard('Casos borde', fmt.format(summary.uncertain_cluster_size || 0), 'Cluster ambiguo a revisar')
    ];

    cards.forEach((card) => els.metrics.appendChild(card));
  }

  function renderThemeList() {
    els.themeList.innerHTML = '';
    if (els.themeListCount) {
      els.themeListCount.textContent = `${fmt.format(themeCoverage.length)} macrothemes`;
    }
    themeCoverage.forEach((theme, index) => {
      const stats = deriveThemeStats(theme);
      const item = document.createElement('article');
      item.className = `theme-item${theme.theme === selectedTheme ? ' active' : ''}`;
      const signalLabel = themeSignalLabel(theme.explanatory_signal);
      item.innerHTML = `
        <div class="theme-topline">
          <button type="button" data-theme="${theme.theme}">${index + 1}. ${theme.theme}</button>
          <span class="pill">${fmt.format(theme.startup_count)}</span>
        </div>
        <div class="item-sub">${theme.theme_description}</div>
        <div class="badge-row">
          <span class="pill ${theme.explanatory_signal === 'noisy' ? 'warning' : ''}">${signalLabel}</span>
          <span class="pill muted">${stats.certaintyPct}% certeza</span>
          <span class="pill muted">${stats.universePct}% del universo</span>
          <span class="pill muted">${fmt.format(theme.microcluster_count || 0)} microclusters</span>
          <span class="pill muted">${theme.gridx_match}</span>
        </div>
      `;
      item.querySelector('button').addEventListener('click', () => {
        selectedTheme = theme.theme;
        renderThemeList();
        renderMicroclusterList();
        renderThemeDetail();
      });
      els.themeList.appendChild(item);
    });
  }

  function renderMicroclusterList() {
    if (!els.microclusterList) return;
    const selected = themeCoverage.find((entry) => entry.theme === selectedTheme);
    const microclusters = [...(selected?.microclusters || [])].sort((a, b) => {
      const countDiff = Number(b.startup_count || 0) - Number(a.startup_count || 0);
      if (countDiff !== 0) return countDiff;
      return Number(b.avg_margin || 0) - Number(a.avg_margin || 0);
    });
    els.microclusterList.innerHTML = '';
    if (els.microclusterCount) {
      els.microclusterCount.textContent = `${fmt.format(microclusters.length)} microclusters`;
    }
    if (!microclusters.length) {
      els.microclusterList.innerHTML = '<div class="empty-state">No hay microclusters cargados para este macrotheme.</div>';
      return;
    }
    microclusters.forEach((cluster, index) => {
      const confidenceShare = round1(percent(Number(cluster.startup_count || 0) - Number(cluster.low_confidence_count || 0), Number(cluster.startup_count || 0)));
      const item = document.createElement('article');
      item.className = 'theme-item';
      item.innerHTML = `
        <div class="theme-topline">
          <strong>${index + 1}. ${cluster.semantic_cluster_id}</strong>
          <span class="pill">${fmt.format(cluster.startup_count || 0)}</span>
        </div>
        <div class="item-sub">Dominante: ${cluster.dominant_current_macro_theme || 'N/D'}</div>
        <div class="badge-row">
          <span class="pill muted">${confidenceShare}% pureza</span>
          <span class="pill muted">margen ${round1(cluster.avg_margin || 0)}</span>
          <span class="pill muted">${cluster.representative_startups || 'sin reps'}</span>
        </div>
      `;
      els.microclusterList.appendChild(item);
    });
  }

  function renderConfidence() {
    const total = confidenceCounts.reduce((sum, item) => sum + Number(item.count || 0), 0) || 1;
    els.confidenceList.innerHTML = '';
    [...confidenceCounts]
      .sort((a, b) => Number(b.count || 0) - Number(a.count || 0))
      .forEach((item) => {
      const count = Number(item.count || 0);
      const row = document.createElement('div');
      row.className = 'bar-row';
      row.innerHTML = `
        <div class="bar-head">
          <span>${item.confidence}</span>
          <strong>${fmt.format(count)}</strong>
        </div>
        <div class="bar-track"><div class="bar-fill ${item.confidence === 'low' ? 'noisy' : ''}" style="width:${(count / total) * 100}%"></div></div>
      `;
      els.confidenceList.appendChild(row);
    });
  }

  function renderUncertain() {
    els.uncertainCount.textContent = fmt.format(uncertainAssignments.length);
    els.uncertainList.innerHTML = '';
    if (!uncertainAssignments.length) {
      els.uncertainList.innerHTML = '<div class="empty-state">No hay casos borde en esta corrida.</div>';
      return;
    }

    uncertainAssignments.forEach((item) => {
      const row = document.createElement('article');
      row.className = 'uncertain-item';
      row.innerHTML = `
        <div class="item-topline">
          <strong>${item.startup_name}</strong>
          <span class="pill warning">${item.semantic_beta_confidence}</span>
        </div>
        <div class="item-sub">${item.current_macro_theme || 'Sin macro theme'}</div>
        <div class="badge-row">
          <span class="pill muted">${item.source_type || 'sin source type'}</span>
          ${item.source_url ? `<a class="pill" href="${item.source_url}" target="_blank" rel="noreferrer">Fuente</a>` : '<span class="pill warning">Sin URL</span>'}
        </div>
      `;
      els.uncertainList.appendChild(row);
    });
  }

  function renderThemeDetail() {
    const theme = themeCoverage.find((entry) => entry.theme === selectedTheme);
    if (!theme) {
      els.detailBadge.textContent = 'Sin seleccion';
      els.themeDetail.innerHTML = '<div class="empty-state">Selecciona un theme.</div>';
      return;
    }

    const stats = deriveThemeStats(theme);
    const signalLabel = themeSignalLabel(theme.explanatory_signal);
    const representatives = splitPills(theme.representative_startups);
    const tokens = splitPills(theme.top_tokens);
    const microclusterCount = Number(theme.microcluster_count || 0);
    const compressionRatio = Number(theme.compression_ratio || 0);
    const avgMargin = round1(theme.avg_margin || 0);
    const avgScore = round1(theme.avg_score || 0);

    els.detailBadge.textContent = `${theme.theme} - ${fmt.format(theme.startup_count)}`;
    els.themeDetail.innerHTML = `
      <div class="detail-grid">
        <section class="detail-card kpi">
          <div class="detail-label">Calidad del cluster</div>
          <div class="detail-value">${stats.qualityScore}/100</div>
          <div class="detail-note">${stats.qualityLabel}</div>
          <div class="quality-meter"><div class="quality-meter-fill" style="width:${stats.qualityScore}%"></div></div>
        </section>
        <section class="detail-card kpi">
          <div class="detail-label">Certeza interna</div>
          <div class="detail-value">${stats.certaintyPct}%</div>
          <div class="detail-note">${fmt.format(stats.startupCount - stats.lowConfidenceCount)} de ${fmt.format(stats.startupCount)} casos no quedaron como low confidence</div>
        </section>
        <section class="detail-card kpi">
          <div class="detail-label">Ambiguedad</div>
          <div class="detail-value">${stats.ambiguityPct}%</div>
          <div class="detail-note">${fmt.format(stats.lowConfidenceCount)} casos todavia dudosos</div>
        </section>
        <section class="detail-card kpi">
          <div class="detail-label">Peso en el universo confirmado</div>
          <div class="detail-value">${stats.universePct}%</div>
          <div class="detail-note">${fmt.format(stats.startupCount)} startups del include + confirmed</div>
        </section>
        <section class="detail-card kpi">
          <div class="detail-label">Compresion editorial</div>
          <div class="detail-value">${fmt.format(microclusterCount)}</div>
          <div class="detail-note">Microclusters dentro de este macrotheme</div>
        </section>
        <section class="detail-card kpi">
          <div class="detail-label">Separacion promedio</div>
          <div class="detail-value">${avgMargin}</div>
          <div class="detail-note">Margen medio contra el segundo cluster mas cercano</div>
        </section>
        <section class="detail-card kpi">
          <div class="detail-label">Carga de compresion</div>
          <div class="detail-value">${compressionRatio}x</div>
          <div class="detail-note">Startups por microcluster agregado</div>
        </section>
        <section class="detail-card kpi">
          <div class="detail-label">Afinidad media</div>
          <div class="detail-value">${avgScore}</div>
          <div class="detail-note">Score promedio de pertenencia al cluster</div>
        </section>
        <section class="detail-card">
          <div class="detail-label">Que representa este theme</div>
          <div>${theme.theme_description}</div>
          <div class="badge-row">
            <span class="pill ${theme.explanatory_signal === 'noisy' ? 'warning' : ''}">${signalLabel}</span>
            <span class="pill">${fmt.format(theme.startup_count)} startups</span>
            <span class="pill muted">${stats.certaintyPct}% de certeza</span>
            <span class="pill muted">${fmt.format(microclusterCount)} microclusters</span>
          </div>
        </section>
        <section class="detail-card">
          <div class="detail-label">Dialogo con marcos externos</div>
          <ul class="detail-list">
            <li><strong>GRIDX:</strong> ${theme.gridx_match || 'N/D'}</li>
            <li><strong>Antom:</strong> ${theme.antom_match || 'N/D'}</li>
            <li><strong>Macro theme productivo dominante:</strong> ${theme.majority_current_macro_theme || 'N/D'}</li>
          </ul>
        </section>
        <section class="detail-card">
          <div class="detail-label">Startups representativas</div>
          <div class="theme-representatives">
            ${representatives.length
              ? representatives.map((item) => `<span class="theme-pill">${item}</span>`).join('')
              : '<span class="item-sub">N/D</span>'}
          </div>
        </section>
        <section class="detail-card">
          <div class="detail-label">Senales semanticas del corpus auditado</div>
          <div class="theme-representatives">
            ${tokens.length
              ? tokens.map((item) => `<span class="theme-pill">${item}</span>`).join('')
              : '<span class="item-sub">N/D</span>'}
          </div>
        </section>
        <section class="detail-card">
          <div class="detail-label">Lectura editorial</div>
          <ul class="detail-list">
            <li><strong>Senal:</strong> ${signalLabel}</li>
            <li><strong>Diagnostico:</strong> ${stats.qualityLabel}</li>
            <li><strong>Siguiente paso:</strong> ${stats.nextAction}</li>
          </ul>
        </section>
      </div>
    `;
  }

  renderMetrics();
  renderThemeList();
  renderMicroclusterList();
  renderConfidence();
  renderUncertain();
  renderThemeDetail();
})();
