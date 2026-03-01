-- Cannabis Social Club - Datenbank Schema
-- DSGVO-konforme Struktur mit getrennten sensiblen Daten

-- Mitglieder (Basisdaten)
CREATE TABLE members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_number INTEGER UNIQUE NOT NULL, -- Mitgliedsnummer (100004, 100005, etc.)
    
    -- Persönliche Daten
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    
    -- Kontakt
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    
    -- Adresse
    street VARCHAR(255),
    zip_code VARCHAR(20),
    city VARCHAR(100),
    
    -- Mitgliedschaft
    join_date DATE NOT NULL, -- Beitrittsdatum
    application_date DATE, -- Aufnahmedatum (Antragsdatum)
    
    -- Abgabelimits (in Gramm)
    monthly_limit INTEGER DEFAULT 50,
    daily_limit INTEGER DEFAULT 25,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, active, suspended, cancelled
    is_verified BOOLEAN DEFAULT FALSE,
    is_accepted BOOLEAN DEFAULT FALSE,
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending, paid, failed
    
    -- Guthaben/Kontostand
    balance DECIMAL(10,2) DEFAULT 0.00,
    
    -- Consent/DSGVO
    privacy_consent BOOLEAN DEFAULT FALSE,
    privacy_consent_date TIMESTAMP,
    sepa_consent BOOLEAN DEFAULT FALSE, -- Lastschrift-Einwilligung
    age_verified BOOLEAN DEFAULT FALSE,
    residence_verified BOOLEAN DEFAULT FALSE,
    no_other_club BOOLEAN DEFAULT FALSE, -- Keine Mitgliedschaft in anderem CSC
    
    -- Newsletter
    newsletter_important BOOLEAN DEFAULT TRUE, -- Wichtige Ankündigungen
    newsletter_optional BOOLEAN DEFAULT FALSE, -- Optionaler Newsletter
    
    -- Meta
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Sicherheit: Datenverschlüsselung empfohlen für sensible Felder
    data_encryption_key_id VARCHAR(100)
);

-- Bankdaten (getrennte Tabelle für erhöhte Sicherheit)
-- Diese Tabelle sollte zusätzlich verschlüsselt werden
CREATE TABLE member_bank_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    
    iban VARCHAR(34) NOT NULL,
    bic VARCHAR(11),
    bank_name VARCHAR(255),
    account_holder VARCHAR(255), -- Kann vom Mitgliedsnamen abweichen
    
    -- SEPA-Mandat
    sepa_mandate_reference VARCHAR(100),
    sepa_mandate_date DATE,
    sepa_mandate_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

-- Produkte/Sorten
CREATE TABLE strains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'flower' (Blüte) oder 'clone' (Steckling)
    price_per_gram DECIMAL(5,2) NOT NULL,
    availability_status INTEGER DEFAULT 0, -- 0 = nicht verfügbar, >0 = verfügbar
    description TEXT,
    thc_content DECIMAL(4,2), -- Optional: THC-Gehalt
    cbd_content DECIMAL(4,2), -- Optional: CBD-Gehalt
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bestellungen
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    
    -- Bestell-Metadaten
    order_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, ready, completed, cancelled
    distribution_month VARCHAR(7), -- Format: YYYY-MM (Ausgabe-Monat)
    
    -- Finanzen
    total_amount DECIMAL(10,2), -- Gesamtwert
    total_weight INTEGER, -- Gesamtgewicht in Gramm
    payment_amount DECIMAL(10,2), -- Bezahlter Betrag
    payment_method VARCHAR(20), -- cash, transfer, direct_debit
    
    -- Status-Tracking
    accepted_at TIMESTAMP,
    verified_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Notizen
    notes TEXT,
    
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

-- Bestellpositionen (einzelne Sorten)
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    strain_id INTEGER NOT NULL,
    quantity_grams INTEGER NOT NULL, -- Menge in Gramm
    price_per_gram DECIMAL(5,2) NOT NULL, -- Preis zum Zeitpunkt der Bestellung
    total_price DECIMAL(10,2) NOT NULL,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (strain_id) REFERENCES strains(id)
);

-- Abgabe-Log (für Compliance/Nachweis)
CREATE TABLE distribution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    order_id INTEGER,
    
    distribution_date DATE NOT NULL,
    strain_name VARCHAR(100),
    quantity_grams INTEGER NOT NULL,
    
    -- Wer hat ausgegeben?
    distributed_by VARCHAR(100),
    
    -- Verbleibendes Limit nach dieser Abgabe
    remaining_monthly_limit INTEGER,
    remaining_daily_limit INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Inventar/Stock-Verwaltung
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strain_id INTEGER NOT NULL,
    batch_id VARCHAR(50), -- Chargen-Nummer für Rückverfolgbarkeit
    quantity_grams INTEGER NOT NULL,
    harvest_date DATE,
    expiry_date DATE,
    quality_grade VARCHAR(20), -- z.B. A, B, C oder medizinisch/standard
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (strain_id) REFERENCES strains(id)
);

-- Audit-Log (für DSGVO und Sicherheit)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values TEXT, -- JSON
    new_values TEXT, -- JSON
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45)
);

-- Indizes für Performance
CREATE INDEX idx_members_email ON members(email);
CREATE INDEX idx_members_number ON members(member_number);
CREATE INDEX idx_members_status ON members(status);
CREATE INDEX idx_orders_member ON orders(member_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_month ON orders(distribution_month);
CREATE INDEX idx_distribution_member ON distribution_log(member_id);
CREATE INDEX idx_distribution_date ON distribution_log(distribution_date);

-- Trigger für updated_at
CREATE TRIGGER update_members_timestamp 
AFTER UPDATE ON members
BEGIN
    UPDATE members SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_bank_details_timestamp 
AFTER UPDATE ON member_bank_details
BEGIN
    UPDATE member_bank_details SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;