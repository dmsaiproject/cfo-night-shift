from typing import TypedDict

from agents.ingestion_agent import load_transactions
from agents.fraud_agent import detect_fraud
from agents.anomaly_agent import detect_anomalies
from agents.insight_agent import generate_insight
from agents.report_agent import create_board_report

from langgraph.graph import StateGraph, START, END


class FinancialState(TypedDict, total=False):
    file_path: str
    transactions: object
    fraud_results: object
    anomaly_results: object
    suspicious_details: str
    anomaly_details: str
    insight: str
    report_path: str


def ingestion_node(state: FinancialState):
    transactions = load_transactions(state["file_path"])

    return {
        "transactions": transactions
    }


def fraud_node(state: FinancialState):
    results = detect_fraud(state["transactions"])

    suspicious = results[
        results["fraud_flag"]
    ]

    suspicious_details = suspicious[
        [
            "transaction_id",
            "department",
            "vendor",
            "amount",
            "duplicate_flag",
            "large_amount_flag",
            "off_hours_flag",
            "unknown_vendor_flag",
        ]
    ].to_string(index=False)

    return {
        "fraud_results": results,
        "suspicious_details": suspicious_details,
    }


def anomaly_node(state: FinancialState):
    results = detect_anomalies(
        state["transactions"]
    )

    anomalies = results[
        results["anomaly_flag"]
    ]

    anomaly_details = anomalies[
        [
            "transaction_id",
            "department",
            "amount",
            "department_average",
        ]
    ].to_string(index=False)

    return {
        "anomaly_results": results,
        "anomaly_details": anomaly_details,
    }


def insight_node(state: FinancialState):
    fraud_results = state["fraud_results"]
    anomaly_results = state["anomaly_results"]

    suspicious_count = int(
        fraud_results["fraud_flag"].sum()
    )

    anomaly_count = int(
        anomaly_results["anomaly_flag"].sum()
    )

    insight = generate_insight(
        total_transactions=len(
            state["transactions"]
        ),
        suspicious_transactions=suspicious_count,
        anomalous_transactions=anomaly_count,
        suspicious_details=state[
            "suspicious_details"
        ],
        anomaly_details=state[
            "anomaly_details"
        ],
    )

    return {
        "insight": insight
    }


def report_node(state: FinancialState):
    fraud_results = state["fraud_results"]
    anomaly_results = state["anomaly_results"]

    suspicious_count = int(
        fraud_results["fraud_flag"].sum()
    )

    anomaly_count = int(
        anomaly_results["anomaly_flag"].sum()
    )

    report_path = (
        "reports/CFO_Night_Shift_Report.pdf"
    )

    create_board_report(
        output_path=report_path,
        total_transactions=len(
            state["transactions"]
        ),
        suspicious_transactions=suspicious_count,
        anomalous_transactions=anomaly_count,
        suspicious_details=state[
            "suspicious_details"
        ],
        anomaly_details=state[
            "anomaly_details"
        ],
        insight=state["insight"],
    )

    return {
        "report_path": report_path
    }


# Create LangGraph workflow
workflow = StateGraph(FinancialState)

workflow.add_node("ingestion", ingestion_node)
workflow.add_node("fraud", fraud_node)
workflow.add_node("anomaly", anomaly_node)
workflow.add_node("insight", insight_node)
workflow.add_node("report", report_node)

workflow.add_edge(START, "ingestion")
workflow.add_edge("ingestion", "fraud")
workflow.add_edge("fraud", "anomaly")
workflow.add_edge("anomaly", "insight")
workflow.add_edge("insight", "report")
workflow.add_edge("report", END)

graph = workflow.compile()


if __name__ == "__main__":

    result = graph.invoke(
        {
            "file_path": "data/transactions.csv"
        }
    )

    print()
    print("==============================")
    print("CFO NIGHT SHIFT WORKFLOW")
    print("==============================")
    print(
        f"Transactions: "
        f"{len(result['transactions'])}"
    )

    print(
        "Suspicious: "
        f"{int(result['fraud_results']['fraud_flag'].sum())}"
    )

    print(
        "Anomalies: "
        f"{int(result['anomaly_results']['anomaly_flag'].sum())}"
    )

    print()
    print("Report generated:")
    print(result["report_path"])