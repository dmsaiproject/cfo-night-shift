from datetime import datetime
from pathlib import Path
import json

from graph import graph


# ============================================================
# FOLDERS / FILES
# ============================================================

INCOMING_FOLDER = Path("incoming")

REPORTS_FOLDER = Path("reports")

RESULTS_FILE = (
    REPORTS_FOLDER / "latest_results.json"
)


# ============================================================
# FIND LATEST CSV
# ============================================================

def find_latest_csv():

    INCOMING_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    csv_files = list(
        INCOMING_FOLDER.glob("*.csv")
    )

    if not csv_files:

        raise FileNotFoundError(
            "No CSV file found in the incoming folder."
        )

    latest_file = max(
        csv_files,
        key=lambda file: file.stat().st_mtime
    )

    return latest_file


# ============================================================
# LOAD PREVIOUS RESULTS
# ============================================================

def load_previous_results():

    if not RESULTS_FILE.exists():

        return None

    try:

        with open(
            RESULTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"Could not read previous results: {error}"
        )

        return None


# ============================================================
# RUN CFO NIGHT SHIFT
# ============================================================

def run_night_shift():

    print(
        "=" * 60
    )

    print(
        "CFO NIGHT SHIFT - AUTOMATED RUN"
    )

    print(
        "=" * 60
    )

    start_time = datetime.now()

    print(
        f"Run started: "
        f"{start_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print()

    # ========================================================
    # LOAD PREVIOUS RUN
    # ========================================================

    previous_results = (
        load_previous_results()
    )

    previous_count = 0

    if previous_results:

        previous_count = int(
            previous_results.get(
                "total_transactions",
                0
            )
        )

    print(
        f"Previous transaction count: "
        f"{previous_count}"
    )

    print()

    # ========================================================
    # FIND LATEST TRANSACTION FILE
    # ========================================================

    transaction_file = (
        find_latest_csv()
    )

    print(
        f"Transaction file selected: "
        f"{transaction_file}"
    )

    print()

    # ========================================================
    # RUN LANGGRAPH
    # ========================================================

    result = graph.invoke(
        {
            "file_path":
                str(transaction_file)
        }
    )

    # ========================================================
    # EXTRACT RESULTS
    # ========================================================

    transactions = (
        result["transactions"]
    )

    fraud_results = (
        result["fraud_results"]
    )

    anomaly_results = (
        result["anomaly_results"]
    )

    suspicious_count = int(
        fraud_results[
            "fraud_flag"
        ].sum()
    )

    anomaly_count = int(
        anomaly_results[
            "anomaly_flag"
        ].sum()
    )

    current_count = len(
        transactions
    )

    # ========================================================
    # DETERMINE NEW TRANSACTIONS
    # ========================================================

    new_transaction_count = max(
        0,
        current_count - previous_count
    )

    print(
        f"Current transaction count : "
        f"{current_count}"
    )

    print(
        f"New transactions           : "
        f"{new_transaction_count}"
    )

    print()

    # ========================================================
    # IDENTIFY NEW TRANSACTION RECORDS
    # ========================================================

    new_transactions = []

    if (
        previous_count > 0
        and current_count > previous_count
    ):

        new_transactions_df = (
            transactions.iloc[
                previous_count:
            ]
        )

        if "transaction_id" in (
            new_transactions_df.columns
        ):

            new_transactions = (
                new_transactions_df[
                    "transaction_id"
                ]
                .astype(str)
                .tolist()
            )

    elif previous_count == 0:

        # First run:
        # all transactions are considered existing,
        # not "new alerts".

        new_transactions = []

    # ========================================================
    # DETERMINE NEW SUSPICIOUS TRANSACTIONS
    # ========================================================

    new_suspicious_transactions = []

    if new_transactions:

        new_suspicious_df = (
            fraud_results[
                fraud_results[
                    "transaction_id"
                ].astype(str).isin(
                    new_transactions
                )
                &
                fraud_results[
                    "fraud_flag"
                ]
            ]
        )

        if not new_suspicious_df.empty:

            new_suspicious_transactions = (
                new_suspicious_df[
                    "transaction_id"
                ]
                .astype(str)
                .tolist()
            )

    print(
        f"New suspicious transactions: "
        f"{len(new_suspicious_transactions)}"
    )

    print()

    # ========================================================
    # NEW RISK STATUS
    # ========================================================

    if new_suspicious_transactions:

        new_risk_alert = True

        new_risk_message = (
            "New suspicious transaction(s) "
            "detected."
        )

    else:

        new_risk_alert = False

        new_risk_message = (
            "No newly detected suspicious "
            "transactions."
        )

    # ========================================================
    # CREATE DASHBOARD DATA
    # ========================================================

    dashboard_data = {

        "run_time":
            start_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "source_file":
            str(transaction_file),

        "total_transactions":
            current_count,

        "previous_transaction_count":
            previous_count,

        "new_transaction_count":
            new_transaction_count,

        "new_transactions":
            new_transactions,

        "suspicious_transactions":
            suspicious_count,

        "new_suspicious_transactions":
            len(
                new_suspicious_transactions
            ),

        "new_suspicious_transaction_ids":
            new_suspicious_transactions,

        "new_risk_alert":
            new_risk_alert,

        "new_risk_message":
            new_risk_message,

        "expense_anomalies":
            anomaly_count,

        "report_path":
            result["report_path"],

        "insight":
            result["insight"]
    }

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    REPORTS_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            dashboard_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # DISPLAY SUMMARY
    # ========================================================

    print(
        "Night Shift completed successfully."
    )

    print()

    print(
        f"Transactions reviewed       : "
        f"{current_count}"
    )

    print(
        f"New transactions            : "
        f"{new_transaction_count}"
    )

    print(
        f"Suspicious transactions     : "
        f"{suspicious_count}"
    )

    print(
        f"New suspicious transactions : "
        f"{len(new_suspicious_transactions)}"
    )

    print(
        f"Expense anomalies           : "
        f"{anomaly_count}"
    )

    print()

    print(
        f"Report generated            : "
        f"{result['report_path']}"
    )

    print(
        f"Dashboard data saved        : "
        f"{RESULTS_FILE}"
    )

    print()

    print(
        f"Run completed: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        "=" * 60
    )


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    run_night_shift()