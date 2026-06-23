// ── BIO LATAM i18n ────────────────────────────────────────────────────────
// Capa de UI exclusivamente. Los datos (nombres de startups, bio_theme,
// tech_codes, etc.) permanecen en su idioma normalizado de origen.
// ─────────────────────────────────────────────────────────────────────────
(function(){

var DICT = {
  es: {
    // Nav
    'nav.paradigmas':   'Paradigmas',
    'nav.atlas':        'Capital Atlas',
    'nav.intel':        'Ecosystem Intel',
    'nav.calidad':      'Calidad',

    // Strip / títulos
    'strip.paradigmas': 'Paradigmas Emergentes',
    'strip.atlas':      'Capital Atlas',
    'strip.intel':      'Inteligencia de Ecosistema',
    'meta.temas':       'temas semánticos',

    // Modos (startup-themes)
    'mode.paradigmas':  'Paradigmas',
    'mode.arbol':       'Árbol',
    'mode.escala':      'Escala',
    'mode.catalogo':    'Catálogo',

    // Layout modes
    'layout.editorial': 'Editorial',
    'layout.hibrido':   'Híbrido',
    'layout.semantico': 'Semántico',
    'layout.nombres':   'Nombres',
    'layout.filtros':   'Filtros',
    'layout.tiempo':    'Tiempo',

    // Search
    'search.startup':   'Buscar startup…',
    'search.ecosystem': 'Buscar en el ecosistema…',
    'search.query':     'Buscar por startup, fondo o tesis…',

    // Sidebar stats
    'stats.destacadas': 'destacadas',
    'stats.funded':     'con inversión',

    // Ejes (Escala)
    'axis.materia':     'Escala de la Materia',
    'axis.paradigma':   'Paradigma Tecnológico',
    'axis.bio_mat':     'Bio\nMaterial',
    'axis.bio_dig':     'Bio·Digital',
    'axis.digital':     'Digital\nComp.',

    // Descripciones escala de materia
    'scale.molecular':  'Escala Molecular — trabaja con genes, proteínas, moléculas o compuestos activos.',
    'scale.celular':    'Escala Celular — células, microorganismos y bioprocesos son su materia de trabajo.',
    'scale.organismo':  'Escala Organismo — la planta individual, el animal o el paciente es su unidad operativa.',
    'scale.lote':       'Escala Lote/Producto — opera a nivel de alimento, formulación o input manufacturado.',
    'scale.campo':      'Escala Campo/Sistema — su unidad es el campo, la finca, el suelo o la cuenca.',
    'scale.paisaje':    'Escala Paisaje/Planeta — ecosistemas, carbono, satélites y ciclos biogeoquímicos globales.',

    // Descripciones paradigma
    'paradigm.bio_mat':       'Bio-Material puro: el IP vive en la biología — una molécula, organismo o formulación.',
    'paradigm.bio_mat_soft':  'Predominantemente biológico, con herramientas digitales de soporte.',
    'paradigm.bio_dig':       'Bio·Digital: combina procesos vivos con plataformas de datos en proporciones similares.',
    'paradigm.digital_soft':  'Predominantemente digital aplicado a sistemas biológicos.',
    'paradigm.digital':       'Digital-Computacional: el IP es informacional — datos, algoritmos o plataforma.',

    // Labels panel detalle startup
    'detail.stage':       'Etapa',
    'detail.investors':   'Inversores',
    'detail.valuation':   'Valoración est.',
    'detail.tech_depth':  'Tech depth',
    'detail.theme':       'Tema semántico',
    'detail.tech_codes':  'Tecnologías',
    'detail.subcluster':  'Sub-cluster',
    'detail.bio_core':    'BIO core',
    'detail.eco_adj':     'eco-adjacent',
    'detail.cta_atlas':   'Ver en Capital Atlas →',
    'detail.cta_close':   'Ver en Capital Atlas →',
    'detail.funded':      'Con inversión',
    'detail.subclusters': 'Sub-clusters',
    'detail.top':         'Top startups',
    'detail.funded_pct':  'financiadas',

    // Stages (etiquetas de display)
    'stage.pre-seed':   'Pre-seed',
    'stage.seed':       'Seed',
    'stage.series-a':   'Serie A',
    'stage.series-b':   'Serie B',
    'stage.series-c+':  'Serie C+',
    'stage.growth':     'Growth',
    'stage.corporate':  'Corporate',
    'stage.public':     'Público',
    'stage.sin-dato':   'Sin dato',
    'stage.accelerator':'Aceleradora',

    // Tech depth
    'depth.deep':    'Deep Tech',
    'depth.applied': 'Applied Tech',
    'depth.enabler': 'Enabler',

    // Filtros
    'filter.stage':     'Etapa',
    'filter.clear':     'limpiar selección',

    // Árbol columnas
    'tree.tema':     'Tema',
    'tree.n':        'n',

    // Capital Atlas vistas
    'view.flow':     'Flujo',
    'view.funnel':   'Embudo',
    'view.country':  'País',
    'view.maturity': 'Madurez',
    'view.pipeline': 'Pipeline',
    'view.stages':   'Etapas',

    // Capital Atlas drawer / fichas
    'fund.portfolio':  'Portfolio',
    'fund.themes':     'Portfolio por tema',
    'fund.featured':   'Portfolio destacado',
    'fund.stage':      'Etapas',
    'fund.countries':  'Países',
    'fund.no_results': 'Sin resultados',
    'fund.thesis':     'Tesis de inversión',

    // Ecosystem Intel
    'intel.results':   'resultados',
    'intel.relevance': 'Relevancia',
    'intel.empty':     'Realizá una búsqueda para explorar el ecosistema.',

    // Scatter tooltip
    'scatter.startups': 'startups',

    // Maturidad (capital atlas)
    'maturity.label': 'MADUREZ — % EN SERIE A+',
  },

  en: {
    'nav.paradigmas':   'Paradigms',
    'nav.atlas':        'Capital Atlas',
    'nav.intel':        'Ecosystem Intel',
    'nav.calidad':      'Quality',

    'strip.paradigmas': 'Emerging Paradigms',
    'strip.atlas':      'Capital Atlas',
    'strip.intel':      'Ecosystem Intelligence',
    'meta.temas':       'semantic themes',

    'mode.paradigmas':  'Paradigms',
    'mode.arbol':       'Tree',
    'mode.escala':      'Scale',
    'mode.catalogo':    'Catalog',

    'layout.editorial': 'Editorial',
    'layout.hibrido':   'Hybrid',
    'layout.semantico': 'Semantic',
    'layout.nombres':   'Names',
    'layout.filtros':   'Filters',
    'layout.tiempo':    'Time',

    'search.startup':   'Search startup…',
    'search.ecosystem': 'Search the ecosystem…',
    'search.query':     'Search by startup, fund or thesis…',

    'stats.destacadas': 'featured',
    'stats.funded':     'with investment',

    'axis.materia':     'Scale of Matter',
    'axis.paradigma':   'Tech Paradigm',
    'axis.bio_mat':     'Bio\nMaterial',
    'axis.bio_dig':     'Bio·Digital',
    'axis.digital':     'Digital\nComp.',

    'scale.molecular':  'Molecular Scale — works with genes, proteins, molecules or active compounds.',
    'scale.celular':    'Cellular Scale — cells, microorganisms and bioprocesses are its material.',
    'scale.organismo':  'Organism Scale — the individual plant, animal or patient is its operative unit.',
    'scale.lote':       'Batch/Product Scale — operates at the level of food, formulation or manufactured input.',
    'scale.campo':      'Field/System Scale — its unit is the field, farm, soil or watershed.',
    'scale.paisaje':    'Landscape/Planet Scale — ecosystems, carbon, satellites and global biogeochemical cycles.',

    'paradigm.bio_mat':       'Pure Bio-Material: the IP lives in biology — a molecule, organism or formulation.',
    'paradigm.bio_mat_soft':  'Predominantly biological, with digital tools as support.',
    'paradigm.bio_dig':       'Bio·Digital: combines living processes with data platforms in similar proportions.',
    'paradigm.digital_soft':  'Predominantly digital applied to biological systems.',
    'paradigm.digital':       'Digital-Computational: the IP is informational — data, algorithms or platform.',

    'detail.stage':       'Stage',
    'detail.investors':   'Investors',
    'detail.valuation':   'Est. Valuation',
    'detail.tech_depth':  'Tech depth',
    'detail.theme':       'Semantic theme',
    'detail.tech_codes':  'Technologies',
    'detail.subcluster':  'Sub-cluster',
    'detail.bio_core':    'BIO core',
    'detail.eco_adj':     'eco-adjacent',
    'detail.cta_atlas':   'View in Capital Atlas →',
    'detail.cta_close':   'View in Capital Atlas →',
    'detail.funded':      'With investment',
    'detail.subclusters': 'Sub-clusters',
    'detail.top':         'Top startups',
    'detail.funded_pct':  'funded',

    'stage.pre-seed':   'Pre-seed',
    'stage.seed':       'Seed',
    'stage.series-a':   'Series A',
    'stage.series-b':   'Series B',
    'stage.series-c+':  'Series C+',
    'stage.growth':     'Growth',
    'stage.corporate':  'Corporate',
    'stage.public':     'Public',
    'stage.sin-dato':   'No data',
    'stage.accelerator':'Accelerator',

    'depth.deep':    'Deep Tech',
    'depth.applied': 'Applied Tech',
    'depth.enabler': 'Enabler',

    'filter.stage':  'Stage',
    'filter.clear':  'clear selection',

    'tree.tema':     'Theme',
    'tree.n':        'n',

    'view.flow':     'Flow',
    'view.funnel':   'Funnel',
    'view.country':  'Country',
    'view.maturity': 'Maturity',
    'view.pipeline': 'Pipeline',
    'view.stages':   'Stages',

    'fund.portfolio':  'Portfolio',
    'fund.themes':     'Portfolio by theme',
    'fund.featured':   'Featured portfolio',
    'fund.stage':      'Stages',
    'fund.countries':  'Countries',
    'fund.no_results': 'No results',
    'fund.thesis':     'Investment thesis',

    'intel.results':   'results',
    'intel.relevance': 'Relevance',
    'intel.empty':     'Run a search to explore the ecosystem.',

    'scatter.startups': 'startups',

    'maturity.label': 'MATURITY — % SERIES A+',
  },

  pt: {
    'nav.paradigmas':   'Paradigmas',
    'nav.atlas':        'Capital Atlas',
    'nav.intel':        'Ecosystem Intel',
    'nav.calidad':      'Qualidade',

    'strip.paradigmas': 'Paradigmas Emergentes',
    'strip.atlas':      'Capital Atlas',
    'strip.intel':      'Inteligência do Ecossistema',
    'meta.temas':       'temas semânticos',

    'mode.paradigmas':  'Paradigmas',
    'mode.arbol':       'Árvore',
    'mode.escala':      'Escala',
    'mode.catalogo':    'Catálogo',

    'layout.editorial': 'Editorial',
    'layout.hibrido':   'Híbrido',
    'layout.semantico': 'Semântico',
    'layout.nombres':   'Nomes',
    'layout.filtros':   'Filtros',
    'layout.tiempo':    'Tempo',

    'search.startup':   'Buscar startup…',
    'search.ecosystem': 'Buscar no ecossistema…',
    'search.query':     'Buscar por startup, fundo ou tese…',

    'stats.destacadas': 'destacadas',
    'stats.funded':     'com investimento',

    'axis.materia':     'Escala da Matéria',
    'axis.paradigma':   'Paradigma Tecnológico',
    'axis.bio_mat':     'Bio\nMaterial',
    'axis.bio_dig':     'Bio·Digital',
    'axis.digital':     'Digital\nComp.',

    'scale.molecular':  'Escala Molecular — trabalha com genes, proteínas, moléculas ou compostos ativos.',
    'scale.celular':    'Escala Celular — células, microrganismos e bioprocessos são sua matéria de trabalho.',
    'scale.organismo':  'Escala Organismo — a planta individual, o animal ou o paciente é sua unidade operativa.',
    'scale.lote':       'Escala Lote/Produto — opera ao nível de alimento, formulação ou insumo manufaturado.',
    'scale.campo':      'Escala Campo/Sistema — sua unidade é o campo, a fazenda, o solo ou a bacia hidrográfica.',
    'scale.paisaje':    'Escala Paisagem/Planeta — ecossistemas, carbono, satélites e ciclos biogeoquímicos globais.',

    'paradigm.bio_mat':       'Bio-Material puro: o IP vive na biologia — uma molécula, organismo ou formulação.',
    'paradigm.bio_mat_soft':  'Predominantemente biológico, com ferramentas digitais de suporte.',
    'paradigm.bio_dig':       'Bio·Digital: combina processos vivos com plataformas de dados em proporções similares.',
    'paradigm.digital_soft':  'Predominantemente digital aplicado a sistemas biológicos.',
    'paradigm.digital':       'Digital-Computacional: o IP é informacional — dados, algoritmos ou plataforma.',

    'detail.stage':       'Etapa',
    'detail.investors':   'Investidores',
    'detail.valuation':   'Avaliação est.',
    'detail.tech_depth':  'Tech depth',
    'detail.theme':       'Tema semântico',
    'detail.tech_codes':  'Tecnologias',
    'detail.subcluster':  'Sub-cluster',
    'detail.bio_core':    'BIO core',
    'detail.eco_adj':     'eco-adjacent',
    'detail.cta_atlas':   'Ver no Capital Atlas →',
    'detail.cta_close':   'Ver no Capital Atlas →',
    'detail.funded':      'Com investimento',
    'detail.subclusters': 'Sub-clusters',
    'detail.top':         'Top startups',
    'detail.funded_pct':  'financiadas',

    'stage.pre-seed':   'Pré-seed',
    'stage.seed':       'Seed',
    'stage.series-a':   'Série A',
    'stage.series-b':   'Série B',
    'stage.series-c+':  'Série C+',
    'stage.growth':     'Growth',
    'stage.corporate':  'Corporate',
    'stage.public':     'Público',
    'stage.sin-dato':   'Sem dado',
    'stage.accelerator':'Aceleradora',

    'depth.deep':    'Deep Tech',
    'depth.applied': 'Applied Tech',
    'depth.enabler': 'Enabler',

    'filter.stage':  'Etapa',
    'filter.clear':  'limpar seleção',

    'tree.tema':     'Tema',
    'tree.n':        'n',

    'view.flow':     'Fluxo',
    'view.funnel':   'Funil',
    'view.country':  'País',
    'view.maturity': 'Maturidade',
    'view.pipeline': 'Pipeline',
    'view.stages':   'Etapas',

    'fund.portfolio':  'Portfólio',
    'fund.themes':     'Portfólio por tema',
    'fund.featured':   'Portfólio destacado',
    'fund.stage':      'Etapas',
    'fund.countries':  'Países',
    'fund.no_results': 'Sem resultados',
    'fund.thesis':     'Tese de investimento',

    'intel.results':   'resultados',
    'intel.relevance': 'Relevância',
    'intel.empty':     'Faça uma busca para explorar o ecossistema.',

    'scatter.startups': 'startups',

    'maturity.label': 'MATURIDADE — % SÉRIE A+',
  }
};

// ── API pública ────────────────────────────────────────────────────────────
window.LANG = localStorage.getItem('bio_lang') || 'es';

window.t = function(key) {
  var d = DICT[window.LANG] || DICT.es;
  return d[key] !== undefined ? d[key] : (DICT.es[key] !== undefined ? DICT.es[key] : key);
};

window.switchLang = function(lang) {
  if (!DICT[lang]) return;
  window.LANG = lang;
  localStorage.setItem('bio_lang', lang);

  // Actualizar botones de idioma
  document.querySelectorAll('.lang-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.lang === lang);
  });

  // Actualizar elementos HTML estáticos con data-i18n
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.dataset.i18n;
    var attr = el.dataset.i18nAttr;
    var val = window.t(key);
    if (attr) { el.setAttribute(attr, val); }
    else { el.textContent = val; }
  });

  // Re-render dinámico: cada dashboard expone sus funciones de rebuild
  if (typeof window.scatterBuild === 'function') window.scatterBuild();
  if (typeof window.treeBuild    === 'function') window.treeBuild();
  if (typeof window.atlasBuildActive === 'function') window.atlasBuildActive();
  if (typeof window.iqRenderAll  === 'function') window.iqRenderAll();
};

// Aplicar idioma guardado al cargar (después de que el DOM esté listo)
document.addEventListener('DOMContentLoaded', function() {
  if (window.LANG !== 'es') window.switchLang(window.LANG);
});

})();
