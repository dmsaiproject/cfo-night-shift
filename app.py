import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

from graph import graph


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="CFO Night Shift",
    page_icon="🌙",
    layout="wide",
)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def generate_cfo_action(suspicious_transactions, expense_anomalies):

    if suspicious_transactions > 0:
        return """
### 🎯 CFO MANAGEMENT ACTION

🔴 **Priority: Immediate Human Review**

**1. REVIEW**  
Review all flagged high-risk transactions and understand the potential business impact.

**2. VERIFY**  
Ask the Finance Head to verify vendor identity, invoice, purchase order, authorization and payment evidence.

**3. INVESTIGATE**  
Contact the responsible department and confirm the business purpose and approval history.

**4. DECIDE**  
Take action according to company policy and authorized approval procedures.

**5. DOCUMENT**  
Record the investigation outcome and escalate confirmed or material issues to the appropriate authority.

---

👤 **CEO Instruction:**  
Review the overall financial risk exposure, prioritize material risks and direct management action where required.

👤 **Finance Head Instruction:**  
Verify vendor, invoice, approval and payment evidence. Investigate flagged transactions and document the outcome.

⚠️ **AI Decision Boundary:**  
AI identifies potential financial risks and provides recommendations. Final investigation, approval, rejection, escalation and financial decisions remain with authorized human personnel.
"""

    elif expense_anomalies > 0:
        return """
### 🎯 CFO MANAGEMENT ACTION

🟠 **Priority: Management Review**

**1. REVIEW**  
Review the identified expense anomalies and their business context.

**2. VERIFY**  
Compare the transactions with budgets, historical spending and supporting documentation.

**3. INVESTIGATE**  
Ask the relevant department to explain significant deviations from normal spending.

**4. DECIDE**  
Take appropriate action according to company policy.

**5. DOCUMENT**  
Record the reason for the deviation and any corrective action.

---

👤 **CEO Instruction:**  
Review the overall financial impact and ensure that significant anomalies receive appropriate management attention.

👤 **Finance Head Instruction:**  
Verify supporting documents, investigate the spending deviation and document the outcome.

⚠️ **AI Decision Boundary:**  
AI identifies potential financial risks. Final decisions remain with authorized human personnel.
"""

    else:
        return """
### 🎯 CFO MANAGEMENT ACTION

🟢 **Priority: Routine Monitoring**

Continue normal financial monitoring and control procedures.

👤 **CEO Instruction:**  
Review the overall financial position and continue routine management oversight.

👤 **Finance Head Instruction:**  
Continue normal transaction verification and financial control procedures.

⚠️ **AI Decision Boundary:**  
AI-assisted monitoring does not replace authorized human financial decisions.
"""


def analyse_transactions(df):

    results = df.copy()

    if "amount" in results.columns:
        results["amount"] = pd.to_numeric(
            results["amount"],
            errors="coerce"
        )

    if "date" in results.columns and "time" in results.columns:
        results["_datetime"] = pd.to_datetime(
            results["date"].astype(str) + " " + results["time"].astype(str),
            errors="coerce"
        )

    duplicate_columns = [
        "vendor",
        "amount",
        "payment_method",
        "description"
    ]

    if all(column in results.columns for column in duplicate_columns):
        results["duplicate_flag"] = results.duplicated(
            subset=duplicate_columns,
            keep=False
        )
    else:
        results["duplicate_flag"] = False

    if "amount" in results.columns:
        results["large_amount_flag"] = results["amount"] >= 10000
    else:
        results["large_amount_flag"] = False

    if "_datetime" in results.columns:
        results["off_hours_flag"] = (
            (results["_datetime"].dt.hour < 6)
            |
            (results["_datetime"].dt.hour >= 22)
        )
    else:
        results["off_hours_flag"] = False

    if "vendor" in results.columns:
        results["unknown_vendor_flag"] = (
            results["vendor"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "unknown vendor"
        )
    else:
        results["unknown_vendor_flag"] = False

    results["fraud_flag"] = (
        results["duplicate_flag"]
        |
        results["large_amount_flag"]
        |
        results["off_hours_flag"]
        |
        results["unknown_vendor_flag"]
    )

    if "department" in results.columns and "amount" in results.columns:

        results["department_average"] = (
            results.groupby("department")["amount"]
            .transform("mean")
        )

        results["anomaly_flag"] = (
            results["amount"]
            > results["department_average"] * 2
        )

    else:

        results["department_average"] = 0
        results["anomaly_flag"] = False

    return results


# ---------------------------------------------------------
# RUN WORKFLOW
# ---------------------------------------------------------

def run_cfo_workflow(df):

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".csv"
    ) as temp_file:

        df.to_csv(
            temp_file.name,
            index=False
        )

        temp_file_path = temp_file.name

    result = graph.invoke(
        {
            "file_path": temp_file_path
        }
    )

    transactions = result["transactions"]
    fraud_results = result["fraud_results"]
    anomaly_results = result["anomaly_results"]

    suspicious_count = int(
        fraud_results["fraud_flag"].sum()
    )

    anomaly_count = int(
        anomaly_results["anomaly_flag"].sum()
    )

    total_count = len(transactions)

    st.session_state["result"] = result
    st.session_state["demo_df"] = transactions
    st.session_state["total_count"] = total_count
    st.session_state["suspicious_count"] = suspicious_count
    st.session_state["anomaly_count"] = anomaly_count

    return result


