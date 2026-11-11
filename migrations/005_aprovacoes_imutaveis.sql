CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    reservation_item_id TEXT NOT NULL REFERENCES reservation_items(id),
    responsible_id TEXT NOT NULL REFERENCES users(id),
    decision_type TEXT NOT NULL,
    decision TEXT NOT NULL,
    justification TEXT NOT NULL CHECK (length(trim(justification)) > 0),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION approvals_immutable_guard()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Approvals are immutable';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS approvals_immutable_guard ON approvals;

CREATE TRIGGER approvals_immutable_guard
BEFORE UPDATE OR DELETE ON approvals
FOR EACH ROW
EXECUTE FUNCTION approvals_immutable_guard();
