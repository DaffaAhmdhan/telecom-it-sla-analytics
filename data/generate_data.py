import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(OUTPUT_DIR, "tickets.csv")

REGIONS = ["Jakarta Selatan", "Bogor", "Bandung", "Sukabumi", "Depok"]
CATEGORIES = [
    ("Network Outage", 0.28),
    ("SIMRS / Application Error", 0.22),
    ("Hardware / Workstation", 0.18),
    ("Fiber / ISP Link Down", 0.14),
    ("Access & Biometric Auth", 0.10),
    ("Database / Backup Alert", 0.08),
]
PRIORITIES = [
    ("P1 - Critical", 4.0, 0.10),
    ("P2 - High", 8.0, 0.25),
    ("P3 - Medium", 24.0, 0.45),
    ("P4 - Low", 48.0, 0.20),
]
TEAMS = ["NOC / Network Ops", "L1 Helpdesk", "L2 Systems & DB", "Field Technician"]
ROOT_CAUSES = [
    "Fiber Cut / ISP Upstream",
    "Switch / Router Config Drift",
    "Server CPU / Memory Spike",
    "OS / Driver Patch Failure",
    "User Misconfiguration",
    "Power / UPS Fluctuation",
    "Database Lock / Timeout",
]


def weighted_choice(items):
    r = random.random()
    upto = 0.0
    for item in items:
        weight = item[-1]
        upto += weight
        if r <= upto:
            return item
    return items[-1]


def main():
    start_date = datetime(2025, 11, 1, 0, 0, 0)
    end_date = datetime(2026, 10, 31, 23, 59, 0)
    total_seconds = int((end_date - start_date).total_seconds())

    rows = []
    for i in range(1, 5001):
        ticket_id = f"TCK-{i:05d}"
        created_at = start_date + timedelta(seconds=random.randint(0, total_seconds))
        # Business hours bias
        if random.random() < 0.72:
            created_at = created_at.replace(hour=random.randint(8, 17))

        region = random.choice(REGIONS)
        category = weighted_choice(CATEGORIES)[0]
        priority, sla_hours, _ = weighted_choice(PRIORITIES)

        if category in ("Network Outage", "Fiber / ISP Link Down"):
            team = random.choice(["NOC / Network Ops", "Field Technician"])
        elif category in ("SIMRS / Application Error", "Database / Backup Alert"):
            team = "L2 Systems & DB"
        else:
            team = random.choice(["L1 Helpdesk", "Field Technician"])

        # Resolution time modeled around SLA with realistic tail & team/region variance
        base_factor = random.lognormvariate(-0.55, 0.65)
        if priority == "P1 - Critical":
            base_factor *= 0.85
        if region == "Sukabumi" and team == "Field Technician":
            base_factor *= 1.35  # Rural travel latency

        resolution_hours = round(max(0.25, sla_hours * base_factor), 2)
        resolved_at = created_at + timedelta(hours=resolution_hours)
        sla_met = 1 if resolution_hours <= sla_hours else 0

        if category == "Fiber / ISP Link Down":
            root_cause = "Fiber Cut / ISP Upstream"
        elif category == "Network Outage":
            root_cause = random.choice(["Switch / Router Config Drift", "Fiber Cut / ISP Upstream", "Power / UPS Fluctuation"])
        elif category == "Database / Backup Alert":
            root_cause = random.choice(["Database Lock / Timeout", "Server CPU / Memory Spike"])
        else:
            root_cause = random.choice(ROOT_CAUSES[2:])

        is_repeat = 1 if random.random() < (0.22 if root_cause in ("Fiber Cut / ISP Upstream", "Switch / Router Config Drift") else 0.09) else 0

        rows.append([
            ticket_id,
            created_at.strftime("%Y-%m-%d %H:%M:%S"),
            resolved_at.strftime("%Y-%m-%d %H:%M:%S"),
            region,
            category,
            priority,
            team,
            root_cause,
            sla_hours,
            resolution_hours,
            sla_met,
            is_repeat,
        ])

    rows.sort(key=lambda r: r[1])

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ticket_id", "created_at", "resolved_at", "region", "category",
            "priority", "assigned_team", "root_cause", "sla_target_hours",
            "resolution_hours", "sla_met", "is_repeat_incident"
        ])
        writer.writerows(rows)

    print(f"Generated {len(rows)} tickets at {CSV_PATH}")


if __name__ == "__main__":
    main()
