import os
from groq import Groq


def generate_insight(
    total_transactions: int,
    suspicious_transactions: int,
    anomalous_transactions: int,
    suspicious_details: str,
    anomaly_details: str,
) -> str:

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Please set the environment variable before running the agent."
        )

    client = Groq(api_key=api_key)

    prompt = f"""
You are a financial monitoring assistant helping a CFO.

Use ONLY the information provided below.
Do not invent financial facts.
Do not claim that a transaction is definitely fraudulent.
Use terms such as "requires investigation" or "potential risk".

Transaction Summary:
- Total transactions: {total_transactions}
- Suspicious transactions: {suspicious_transactions}
- Anomalous transactions: {anomalous_transactions}

Suspicious Transaction Details:
{suspicious_details}

Anomaly Details:
{anomaly_details}

Write a concise CFO-level summary with these sections:

1. Executive Summary
2. Key Risks
3. Recommended Actions

Keep the language simple, professional and suitable for a management report.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    return response.choices[0].message.content
