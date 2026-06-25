"""Batch 5 — últimas 3 startups nuevas de la cola."""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
date = "2026-06-25"
src = "swarm_inline_sonnet_v1"

batch5 = [
  ("viobact-cl",              "bio_lens_tags","biocentric,biobased",                                0.92),
  ("viobact-cl",              "domain_tags",  "agri-food",                                          0.92),
  ("viobact-cl",              "technology_tags","bioinputs",                                        0.92),
  ("viobact-cl",              "scale_tags",   "agroecosystem-scale",                                0.92),
  ("welii-ar",                "bio_lens_tags","human-health-bio",                                   0.85),
  ("welii-ar",                "domain_tags",  "diagnostics-medtech",                                0.85),
  ("welii-ar",                "technology_tags","ai-data,diagnostics",                              0.85),
  ("welii-ar",                "scale_tags",   "human-scale",                                        0.85),
  ("xeptiva-therapeutics-uy", "bio_lens_tags","biocentric,human-health-bio",                        0.90),
  ("xeptiva-therapeutics-uy", "domain_tags",  "therapeutics-regenerative",                          0.90),
  ("xeptiva-therapeutics-uy", "technology_tags","therapeutics",                                    0.90),
  ("xeptiva-therapeutics-uy", "scale_tags",   "molecular-scale,human-scale",                       0.90),
]

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for eid, field, val, conf in batch5:
        w.writerow([eid, "startup_extended", field, val, src, conf, f"swarm_inline_tags {date}"])

total = sum(1 for _ in open(out, encoding="utf-8")) - 1
print(f"Batch 5: {len(batch5)} filas. Total entity_enrichments: {total}")
