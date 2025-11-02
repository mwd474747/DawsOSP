-- Migration: Add Derived Macro Indicators Calculation
-- Purpose: Calculate derived indicators from base FRED indicators
-- Created: 2025-11-02
-- Description: Adds function to compute derived indicators like gdp_gap, real_interest_rate, money_velocity etc.

-- ============================================================================
-- 1. DERIVED INDICATORS FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION compute_derived_indicators(
    p_date DATE DEFAULT NULL
) RETURNS VOID AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
    v_record_count INT;
BEGIN
    -- If no date specified, compute for all available dates
    IF p_date IS NULL THEN
        -- Get date range from existing indicators
        SELECT MIN(date), MAX(date)
        INTO v_start_date, v_end_date
        FROM macro_indicators
        WHERE source = 'FRED';
        
        IF v_start_date IS NULL OR v_end_date IS NULL THEN
            RAISE NOTICE 'No FRED data found to compute derived indicators';
            RETURN;
        END IF;
    ELSE
        v_start_date := p_date;
        v_end_date := p_date;
    END IF;

    RAISE NOTICE 'Computing derived indicators from % to %', v_start_date, v_end_date;

    -- ============================================================================
    -- Real Interest Rate = Nominal Rate - Inflation Rate
    -- ============================================================================
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    SELECT 
        'REAL_INTEREST_RATE',
        'Real Interest Rate (Nominal - Inflation)',
        ir.date,
        ir.value - inf.value,
        'Percent',
        'Daily',
        'calculated',
        NOW()
    FROM macro_indicators ir
    JOIN macro_indicators inf ON ir.date = inf.date
    WHERE ir.indicator_id IN ('DFF', 'FEDFUNDS')  -- Federal Funds Rate
        AND inf.indicator_id = 'CPIAUCSL'  -- Consumer Price Index (as YoY change)
        AND ir.date BETWEEN v_start_date AND v_end_date
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % real interest rate records', v_record_count;

    -- ============================================================================
    -- Term Spread (already exists as T10Y2Y, but we can also compute it)
    -- Long-term rate (10Y) - Short-term rate (2Y)
    -- ============================================================================
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    SELECT 
        'TERM_SPREAD_CALC',
        'Calculated Term Spread (10Y-2Y Treasury)',
        t10.date,
        t10.value - t2.value,
        'Percent',
        'Daily',
        'calculated',
        NOW()
    FROM macro_indicators t10
    JOIN macro_indicators t2 ON t10.date = t2.date
    WHERE t10.indicator_id = 'DGS10'  -- 10-Year Treasury
        AND t2.indicator_id = 'DGS2'   -- 2-Year Treasury
        AND t10.date BETWEEN v_start_date AND v_end_date
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % term spread records', v_record_count;

    -- ============================================================================
    -- GDP Gap = (Actual GDP - Potential GDP) / Potential GDP
    -- Note: Requires GDPPOT (Potential GDP) series to be fetched from FRED
    -- ============================================================================
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    SELECT 
        'GDP_GAP',
        'GDP Gap (Actual vs Potential)',
        gdp.date,
        CASE 
            WHEN pot.value > 0 THEN (gdp.value - pot.value) / pot.value
            ELSE NULL
        END,
        'Percent',
        'Quarterly',
        'calculated',
        NOW()
    FROM macro_indicators gdp
    JOIN macro_indicators pot ON gdp.date = pot.date
    WHERE gdp.indicator_id = 'GDP'  -- Actual GDP
        AND pot.indicator_id = 'GDPPOT'  -- Potential GDP
        AND gdp.date BETWEEN v_start_date AND v_end_date
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % GDP gap records', v_record_count;

    -- ============================================================================
    -- Output Gap (Similar to GDP gap, using real GDP)
    -- Using GDPC1 (Real GDP) and GDPPOT if available
    -- ============================================================================
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    SELECT 
        'OUTPUT_GAP',
        'Output Gap (Real GDP vs Potential)',
        gdp.date,
        CASE 
            WHEN pot.value > 0 THEN (gdp.value - pot.value) / pot.value
            ELSE NULL
        END,
        'Percent',
        'Quarterly',
        'calculated',
        NOW()
    FROM macro_indicators gdp
    JOIN macro_indicators pot ON gdp.date = pot.date
    WHERE gdp.indicator_id = 'GDPC1'  -- Real GDP
        AND pot.indicator_id = 'GDPPOT'  -- Potential GDP
        AND gdp.date BETWEEN v_start_date AND v_end_date
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % output gap records', v_record_count;

    -- ============================================================================
    -- Employment Gap = Unemployment Rate - Natural Rate of Unemployment
    -- ============================================================================
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    SELECT 
        'EMPLOYMENT_GAP',
        'Employment Gap (Unemployment - Natural Rate)',
        un.date,
        un.value - nru.value,
        'Percent',
        'Monthly',
        'calculated',
        NOW()
    FROM macro_indicators un
    JOIN macro_indicators nru ON un.date = nru.date
    WHERE un.indicator_id = 'UNRATE'  -- Unemployment Rate
        AND nru.indicator_id IN ('NROU', 'NROUST')  -- Natural Rate of Unemployment
        AND un.date BETWEEN v_start_date AND v_end_date
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % employment gap records', v_record_count;

    -- ============================================================================
    -- Money Velocity = GDP / M2 Money Supply
    -- ============================================================================
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    SELECT 
        'MONEY_VELOCITY',
        'Money Velocity (GDP/M2)',
        gdp.date,
        CASE 
            WHEN m2.value > 0 THEN gdp.value / m2.value
            ELSE NULL
        END,
        'Ratio',
        'Quarterly',
        'calculated',
        NOW()
    FROM macro_indicators gdp
    JOIN macro_indicators m2 ON gdp.date = m2.date
    WHERE gdp.indicator_id = 'GDP'  -- Nominal GDP
        AND m2.indicator_id = 'M2SL'  -- M2 Money Supply
        AND gdp.date BETWEEN v_start_date AND v_end_date
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % money velocity records', v_record_count;

    -- ============================================================================
    -- Fiscal Impulse = Change in Fiscal Deficit (Year-over-Year)
    -- ============================================================================
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    SELECT 
        'FISCAL_IMPULSE',
        'Fiscal Impulse (YoY Change in Deficit)',
        curr.date,
        curr.value - prev.value,
        'Percent of GDP',
        'Annual',
        'calculated',
        NOW()
    FROM macro_indicators curr
    LEFT JOIN macro_indicators prev 
        ON prev.indicator_id = curr.indicator_id
        AND prev.date = (curr.date - INTERVAL '1 year')::date
    WHERE curr.indicator_id IN ('FYFSGDA188S', 'FYFSD')  -- Federal Deficit
        AND curr.date BETWEEN v_start_date AND v_end_date
        AND prev.value IS NOT NULL
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % fiscal impulse records', v_record_count;

    -- ============================================================================
    -- Credit Impulse = Change in Credit Growth (as % of GDP)
    -- ============================================================================
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    WITH credit_growth AS (
        SELECT 
            date,
            value,
            LAG(value) OVER (ORDER BY date) as prev_value
        FROM macro_indicators
        WHERE indicator_id = 'TOTBKCR'
    ),
    gdp_values AS (
        SELECT 
            date,
            value as gdp_value
        FROM macro_indicators
        WHERE indicator_id = 'GDP'
    )
    SELECT 
        'CREDIT_IMPULSE',
        'Credit Impulse (Change in Credit Growth/GDP)',
        cg.date,
        CASE 
            WHEN gv.gdp_value > 0 AND cg.prev_value IS NOT NULL 
            THEN ((cg.value - cg.prev_value) / cg.prev_value) / gv.gdp_value
            ELSE NULL
        END,
        'Percent of GDP',
        'Quarterly',
        'calculated',
        NOW()
    FROM credit_growth cg
    JOIN gdp_values gv ON DATE_TRUNC('quarter', cg.date) = DATE_TRUNC('quarter', gv.date)
    WHERE cg.date BETWEEN v_start_date AND v_end_date
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % credit impulse records', v_record_count;

    -- ============================================================================
    -- Additional useful derived indicators
    -- ============================================================================

    -- Real GDP Growth (if we have GDP deflator)
    INSERT INTO macro_indicators (
        indicator_id, 
        indicator_name, 
        date, 
        value, 
        units, 
        frequency, 
        source,
        last_updated
    )
    WITH gdp_changes AS (
        SELECT 
            date,
            value,
            LAG(value, 4) OVER (ORDER BY date) as year_ago_value
        FROM macro_indicators
        WHERE indicator_id IN ('GDPC1', 'GDP')
    )
    SELECT 
        'REAL_GDP_GROWTH',
        'Real GDP Growth (YoY)',
        date,
        CASE 
            WHEN year_ago_value > 0 
            THEN ((value - year_ago_value) / year_ago_value) * 100
            ELSE NULL
        END,
        'Percent',
        'Quarterly',
        'calculated',
        NOW()
    FROM gdp_changes
    WHERE date BETWEEN v_start_date AND v_end_date
        AND year_ago_value IS NOT NULL
    ON CONFLICT (indicator_id, date) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        last_updated = NOW();

    GET DIAGNOSTICS v_record_count = ROW_COUNT;
    RAISE NOTICE 'Computed % real GDP growth records', v_record_count;

    -- Summary
    SELECT COUNT(DISTINCT indicator_id) INTO v_record_count
    FROM macro_indicators
    WHERE source = 'calculated'
        AND date BETWEEN v_start_date AND v_end_date;

    RAISE NOTICE 'Successfully computed derived indicators. Total distinct calculated indicators: %', v_record_count;

EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Error computing derived indicators: %', SQLERRM;
        RAISE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION compute_derived_indicators IS 'Calculates derived macro indicators from base FRED data';

-- ============================================================================
-- 2. HELPER FUNCTION TO LIST AVAILABLE DERIVED INDICATORS
-- ============================================================================

CREATE OR REPLACE FUNCTION list_derived_indicators()
RETURNS TABLE (
    indicator_id TEXT,
    indicator_name TEXT,
    formula TEXT,
    required_inputs TEXT[],
    frequency TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'REAL_INTEREST_RATE'::TEXT,
        'Real Interest Rate'::TEXT,
        'Federal Funds Rate - CPI YoY Change'::TEXT,
        ARRAY['DFF or FEDFUNDS', 'CPIAUCSL']::TEXT[],
        'Daily'::TEXT
    UNION ALL
    SELECT 
        'TERM_SPREAD_CALC'::TEXT,
        'Term Spread (Calculated)'::TEXT,
        '10Y Treasury - 2Y Treasury'::TEXT,
        ARRAY['DGS10', 'DGS2']::TEXT[],
        'Daily'::TEXT
    UNION ALL
    SELECT 
        'GDP_GAP'::TEXT,
        'GDP Gap'::TEXT,
        '(Actual GDP - Potential GDP) / Potential GDP'::TEXT,
        ARRAY['GDP', 'GDPPOT']::TEXT[],
        'Quarterly'::TEXT
    UNION ALL
    SELECT 
        'OUTPUT_GAP'::TEXT,
        'Output Gap'::TEXT,
        '(Real GDP - Potential GDP) / Potential GDP'::TEXT,
        ARRAY['GDPC1', 'GDPPOT']::TEXT[],
        'Quarterly'::TEXT
    UNION ALL
    SELECT 
        'EMPLOYMENT_GAP'::TEXT,
        'Employment Gap'::TEXT,
        'Unemployment Rate - Natural Rate'::TEXT,
        ARRAY['UNRATE', 'NROU or NROUST']::TEXT[],
        'Monthly'::TEXT
    UNION ALL
    SELECT 
        'MONEY_VELOCITY'::TEXT,
        'Money Velocity'::TEXT,
        'GDP / M2 Money Supply'::TEXT,
        ARRAY['GDP', 'M2SL']::TEXT[],
        'Quarterly'::TEXT
    UNION ALL
    SELECT 
        'FISCAL_IMPULSE'::TEXT,
        'Fiscal Impulse'::TEXT,
        'YoY Change in Fiscal Deficit'::TEXT,
        ARRAY['FYFSGDA188S or FYFSD']::TEXT[],
        'Annual'::TEXT
    UNION ALL
    SELECT 
        'CREDIT_IMPULSE'::TEXT,
        'Credit Impulse'::TEXT,
        'Change in Credit Growth / GDP'::TEXT,
        ARRAY['TOTBKCR', 'GDP']::TEXT[],
        'Quarterly'::TEXT
    UNION ALL
    SELECT 
        'REAL_GDP_GROWTH'::TEXT,
        'Real GDP Growth'::TEXT,
        'YoY % Change in Real GDP'::TEXT,
        ARRAY['GDPC1 or GDP']::TEXT[],
        'Quarterly'::TEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION list_derived_indicators IS 'Lists all available derived indicators and their formulas';

-- ============================================================================
-- 3. VIEW FOR EASIER QUERYING OF DERIVED INDICATORS
-- ============================================================================

CREATE OR REPLACE VIEW v_derived_indicators AS
SELECT 
    mi.date,
    mi.indicator_id,
    mi.indicator_name,
    mi.value,
    mi.units,
    mi.frequency,
    mi.last_updated
FROM macro_indicators mi
WHERE mi.source = 'calculated'
ORDER BY mi.date DESC, mi.indicator_id;

COMMENT ON VIEW v_derived_indicators IS 'View of all calculated/derived macro indicators';

-- ============================================================================
-- 4. FUNCTION TO CHECK DATA AVAILABILITY FOR DERIVED INDICATORS
-- ============================================================================

CREATE OR REPLACE FUNCTION check_derived_indicators_availability(
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    derived_indicator TEXT,
    can_calculate BOOLEAN,
    missing_inputs TEXT[],
    available_inputs TEXT[]
) AS $$
BEGIN
    -- Check Real Interest Rate
    RETURN QUERY
    WITH inputs AS (
        SELECT 
            array_agg(DISTINCT indicator_id) as available
        FROM macro_indicators
        WHERE indicator_id IN ('DFF', 'FEDFUNDS', 'CPIAUCSL')
            AND date = p_date
    )
    SELECT 
        'REAL_INTEREST_RATE'::TEXT,
        ('CPIAUCSL' = ANY(inputs.available) AND ('DFF' = ANY(inputs.available) OR 'FEDFUNDS' = ANY(inputs.available))),
        CASE 
            WHEN NOT ('CPIAUCSL' = ANY(inputs.available) AND ('DFF' = ANY(inputs.available) OR 'FEDFUNDS' = ANY(inputs.available)))
            THEN array_remove(array_remove(ARRAY['DFF/FEDFUNDS', 'CPIAUCSL'], 
                CASE WHEN 'CPIAUCSL' = ANY(inputs.available) THEN 'CPIAUCSL' ELSE NULL END),
                CASE WHEN 'DFF' = ANY(inputs.available) OR 'FEDFUNDS' = ANY(inputs.available) THEN 'DFF/FEDFUNDS' ELSE NULL END)
            ELSE ARRAY[]::TEXT[]
        END,
        inputs.available
    FROM inputs;

    -- Check Term Spread
    RETURN QUERY
    WITH inputs AS (
        SELECT 
            array_agg(DISTINCT indicator_id) as available
        FROM macro_indicators
        WHERE indicator_id IN ('DGS10', 'DGS2')
            AND date = p_date
    )
    SELECT 
        'TERM_SPREAD_CALC'::TEXT,
        ('DGS10' = ANY(inputs.available) AND 'DGS2' = ANY(inputs.available)),
        CASE 
            WHEN NOT ('DGS10' = ANY(inputs.available) AND 'DGS2' = ANY(inputs.available))
            THEN array_remove(array_remove(ARRAY['DGS10', 'DGS2'], 
                CASE WHEN 'DGS10' = ANY(inputs.available) THEN 'DGS10' ELSE NULL END),
                CASE WHEN 'DGS2' = ANY(inputs.available) THEN 'DGS2' ELSE NULL END)
            ELSE ARRAY[]::TEXT[]
        END,
        inputs.available
    FROM inputs;

    -- Add similar checks for other indicators...
    
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_derived_indicators_availability IS 'Checks which derived indicators can be calculated based on available data';

-- ============================================================================
-- 5. GRANT PERMISSIONS
-- ============================================================================

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION compute_derived_indicators(DATE) TO PUBLIC;
GRANT EXECUTE ON FUNCTION list_derived_indicators() TO PUBLIC;
GRANT EXECUTE ON FUNCTION check_derived_indicators_availability(DATE) TO PUBLIC;

-- Grant select on view
GRANT SELECT ON v_derived_indicators TO PUBLIC;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- List all derived indicators
SELECT * FROM list_derived_indicators();

-- Check if we can calculate any derived indicators with current data
SELECT * FROM check_derived_indicators_availability(CURRENT_DATE);

-- Test computing derived indicators for today (won't insert if no data)
SELECT compute_derived_indicators(CURRENT_DATE);

-- Show any calculated indicators
SELECT 
    indicator_id,
    COUNT(*) as record_count,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
FROM v_derived_indicators
GROUP BY indicator_id
ORDER BY indicator_id;

-- Success message
SELECT 'Derived indicators migration completed successfully' AS status;