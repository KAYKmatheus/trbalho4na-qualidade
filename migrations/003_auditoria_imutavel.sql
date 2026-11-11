ALTER TABLE audit_entries
    ADD COLUMN IF NOT EXISTS actor_id TEXT;

ALTER TABLE audit_entries
    ADD COLUMN IF NOT EXISTS before_value TEXT;

ALTER TABLE audit_entries
    ADD COLUMN IF NOT EXISTS after_value TEXT;

CREATE OR REPLACE FUNCTION audit_entries_immutable_guard()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Audit entries are immutable';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_entries_immutable_guard ON audit_entries;

CREATE TRIGGER audit_entries_immutable_guard
BEFORE UPDATE OR DELETE ON audit_entries
FOR EACH ROW
EXECUTE FUNCTION audit_entries_immutable_guard();

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

CREATE OR REPLACE FUNCTION material_movements_immutable_guard()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Material movements are immutable';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS material_movements_immutable_guard ON material_movements;

CREATE TRIGGER material_movements_immutable_guard
BEFORE UPDATE OR DELETE ON material_movements
FOR EACH ROW
EXECUTE FUNCTION material_movements_immutable_guard();
