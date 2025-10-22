-- Migration 5: Knowledge Graph
-- Purpose: Add tables for knowledge graph (nodes, edges, analysis snapshots)
-- Date: 2025-10-21
-- Phase: Sprint 3 (Intelligence)
-- Priority: P1 (Required for pattern memory and analysis provenance)

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS kg_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN (
    'macro_var', 'regime', 'factor', 'sector', 'company', 'instrument',
    'pattern', 'series_id', 'event', 'analysis_snapshot'
  )),
  data_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE kg_nodes IS 'Knowledge graph nodes for macro variables, companies, patterns, and analysis snapshots';
COMMENT ON COLUMN kg_nodes.type IS 'Node type: macro_var, regime, factor, sector, company, instrument, pattern, series_id, event, analysis_snapshot';
COMMENT ON COLUMN kg_nodes.data_json IS 'Node data (varies by type): {name, code, description, ...}';

-- Index for fast type-based queries
CREATE INDEX IF NOT EXISTS idx_kg_nodes_type ON kg_nodes (type);

-- GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_kg_nodes_data ON kg_nodes USING GIN (data_json);

CREATE TABLE IF NOT EXISTS kg_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
  target_id UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
  relation TEXT NOT NULL CHECK (relation IN (
    'influences', 'sensitive_to', 'belongs_to', 'hedged_by',
    'derived_from', 'computed_by', 'correlates_with'
  )),
  weight NUMERIC(8,4),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source_id, target_id, relation)
);

COMMENT ON TABLE kg_edges IS 'Knowledge graph edges representing relationships between nodes';
COMMENT ON COLUMN kg_edges.relation IS 'Relationship type: influences, sensitive_to, belongs_to, hedged_by, derived_from, computed_by, correlates_with';
COMMENT ON COLUMN kg_edges.weight IS 'Optional edge weight (e.g., correlation coefficient, beta)';
COMMENT ON COLUMN kg_edges.metadata_json IS 'Edge metadata (e.g., time period, confidence, source)';

-- Indexes for fast graph traversal
CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON kg_edges (source_id, relation);
CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges (target_id, relation);
CREATE INDEX IF NOT EXISTS idx_kg_edges_relation ON kg_edges (relation);

-- GIN index for metadata queries
CREATE INDEX IF NOT EXISTS idx_kg_edges_metadata ON kg_edges USING GIN (metadata_json);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Get neighbors of a node
CREATE OR REPLACE FUNCTION kg_neighbors(node_id UUID, relation_filter TEXT DEFAULT NULL)
RETURNS TABLE (
  neighbor_id UUID,
  neighbor_type TEXT,
  neighbor_data JSONB,
  edge_relation TEXT,
  edge_weight NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT n.id, n.type, n.data_json, e.relation, e.weight
  FROM kg_edges e
  JOIN kg_nodes n ON e.target_id = n.id
  WHERE e.source_id = node_id
    AND (relation_filter IS NULL OR e.relation = relation_filter);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION kg_neighbors IS 'Get all neighbors of a node (optionally filtered by relation)';

-- Function: Get reverse neighbors (incoming edges)
CREATE OR REPLACE FUNCTION kg_reverse_neighbors(node_id UUID, relation_filter TEXT DEFAULT NULL)
RETURNS TABLE (
  neighbor_id UUID,
  neighbor_type TEXT,
  neighbor_data JSONB,
  edge_relation TEXT,
  edge_weight NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT n.id, n.type, n.data_json, e.relation, e.weight
  FROM kg_edges e
  JOIN kg_nodes n ON e.source_id = n.id
  WHERE e.target_id = node_id
    AND (relation_filter IS NULL OR e.relation = relation_filter);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION kg_reverse_neighbors IS 'Get all reverse neighbors of a node (optionally filtered by relation)';

-- ============================================================================
-- SEED DATA (Example nodes and edges)
-- ============================================================================

-- Macro variables
INSERT INTO kg_nodes (type, data_json) VALUES
  ('macro_var', '{"code": "T10Y2Y", "name": "10Y-2Y Treasury Spread", "description": "Yield curve slope indicator"}'),
  ('macro_var', '{"code": "CPIAUCSL", "name": "CPI All Urban Consumers", "description": "Inflation measure"}'),
  ('macro_var', '{"code": "UNRATE", "name": "Unemployment Rate", "description": "Labor market indicator"}'),
  ('macro_var', '{"code": "BAA10Y", "name": "BAA-10Y Spread", "description": "Credit spread indicator"}')
ON CONFLICT DO NOTHING;

-- Regimes
INSERT INTO kg_nodes (type, data_json) VALUES
  ('regime', '{"label": "expansion", "description": "Economic expansion phase"}'),
  ('regime', '{"label": "slowdown", "description": "Economic slowdown phase"}'),
  ('regime', '{"label": "recession", "description": "Economic recession phase"}'),
  ('regime', '{"label": "recovery", "description": "Economic recovery phase"}')
ON CONFLICT DO NOTHING;

-- Factors
INSERT INTO kg_nodes (type, data_json) VALUES
  ('factor', '{"name": "real_rate", "description": "Real interest rate factor"}'),
  ('factor', '{"name": "inflation", "description": "Inflation factor"}'),
  ('factor', '{"name": "credit", "description": "Credit spread factor"}'),
  ('factor', '{"name": "usd", "description": "USD strength factor"}')
ON CONFLICT DO NOTHING;

-- Example edges: macro_var influences regime
INSERT INTO kg_edges (source_id, target_id, relation, weight)
SELECT
  (SELECT id FROM kg_nodes WHERE type = 'macro_var' AND data_json->>'code' = 'T10Y2Y'),
  (SELECT id FROM kg_nodes WHERE type = 'regime' AND data_json->>'label' = 'recession'),
  'influences',
  -0.7  -- Inverted curve strongly signals recession
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE type = 'macro_var' AND data_json->>'code' = 'T10Y2Y')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE type = 'regime' AND data_json->>'label' = 'recession')
ON CONFLICT DO NOTHING;

INSERT INTO kg_edges (source_id, target_id, relation, weight)
SELECT
  (SELECT id FROM kg_nodes WHERE type = 'macro_var' AND data_json->>'code' = 'UNRATE'),
  (SELECT id FROM kg_nodes WHERE type = 'regime' AND data_json->>'label' = 'recession'),
  'influences',
  0.6  -- Rising unemployment signals recession
WHERE EXISTS (SELECT 1 FROM kg_nodes WHERE type = 'macro_var' AND data_json->>'code' = 'UNRATE')
  AND EXISTS (SELECT 1 FROM kg_nodes WHERE type = 'regime' AND data_json->>'label' = 'recession')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- ROLLBACK
-- ============================================================================

-- To rollback:
-- DROP FUNCTION IF EXISTS kg_neighbors(UUID, TEXT);
-- DROP FUNCTION IF EXISTS kg_reverse_neighbors(UUID, TEXT);
-- DROP INDEX IF EXISTS idx_kg_edges_source;
-- DROP INDEX IF EXISTS idx_kg_edges_target;
-- DROP INDEX IF EXISTS idx_kg_edges_relation;
-- DROP INDEX IF EXISTS idx_kg_edges_metadata;
-- DROP INDEX IF EXISTS idx_kg_nodes_type;
-- DROP INDEX IF EXISTS idx_kg_nodes_data;
-- DROP TABLE IF EXISTS kg_edges;
-- DROP TABLE IF EXISTS kg_nodes;
