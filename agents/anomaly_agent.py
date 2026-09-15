import pandas as pd


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect unusually high transactions compared with
    the normal spending level of each department.
    """

    results = df.copy()

    # Calculate average transaction amount for each department
    department_average = results.groupby(
        "department"
    )["amount"].transform("mean")

    results["department_average"] = department_average

    # Flag transactions more than 2x department average
    results["anomaly_flag"] = (
        results["amount"] > results["department_average"] * 2
    )

    return results


if __name__ == "__main__":
    from ingestion_agent import load_transactions

    file_path = "data/transactions.csv"

    transactions = load_transactions(file_path)

    anomaly_results = detect_anomalies(transactions)

    anomalies = anomaly_results[
        anomaly_results["anomaly_flag"]
    ]

    print("Expense anomaly detection completed.")
    print(f"Total transactions: {len(anomaly_results)}")
    print(f"Anomalous transactions: {len(anomalies)}")
    print()

    print(
        anomalies[
            [
                "transaction_id",
                "department",
                "amount",
                "department_average",
                "anomaly_flag",
            ]
        ].to_string(index=False)
    )
