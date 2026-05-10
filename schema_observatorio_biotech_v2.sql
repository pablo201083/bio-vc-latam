CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    short_description TEXT,
    country_code TEXT,
    region_code TEXT,
    city TEXT,
    website TEXT,
    status TEXT,
    founded_year INTEGER,
    last_verified_at TEXT
);

CREATE TABLE entity_aliases (
    alias_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    alias_type TEXT,
    is_preferred INTEGER DEFAULT 0,
    UNIQUE(entity_id, alias),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE startups (
    startup_id TEXT PRIMARY KEY,
    stage TEXT,
    commercial_stage TEXT,
    biotech_vertical TEXT,
    biotech_subvertical TEXT,
    science_domain TEXT,
    technology_platform TEXT,
    materials_focus TEXT,
    trl_level INTEGER,
    validation_status TEXT,
    pilot_status TEXT,
    export_potential TEXT,
    origin_org_id TEXT,
    FOREIGN KEY (startup_id) REFERENCES entities(entity_id),
    FOREIGN KEY (origin_org_id) REFERENCES entities(entity_id)
);

CREATE TABLE investors (
    investor_id TEXT PRIMARY KEY,
    investor_type TEXT,
    thesis TEXT,
    preferred_stages TEXT,
    geography_focus TEXT,
    vertical_focus TEXT,
    ticket_min_usd REAL,
    ticket_max_usd REAL,
    lead_behavior TEXT,
    active_status TEXT,
    FOREIGN KEY (investor_id) REFERENCES entities(entity_id)
);

CREATE TABLE organizations (
    org_id TEXT PRIMARY KEY,
    org_type TEXT NOT NULL,
    parent_org_id TEXT,
    focus_area TEXT,
    FOREIGN KEY (org_id) REFERENCES entities(entity_id),
    FOREIGN KEY (parent_org_id) REFERENCES entities(entity_id)
);

CREATE TABLE corporates (
    corporate_id TEXT PRIMARY KEY,
    industry TEXT,
    demand_profile TEXT,
    innovation_maturity TEXT,
    FOREIGN KEY (corporate_id) REFERENCES entities(entity_id)
);

CREATE TABLE esos (
    eso_id TEXT PRIMARY KEY,
    eso_type TEXT,
    service_profile TEXT,
    geography_focus TEXT,
    FOREIGN KEY (eso_id) REFERENCES entities(entity_id)
);

CREATE TABLE people (
    person_id TEXT PRIMARY KEY,
    primary_role TEXT,
    profile_url TEXT,
    FOREIGN KEY (person_id) REFERENCES entities(entity_id)
);

CREATE TABLE technology_domains (
    domain_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    domain_type TEXT NOT NULL,
    parent_domain_id TEXT,
    UNIQUE(canonical_name, domain_type),
    FOREIGN KEY (parent_domain_id) REFERENCES technology_domains(domain_id)
);

CREATE TABLE market_needs (
    need_id TEXT PRIMARY KEY,
    demander_entity_id TEXT NOT NULL,
    need_title TEXT NOT NULL,
    vertical TEXT,
    subvertical TEXT,
    problem_description TEXT,
    urgency_level TEXT,
    readiness_required TEXT,
    pilot_required INTEGER,
    regulatory_complexity TEXT,
    status TEXT,
    detected_at TEXT,
    last_verified_at TEXT,
    FOREIGN KEY (demander_entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE policy_instruments (
    instrument_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    operator_entity_id TEXT,
    geography_scope TEXT,
    target_stage TEXT,
    target_actor_type TEXT,
    financial_type TEXT,
    notes TEXT,
    FOREIGN KEY (operator_entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE interventions (
    intervention_id TEXT PRIMARY KEY,
    intervention_type TEXT NOT NULL,
    title TEXT NOT NULL,
    lead_entity_id TEXT,
    started_at TEXT,
    ended_at TEXT,
    status TEXT,
    notes TEXT,
    FOREIGN KEY (lead_entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    title TEXT,
    publisher TEXT,
    url TEXT,
    published_at TEXT,
    retrieved_at TEXT,
    excerpt TEXT
);

CREATE TABLE investment_edges (
    investment_id TEXT PRIMARY KEY,
    investor_id TEXT NOT NULL,
    startup_id TEXT NOT NULL,
    round_name TEXT,
    round_stage TEXT,
    announced_date TEXT,
    amount REAL,
    currency TEXT,
    is_lead INTEGER,
    confidence_score REAL,
    source_id TEXT,
    notes TEXT,
    UNIQUE(investor_id, startup_id, round_name, announced_date),
    FOREIGN KEY (investor_id) REFERENCES investors(investor_id),
    FOREIGN KEY (startup_id) REFERENCES startups(startup_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE startup_org_edges (
    relation_id TEXT PRIMARY KEY,
    startup_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    confidence_score REAL,
    source_id TEXT,
    notes TEXT,
    FOREIGN KEY (startup_id) REFERENCES startups(startup_id),
    FOREIGN KEY (org_id) REFERENCES organizations(org_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE founder_edges (
    founder_relation_id TEXT PRIMARY KEY,
    startup_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    start_date TEXT,
    confidence_score REAL,
    source_id TEXT,
    FOREIGN KEY (startup_id) REFERENCES startups(startup_id),
    FOREIGN KEY (person_id) REFERENCES people(person_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE entity_domain_edges (
    relation_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    domain_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    strength_score REAL,
    source_id TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (domain_id) REFERENCES technology_domains(domain_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE need_match_edges (
    match_id TEXT PRIMARY KEY,
    need_id TEXT NOT NULL,
    startup_id TEXT NOT NULL,
    match_status TEXT,
    fit_score REAL,
    evidence TEXT,
    source_id TEXT,
    FOREIGN KEY (need_id) REFERENCES market_needs(need_id),
    FOREIGN KEY (startup_id) REFERENCES startups(startup_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE validation_edges (
    validation_id TEXT PRIMARY KEY,
    startup_id TEXT NOT NULL,
    counterparty_entity_id TEXT NOT NULL,
    validation_type TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    status TEXT,
    confidence_score REAL,
    source_id TEXT,
    notes TEXT,
    FOREIGN KEY (startup_id) REFERENCES startups(startup_id),
    FOREIGN KEY (counterparty_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE support_edges (
    support_id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    support_type TEXT NOT NULL,
    instrument_id TEXT,
    started_at TEXT,
    ended_at TEXT,
    source_id TEXT,
    notes TEXT,
    FOREIGN KEY (source_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (target_entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (instrument_id) REFERENCES policy_instruments(instrument_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE intervention_participants (
    participant_id TEXT PRIMARY KEY,
    intervention_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    role_in_intervention TEXT,
    outcome_status TEXT,
    notes TEXT,
    FOREIGN KEY (intervention_id) REFERENCES interventions(intervention_id),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE ecosystem_metrics_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    snapshot_date TEXT NOT NULL,
    geography_scope TEXT,
    notes TEXT
);

CREATE TABLE derived_graph_metrics (
    metric_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    pagerank REAL,
    indegree INTEGER,
    outdegree INTEGER,
    degree_total INTEGER,
    weighted_degree REAL,
    betweenness REAL,
    modularity_class TEXT,
    bridge_score REAL,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
    FOREIGN KEY (snapshot_id) REFERENCES ecosystem_metrics_snapshots(snapshot_id)
);

CREATE TABLE observatory_kpis (
    kpi_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    kpi_name TEXT NOT NULL,
    geography_scope TEXT,
    actor_scope TEXT,
    value_numeric REAL,
    value_text TEXT,
    notes TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES ecosystem_metrics_snapshots(snapshot_id)
);
