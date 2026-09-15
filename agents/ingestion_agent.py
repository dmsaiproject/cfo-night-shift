from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = [
    "transaction_id",
    "date",
    "time",
    "department",
    "vendor",
    "category",
    "amount",
    "currency",
    "payment_method",
    "description",
]


def load_transactions(file_path: str) -> pd.DataFrame:
    """
    Load and validate the financial transaction CSV file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Transaction file not found: {path}")

    df = pd.read_csv(path)

    # Check required columns
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Clean column names
    df.columns = df.columns.str.strip()

    # Convert amount to numeric
    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    if df["amount"].isna().any():
        raise ValueError(
            "One or more transactions contain an invalid amount."
        )

    # Combine date and time
    df["datetime"] = pd.to_datetime(
        df["date"].astype(str) + " " + df["time"].astype(str),
        errors="coerce"
    )

    if df["datetime"].isna().any():
        raise ValueError(
            "One or more transactions contain an invalid date/time."
        )

    return df


if __name__ == "__main__":
    file_path = "data/transactions.csv"

    transactions = load_transactions(file_path)

    print("Transaction ingestion successful.")
    print(f"Total transactions: {len(transactions)}")
    print(f"Total transaction value: ${transactions['amount'].sum():,.2f}")
    print()
    print(transactions.head())
