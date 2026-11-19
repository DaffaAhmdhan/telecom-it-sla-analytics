-- ============================================================================
-- Telecom & IT Service SLA Analytics - Star Schema & KPI Queries (SQLite/SQL)
-- ============================================================================

-- 1. Overall Executive KPI Summary
SELECT
    COUNT(*) AS total_tickets,
    SUM(sla_met) AS sla_met_count,
    ROUND(100.0 * SUM(sla_met) / COUNT(*), 2) AS sla_compliance_pct,
    ROUND(AVG(resolution_hours), 2) AS avg_mttr_hours,
    ROUND(100.0 * SUM(is_repeat_incident) / COUNT(*), 2) AS repeat_incident_pct
FROM fact_tickets;

-- 2. SLA Compliance & MTTR by Priority Tier
SELECT
    priority,
    COUNT(*) AS ticket_count,
    ROUND(AVG(sla_target_hours), 1) AS sla_target_hrs,
    ROUND(AVG(resolution_hours), 2) AS avg_mttr_hrs,
    ROUND(100.0 * SUM(sla_met) / COUNT(*), 2) AS sla_compliance_pct,
    SUM(CASE WHEN sla_met = 0 THEN 1 ELSE 0 END) AS sla_breaches
FROM fact_tickets
GROUP BY priority
ORDER BY priority;

-- 3. Monthly Ticket Volume, MTTR, and MoM SLA Delta (Window Function: LAG)
WITH monthly_stats AS (
    SELECT
        strftime('%Y-%m', created_at) AS month,
        COUNT(*) AS total_tickets,
        ROUND(AVG(resolution_hours), 2) AS avg_mttr_hours,
        ROUND(100.0 * SUM(sla_met) / COUNT(*), 2) AS sla_pct
    FROM fact_tickets
    GROUP BY strftime('%Y-%m', created_at)
)
SELECT
    month,
    total_tickets,
    avg_mttr_hours,
    sla_pct,
    ROUND(sla_pct - LAG(sla_pct) OVER (ORDER BY month), 2) AS mom_sla_change_pct
FROM monthly_stats
ORDER BY month;

-- 4. Pareto (80/20) Analysis of SLA Breaches by Root Cause
WITH breach_counts AS (
    SELECT
        root_cause,
        COUNT(*) AS breach_count
    FROM fact_tickets
    WHERE sla_met = 0
    GROUP BY root_cause
),
total_breaches AS (
    SELECT SUM(breach_count) AS total FROM breach_counts
)
SELECT
    b.root_cause,
    b.breach_count,
    ROUND(100.0 * b.breach_count / t.total, 2) AS pct_of_breaches,
    ROUND(100.0 * SUM(b.breach_count) OVER (ORDER BY b.breach_count DESC) / t.total, 2) AS cumulative_pct
FROM breach_counts b
CROSS JOIN total_breaches t
ORDER BY b.breach_count DESC;

-- 5. Regional & Team Performance Bottlenecks
SELECT
    region,
    assigned_team,
    COUNT(*) AS tickets,
    ROUND(AVG(resolution_hours), 2) AS avg_mttr_hours,
    ROUND(100.0 * SUM(sla_met) / COUNT(*), 2) AS sla_compliance_pct
FROM fact_tickets
GROUP BY region, assigned_team
HAVING COUNT(*) >= 50
ORDER BY sla_compliance_pct ASC;
