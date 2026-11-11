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
