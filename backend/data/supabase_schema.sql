-- =========================================================================
-- upay Ops Intelligence — Supabase PostgreSQL Schema Migration
-- Project: https://mfpbiwqesrlcljkumgxc.supabase.co
-- =========================================================================

-- 1. Transactions Table
CREATE TABLE IF NOT EXISTS public.transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    merchant_id VARCHAR(50),
    amount NUMERIC(12, 2) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL DEFAULT 'MERCHANT_PAYMENT',
    transaction_status VARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
    failure_code VARCHAR(50) NOT NULL DEFAULT 'NONE',
    ground_truth_root_cause VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_tx_customer ON public.transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_tx_merchant ON public.transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_tx_created ON public.transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_tx_status ON public.transactions(transaction_status);

-- 2. Transaction Events (Chronological Telemetry Stream)
CREATE TABLE IF NOT EXISTS public.transaction_events (
    event_id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) NOT NULL REFERENCES public.transactions(transaction_id) ON DELETE CASCADE,
    event_type VARCHAR(80) NOT NULL,
    event_status VARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_event_tx ON public.transaction_events(transaction_id);
CREATE INDEX IF NOT EXISTS idx_event_timestamp ON public.transaction_events(timestamp);

-- 3. Customer Complaints Table
CREATE TABLE IF NOT EXISTS public.complaints (
    complaint_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(50) REFERENCES public.transactions(transaction_id) ON DELETE SET NULL,
    complaint_text TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'TRANSACTION_DISPUTE',
    status VARCHAR(50) NOT NULL DEFAULT 'NEW',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_complaint_customer ON public.complaints(customer_id);
CREATE INDEX IF NOT EXISTS idx_complaint_status ON public.complaints(status);

-- 4. Dispatched Operational Cases
CREATE TABLE IF NOT EXISTS public.cases (
    case_id VARCHAR(50) PRIMARY KEY,
    complaint_id VARCHAR(50) UNIQUE REFERENCES public.complaints(complaint_id) ON DELETE SET NULL,
    transaction_id VARCHAR(50),
    root_cause VARCHAR(100) NOT NULL,
    confidence NUMERIC(5, 4) DEFAULT 0.0 NOT NULL,
    priority VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
    assigned_team VARCHAR(80) NOT NULL,
    recommendation TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'OPEN' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cases_tx ON public.cases(transaction_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON public.cases(status);

-- 5. Human-in-the-Loop Resolution History (Feedback & Retraining Loop)
CREATE TABLE IF NOT EXISTS public.resolution_history (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL REFERENCES public.cases(case_id) ON DELETE CASCADE,
    predicted_root_cause VARCHAR(100) NOT NULL,
    actual_root_cause VARCHAR(100) NOT NULL,
    predicted_team VARCHAR(80) NOT NULL,
    actual_team VARCHAR(80) NOT NULL,
    operator_action VARCHAR(50) DEFAULT 'ACCEPTED' NOT NULL,
    resolved_by VARCHAR(100) DEFAULT 'Ops_Officer' NOT NULL,
    resolution_notes TEXT,
    is_feedback_approved BOOLEAN DEFAULT TRUE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_resolution_case ON public.resolution_history(case_id);

-- 6. Historical Resolved Cases (RAG Knowledge Base)
CREATE TABLE IF NOT EXISTS public.historical_cases (
    id BIGSERIAL PRIMARY KEY,
    case_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    scenario VARCHAR(100) NOT NULL,
    symptoms TEXT NOT NULL,
    root_cause VARCHAR(100) NOT NULL,
    resolution TEXT NOT NULL,
    assigned_team VARCHAR(80) NOT NULL,
    embedding_json TEXT
);

-- Enable Row Level Security (RLS) optionally:
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read/write policy for hackathon demo:
CREATE POLICY "Public Read Access" ON public.transactions FOR SELECT USING (true);
CREATE POLICY "Public Read Access" ON public.complaints FOR SELECT USING (true);
CREATE POLICY "Public Read Access" ON public.cases FOR ALL USING (true);
