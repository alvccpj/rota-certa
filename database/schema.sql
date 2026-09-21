BEGIN;

CREATE TABLE establishments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    document VARCHAR(20),
    depot_address VARCHAR(255) NOT NULL,
    depot_latitude NUMERIC(9, 6),
    depot_longitude NUMERIC(9, 6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    establishment_id BIGINT NOT NULL REFERENCES establishments(id),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(180) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'ATTENDANT', 'COURIER')),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE couriers (
    id BIGSERIAL PRIMARY KEY,
    establishment_id BIGINT NOT NULL REFERENCES establishments(id),
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(id),
    load_capacity_kg NUMERIC(8, 2) NOT NULL CHECK (load_capacity_kg > 0),
    availability VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (availability IN ('AVAILABLE', 'BUSY', 'OFFLINE')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customers (
    id BIGSERIAL PRIMARY KEY,
    establishment_id BIGINT NOT NULL REFERENCES establishments(id),
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(25),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    establishment_id BIGINT NOT NULL REFERENCES establishments(id),
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    assigned_courier_id BIGINT REFERENCES couriers(id),
    delivery_address VARCHAR(255) NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    weight_kg NUMERIC(8, 2) NOT NULL DEFAULT 1 CHECK (weight_kg > 0),
    priority SMALLINT NOT NULL DEFAULT 2 CHECK (priority BETWEEN 1 AND 3),
    desired_start TIMESTAMPTZ,
    desired_end TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'ASSIGNED', 'IN_ROUTE', 'DELIVERED', 'CANCELLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (desired_end IS NULL OR desired_start IS NULL OR desired_end >= desired_start)
);

CREATE TABLE routes (
    id BIGSERIAL PRIMARY KEY,
    establishment_id BIGINT NOT NULL REFERENCES establishments(id),
    courier_id BIGINT NOT NULL REFERENCES couriers(id),
    route_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PLANNED'
        CHECK (status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    algorithm VARCHAR(40) NOT NULL,
    execution_mode VARCHAR(20) NOT NULL
        CHECK (execution_mode IN ('SEQUENTIAL', 'PARALLEL')),
    total_distance_km NUMERIC(10, 3),
    estimated_duration_min INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE route_stops (
    id BIGSERIAL PRIMARY KEY,
    route_id BIGINT NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    order_id BIGINT NOT NULL UNIQUE REFERENCES orders(id),
    stop_sequence INTEGER NOT NULL CHECK (stop_sequence > 0),
    estimated_arrival TIMESTAMPTZ,
    distance_from_previous_km NUMERIC(10, 3),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'ARRIVED', 'COMPLETED', 'FAILED')),
    UNIQUE (route_id, stop_sequence)
);

CREATE TABLE optimization_runs (
    id BIGSERIAL PRIMARY KEY,
    establishment_id BIGINT NOT NULL REFERENCES establishments(id),
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    algorithm VARCHAR(40) NOT NULL,
    execution_mode VARCHAR(20) NOT NULL
        CHECK (execution_mode IN ('SEQUENTIAL', 'PARALLEL')),
    worker_count INTEGER NOT NULL DEFAULT 1 CHECK (worker_count > 0),
    order_count INTEGER NOT NULL CHECK (order_count >= 0),
    courier_count INTEGER NOT NULL CHECK (courier_count >= 0),
    execution_time_ms NUMERIC(12, 3) NOT NULL CHECK (execution_time_ms >= 0),
    total_distance_km NUMERIC(12, 3) NOT NULL CHECK (total_distance_km >= 0)
);

CREATE INDEX idx_users_establishment ON users(establishment_id);
CREATE INDEX idx_orders_establishment_status ON orders(establishment_id, status);
CREATE INDEX idx_orders_courier ON orders(assigned_courier_id);
CREATE INDEX idx_routes_courier_date ON routes(courier_id, route_date);
CREATE INDEX idx_optimization_runs_mode ON optimization_runs(establishment_id, execution_mode);

COMMIT;
