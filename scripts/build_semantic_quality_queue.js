const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const outPath = path.join(root, "quality", "semantic_quality_queue.csv");
const summaryPath = path.join(root, "quality", "semantic_quality_queue.md");

function loadCsv(file) {
  const text = fs.readFileSync(file, "utf8").replace(/^\uFEFF/, "");
  const rows = [];
  const cells = [];
  let cell = "";
  let row = [];
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (quoted) {
      if (ch === '"' && next === '"') {
        cell += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        cell += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(cell);
      cell = "";
    } else if (ch === "\n") {
      row.push(cell);
      cells.push(row);
      row = [];
      cell = "";
    } else if (ch !== "\r") {
      cell += ch;
    }
  }
  if (cell.length || row.length) {
    row.push(cell);
    cells.push(row);
  }
  if (!cells.length) return [];
  const headers = cells.shift();
  return cells
    .filter((values) => values.some((value) => String(value || "").trim()))
    .map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] || ""])));
}

function csv(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function clean(value) {
  const text = String(value || "").trim();
  return !text || text.toLowerCase() === "nan" ? "" : text;
}

function norm(value) {
  return clean(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function wordCount(value) {
  return norm(value).split(/\s+/).filter(Boolean).length;
}

function titleCase(value) {
  return clean(value).replace(/[_-]/g, " ").split(/\s+/).filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

const semanticContext = { window: {} };
vm.createContext(semanticContext);
vm.runInContext(fs.readFileSync(path.join(root, "pilot", "semantic-single-level-data.js"), "utf8"), semanticContext);
const semanticData = semanticContext.window.SEMANTIC_SINGLE_LEVEL_DATA || {};
const master = loadCsv(path.join(root, "startup_master_dataset.csv"));
const taxonomyRows = loadCsv(path.join(root, "startup_taxonomy_assignments_v1.csv"));
const taxonomyById = new Map(taxonomyRows.map((row) => [clean(row.startup_id), row]));
const manualOverridePath = path.join(root, "quality", "manual_semantic_theme_overrides.csv");
const manualOverrides = fs.existsSync(manualOverridePath)
  ? new Map(loadCsv(manualOverridePath).map((row) => [clean(row.startup_id), row]))
  : new Map();
const fitAuditPath = path.join(root, "quality", "semantic_cluster_fit_audit.csv");
const fitRows = fs.existsSync(fitAuditPath) ? loadCsv(fitAuditPath) : [];
const fitByName = new Map(fitRows.map((row) => [norm(row.startup_name), row]));
const recommendedById = new Map(Object.entries(semanticData.recommended?.assignmentsById || {}).map(([id, value]) => {
  const row = Array.isArray(value) ? value[0] : value;
  return [clean(id), {
    theme: clean(row?.semantic_single_theme),
    cluster_id: clean(row?.semantic_single_cluster_id),
    margin: Number(row?.semantic_single_margin || 0),
    confidence: clean(row?.semantic_single_confidence),
    score: Number(row?.semantic_single_score || 0),
    override: clean(row?.semantic_single_override)
  }];
}));

const candidateAssignments = new Map();
for (const candidate of semanticData.candidates || []) {
  const candidateKey = `${candidate.feature_profile || "unknown"}::k${candidate.k}`;
  for (const cluster of candidate.clusters || []) {
    for (const member of cluster.members || []) {
      const key = norm(member.startup_name || member.startup_id);
      if (!key) continue;
      if (!candidateAssignments.has(key)) candidateAssignments.set(key, []);
      candidateAssignments.get(key).push({
        candidate: candidateKey,
        profile: candidate.feature_profile,
        k: Number(candidate.k),
        theme: clean(cluster.label),
        cluster_id: clean(cluster.cluster_id),
        margin: Number(member.margin || 0),
        confidence: clean(member.confidence || member.semantic_single_confidence),
        score: Number(member.score || member.semantic_single_score || 0)
      });
    }
  }
}

function assignmentStats(row) {
  const key = norm(row.startup_name || row.name || row.startup_id);
  const assignments = candidateAssignments.get(key) || [];
  const labels = assignments.map((item) => item.theme).filter(Boolean);
  const uniqueThemes = new Set(labels);
  const lowMargins = assignments.filter((item) => Number.isFinite(item.margin) && item.margin < 5).length;
  const avgMargin = assignments.length
    ? assignments.reduce((sum, item) => sum + (Number.isFinite(item.margin) ? item.margin : 0), 0) / assignments.length
    : 0;
  const recommended = recommendedById.get(clean(row.startup_id)) || assignments.find((item) =>
    item.profile === semanticData.summary?.recommended_profile &&
    Number(item.k) === Number(semanticData.summary?.recommended_k)
  ) || assignments[0] || {};
  return { assignments, uniqueThemes, lowMargins, avgMargin, recommended };
}

const rows = master
  .filter((row) => clean(row.scope_decision) === "include")
  .map((row) => {
    const taxonomy = taxonomyById.get(clean(row.startup_id)) || {};
    const stats = assignmentStats(row);
    const fit = fitByName.get(norm(row.startup_name)) || {};
    const manualOverride = manualOverrides.get(clean(row.startup_id));
    const wc = wordCount(row.startup_summary_v1);
    const reasons = [];
    let risk = 0;

    if (stats.recommended.confidence === "low") { risk += 35; reasons.push("low_recommended_confidence"); }
    if (stats.recommended.confidence === "medium") { risk += 18; reasons.push("medium_recommended_confidence"); }
    if (Number(stats.recommended.margin || 0) < 4) { risk += 28; reasons.push("very_low_recommended_margin"); }
    else if (Number(stats.recommended.margin || 0) < 8) { risk += 14; reasons.push("low_recommended_margin"); }
    if (stats.uniqueThemes.size >= 6) { risk += 26; reasons.push("unstable_across_k_profiles"); }
    else if (stats.uniqueThemes.size >= 4) { risk += 14; reasons.push("moderately_unstable_across_k_profiles"); }
    if (stats.lowMargins >= 4) { risk += 15; reasons.push("repeated_low_margin_assignments"); }
    if (fit.fit === "review") { risk += 25; reasons.push(`cluster_fit_review:${fit.flags || "unspecified"}`); }
    else if (fit.fit === "watch") { risk += 12; reasons.push(`cluster_fit_watch:${fit.flags || "unspecified"}`); }
    if (Number(row.data_quality_score_10 || 0) < 8) { risk += 14; reasons.push("data_quality_below_8"); }
    if (clean(row.source_type).match(/linkedin|f6s|external|portfolio|listing/i)) { risk += 10; reasons.push("source_needs_upgrade_or_startup_source"); }
    if (wc < 45) { risk += 18; reasons.push("summary_too_short"); }
    else if (wc > 150) { risk += 8; reasons.push("summary_too_long"); }
    if (clean(row.startup_summary_v1).match(/\b(Entra|Queda|produccion|biotecnologica|agricultura|plataforma)\b/i)) { risk += 8; reasons.push("mixed_language_or_editorial_style"); }
    const technicalStack = clean(row.technical_stack) || clean(taxonomy.technical_stack);
    const outputClass = clean(row.output_class) || clean(taxonomy.output_class);
    const industryDestination = clean(row.industry_destination) || clean(taxonomy.industry_destination);
    if (!technicalStack || !outputClass || !industryDestination) { risk += 8; reasons.push("missing_semantic_structured_fields"); }
    if (manualOverride) {
      risk = Math.max(0, risk - 35);
      reasons.push("source_backed_semantic_override_applied");
    }

    return {
      semantic_risk_score: risk,
      startup_id: row.startup_id,
      startup_name: row.startup_name,
      current_recommended_theme: stats.recommended.theme || row.semantic_single_theme || "",
      recommended_confidence: stats.recommended.confidence || "",
      recommended_margin: stats.recommended.margin === undefined ? "" : Math.round(stats.recommended.margin * 10) / 10,
      semantic_override: manualOverride ? "yes" : "no",
      semantic_override_reason: manualOverride ? clean(manualOverride.override_reason) : "",
      unique_themes_across_candidates: stats.uniqueThemes.size,
      low_margin_assignments: stats.lowMargins,
      avg_margin_across_candidates: Math.round(stats.avgMargin * 10) / 10,
      fit_status: fit.fit || "",
      fit_flags: fit.flags || "",
      data_quality_score_10: row.data_quality_score_10,
      quality_band: row.quality_band,
      source_type: row.source_type,
      source_url: row.source_url,
      summary_words: wc,
      risk_reasons: reasons.join("; "),
      recommended_action: risk >= 70
        ? "rewrite source-backed English summary and verify cluster/category"
        : risk >= 45
          ? "enrich semantic fields and inspect k-stability"
          : "watch after next semantic rebuild",
      current_one_liner: row.business_one_liner,
      current_summary: row.startup_summary_v1,
      evidence_excerpt: row.evidence_excerpt
    };
  })
  .sort((a, b) => b.semantic_risk_score - a.semantic_risk_score || a.startup_name.localeCompare(b.startup_name));

const headers = Object.keys(rows[0] || {});
fs.writeFileSync(outPath, [headers.join(","), ...rows.map((row) => headers.map((key) => csv(row[key])).join(","))].join("\n"), "utf8");

const top = rows.slice(0, 20);
const high = rows.filter((row) => row.semantic_risk_score >= 70).length;
const medium = rows.filter((row) => row.semantic_risk_score >= 45 && row.semantic_risk_score < 70).length;
const md = [
  "# Semantic Quality Queue",
  "",
  "Prioriza startups include que mas pueden danar la credibilidad del mapa semantico.",
  "",
  `- startups include evaluadas: ${rows.length}`,
  `- alto riesgo semantico (>=70): ${high}`,
  `- riesgo medio (45-69): ${medium}`,
  `- recommended profile/k: ${semanticData.summary?.recommended_profile || "n/d"} / k=${semanticData.summary?.recommended_k || "n/d"}`,
  "",
  "## Top 20",
  "",
  "| rank | startup | risk | recommended theme | reasons | action |",
  "|---:|---|---:|---|---|---|",
  ...top.map((row, index) => `| ${index + 1} | ${row.startup_name} | ${row.semantic_risk_score} | ${row.current_recommended_theme} | ${row.risk_reasons.replace(/\|/g, "/")} | ${row.recommended_action} |`)
].join("\n");
fs.writeFileSync(summaryPath, md, "utf8");

console.log(`Wrote ${outPath}`);
console.log(`Wrote ${summaryPath}`);
console.log(`High risk: ${high}; medium risk: ${medium}; top offender: ${rows[0]?.startup_name || "n/a"} (${rows[0]?.semantic_risk_score || 0})`);
