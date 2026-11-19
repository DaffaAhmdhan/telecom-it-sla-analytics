# Telecom & IT Service SLA Analytics

End-to-end operational data analytics project analyzing **5,000 IT & Telecom incident tickets** across 5 regions, 4 priority tiers, and 12 months (Nov 2025 – Oct 2026) using **SQL (SQLite / Star Schema)**, **Python**, and an interactive **Chart.js Executive Dashboard**.

## Business Questions
1. What is the overall SLA compliance rate and Mean Time to Resolve (MTTR) across priority tiers?
2. Which root causes drive the majority of SLA breaches (Pareto 80/20 analysis)?
3. Where do regional and team bottlenecks occur?

## Key Findings (Verified from `output/kpi_summary.json`)
- **Overall SLA Compliance:** **79.3%** (3,965 of 5,000 tickets resolved within SLA), with an average MTTR of **16.41 hours** and a **12.66%** repeat-incident rate.
- **Pareto Root Cause Concentration:** Just 5 root causes account for **80.87%** of all SLA breaches, led by **Fiber Cut / ISP Upstream (23.0%)** and **Power / UPS Fluctuation (18.36%)**.
- **Regional Bottleneck:** **Sukabumi** recorded the lowest SLA compliance at **74.17%** (MTTR **18.49 hrs**), compared to **Depok (81.68%)** and **Jakarta Selatan (80.73%)**, driven by field dispatch travel times.
- **Priority Tier Gap:** **P2 - High** had the lowest SLA compliance (**77.13%**, 292 breaches) despite P1 Critical achieving **83.87%** (avg 2.60 hrs).

## Actionable Recommendations
1. **Redundant ISP Failover & UPS Monitoring:** Deploy automated failover links and UPS battery telemetry in high-breach sites to address 41.35% of SLA breaches.
2. **Pre-staged Spare Kits in Sukabumi:** Station local field-tech spares in Sukabumi to cut dispatch travel latency and lift regional SLA above 80%.
3. **Automated P2 Escalation Alerts:** Add a 6-hour warning trigger (75% of 8h SLA) in the ticketing bot for P2 High incidents.

## Project Structure
```text
telecom-it-sla-analytics/
├── data/
│   ├── generate_data.py        # Reproducible 5,000-ticket dataset generator
│   └── tickets.csv             # Generated incident dataset
├── sql/
│   └── schema_and_kpis.sql     # Star schema & window-function KPI queries
├── src/
│   └── run_analysis.py         # SQLite ETL + automated KPI JSON export
├── output/
│   └── kpi_summary.json        # Verified query outputs
├── dashboard.html              # Interactive Chart.js SLA dashboard
└── README.md
```

## How to Run
```bash
python data/generate_data.py
python src/run_analysis.py
```
Open `dashboard.html` in any browser to explore the interactive charts.