# ---------------------------------------------------------
# SIMULATE NEW TRANSACTION
# ---------------------------------------------------------

def create_demo_transaction(df):

    now = datetime.now()

    existing_ids = (
        df["transaction_id"].astype(str).tolist()
        if "transaction_id" in df.columns
        else []
    )

    transaction_id = f"LIVE-{len(existing_ids) + 1:04d}"

    while transaction_id in existing_ids:
        transaction_id = f"LIVE-{len(existing_ids) + 2:04d}"

    new_transaction = {}

    for column in df.columns:

        new_transaction[column] = ""

    if "transaction_id" in df.columns:
        new_transaction["transaction_id"] = transaction_id

    if "date" in df.columns:
        new_transaction["date"] = now.strftime("%Y-%m-%d")

    if "time" in df.columns:
        # Deliberately off-hours for the demonstration.
        new_transaction["time"] = "23:45:00"

    if "department" in df.columns:
        new_transaction["department"] = "Finance"

    if "vendor" in df.columns:
        new_transaction["vendor"] = "Unknown Vendor"

    if "category" in df.columns:
        new_transaction["category"] = "Consulting"

    if "amount" in df.columns:
        new_transaction["amount"] = 19500

    if "currency" in df.columns:

        if len(df) > 0 and str(df.iloc[0]["currency"]).strip():
            new_transaction["currency"] = df.iloc[0]["currency"]
        else:
            new_transaction["currency"] = "USD"

    if "payment_method" in df.columns:
        new_transaction["payment_method"] = "Bank Transfer"

    if "description" in df.columns:
        new_transaction["description"] = (
            "Urgent consulting payment"
        )

    return pd.DataFrame(
        [new_transaction],
        columns=df.columns
    )


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🌙 CFO NIGHT SHIFT")

st.subheader(
    "Agentic AI Financial Monitoring & Executive Decision-Support System"
)

