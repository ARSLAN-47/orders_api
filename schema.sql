-- -----------------------------------------------------
-- Orders table
-- -----------------------------------------------------
CREATE TABLE orders_app_order (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    version INT NOT NULL DEFAULT 1,
    total_cents INT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for tenant_id + created_at + id
CREATE INDEX orders_tenant_created_id_idx 
    ON orders_app_order (tenant_id, created_at DESC, id DESC);

-- -----------------------------------------------------
-- Outbox table
-- -----------------------------------------------------
CREATE TABLE orders_app_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(255) NOT NULL,
    order_id UUID NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for tenant_id + created_at
CREATE INDEX outbox_tenant_created_idx
    ON orders_app_outbox (tenant_id, created_at);

-- -----------------------------------------------------
-- IdempotencyKey table
-- -----------------------------------------------------
CREATE TABLE orders_app_idempotencykey (
    tenant_id VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    request_body BYTEA,
    response_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, key)
);

-- Index for tenant_id + key (redundant with PK but for faster lookups)
CREATE INDEX idempotency_tenant_key_idx
    ON orders_app_idempotencykey (tenant_id, key);
