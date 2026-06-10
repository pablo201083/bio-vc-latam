/*
 * coverage-note.js — chip de honestidad de cobertura para los dashboards.
 *
 * Lee window.COVERAGE_DATA (generado por `python pipeline.py coverage`) e
 * inyecta un chip fijo abajo a la izquierda: cuántas celdas tema×país están
 * bien mapeadas y qué países siguen poco explorados. Click expande la leyenda.
 *
 * Regla de producto: la ausencia en el mapa NO se lee como inexistencia salvo
 * en zonas bien barridas. Este chip es el recordatorio permanente de eso.
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
      '<strong style="color:var(--ink,#181714)">Cobertura del mapa:</strong> ' +
      ok + '/' + latam.length + ' celdas tema×país bien mapeadas · ' +
      under.length + ' países LATAM poco explorados';

    var detail =
      '<div style="margin-top:7px;border-top:1px solid var(--line,#d8ccc0);padding-top:7px">' +
      '<div style="margin-bottom:5px">Poco explorados: <strong>' + under.join(', ') + '</strong>' +
      ' — ahí la ausencia <em>no</em> significa inexistencia.</div>' +
      Object.keys(data.legend || {}).map(function (k) {
        return '<div><strong>' + k + '</strong>: ' + data.legend[k] + '</div>';
      }).join('') +
      '<div style="margin-top:5px;opacity:.75">Detalle: quality/coverage_matrix.csv · ' +
      'generado ' + (data.generated_at || '').slice(0, 10) + '</div></div>';

    var expanded = false;
    chip.innerHTML = headline;
    chip.title = 'Click para ver la leyenda de cobertura';
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
