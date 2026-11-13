-- nomi.sqlite schema. See docs/system-design.md section 7.1.
-- Tables marked "populated later" are scaffolded here so #56/#58 never need a schema migration.

CREATE TABLE meta (
    dataset_version TEXT NOT NULL,
    model_version TEXT,
    rubric_version TEXT,
    built_at TEXT NOT NULL
);

CREATE TABLE products (
    ndc11 TEXT PRIMARY KEY,
    set_id TEXT,
    brand TEXT,
    generic TEXT,
    form TEXT,
    category TEXT,
    scope_flag TEXT,
    review_status TEXT
);

CREATE TABLE product_ingredients (
    ndc11 TEXT NOT NULL,
    unii TEXT,
    strength REAL,
    unit TEXT
);

CREATE TABLE ingredients (
    unii TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE product_uses (
    ndc11 TEXT NOT NULL,
    use TEXT NOT NULL
);

-- Populated later (extract stage, no ticket yet)
CREATE TABLE label_warnings (
    ndc11 TEXT NOT NULL,
    warning_code TEXT NOT NULL
);

-- Populated later by #56
CREATE TABLE terms (
    unii TEXT,
    dimension TEXT,
    persona_or_modifier TEXT,
    points REAL,
    citation_id TEXT
);

-- Populated later by #56
CREATE TABLE hard_stops (
    unii_or_ndc11 TEXT,
    persona_or_modifier TEXT,
    reason TEXT,
    citation_id TEXT
);

-- Populated later by #56
CREATE TABLE benchmarks (
    use TEXT,
    persona TEXT,
    breakpoints TEXT
);

-- Populated later by #56
CREATE TABLE alternatives (
    ndc11 TEXT,
    alt_ndc11 TEXT,
    shared_use TEXT,
    tradeoff TEXT
);

-- Populated later by #56
CREATE TABLE citations (
    id TEXT PRIMARY KEY,
    source TEXT,
    title TEXT,
    section TEXT,
    url TEXT
);

-- Populated later by #56
CREATE TABLE templates (
    id TEXT PRIMARY KEY,
    dimension TEXT,
    severity TEXT,
    text TEXT
);

-- Populated later by #58 (FTS5 virtual table over brand, generic, ingredient names)
CREATE VIRTUAL TABLE products_fts USING fts5(ndc11, brand, generic, ingredient_names);

-- Populated later, no ticket yet
CREATE TABLE interactions (
    class_a TEXT,
    class_b TEXT,
    severity TEXT,
    citation_id TEXT
);
