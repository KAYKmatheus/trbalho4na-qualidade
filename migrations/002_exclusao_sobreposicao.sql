CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE reservation_items
    DROP CONSTRAINT IF EXISTS reservation_items_no_overlap;

ALTER TABLE reservation_items
    ADD CONSTRAINT reservation_items_no_overlap
    EXCLUDE USING gist (
        resource_type WITH =,
        resource_id WITH =,
        tstzrange(start, "end", '[)') WITH &&
    ) WHERE (status IN ('APROVADA', 'CONFIRMADA', 'EM_USO') AND resource_type <> 'material');
