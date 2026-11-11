CREATE TABLE IF NOT EXISTS reservations (
    id TEXT PRIMARY KEY,
    solicitante_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reservation_items (
    id TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL REFERENCES reservations(id),
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    start TIMESTAMPTZ NOT NULL,
    "end" TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_entries (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reservation_items_resource
ON reservation_items (resource_type, resource_id, start, "end");

CREATE INDEX IF NOT EXISTS idx_reservation_items_status
ON reservation_items (status);

ALTER TABLE reservation_items
    ADD COLUMN IF NOT EXISTS quantity INTEGER NOT NULL DEFAULT 1;

CREATE TABLE IF NOT EXISTS resource_blocks (
    id TEXT PRIMARY KEY,
    resource_id TEXT NOT NULL REFERENCES resources(id),
    start TIMESTAMPTZ NOT NULL,
    "end" TIMESTAMPTZ NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ATIVO',
    created_by TEXT REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (start < "end")
);

CREATE INDEX IF NOT EXISTS idx_resource_blocks_resource_period
ON resource_blocks (resource_id, status, start, "end");

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

CREATE TABLE IF NOT EXISTS material_movements (
    id TEXT PRIMARY KEY,
    reservation_item_id TEXT NOT NULL REFERENCES reservation_items(id),
    responsible_id TEXT NOT NULL REFERENCES users(id),
    movement_type TEXT NOT NULL CHECK (movement_type IN ('RETIRADA', 'DEVOLUCAO')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    observation TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    reservation_id TEXT NOT NULL REFERENCES reservations(id),
    event TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ENVIADA',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_created
ON notifications (user_id, created_at);
