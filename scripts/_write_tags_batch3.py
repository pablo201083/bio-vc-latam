"""Batch 3 de tags inline — 18 startups nuevas (excluye overlaps ya procesados en batches 1-2)."""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ROOT / "staging" / "entity_enrichments.csv"
date = "2026-06-25"
src = "swarm_inline_sonnet_v1"

batch3 = [
  ("energytop-via-proinpa-bo","bio_lens_tags","biocentric,biobased",                               0.90),
  ("energytop-via-proinpa-bo","domain_tags",  "agri-food",                                         0.90),
  ("energytop-via-proinpa-bo","technology_tags","bioinputs",                                       0.90),
  ("energytop-via-proinpa-bo","scale_tags",   "agroecosystem-scale",                               0.90),
  ("fermentlab-br",  "bio_lens_tags","biobased,bio-enabled-industrial-transition",                  0.88),
  ("fermentlab-br",  "domain_tags",  "biomanufacturing",                                            0.88),
  ("fermentlab-br",  "technology_tags","fermentation,biomanufacturing",                            0.88),
  ("fermentlab-br",  "scale_tags",   "industrial-scale",                                            0.88),
  ("fermentlabs-co", "bio_lens_tags","biobased,circular,bio-enabled-industrial-transition",         0.88),
  ("fermentlabs-co", "domain_tags",  "industrial-biotech,biomanufacturing",                        0.88),
  ("fermentlabs-co", "technology_tags","precision-fermentation",                                   0.88),
  ("fermentlabs-co", "scale_tags",   "industrial-scale",                                            0.88),
  ("fungicontrol-co","bio_lens_tags","biocentric,biobased",                                         0.90),
  ("fungicontrol-co","domain_tags",  "agri-food",                                                   0.90),
  ("fungicontrol-co","technology_tags","bioinputs",                                                 0.90),
  ("fungicontrol-co","scale_tags",   "agroecosystem-scale",                                         0.90),
  ("geanext-cr",     "bio_lens_tags","biocentric",                                                  0.72),
  ("geanext-cr",     "domain_tags",  "agri-food",                                                   0.72),
  ("geanext-cr",     "technology_tags","ai-data",                                                   0.72),
  ("geanext-cr",     "scale_tags",   "agroecosystem-scale",                                         0.72),
  ("green-xpo-lab-cr","bio_lens_tags","biocentric,planetary-boundary",                              0.85),
  ("green-xpo-lab-cr","domain_tags", "biodiversity-nature,climate-resource",                        0.85),
  ("green-xpo-lab-cr","technology_tags","remote-sensing,ai-data",                                   0.85),
  ("green-xpo-lab-cr","scale_tags",  "territorial-scale,agroecosystem-scale",                       0.85),
  ("grupo-bios-co",  "bio_lens_tags","biobased",                                                    0.72),
  ("grupo-bios-co",  "domain_tags",  "biomanufacturing",                                            0.72),
  ("grupo-bios-co",  "technology_tags","biomanufacturing",                                          0.72),
  ("grupo-bios-co",  "scale_tags",   "industrial-scale",                                            0.72),
  ("healthpoint-bo", "bio_lens_tags","human-health-bio",                                            0.70),
  ("healthpoint-bo", "domain_tags",  "diagnostics-medtech",                                         0.70),
  ("healthpoint-bo", "technology_tags","diagnostics",                                               0.70),
  ("healthpoint-bo", "scale_tags",   "human-scale",                                                 0.70),
  ("hem-healthtech-co","bio_lens_tags","human-health-bio",                                          0.92),
  ("hem-healthtech-co","domain_tags",  "diagnostics-medtech",                                        0.92),
  ("hem-healthtech-co","technology_tags","diagnostics",                                              0.92),
  ("hem-healthtech-co","scale_tags",   "human-scale,product-scale",                                  0.92),
  ("inkus-biotech-cl","bio_lens_tags","biocentric,biobased",                                        0.90),
  ("inkus-biotech-cl","domain_tags",  "agri-food",                                                   0.90),
  ("inkus-biotech-cl","technology_tags","ai-data,synthetic-biology",                                 0.90),
  ("inkus-biotech-cl","scale_tags",   "agroecosystem-scale,molecular-scale",                         0.90),
  ("innovatech-bo",  "bio_lens_tags","biocentric",                                                   0.75),
  ("innovatech-bo",  "domain_tags",  "agri-food",                                                    0.75),
  ("innovatech-bo",  "technology_tags","ai-data",                                                    0.75),
  ("innovatech-bo",  "scale_tags",   "agroecosystem-scale,territorial-scale",                        0.75),
  ("labtronics-sas-co","bio_lens_tags","human-health-bio",                                           0.90),
  ("labtronics-sas-co","domain_tags",  "diagnostics-medtech",                                        0.90),
  ("labtronics-sas-co","technology_tags","diagnostics",                                              0.90),
  ("labtronics-sas-co","scale_tags",   "human-scale,molecular-scale",                                0.90),
  ("lifepack-co",    "bio_lens_tags","biobased,circular",                                            0.90),
  ("lifepack-co",    "domain_tags",  "biomaterials",                                                  0.90),
  ("lifepack-co",    "technology_tags","biomaterials",                                                0.90),
  ("lifepack-co",    "scale_tags",   "product-scale",                                                 0.90),
  ("lilliput-technologies-cr","bio_lens_tags","biocentric,biobased",                                 0.88),
  ("lilliput-technologies-cr","domain_tags",  "agri-food",                                            0.88),
  ("lilliput-technologies-cr","technology_tags","biomaterials,bioinputs",                             0.88),
  ("lilliput-technologies-cr","scale_tags",   "agroecosystem-scale",                                  0.88),
  ("lilliput-technologies-ltd-cr","bio_lens_tags","biocentric,biobased",                              0.88),
  ("lilliput-technologies-ltd-cr","domain_tags",  "agri-food",                                        0.88),
  ("lilliput-technologies-ltd-cr","technology_tags","biomaterials,bioinputs",                         0.88),
  ("lilliput-technologies-ltd-cr","scale_tags",   "agroecosystem-scale",                              0.88),
  ("magenta-biolabs-cr","bio_lens_tags","biobased",                                                   0.88),
  ("magenta-biolabs-cr","domain_tags",  "biomanufacturing",                                            0.88),
  ("magenta-biolabs-cr","technology_tags","fermentation,enzymes",                                      0.88),
  ("magenta-biolabs-cr","scale_tags",   "molecular-scale,industrial-scale",                            0.88),
  ("magic-green-cr", "bio_lens_tags","biocentric",                                                    0.70),
  ("magic-green-cr", "domain_tags",  "agri-food",                                                     0.70),
  ("magic-green-cr", "technology_tags","ai-data",                                                     0.70),
  ("magic-green-cr", "scale_tags",   "agroecosystem-scale",                                           0.70),
  ("medimarket-online-ve","bio_lens_tags","human-health-bio",                                         0.68),
  ("medimarket-online-ve","domain_tags",  "diagnostics-medtech",                                       0.68),
  ("medimarket-online-ve","technology_tags","ai-data",                                                 0.68),
  ("medimarket-online-ve","scale_tags",   "human-scale",                                               0.68),
]

with open(out, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for eid, field, val, conf in batch3:
        w.writerow([eid, "startup_extended", field, val, src, conf, f"swarm_inline_tags {date}"])

total = sum(1 for _ in open(out, encoding="utf-8")) - 1
print(f"Batch 3: {len(batch3)} filas. Total entity_enrichments: {total}")
