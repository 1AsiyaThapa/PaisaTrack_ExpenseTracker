from .models import TransactionType


def process_dashboard_summary(raw_data, months: int) -> list[dict]:
    """
    Process raw transaction data into a dashboard summary format.
    Aggregates income and expenses by category per month.
    """
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    # Find the most recent N months present in the data
    unique_months = sorted(
        set((int(row.year), int(row.month)) for row in raw_data), reverse=True
    )[:months]
    unique_months.reverse()

    # Filter data to only include those months
    filtered_data = [
        row for row in raw_data if (int(row.year), int(row.month)) in unique_months
    ]

    summary = {}
    for row in filtered_data:
        year = int(row.year)
        month = int(row.month)
        month_key = f"{year}-{month:02d}"
        month_label = f"{month_names[month - 1]} {year}"

        if month_key not in summary:
            summary[month_key] = {"month": month_label, "Income": 0.0}

        if row.type == TransactionType.INCOME:
            current = summary[month_key].get("Income", 0.0)
            summary[month_key]["Income"] = current + float(row.total)
        else:
            summary[month_key][row.category] = float(row.total)

    result = []
    for month_key in sorted(summary.keys()):
        month_data = summary[month_key]
        result.append(month_data)

    return result
