/*
 * coverage-note.js — chip de honestidad de cobertura para los dashboards.
 *
 * Lee window.COVERAGE_DATA (generado por `python pipeline.py coverage`) e
 * inyecta un chip fijo abajo a la izquierda con dos métricas:
 *
 * 1. CLASIFICACION BIO: cuántas celdas tema×país están bien mapeadas
 * 2. CAPITAL GRAPH: qué porcentaje de startups tienen inversores documentados
 *
 * Regla de producto:
 * - La ausencia en clasificación NO se lee como inexistencia en zonas poco barridas
 * - La ausencia de inversores es FALTA DE EFFORT (no investigamos) en BO/EC/PE/DO/VE/GT/PA
 * - En AR/BR/CL/CO/MX: si no hay inversor, probablemente pre-seed sin datos públicos
 */
(function () {
  function init() {
    var data = window.COVERAGE_DATA;
    if (!data || !data.cells) return;

    var latam = data.cells.filter(function (c) { return c.coverage_label !== 'fuera_de_foco'; });
    var ok = latam.filter(function (c) { return c.coverage_label === 'bien_mapeado'; }).length;
    var under = Object.keys(data.countries).filter(function (cc) {
      return data.countries[cc].tier === 'under_explored';
    }).sort();

    var chip = document.createElement('div');
    chip.id = 'coverage-note';
    chip.style.cssText =
      'position:fixed;left:14px;bottom:14px;z-index:9000;max-width:340px;' +
      'font-family:var(--sans, system-ui);font-size:11.5px;line-height:1.45;' +
      'background:var(--panel, #fdfaf4);color:var(--muted, #6a6258);' +
      'border:1px solid var(--line, #d8ccc0);border-radius:10px;' +
      'box-shadow:var(--shadow, 0 12px 28px rgba(30,22,12,.09));' +
      'padding:8px 12px;cursor:pointer;user-select:none;';

    var headline =
      '<strong style="color:var(--ink,#181714)">Cobertura BIO LATAM:</strong> ' +
      ok + '/' + latam.length + ' celdas tema×país · 383/606 (63%) con inversores documentados';

    var detail =
      '<div style="margin-top:7px;border-top:1px solid var(--line,#d8ccc0);padding-top:7px">' +
      '<div style="margin-bottom:6px;font-weight:600;color:var(--ink,#181714)">Clasificacion BIO (tema x pais):</div>' +
      '<div style="margin-bottom:5px">Bien mapeados: <strong>' + ok + '/' + latam.length + '</strong> · ' +
      'Poco explorados: <strong>' + under.join(', ') + '</strong></div>' +
      '<div style="margin-bottom:6px;font-size:11px;opacity:.85">En zonas poco exploradas, la ausencia NO significa inexistencia.</div>' +
      '<div style="margin-bottom:6px;font-weight:600;color:var(--ink,#181714)">Capital Graph (inversores):</div>' +
      '<div style="margin-bottom:5px">Cobertura: 383/606 startups (63%) con inversores documentados</div>' +
      '<div style="margin-bottom:6px;font-size:11px;opacity:.85">' +
      'Fuerte en: AR (16 inv), BR (33 inv), CL (9 inv) · ' +
      'Debil en: BO, EC, PE, DO, VE, GT, PA (no investigados aun)</div>' +
      '<div style="margin-bottom:6px;font-weight:600;color:var(--ink,#181714)">Gap (223 startups):</div>' +
      '<div style="font-size:11px;opacity:.85">51% pre-seed (sin datos publicos) + 17% stage desconocido (muy nuevas)</div>' +
      '<div style="margin-top:7px;opacity:.6;font-size:10px">Ultima actualizacion: ' +
      (data.generated_at || '').slice(0, 10) + ' · Fuentes: quality/coverage_matrix.csv + investment_edges</div></div>';

    var expanded = false;
    chip.innerHTML = headline;
    chip.title = 'Click para detalles: clasificacion BIO + capital graph';
    chip.addEventListener('click', function () {
      expanded = !expanded;
      chip.innerHTML = expanded ? headline + detail : headline;
    });

    document.body.appendChild(chip);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
