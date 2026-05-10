const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const dataPath = path.join(root, "pilot", "semantic-single-level-data.js");
const profilesPath = path.join(root, "pilot", "startup-profiles-data.js");
const taxonomyPath = path.join(root, "pilot", "startup-taxonomy-data.js");
const outPath = path.join(root, "quality", "semantic_cluster_fit_audit.csv");

const context = { window: {} };
vm.createContext(context);
vm.runInContext(fs.readFileSync(dataPath, "utf8"), context);
vm.runInContext(fs.readFileSync(profilesPath, "utf8"), context);
vm.runInContext(fs.readFileSync(taxonomyPath, "utf8"), context);

const data = context.window.SEMANTIC_SINGLE_LEVEL_DATA || {};
const profiles = context.window.STARTUP_PROFILES_DATA || {};
const taxonomy = context.window.STARTUP_TAXONOMY_DATA || {};
const profileById = new Map((profiles.profiles || []).map((item) => [item.startup_id, item]));
const taxonomyById = taxonomy.assignmentsById || {};
const candidate = (data.candidates || []).find(
  (item) =>
    item.feature_profile === data.summary?.recommended_profile &&
    Number(item.k) === Number(data.summary?.recommended_k)
);

if (!candidate) {
  throw new Error(`Missing recommended semantic candidate: ${data.summary?.recommended_profile || "unknown"} / k=${data.summary?.recommended_k || "unknown"}.`);
}

function policyForLabel(label) {
  const normalized = String(label || "").toLowerCase();
  const policy = (anchor) => ({ label, anchor });
  if (normalized.includes("clinical") || normalized.includes("diagnostic") || normalized.includes("medical")) {
    return policy(/diagnostics|diagnostic|medtech|medical|clinical|device|biopsy|imaging|respiratory|tumor|cancer|genomics|molecular|screening|neuro|glaucoma|ventilation/i);
  }
  if (normalized.includes("therapeutic") || normalized.includes("regenerative")) {
    return policy(/therapeutic|therapy|treatment|disease|cells|cell|tissue|regenerative|stem|wound|oncology|immunotherapy|vaccine|nanomedicine|drug/i);
  }
  if (normalized.includes("food") || normalized.includes("biofactor") || normalized.includes("ingredient")) {
    return policy(/food|ingredient|protein|fermentation|precision fermentation|enzyme|dairy|yeast|bacteria|plant based|prebiotic|microbiome|nutraceutical/i);
  }
  if (normalized.includes("chemistry") || normalized.includes("material")) {
    return policy(/biomaterial|material|chemistry|polymer|fungal|mycelium|waste|residue|biopolymer|biodegradable|pigment|textile|packaging|mineral|lithium|biomining/i);
  }
  if (normalized.includes("biological") || normalized.includes("crop resilience")) {
    return policy(/biological|bioinput|microbial|inoculant|crop|soil|seed|pest|pollination|plant|resilience|agriculture|farm|agronomic/i);
  }
  if (normalized.includes("grain") || normalized.includes("traceability") || normalized.includes("producer")) {
    return policy(/grain|traceability|producer|grower|agro|agri|farm|credit|financing|inputs|marketplace|supply chain|silo|quality analysis/i);
  }
  if (normalized.includes("agri intelligence") || normalized.includes("traceable markets")) {
    return policy(/agri|agtech|crop|farm|field|producer|satellite|geospatial|monitoring|precision|risk|credit|traceability|supply chain|coffee|grain/i);
  }
  if (normalized.includes("planetary") || normalized.includes("climate")) {
    return policy(/planetary|climate|water|energy|environment|monitoring|wildfire|forest|emissions|carbon|biodiversity|conservation|restoration|resource|satellite/i);
  }
  if (normalized.includes("resource") || normalized.includes("remediation")) {
    return policy(/resource|recovery|remediation|carbon|soil|biodiversity|restoration|organic|waste|hydrocarbon|microbial|circular|nature/i);
  }
  if (normalized.includes("animal") || normalized.includes("protein")) {
    return policy(/animal|livestock|protein|feed|poultry|cattle|fish|fermentation|ingredient|agtech|farm|production/i);
  }
  return policy(null);
}

function splitTokens(value) {
  return String(value || "")
    .split(/[;,|]/)
    .map((token) => token.trim().toLowerCase())
    .filter(Boolean);
}

function csv(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

const rows = [];
const summary = [];

for (const cluster of candidate.clusters || []) {
  const policy = policyForLabel(cluster.label);
  const topTokens = splitTokens(cluster.top_tokens);
  let good = 0;
  let watch = 0;
  let review = 0;

  for (const member of cluster.members || []) {
    const profile = profileById.get(member.startup_id) || {};
    const tax = taxonomyById[member.startup_id] || {};
    const text = [
      member.startup_name,
      member.technology_features,
      member.industry_features,
      member.market_label,
      profile.startup_summary_v1,
      profile.business_one_liner,
      profile.thesis_scope_note,
      profile.evidence_excerpt,
      tax.market_label,
      tax.technical_stack,
      tax.transition_function,
      tax.output_class,
      tax.feedstock,
      tax.industry_destination
    ].join(" ").toLowerCase();
    const overlap = topTokens.filter((token) => text.includes(token));
    const margin = Number(member.margin || 0);
    const policyFit = !policy.anchor || policy.anchor.test(text);
    const flags = [];
    if (margin < 4) flags.push("low_margin");
    if (topTokens.length && overlap.length < 1) flags.push("weak_token_overlap");
    if (!policyFit) flags.push("weak_policy_fit");
    const fit = flags.length === 0 ? "good" : policyFit && !flags.includes("low_margin") ? "watch" : "review";
    if (fit === "good") good += 1;
    if (fit === "watch") watch += 1;
    if (fit === "review") review += 1;
    rows.push({
      cluster_id: cluster.cluster_id,
      original_label: cluster.label,
      curated_label: policy.label,
      startup_name: member.startup_name,
      fit,
      flags: flags.join("; "),
      margin,
      token_overlap: overlap.join("; "),
      policy_fit: policyFit,
      technology_features: member.technology_features || "",
      industry_features: member.industry_features || ""
    });
  }

  const credibility = Math.max(0, Math.round(100 - (((review * 7 + watch * 2.5 + Number(cluster.low_confidence_count || 0) * 3) / Math.max(1, cluster.size || 1)) * 10)));
  summary.push({ cluster_id: cluster.cluster_id, label: policy.label, size: cluster.size, good, watch, review, credibility });
}

const header = Object.keys(rows[0] || { cluster_id: "", startup_name: "" });
fs.writeFileSync(
  outPath,
  [header.join(","), ...rows.map((row) => header.map((key) => csv(row[key])).join(","))].join("\n"),
  "utf8"
);

console.log("Semantic cluster fit audit written:", outPath);
for (const item of summary) {
  console.log(`${item.cluster_id} | ${item.label} | size=${item.size} | credibility=${item.credibility}/100 | review=${item.review} | watch=${item.watch}`);
}
