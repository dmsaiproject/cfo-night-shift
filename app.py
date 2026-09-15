def create_demo_transaction(df):

    existing_ids = (
        df["transaction_id"].astype(str).tolist()
        if "transaction_id" in df.columns
        else []
    )

    transaction_number = len(existing_ids) + 1
    transaction_id = f"LIVE-{transaction_number:04d}"

    while transaction_id in existing_ids:
        transaction_number += 1
        transaction_id = f"LIVE-{transaction_number:04d}"

    new_transaction = {}

    # Keep every existing column
    for column in df.columns:
        new_transaction[column] = ""

    # -----------------------------------------------------
    # TRANSACTION ID
    # -----------------------------------------------------

    if "transaction_id" in df.columns:
        new_transaction["transaction_id"] = transaction_id

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    if "date" in df.columns:

        if len(df) > 0:

            sample_date = df.iloc[0]["date"]

            # Convert existing date to a real datetime first.
            parsed_date = pd.to_datetime(
                sample_date,
                errors="coerce",
                dayfirst=True
            )

            if pd.isna(parsed_date):
                raise ValueError(
                    f"Existing CSV contains an invalid date: {sample_date}"
                )

            # Use the same textual format as the existing CSV.
            sample_date_text = str(sample_date).strip()

            if "/" in sample_date_text:

                parts = sample_date_text.split("/")

                if len(parts) == 3 and len(parts[-1]) == 4:
                    new_transaction["date"] = parsed_date.strftime(
                        "%d/%m/%Y"
                    )
                else:
                    new_transaction["date"] = parsed_date.strftime(
                        "%Y/%m/%d"
                    )

            elif "-" in sample_date_text:

                new_transaction["date"] = parsed_date.strftime(
                    "%Y-%m-%d"
                )

            else:

                new_transaction["date"] = parsed_date.strftime(
                    "%Y-%m-%d"
                )

        else:

            new_transaction["date"] = datetime.now().strftime(
                "%Y-%m-%d"
            )

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    if "time" in df.columns:

        if len(df) > 0:

            sample_time = str(
                df.iloc[0]["time"]
            ).strip()

            # Check how the existing CSV stores time.
            parsed_time = pd.to_datetime(
                sample_time,
                errors="coerce"
            )

            if pd.isna(parsed_time):
                raise ValueError(
                    f"Existing CSV contains an invalid time: {sample_time}"
                )

            # Preserve a standard HH:MM:SS representation.
            new_transaction["time"] = "23:45:00"

        else:

            new_transaction["time"] = "23:45:00"

    # -----------------------------------------------------
    # OTHER TRANSACTION DETAILS
    # -----------------------------------------------------

    if "department" in df.columns:
        new_transaction["department"] = "Finance"

    if "vendor" in df.columns:
        new_transaction["vendor"] = "Unknown Vendor"

    if "category" in df.columns:
        new_transaction["category"] = "Consulting"

    if "amount" in df.columns:
        new_transaction["amount"] = 19500

    if "currency" in df.columns:

        if (
            len(df) > 0
            and str(df.iloc[0]["currency"]).strip()
        ):
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
