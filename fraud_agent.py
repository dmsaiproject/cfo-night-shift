import pandas as pd


def detect_fraud(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect potentially suspicious financial transactions
    using deterministic business rules.
    """

    results = df.copy()

    # Rule 1: Duplicate transactions
    results["duplicate_flag"] = results.duplicated(
        subset=["vendor", "amount", "payment_method", "description"],
        keep=False
    )

    # Rule 2: Large transaction
    results["large_amount_flag"] = results["amount"] >= 10000

    # Rule 3: Off-hours transaction
    results["off_hours_flag"] = (
        (results["datetime"].dt.hour < 6) |
        (results["datetime"].dt.hour >= 22)
    )

    # Rule 4: Unknown vendor
    results["unknown_vendor_flag"] = (
        results["vendor"].str.strip().str.lower() == "unknown vendor"
    )

    # Overall fraud/suspicion flag
    results["fraud_flag"] = (
        results["duplicate_flag"] |
        results["large_amount_flag"] |
        results["off_hours_flag"] |
        results["unknown_vendor_flag"]
    )

    return results


if __name__ == "__main__":
    from ingestion_agent import load_transactions

    file_path = "data/transactions.csv"

    transactions = load_transactions(file_path)

    flagged_transactions = detect_fraud(transactions)

    suspicious = flagged_transactions[
        flagged_transactions["fraud_flag"]
    ]

    print("Fraud detection completed.")
    print(f"Total transactions: {len(flagged_transactions)}")
    print(f"Suspicious transactions: {len(suspicious)}")
    print()

    print(
        suspicious[
            [
                "transaction_id",
                "vendor",
                "amount",
                "duplicate_flag",
                "large_amount_flag",
                "off_hours_flag",
                "unknown_vendor_flag",
            ]
        ].to_string(index=False)
    )