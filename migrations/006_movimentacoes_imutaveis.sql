CREATE TABLE IF NOT EXISTS material_movements (
    id TEXT PRIMARY KEY,
    reservation_item_id TEXT NOT NULL REFERENCES reservation_items(id),
    responsible_id TEXT NOT NULL REFERENCES users(id),
    movement_type TEXT NOT NULL CHECK (movement_type IN ('RETIRADA', 'DEVOLUCAO')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    observation TEXT
);

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
