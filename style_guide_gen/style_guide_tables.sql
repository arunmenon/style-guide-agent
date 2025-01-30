-- style_guide_tables.sql

-- Table for baseline style guidelines
-- baseline_style_guidelines table
CREATE TABLE IF NOT EXISTS baseline_style_guidelines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    product_type TEXT,          -- can be "ALL", or a specific product, or NULL
    guidelines_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- Table for legal guidelines
CREATE TABLE IF NOT EXISTS legal_guidelines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    legal_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing final style guides, if you want to persist them
CREATE TABLE IF NOT EXISTS published_style_guides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    product_type TEXT NOT NULL,
    style_guide_md TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

--sqlite3 style_guide.db < style_guide_tables.sql

INSERT INTO baseline_style_guidelines (category, product_type, guidelines_text)
VALUES 
  ("Fashion", NULL, "Generic fashion guidelines for brand ordering, color mention, etc."),
  ("Fashion", "Women's Dress", "Additional best practices for dresses, e.g. mention length, fit, etc.");

INSERT INTO legal_guidelines (domain, legal_text)
VALUES
  ("ALL", "No competitor brand references. No extreme claims. Must not violate trademark usage..."),
  ("Fashion", "If referencing brand logos, disclaim usage. Must not mention competitor brand in the title, disclaimers for brand usage...");
