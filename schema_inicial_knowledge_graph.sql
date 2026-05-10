CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    country_code TEXT,
    city TEXT,
    website TEXT,
    description TEXT,
    status TEXT,
    founded_year INTEGER,
    last_verified_at TEXT
);

CREATE TABLE entity_aliases (
    alias_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    alias_type TEXT,
    UNIQUE(entity_id, alias),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE investors (
    investor_id TEXT PRIMARY KEY,
    investor_type TEXT,
    thesis TEXT,
    preferred_stages TEXT,
    ticket_min_usd REAL,
    ticket_max_usd REAL,
    lead_behavior TEXT,
    FOREIGN KEY (investor_id) REFERENCES entities(entity_id)
);

CREATE TABLE startups (
    startup_id TEXT PRIMARY KEY,
    stage TEXT,
    vertical TEXT,
    subvertical TEXT,
    science_domain TEXT,
    materials_focus TEXT,
    origin_type TEXT,
    origin_org_id TEXT,
    FOREIGN KEY (startup_id) REFERENCES entities(entity_id),
    FOREIGN KEY (origin_org_id) REFERENCES entities(entity_id)
);

CREATE TABLE organizations (
    org_id TEXT PRIMARY KEY,
    org_type TEXT NOT NULL,
    parent_org_id TEXT,
    FOREIGN KEY (org_id) REFERENCES entities(entity_id),
    FOREIGN KEY (parent_org_id) REFERENCES entities(entity_id)
);

CREATE TABLE people (
    person_id TEXT PRIMARY KEY,
    primary_role TEXT,
    profile_url TEXT,
    FOREIGN KEY (person_id) REFERENCES entities(entity_id)
);

CREATE TABLE domains (
    domain_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    domain_type TEXT NOT NULL,
    parent_domain_id TEXT,
    UNIQUE(canonical_name, domain_type),
    FOREIGN KEY (parent_domain_id) REFERENCES domains(domain_id)
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
    FOREIGN KEY (domain_id) REFERENCES domains(domain_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE derived_graph_metrics (
    metric_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    graph_snapshot_id TEXT NOT NULL,
    pagerank REAL,
    indegree INTEGER,
    outdegree INTEGER,
    degree_total INTEGER,
    weighted_degree REAL,
    betweenness REAL,
    modularity_class TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);
