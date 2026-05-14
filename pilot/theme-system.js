(function () {
  const CANONICAL_THEME_ORDER = [
    "ag biologicals and crop resilience",
    "food ingredients and biofactories",
    "industrial enzymes and bioprocess platforms",
    "agri intelligence and traceable markets",
    "clinical diagnostics and medical devices",
    "therapeutics and regenerative bio",
    "climate and resource intelligence platforms",
    "biobased chemistry and advanced materials",
    "computational biology and scientific software",
    "frontier hardware and infrastructure systems",
    "semantic edge cases",
    "outside thesis digital ventures"
  ];

  const CANONICAL_THEME_META = {
    "ag biologicals and crop resilience": {
      label: "Ag Biologicals And Crop Resilience",
      color: "#7e57c2",
      description: "Biological inputs and productive resilience for agricultural systems.",
      gridx: "Agri-food-land use",
      antom: "Deployment / intervention",
      position: { x: 0.68, y: 0.36 }
    },
    "food ingredients and biofactories": {
      label: "Food Ingredients And Biofactories",
      color: "#00acc1",
      description: "Food ingredients, fermentation and biofactory systems.",
      gridx: "Agri-food-land use / Bio-industry",
      antom: "Material deployment",
      position: { x: 0.45, y: 0.58 }
    },
    "industrial enzymes and bioprocess platforms": {
      label: "Industrial Enzymes And Bioprocess Platforms",
      color: "#8bc34a",
      description: "Enzymes, bioindustrial tools and process platforms for biological manufacturing.",
      gridx: "Bio-industry / Deep-biotech",
      antom: "Material deployment",
      position: { x: 0.56, y: 0.46 }
    },
    "agri intelligence and traceable markets": {
      label: "Agri Intelligence And Traceable Markets",
      color: "#d16ba5",
      description: "Agronomic decisioning, traceability and material coordination of agri-food chains.",
      gridx: "Agri-food-land use",
      antom: "Connection / deployment",
      position: { x: 0.28, y: 0.72 }
    },
    "clinical diagnostics and medical devices": {
      label: "Clinical Diagnostics And Medical Devices",
      color: "#1f4e6c",
      description: "Diagnostics, detection and clinical devices.",
      gridx: "Human health",
      antom: "Clinical intervention on living systems",
      position: { x: 0.79, y: 0.18 }
    },
    "therapeutics and regenerative bio": {
      label: "Therapeutics And Regenerative Bio",
      color: "#b23a48",
      description: "Therapeutics, biological delivery and regenerative medicine.",
      gridx: "Human health",
      antom: "Biocentric",
      position: { x: 0.22, y: 0.26 }
    },
    "climate and resource intelligence platforms": {
      label: "Climate And Resource Intelligence Platforms",
      color: "#ff7043",
      description: "Software coupled to physical systems for energy, resources and decarbonization.",
      gridx: "Climate systems / Resource systems",
      antom: "Deployment / coordination / MRV",
      position: { x: 0.82, y: 0.56 }
    },
    "biobased chemistry and advanced materials": {
      label: "Biobased Chemistry And Advanced Materials",
      color: "#26c6da",
      description: "Biomaterials, biobased chemistry, material circularity and fossil-input substitution.",
      gridx: "Bio-industry / Materials",
      antom: "Material deployment",
      position: { x: 0.64, y: 0.76 }
    },
    "computational biology and scientific software": {
      label: "Computational Biology And Scientific Software",
      color: "#ef5350",
      description: "Scientific software, computational discovery and data platforms for life sciences.",
      gridx: "Deep-biotech / Human health",
      antom: "Intelligence layer",
      position: { x: 0.36, y: 0.16 }
    },
    "frontier hardware and infrastructure systems": {
      label: "Frontier Hardware And Infrastructure Systems",
      color: "#78909c",
      description: "Frontier hardware and infrastructure when clearly coupled to material or planetary systems.",
      gridx: "Infrastructure / Frontier systems",
      antom: "Enabling infrastructure",
      position: { x: 0.9, y: 0.82 }
    },
    "semantic edge cases": {
      label: "Semantic Edge Cases",
      color: "#90a4ae",
      description: "Cases where semantic segmentation still mixes categories or loses definition.",
      gridx: "Mixed / unresolved",
      antom: "Mixed",
      position: { x: 0.5, y: 0.88 }
    },
    "outside thesis digital ventures": {
      label: "Outside Thesis Digital Ventures",
      color: "#607d8b",
      description: "Horizontal software or ventures without enough material or biocentric coupling for the thesis.",
      gridx: "Out of domain",
      antom: "Outside thesis",
      position: { x: 0.1, y: 0.9 }
    },

    // ── v3 Editorial Taxonomy (7 categories) ─────────────────────────────────
    "Therapeutics": {
      label: "Therapeutics",
      color: "#7033BC",
      description: "Drugs, biologics, cell & gene therapies, animal health medicines, wound care.",
      gridx: "Human health",
      antom: "Biocentric / therapeutic",
      position: { x: 0.22, y: 0.24 }
    },
    "Diagnostics & Health Access": {
      label: "Diagnostics & Health Access",
      color: "#1A6DB5",
      description: "Diagnostic devices, lab-on-chip, digital health, point-of-care testing.",
      gridx: "Human health",
      antom: "Clinical intervention / diagnostics",
      position: { x: 0.76, y: 0.18 }
    },
    "Food Systems & Alt Proteins": {
      label: "Food Systems & Alt Proteins",
      color: "#C25A2A",
      description: "Alternative proteins, precision fermentation for food, aquaculture biotech, functional foods.",
      gridx: "Agri-food-land use / Bio-industry",
      antom: "Material deployment / food",
      position: { x: 0.44, y: 0.62 }
    },
    "Bioinputs & Crop Resilience": {
      label: "Bioinputs & Crop Resilience",
      color: "#2A7A42",
      description: "Biofertilizers, biocontrol, biopesticides, CRISPR crops, precision breeding, seed treatments.",
      gridx: "Agri-food-land use",
      antom: "Deployment / intervention",
      position: { x: 0.68, y: 0.38 }
    },
    "Nature & Ecosystem Tech": {
      label: "Nature & Ecosystem Tech",
      color: "#127A6E",
      description: "Ecosystem monitoring, biodiversity finance, carbon/nature markets, agri-monitoring platforms.",
      gridx: "Climate systems / Agri-food-land use",
      antom: "MRV / coordination / deployment",
      position: { x: 0.82, y: 0.56 }
    },
    "Farm Intelligence": {
      label: "Farm Intelligence",
      color: "#2E4E8C",
      description: "Precision agriculture platforms, agrifintech, IoT sensors, agronomic decision tools.",
      gridx: "Agri-food-land use",
      antom: "Connection / intelligence",
      position: { x: 0.28, y: 0.74 }
    },
    "Biomaterials & Circular Economy": {
      label: "Biomaterials & Circular Economy",
      color: "#8B6D14",
      description: "Bioplastics, industrial enzymes, green chemistry, e-fuels, mycelium materials, biobased chemicals.",
      gridx: "Bio-industry / Deep-biotech",
      antom: "Material deployment / circular",
      position: { x: 0.56, y: 0.46 }
    }
  };

  const LEGACY_TO_SEMANTIC = {
    "food biotech and novel ingredients": "food ingredients and biofactories",
    "food transition ingredients and proteins": "food ingredients and biofactories",
    "food biofactories and functional ingredients": "food ingredients and biofactories",
    "fermented functional ingredients": "food ingredients and biofactories",
    "food ingredients and biofactories": "food ingredients and biofactories",

    "ag biologicals and crop resilience": "ag biologicals and crop resilience",
    "genome-enabled crop resilience": "ag biologicals and crop resilience",
    "extremophile microbial ag inputs": "ag biologicals and crop resilience",
    "data-driven pollination systems": "ag biologicals and crop resilience",

    "precision agriculture and resource intelligence": "agri intelligence and traceable markets",
    "precision agriculture intelligence": "agri intelligence and traceable markets",
    "water intelligence for resilient agriculture": "agri intelligence and traceable markets",
    "traceability and tokenized resource infrastructure": "agri intelligence and traceable markets",
    "ag-input market infrastructure": "agri intelligence and traceable markets",
    "agri intelligence and traceable markets": "agri intelligence and traceable markets",

    "diagnostics and medtech": "clinical diagnostics and medical devices",
    "health diagnostics and medtech": "clinical diagnostics and medical devices",
    "distributed diagnostics and clinical devices": "clinical diagnostics and medical devices",
    "clinical diagnostics and medical devices": "clinical diagnostics and medical devices",

    "therapeutics and regenerative medicine": "therapeutics and regenerative bio",
    "therapeutic and regenerative biology": "therapeutics and regenerative bio",
    "therapeutics and regenerative bio": "therapeutics and regenerative bio",

    "biomanufacturing and bioindustrial platforms": "industrial enzymes and bioprocess platforms",
    "industrial biotech and molecular tools": "industrial enzymes and bioprocess platforms",
    "biomanufacturing and molecular platforms": "industrial enzymes and bioprocess platforms",
    "industrial enzymes and bioprocess platforms": "industrial enzymes and bioprocess platforms",

    "computational biology and scientific software": "computational biology and scientific software",
    "computational biology and life-science software": "computational biology and scientific software",
    "computational biology and genomic intelligence": "computational biology and scientific software",

    "climate, energy and resource systems": "climate and resource intelligence platforms",
    "frontier hardware and infrastructure systems": "frontier hardware and infrastructure systems",
    "frontier hardware and space systems": "frontier hardware and infrastructure systems",
    "planetary monitoring and resilience systems": "climate and resource intelligence platforms",
    "resource recovery and remediation": "climate and resource intelligence platforms",
    "resource recovery, circularity and remediation": "climate and resource intelligence platforms",
    "biobased chemistry and advanced materials": "biobased chemistry and advanced materials",
    "biobased chemistry and circular materials": "biobased chemistry and advanced materials",

    "uncertain source-backed edge cases": "semantic edge cases",
    "semantic edge cases": "semantic edge cases",
    "peripheral or underclassified ventures": "semantic edge cases",
    "unclassified / needs review resolved": "semantic edge cases",
    "other / unclassified": "semantic edge cases",

    "digital economy": "outside thesis digital ventures",
    "peripheral or non-core digital ventures": "outside thesis digital ventures",
    "outside thesis digital ventures": "outside thesis digital ventures"
  };

  function normalizeThemeKey(value) {
    const text = String(value || "").trim();
    if (!text || text.toLowerCase() === "nan") return "semantic edge cases";
    const mapped = LEGACY_TO_SEMANTIC[text.toLowerCase()];
    if (mapped) return mapped;
    return CANONICAL_THEME_META[text] ? text : "semantic edge cases";
  }

  function themeMeta(key) {
    return CANONICAL_THEME_META[normalizeThemeKey(key)] || CANONICAL_THEME_META["semantic edge cases"];
  }

  function themeLabel(key) {
    return themeMeta(key).label;
  }

  function themeColor(key) {
    return themeMeta(key).color;
  }

  function themeSortScore(key) {
    const normalized = normalizeThemeKey(key);
    const index = CANONICAL_THEME_ORDER.indexOf(normalized);
    return index === -1 ? 999 : index;
  }

  function themePosition(key) {
    return themeMeta(key).position || { x: 0.5, y: 0.5 };
  }

  window.THEME_SYSTEM = {
    order: CANONICAL_THEME_ORDER,
    meta: CANONICAL_THEME_META,
    legacyMap: LEGACY_TO_SEMANTIC,
    normalizeThemeKey,
    themeMeta,
    themeLabel,
    themeColor,
    themeSortScore,
    themePosition
  };
})();
