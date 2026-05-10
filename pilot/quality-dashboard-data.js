window.QUALITY_DASHBOARD_DATA = {
    "summary":  {
                    "generated_at":  "2026-05-09T13:11:08",
                    "startup_total":  384,
                    "include":  283,
                    "review":  0,
                    "exclude":  101,
                    "high_quality":  175,
                    "medium_quality":  209,
                    "fragile_quality":  0,
                    "poor_quality":  0,
                    "avg_quality_score":  8.23,
                    "source_url_coverage_pct":  87.8,
                    "include_source_url_coverage_pct":  100,
                    "validation_errors":  0,
                    "validation_warnings":  1,
                    "include_reviewed":  283,
                    "include_seeded":  0,
                    "include_high_quality":  130,
                    "include_medium_quality":  153,
                    "include_fragile_quality":  0,
                    "semantic_high_confidence":  226,
                    "semantic_medium_confidence":  36,
                    "semantic_low_confidence":  11,
                    "exclude_reviewed":  51,
                    "include_reviewed_pct":  100,
                    "include_high_quality_pct":  45.9,
                    "semantic_high_confidence_pct":  79.9,
                    "exclude_reviewed_pct":  50.5,
                    "overall_readiness_pct":  75.3
                },
    "readiness_dimensions":  [
                                 {
                                     "dimension":  "Fuente externa",
                                     "ready":  283,
                                     "total":  283,
                                     "pct":  100,
                                     "note":  "Include con source_url"
                                 },
                                 {
                                     "dimension":  "Pais/base",
                                     "ready":  283,
                                     "total":  283,
                                     "pct":  100,
                                     "note":  "Include con structured_country"
                                 },
                                 {
                                     "dimension":  "Perfil revisado",
                                     "ready":  283,
                                     "total":  283,
                                     "pct":  100,
                                     "note":  "Include con review_status reviewed"
                                 },
                                 {
                                     "dimension":  "Scope confirmado",
                                     "ready":  283,
                                     "total":  283,
                                     "pct":  100,
                                     "note":  "Include confirmed"
                                 },
                                 {
                                     "dimension":  "Capital mapeado",
                                     "ready":  230,
                                     "total":  283,
                                     "pct":  81.3,
                                     "note":  "Include en carteras publicables"
                                 },
                                 {
                                     "dimension":  "Theme asignado",
                                     "ready":  283,
                                     "total":  283,
                                     "pct":  100,
                                     "note":  "Include con categoria semantica"
                                 }
                             ],
    "source_trust":  [
                         {
                             "trust_tier":  "1",
                             "source_count":  255,
                             "include_count":  248
                         },
                         {
                             "trust_tier":  "2",
                             "source_count":  24,
                             "include_count":  16
                         },
                         {
                             "trust_tier":  "3",
                             "source_count":  16,
                             "include_count":  14
                         },
                         {
                             "trust_tier":  "4",
                             "source_count":  9,
                             "include_count":  5
                         }
                     ],
    "validation":  [
                       {
                           "check_id":  "canonical_edge_startup_resolution",
                           "severity":  "warning",
                           "status":  "warn",
                           "count":  "65",
                           "message":  "Canonical investment edges with startup ids not present in master should be reviewed or resolved by aliases."
                       },
                       {
                           "check_id":  "canonical_edge_investor_resolution",
                           "severity":  "error",
                           "status":  "pass",
                           "count":  "0",
                           "message":  "Canonical investment edges must point to canonical investor ids."
                       },
                       {
                           "check_id":  "duplicate_investor_names",
                           "severity":  "error",
                           "status":  "pass",
                           "count":  "0",
                           "message":  "Investor names should not duplicate after normalization."
                       },
                       {
                           "check_id":  "duplicate_startup_names",
                           "severity":  "error",
                           "status":  "pass",
                           "count":  "0",
                           "message":  "Startup names should not duplicate after normalization."
                       },
                       {
                           "check_id":  "include_country_coverage",
                           "severity":  "warning",
                           "status":  "pass",
                           "count":  "0",
                           "message":  "Include rows should have structured_country for regional coverage analysis."
                       },
                       {
                           "check_id":  "include_fragile_or_stub",
                           "severity":  "warning",
                           "status":  "pass",
                           "count":  "0",
                           "message":  "Include rows should be moved from fragile/taxonomy_stub to source-backed seeded or reviewed."
                       },
                       {
                           "check_id":  "include_source_url",
                           "severity":  "error",
                           "status":  "pass",
                           "count":  "0",
                           "message":  "Include rows must have an auditable source_url."
                       },
                       {
                           "check_id":  "source_registry_tier1",
                           "severity":  "info",
                           "status":  "pass",
                           "count":  "255",
                           "message":  "Source registry should contain tier 1 official sources."
                       }
                   ],
    "quality_bands":  [
                          {
                              "band":  "high",
                              "count":  175
                          },
                          {
                              "band":  "medium",
                              "count":  209
                          }
                      ],
    "scope_counts":  [
                         {
                             "scope":  "exclude",
                             "count":  101
                         },
                         {
                             "scope":  "include",
                             "count":  283
                         }
                     ],
    "semantic_categories":  [
                                {
                                    "theme":  "agri intelligence and traceable markets",
                                    "count":  39
                                },
                                {
                                    "theme":  "ag biologicals and crop resilience",
                                    "count":  36
                                },
                                {
                                    "theme":  "therapeutics and regenerative bio",
                                    "count":  34
                                },
                                {
                                    "theme":  "clinical diagnostics and medical devices",
                                    "count":  32
                                },
                                {
                                    "theme":  "resource recovery and remediation",
                                    "count":  27
                                },
                                {
                                    "theme":  "food ingredients and biofactories",
                                    "count":  24
                                },
                                {
                                    "theme":  "drug discovery and disease therapeutics",
                                    "count":  24
                                },
                                {
                                    "theme":  "grain traceability and producer infrastructure",
                                    "count":  23
                                },
                                {
                                    "theme":  "biomanufacturing and molecular platforms",
                                    "count":  15
                                },
                                {
                                    "theme":  "biobased materials and waste valorization",
                                    "count":  13
                                },
                                {
                                    "theme":  "bioactive products and regenerative edge cases",
                                    "count":  8
                                },
                                {
                                    "theme":  "biobased chemistry and circular materials",
                                    "count":  8
                                }
                            ],
    "strategic_tag_counts":  {
                                 "bio_lens":  [
                                                  {
                                                      "tag":  "biocentric",
                                                      "count":  173
                                                  },
                                                  {
                                                      "tag":  "planetary-boundary",
                                                      "count":  158
                                                  },
                                                  {
                                                      "tag":  "human-health-bio",
                                                      "count":  125
                                                  },
                                                  {
                                                      "tag":  "regenerative",
                                                      "count":  115
                                                  },
                                                  {
                                                      "tag":  "biobased",
                                                      "count":  98
                                                  },
                                                  {
                                                      "tag":  "bio-enabled-industrial-transition",
                                                      "count":  51
                                                  },
                                                  {
                                                      "tag":  "circular",
                                                      "count":  33
                                                  }
                                              ],
                                 "domain":  [
                                                {
                                                    "tag":  "agri-food",
                                                    "count":  181
                                                },
                                                {
                                                    "tag":  "human-health",
                                                    "count":  125
                                                },
                                                {
                                                    "tag":  "climate-resource",
                                                    "count":  97
                                                },
                                                {
                                                    "tag":  "therapeutics-regenerative",
                                                    "count":  66
                                                },
                                                {
                                                    "tag":  "diagnostics-medtech",
                                                    "count":  54
                                                },
                                                {
                                                    "tag":  "biomanufacturing",
                                                    "count":  44
                                                },
                                                {
                                                    "tag":  "biodiversity-nature",
                                                    "count":  36
                                                },
                                                {
                                                    "tag":  "biomaterials",
                                                    "count":  35
                                                },
                                                {
                                                    "tag":  "industrial-biotech",
                                                    "count":  25
                                                }
                                            ],
                                 "technology":  [
                                                    {
                                                        "tag":  "ai-data",
                                                        "count":  201
                                                    },
                                                    {
                                                        "tag":  "therapeutics",
                                                        "count":  65
                                                    },
                                                    {
                                                        "tag":  "diagnostics",
                                                        "count":  47
                                                    },
                                                    {
                                                        "tag":  "biomaterials",
                                                        "count":  31
                                                    },
                                                    {
                                                        "tag":  "biomanufacturing",
                                                        "count":  30
                                                    },
                                                    {
                                                        "tag":  "bioinputs",
                                                        "count":  26
                                                    },
                                                    {
                                                        "tag":  "fermentation",
                                                        "count":  25
                                                    },
                                                    {
                                                        "tag":  "remote-sensing",
                                                        "count":  23
                                                    },
                                                    {
                                                        "tag":  "synthetic-biology",
                                                        "count":  13
                                                    },
                                                    {
                                                        "tag":  "iot",
                                                        "count":  12
                                                    },
                                                    {
                                                        "tag":  "precision-fermentation",
                                                        "count":  11
                                                    },
                                                    {
                                                        "tag":  "carbon-mrv",
                                                        "count":  9
                                                    },
                                                    {
                                                        "tag":  "enzymes",
                                                        "count":  6
                                                    },
                                                    {
                                                        "tag":  "remediation",
                                                        "count":  5
                                                    }
                                                ],
                                 "scale":  [
                                               {
                                                   "tag":  "industrial-scale",
                                                   "count":  157
                                               },
                                               {
                                                   "tag":  "agroecosystem-scale",
                                                   "count":  144
                                               },
                                               {
                                                   "tag":  "human-scale",
                                                   "count":  127
                                               },
                                               {
                                                   "tag":  "planetary-scale",
                                                   "count":  121
                                               },
                                               {
                                                   "tag":  "molecular-scale",
                                                   "count":  101
                                               },
                                               {
                                                   "tag":  "product-scale",
                                                   "count":  98
                                               },
                                               {
                                                   "tag":  "territorial-scale",
                                                   "count":  65
                                               }
                                           ]
                             },
    "top_flags":  [
                      {
                          "flag":  "needs_current_trl_research",
                          "count":  283
                      },
                      {
                          "flag":  "country_unconfirmed",
                          "count":  30
                      },
                      {
                          "flag":  "thin_graph_context",
                          "count":  23
                      }
                  ],
    "review_queue":  [

                     ],
    "curation_progress":  [
                              {
                                  "dimension":  "Fuente externa include",
                                  "pct":  100,
                                  "ready":  283,
                                  "total":  283,
                                  "note":  "Base para evidencia auditable",
                                  "tone":  "good"
                              },
                              {
                                  "dimension":  "Perfiles reviewed",
                                  "pct":  100,
                                  "ready":  283,
                                  "total":  283,
                                  "note":  "Seeded restante es backlog editorial",
                                  "tone":  "work"
                              },
                              {
                                  "dimension":  "Alta calidad include",
                                  "pct":  45.9,
                                  "ready":  130,
                                  "total":  283,
                                  "note":  "Fuente + summary + estructura defendible",
                                  "tone":  "work"
                              },
                              {
                                  "dimension":  "Alta confianza semantica",
                                  "pct":  79.9,
                                  "ready":  226,
                                  "total":  283,
                                  "note":  "Menos ruido para clustering y mapa",
                                  "tone":  "watch"
                              },
                              {
                                  "dimension":  "Frontera exclude revisada",
                                  "pct":  50.5,
                                  "ready":  51,
                                  "total":  101,
                                  "note":  "Defiende el recorte del universo BIO",
                                  "tone":  "work"
                              }
                          ],
    "curation_queue":  [
                           {
                               "startup_name":  "NotFossil",
                               "current_theme":  "therapeutics and regenerative bio",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "1.2",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "low_semantic_confidence; fund_profile_needs_startup_source_check; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Heartbest",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "0.5",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "low_semantic_confidence; fund_profile_needs_startup_source_check",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Agroforte",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "1.2",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "low_semantic_confidence; fund_profile_needs_startup_source_check",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Inprenha",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "3.3",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "low_semantic_confidence; fund_profile_needs_startup_source_check",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Calice",
                               "current_theme":  "grain traceability and producer infrastructure",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "0.2",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "LogShare",
                               "current_theme":  "ag biologicals and crop resilience",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "1.2",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "SeedMatriz",
                               "current_theme":  "grain traceability and producer infrastructure",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "2.2",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Horus Aeronaves",
                               "current_theme":  "food ingredients and biofactories",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "2.3",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "secondary_public_profile",
                               "curation_reasons":  "low_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Agrojusto",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "3.1",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Splight",
                               "current_theme":  "ag biologicals and crop resilience",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "0.6",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Michroma",
                               "current_theme":  "biomanufacturing and molecular platforms",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "0.9",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "BemAgro",
                               "current_theme":  "resource recovery and remediation",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "2.1",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "MultiplAI Health",
                               "current_theme":  "therapeutics and regenerative bio",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "2.2",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Nat4Bio",
                               "current_theme":  "drug discovery and disease therapeutics",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "2.3",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Asclepii",
                               "current_theme":  "therapeutics and regenerative bio",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "2.5",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Outpost",
                               "current_theme":  "therapeutics and regenerative bio",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "2.7",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Sensix",
                               "current_theme":  "ag biologicals and crop resilience",
                               "semantic_confidence":  "low",
                               "semantic_margin":  "3.2",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "low_semantic_confidence",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Zavia Bio",
                               "current_theme":  "grain traceability and producer infrastructure",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "7.6",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "external_profile",
                               "curation_reasons":  "medium_semantic_confidence; weak_or_secondary_source; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "CellCo",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "8.8",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "linkedin_company_profile",
                               "curation_reasons":  "medium_semantic_confidence; weak_or_secondary_source; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Geoprot",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "7.3",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "medium_semantic_confidence; fund_profile_needs_startup_source_check; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "TBIT",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "8.4",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "medium_semantic_confidence; fund_profile_needs_startup_source_check; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Libera",
                               "current_theme":  "drug discovery and disease therapeutics",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "8.5",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "medium_semantic_confidence; fund_profile_needs_startup_source_check; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Dogma Biotech",
                               "current_theme":  "drug discovery and disease therapeutics",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "8.7",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "medium_semantic_confidence; fund_profile_needs_startup_source_check; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Produzindo Certo",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "10.1",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_listing",
                               "curation_reasons":  "medium_semantic_confidence; fund_profile_needs_startup_source_check; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Algalife",
                               "current_theme":  "food ingredients and biofactories",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "10.8",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_portfolio_profile",
                               "curation_reasons":  "medium_semantic_confidence; fund_profile_needs_startup_source_check",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "InCeres",
                               "current_theme":  "ag biologicals and crop resilience",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "5.4",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "medium_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Tracestory",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "6",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "medium_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Ergo Bioscience",
                               "current_theme":  "drug discovery and disease therapeutics",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "6.4",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "medium_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "AGROTOOLS",
                               "current_theme":  "grain traceability and producer infrastructure",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "7.6",
                               "quality_band":  "medium",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "medium_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           },
                           {
                               "startup_name":  "Sima",
                               "current_theme":  "agri intelligence and traceable markets",
                               "semantic_confidence":  "medium",
                               "semantic_margin":  "7.9",
                               "quality_band":  "high",
                               "review_status":  "reviewed",
                               "source_type":  "official_website",
                               "curation_reasons":  "medium_semantic_confidence; summary_not_normalized_to_english",
                               "suggested_action":  "verify cluster fit and enrich description with technology, biology/materiality, market"
                           }
                       ],
    "curation_workstreams":  [
                                 {
                                     "workstream":  "easy_review_promotions",
                                     "count":  "0",
                                     "purpose":  "Cheap reviewed gains from already complete official-source records.",
                                     "output":  "quality\\easy_review_promotions.csv"
                                 },
                                 {
                                     "workstream":  "official_seeded_enrichment",
                                     "count":  "0",
                                     "purpose":  "Official-source include records that only need template rewrite and structured-field completion.",
                                     "output":  "quality\\official_seeded_enrichment.csv"
                                 },
                                 {
                                     "workstream":  "source_upgrade_batch",
                                     "count":  "0",
                                     "purpose":  "Find direct sources for seeded include records still backed by portfolio/external/candidate evidence.",
                                     "output":  "quality\\source_upgrade_batch.csv"
                                 },
                                 {
                                     "workstream":  "semantic_conflict_batch",
                                     "count":  "56",
                                     "purpose":  "Good or medium records whose semantic placement remains uncertain.",
                                     "output":  "quality\\semantic_conflict_batch.csv"
                                 },
                                 {
                                     "workstream":  "exclude_defense_batch",
                                     "count":  "50",
                                     "purpose":  "Weak excludes to close the boundary of the BIO universe.",
                                     "output":  "quality\\exclude_defense_batch.csv"
                                 }
                             ],
    "best_quality":  [
                         {
                             "startup_name":  "Aloi",
                             "data_quality_score_10":  "9.5",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Blerify",
                             "data_quality_score_10":  "9.5",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Lemon",
                             "data_quality_score_10":  "9.5",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Webee",
                             "data_quality_score_10":  "9.5",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "123Seguro",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "AbAstra",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Agrojusto",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "include",
                             "semantic_single_theme":  "grain traceability and producer infrastructure"
                         },
                         {
                             "startup_name":  "Agrotoken",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "include",
                             "semantic_single_theme":  "grain traceability and producer infrastructure"
                         },
                         {
                             "startup_name":  "Amaro",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Auravant",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "include",
                             "semantic_single_theme":  "agri intelligence and traceable markets"
                         },
                         {
                             "startup_name":  "Barte",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "BioSynaptica",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "include",
                             "semantic_single_theme":  "therapeutics and regenerative bio"
                         },
                         {
                             "startup_name":  "Capim",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Cargo Sapiens",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Cell Farm",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "include",
                             "semantic_single_theme":  "therapeutics and regenerative bio"
                         },
                         {
                             "startup_name":  "Circular",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Clover",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Cobli",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "Conciencia",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         },
                         {
                             "startup_name":  "CRInsurance",
                             "data_quality_score_10":  "9",
                             "scope_decision":  "exclude",
                             "semantic_single_theme":  ""
                         }
                     ]
};
