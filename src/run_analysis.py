import csv
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "tickets.csv")
DB_PATH = os.path.join(BASE_DIR, "output", "sla_analytics.db")
JSON_PATH = os.path.join(BASE_DIR, "output", "kpi_summary.json")


def load_csv_to_sqlite(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS fact_tickets;")
    cur.execute("""
        CREATE TABLE fact_tickets (
            ticket_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            resolved_at TEXT NOT NULL,
            region TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            assigned_team TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            sla_target_hours REAL NOT NULL,
            resolution_hours REAL NOT NULL,
            sla_met INTEGER NOT NULL,
            is_repeat_incident INTEGER NOT NULL
        );
    """)
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                r["ticket_id"], r["created_at"], r["resolved_at"], r["region"],
                r["category"], r["priority"], r["assigned_team"], r["root_cause"],
                float(r["sla_target_hours"]), float(r["resolution_hours"]),
                int(r["sla_met"]), int(r["is_repeat_incident"])
            )
            for r in reader
        ]
    cur.executemany(
        "INSERT INTO fact_tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        rows
    )
    conn.commit()
    return len(rows)


def query_dicts(conn, sql):
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    return [dict(row) for row in cur.fetchall()]


def main():
    os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    loaded = load_csv_to_sqlite(conn)

    executive = query_dicts(conn, """
        SELECT
            COUNT(*) AS total_tickets,
            SUM(sla_met) AS sla_met_count,
            ROUND(100.0 * SUM(sla_met) / COUNT(*), 2) AS sla_compliance_pct,
            ROUND(AVG(resolution_hours), 2) AS avg_mttr_hours,
            ROUND(100.0 * SUM(is_repeat_incident) / COUNT(*), 2) AS repeat_incident_pct
        FROM fact_tickets;
    """)[0]

    by_priority = query_dicts(conn, """
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
    """)

    monthly = query_dicts(conn, """
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
    """)

    pareto_breaches = query_dicts(conn, """
        WITH breach_counts AS (
            SELECT root_cause, COUNT(*) AS breach_count
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
    """)

    by_region = query_dicts(conn, """
        SELECT
            region,
            COUNT(*) AS tickets,
            ROUND(AVG(resolution_hours), 2) AS avg_mttr_hours,
            ROUND(100.0 * SUM(sla_met) / COUNT(*), 2) AS sla_compliance_pct
        FROM fact_tickets
        GROUP BY region
        ORDER BY sla_compliance_pct ASC;
    """)

    summary = {
        "records_loaded": loaded,
        "executive": executive,
        "by_priority": by_priority,
        "monthly": monthly,
        "pareto_breaches": pareto_breaches,
        "by_region": by_region,
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    conn.close()
    print(json.dumps(summary["executive"], indent=2))


if __name__ == "__main__":
    main()