st.info(
    "Upload transaction data or simulate a new live transaction. "
    "The five-agent workflow analyzes financial risks, generates "
    "CFO-level insight and creates a board-ready report."
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.header("📁 Transaction Input")

    uploaded_file = st.file_uploader(
        "Upload CSV transaction data",
        type=["csv"]
    )

    st.markdown("---")

    st.markdown(
        """
### 🤖 Agent Workflow

1. Transaction Ingestion
2. Fraud Detection
3. Expense Anomaly Detection
4. CFO Insight
5. Board Report

### 🔐 AI Boundary

AI identifies potential risks and provides recommendations.

Final financial decisions remain with authorized human personnel.
"""
    )


# ---------------------------------------------------------
# INITIAL DATA
# ---------------------------------------------------------

if uploaded_file is None and "demo_df" not in st.session_state:

    st.warning(
        "Please upload a CSV transaction file from the sidebar to begin."
    )

    st.markdown("## 📋 Expected CSV Columns")

    st.code(
        """
transaction_id
date
time
department
vendor
category
amount
currency
payment_method
description
""".strip()
    )

else:

    # -----------------------------------------------------
    # LOAD INITIAL CSV
    # -----------------------------------------------------

    if uploaded_file is not None and "demo_df" not in st.session_state:

        df = pd.read_csv(uploaded_file)

        df.columns = df.columns.str.strip()

        st.session_state["demo_df"] = df

        st.session_state["source_file"] = uploaded_file.name

    elif "demo_df" in st.session_state:

        df = st.session_state["demo_df"].copy()

    else:

        df = pd.DataFrame()


    # -----------------------------------------------------
    # TRANSACTION PREVIEW
    # -----------------------------------------------------

    st.success(
        f"Transactions loaded: **{len(df)}**"
    )

    st.markdown("## 📊 Transaction Preview")

    st.dataframe(
        df.tail(10),
        use_container_width=True
    )

    st.markdown("---")


    # -----------------------------------------------------
    # LIVE DEMO CONTROLS
    # -----------------------------------------------------

    st.header("⚡ Live Transaction Simulation")

    st.info(
        "Use this button during a demonstration to simulate a "
        "new high-value transaction arriving during the night."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🚨 Simulate New Transaction",
            type="primary",
            use_container_width=True
        ):

            try:

                new_transaction = create_demo_transaction(
                    df
                )

                updated_df = pd.concat(
                    [
                        df,
                        new_transaction
                    ],
                    ignore_index=True
                )

                st.session_state["demo_df"] = updated_df

                st.success(
                    "🚨 New transaction received!"
                )

                st.dataframe(
                    new_transaction,
                    use_container_width=True
                )

                with st.spinner(
                    "AI agents are analyzing the new transaction..."
                ):

                    run_cfo_workflow(
                        updated_df
                    )

                st.success(
                    "✅ New transaction analyzed successfully."
                )

            except Exception as error:

                st.error(
                    f"❌ Live transaction workflow error: {error}"
                )

    with col2:

        if st.button(
            "🔄 Run CFO Night Shift",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Running the five-agent CFO Night Shift workflow..."
                ):

                    run_cfo_workflow(
                        df
                    )

                st.success(
                    "✅ CFO Night Shift completed successfully."
                )

            except Exception as error:

                st.error(
                    f"❌ Workflow error: {error}"
                )


# ---------------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------------

if "result" in st.session_state:

    result = st.session_state["result"]

    total_count = st.session_state["total_count"]
    suspicious_count = st.session_state["suspicious_count"]
    anomaly_count = st.session_state["anomaly_count"]

    transactions = result["transactions"]
    fraud_results = result["fraud_results"]
    anomaly_results = result["anomaly_results"]


    # -----------------------------------------------------
    # EXECUTIVE KPI
    # -----------------------------------------------------

    st.markdown("---")

    st.header("📊 Executive Risk Overview")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Transactions",
            total_count
        )

    with col2:

        st.metric(
            "Suspicious Transactions",
            suspicious_count
        )

    with col3:

        st.metric(
            "Expense Anomalies",
            anomaly_count
        )


    # -----------------------------------------------------
    # RISK STATUS
    # -----------------------------------------------------

    st.markdown("---")

    st.header("🚨 Executive Risk Status")

    if suspicious_count > 0:

        st.error(
            f"🔴 HIGH RISK — "
            f"{suspicious_count} suspicious transaction(s) detected."
        )

    elif anomaly_count > 0:

        st.warning(
            f"🟠 MEDIUM RISK — "
            f"{anomaly_count} expense anomaly/anomalies detected."
        )

    else:

        st.success(
            "🟢 LOW RISK — No significant risk detected."
        )


    # -----------------------------------------------------
    # ANALYSIS
    # -----------------------------------------------------

    analysed_df = analyse_transactions(
        transactions
    )


    # -----------------------------------------------------
    # SUSPICIOUS TRANSACTIONS
    # -----------------------------------------------------

    st.markdown("---")

    st.header("🔎 Suspicious Transactions")

    suspicious_df = analysed_df[
        analysed_df["fraud_flag"]
    ].copy()

    if not suspicious_df.empty:

        display_columns = [
            "transaction_id",
            "date",
            "time",
            "department",
            "vendor",
            "amount",
            "payment_method"
        ]

        available_columns = [
            column
            for column in display_columns
            if column in suspicious_df.columns
        ]

        st.dataframe(
            suspicious_df[available_columns],
            use_container_width=True
        )

    else:

        st.success(
            "No suspicious transactions detected."
        )


    # -----------------------------------------------------
    # EXPENSE ANOMALIES
    # -----------------------------------------------------

    st.markdown("---")

    st.header("📈 Expense Anomalies")

    anomaly_df = analysed_df[
        analysed_df["anomaly_flag"]
    ].copy()

    if not anomaly_df.empty:

        display_columns = [
            "transaction_id",
            "department",
            "vendor",
            "amount",
            "department_average"
        ]

        available_columns = [
            column
            for column in display_columns
            if column in anomaly_df.columns
        ]

        st.dataframe(
            anomaly_df[available_columns],
            use_container_width=True
        )

    else:

        st.success(
            "No significant expense anomalies detected."
        )


    # -----------------------------------------------------
    # CFO AI INSIGHT
    # -----------------------------------------------------

    st.markdown("---")

    st.header("🧠 CFO AI Insight")

    st.markdown(
        result["insight"]
    )


    # -----------------------------------------------------
    # CFO MANAGEMENT ACTION
    # -----------------------------------------------------

    st.markdown("---")

    st.markdown(
        generate_cfo_action(
            suspicious_count,
            anomaly_count
        )
    )


    # -----------------------------------------------------
    # BOARD REPORT
    # -----------------------------------------------------

    st.markdown("---")

    st.header("📄 Board Report")

    report_path = Path(
        result["report_path"]
    )

    if report_path.exists():

        with open(
            report_path,
            "rb"
        ) as report_file:

            st.download_button(
                label="📥 Download CFO Board Report",
                data=report_file.read(),
                file_name="CFO_Night_Shift_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    else:

        st.warning(
            "Board report file was not found."
        )


    # -----------------------------------------------------
    # HUMAN OVERSIGHT
    # -----------------------------------------------------

    st.markdown("---")

    st.warning(
        """
### ⚠️ Human Oversight

Flagged transactions represent **potential financial risks** requiring human investigation.

Automated detection does not establish fraud, wrongdoing or financial liability.

**AI detects and recommends. Humans investigate and decide.**
"""
    )
