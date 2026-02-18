-- Repair Invoice Processor — Schema
-- Applied to: Neon project groo-lkw, database neondb
-- Schema: repair (isolated from public LKW tables)

CREATE SCHEMA IF NOT EXISTS repair;

-- ── Invoices ─────────────────────────────────────────────
CREATE TABLE repair.invoices (
    id              BIGSERIAL PRIMARY KEY,
    -- Core fields (match Excel output)
    invoice_year    SMALLINT        NOT NULL,
    invoice_month   SMALLINT        NOT NULL,
    invoice_week    SMALLINT        NOT NULL,
    invoice_date    DATE            NOT NULL,
    truck           VARCHAR(20)     NOT NULL,
    total_price     NUMERIC(12,2)   NOT NULL,  -- negative for Gutschrift
    invoice_nr      VARCHAR(100)    NOT NULL,
    seller          VARCHAR(200)    NOT NULL,
    buyer           VARCHAR(200)    NOT NULL,
    kategorie       VARCHAR(50),

    -- Metadata
    pdf_filename    VARCHAR(500),
    ai_confidence   REAL,                       -- 0.0-1.0
    ai_model        VARCHAR(50),                -- gpt-4o-mini / gpt-4o
    prompt_version  VARCHAR(20),
    tokens_used     INTEGER,
    cost_usd        NUMERIC(8,5),
    is_gutschrift   BOOLEAN         DEFAULT FALSE,
    is_review       BOOLEAN         DEFAULT FALSE, -- flagged for human review
    processed_at    TIMESTAMPTZ     DEFAULT now(),

    -- Duplicate prevention
    CONSTRAINT uq_invoice UNIQUE (invoice_nr, seller, invoice_date)
);

-- ── Indexes ──────────────────────────────────────────────
CREATE INDEX idx_inv_date     ON repair.invoices (invoice_date);
CREATE INDEX idx_inv_truck    ON repair.invoices (truck);
CREATE INDEX idx_inv_seller   ON repair.invoices (seller);
CREATE INDEX idx_inv_year_wk  ON repair.invoices (invoice_year, invoice_week);
CREATE INDEX idx_inv_kategorie ON repair.invoices (kategorie);

-- ── Processing log (audit trail) ─────────────────────────
CREATE TABLE repair.processing_log (
    id              BIGSERIAL PRIMARY KEY,
    batch_id        UUID            NOT NULL,   -- groups one button press
    pdf_filename    VARCHAR(500)    NOT NULL,
    status          VARCHAR(20)     NOT NULL,   -- success / review / manual / error
    invoice_id      BIGINT REFERENCES repair.invoices(id),
    error_message   TEXT,
    ai_model        VARCHAR(50),
    tokens_input    INTEGER,
    tokens_output   INTEGER,
    cost_usd        NUMERIC(8,5),
    ai_response     JSONB,                      -- full AI response for audit
    duration_ms     INTEGER,
    created_at      TIMESTAMPTZ     DEFAULT now()
);

CREATE INDEX idx_plog_batch   ON repair.processing_log (batch_id);
CREATE INDEX idx_plog_date    ON repair.processing_log (created_at);
CREATE INDEX idx_plog_status  ON repair.processing_log (status);
