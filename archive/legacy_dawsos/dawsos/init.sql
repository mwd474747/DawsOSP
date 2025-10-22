-- DawsOS PostgreSQL Schema
-- Optional: For production deployments with PostgreSQL

-- Create schema
CREATE SCHEMA IF NOT EXISTS dawsos;

-- Knowledge Graph Nodes table
CREATE TABLE IF NOT EXISTS dawsos.nodes (
    id VARCHAR(255) PRIMARY KEY,
    node_type VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Graph Edges table
CREATE TABLE IF NOT EXISTS dawsos.edges (
    id SERIAL PRIMARY KEY,
    from_node VARCHAR(255) NOT NULL,
    to_node VARCHAR(255) NOT NULL,
    edge_type VARCHAR(100) NOT NULL,
    strength FLOAT DEFAULT 0.5,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_node) REFERENCES dawsos.nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (to_node) REFERENCES dawsos.nodes(id) ON DELETE CASCADE,
    UNIQUE(from_node, to_node, edge_type)
);

-- Patterns table
CREATE TABLE IF NOT EXISTS dawsos.patterns (
    id VARCHAR(255) PRIMARY KEY,
    pattern_type VARCHAR(100) NOT NULL,
    description TEXT,
    trigger_conditions JSONB,
    confidence FLOAT DEFAULT 0.5,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP
);

-- Workflow History table
CREATE TABLE IF NOT EXISTS dawsos.workflow_history (
    id SERIAL PRIMARY KEY,
    workflow_name VARCHAR(255) NOT NULL,
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    steps JSONB NOT NULL,
    result JSONB,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT true
);

-- API Cache table
CREATE TABLE IF NOT EXISTS dawsos.api_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    api_name VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- User Sessions table
CREATE TABLE IF NOT EXISTS dawsos.sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_data JSONB,
    chat_history JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market Data table (for historical tracking)
CREATE TABLE IF NOT EXISTS dawsos.market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(10,2),
    volume BIGINT,
    market_cap BIGINT,
    pe_ratio DECIMAL(6,2),
    data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_timestamp (symbol, timestamp DESC)
);

-- Economic Indicators table
CREATE TABLE IF NOT EXISTS dawsos.economic_indicators (
    id SERIAL PRIMARY KEY,
    indicator_code VARCHAR(50) NOT NULL,
    value DECIMAL(15,4),
    date DATE NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(indicator_code, date)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nodes_type ON dawsos.nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_nodes_created ON dawsos.nodes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_edges_from ON dawsos.edges(from_node);
CREATE INDEX IF NOT EXISTS idx_edges_to ON dawsos.edges(to_node);
CREATE INDEX IF NOT EXISTS idx_workflow_name ON dawsos.workflow_history(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_time ON dawsos.workflow_history(execution_time DESC);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON dawsos.api_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_activity ON dawsos.sessions(last_activity DESC);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_nodes_updated_at BEFORE UPDATE ON dawsos.nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean expired cache
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM dawsos.api_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create function to get node connections
CREATE OR REPLACE FUNCTION get_node_connections(node_id VARCHAR)
RETURNS TABLE(
    connected_node VARCHAR,
    connection_type VARCHAR,
    direction VARCHAR,
    strength FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT to_node, edge_type, 'outgoing'::VARCHAR, strength
    FROM dawsos.edges
    WHERE from_node = node_id
    UNION ALL
    SELECT from_node, edge_type, 'incoming'::VARCHAR, strength
    FROM dawsos.edges
    WHERE to_node = node_id;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA dawsos TO dawsos;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dawsos TO dawsos;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA dawsos TO dawsos;

-- Initial data
INSERT INTO dawsos.nodes (id, node_type, data) VALUES
    ('SYSTEM', 'system', '{"version": "1.0.0", "initialized": true}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'DawsOS database initialized successfully!';
END $$;