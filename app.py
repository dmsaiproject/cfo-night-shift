import tempfile
from pathlib import Path

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
# HEADER
# ---------------------------------------------------------

st.title("🌙 CFO NIGHT SHIFT")

st.subheader(
    "Agentic AI Financial Monitoring & Executive Decision-Support System"
)

st.info(
    "Upload a transaction CSV. The five-agent workflow will analyze "
    "financial risks, generate CFO-level insight and create a board-ready report."
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
# MAIN PROCESSING
# ---------------------------------------------------------

if uploaded_file is None:

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

    st.success(
        f"CSV uploaded successfully: **{uploaded_file.name}**"
    )

    # -----------------------------------------------------
    # READ UPLOADED CSV
    # -----------------------------------------------------

    df = pd.read_csv(uploaded_file)

    df.columns = df.columns.str.strip()

    st.markdown("## 📊 Transaction Preview")

    st.dataframe(
        df.head(10),
        use_container_width=True
    )

    st.markdown("---")

    # -----------------------------------------------------
    # RUN AGENTIC WORKFLOW
    # -----------------------------------------------------

    if st.button(
        "⚡ Run CFO Night Shift",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Running the five-agent CFO Night Shift workflow..."
        ):

            try:

                # Save uploaded file temporarily.
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".csv"
                ) as temp_file:

                    temp_file.write(
                        uploaded_file.getvalue()
                    )

                    temp_file_path = temp_file.name

                # Run existing LangGraph workflow.
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

                # -------------------------------------------------
                # SAVE RESULTS TO SESSION
                # -------------------------------------------------

                st.session_state["result"] = result
                st.session_state["total_count"] = total_count
                st.session_state["suspicious_count"] = suspicious_count
                st.session_state["anomaly_count"] = anomaly_count

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
