import csv
from pathlib import Path
from typing import Any


def is_financial_csv(fieldnames: list[str]) -> bool:
    """Heuristic to detect if a CSV represents banking, Hawala, or ledger records."""
    normalized = [f.strip().lower().replace(" ", "_") for f in fieldnames if f]
    account_indicators = {"account", "acc_no", "sender_account", "beneficiary_account", "acc", "from_account", "to_account"}
    amount_indicators = {"amount", "amt", "debit", "credit", "txn_amount", "volume"}
    
    has_account = any(any(ind in f for ind in account_indicators) for f in normalized)
    has_amount = any(any(ind in f for ind in amount_indicators) for f in normalized)
    return has_account and has_amount


def parse_financial_file(path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """
    Parses a financial ledger or bank statement CSV into structured monetary intelligence text,
    detecting potential smurfing (structuring) and high-value transfers.
    """
    records = []
    beneficiary_inflow: dict[str, float] = {}
    smurfing_candidates: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError("Financial CSV must have a header row.")

        field_map = {}
        for f in reader.fieldnames:
            norm = f.strip().lower().replace(" ", "_")
            if any(k in norm for k in ["from", "sender", "source_acc", "remitter"]):
                field_map["sender"] = f
            elif any(k in norm for k in ["to", "beneficiary", "dest_acc", "recipient"]):
                field_map["beneficiary"] = f
            elif any(k in norm for k in ["amount", "amt", "debit", "credit"]):
                field_map["amount"] = f
            elif any(k in norm for k in ["date", "time", "txn_date"]):
                field_map["date"] = f
            elif any(k in norm for k in ["channel", "mode", "type", "payment_mode"]):
                field_map["channel"] = f
            elif any(k in norm for k in ["ref", "utr", "txn_id", "narration", "description"]):
                field_map["ref"] = f

        sender_col = field_map.get("sender")
        beneficiary_col = field_map.get("beneficiary")
        amount_col = field_map.get("amount")
        date_col = field_map.get("date")
        channel_col = field_map.get("channel")
        ref_col = field_map.get("ref")

        for row_idx, row in enumerate(reader, start=1):
            sender = (row.get(sender_col) or "").strip()
            beneficiary = (row.get(beneficiary_col) or "").strip()
            raw_amt = (row.get(amount_col) or "0").replace(",", "").replace("₹", "").replace("$", "").strip()
            date = (row.get(date_col) or "").strip()
            channel = (row.get(channel_col) or "NEFT/RTGS").strip()
            ref = (row.get(ref_col) or "").strip()

            try:
                amount_val = float(raw_amt)
            except ValueError:
                amount_val = 0.0

            if not sender and not beneficiary:
                continue

            # Update beneficiary inflows
            if beneficiary:
                beneficiary_inflow[beneficiary] = beneficiary_inflow.get(beneficiary, 0.0) + amount_val

            # Structuring / Smurfing heuristic (repeated amounts under 50,000 threshold)
            if 10000 <= amount_val <= 49999:
                smurfing_candidates.append({
                    "row": row_idx,
                    "sender": sender,
                    "beneficiary": beneficiary,
                    "amount": amount_val,
                    "date": date,
                })

            formatted_line = (
                f"[FINANCIAL TRANSACTION #{row_idx}] "
                f"SENDER_ACCOUNT: {sender or 'EXTERNAL_POOL'} -> "
                f"BENEFICIARY_ACCOUNT: {beneficiary or 'CASH_WITHDRAWAL'} | "
                f"AMOUNT: ₹{amount_val:,.2f} | DATE: {date or 'N/A'} | "
                f"CHANNEL: {channel} | REF_UTR: {ref or 'N/A'}"
            )
            records.append(formatted_line)

    summary = {
        "total_transactions": len(records),
        "total_volume": sum(beneficiary_inflow.values()),
        "smurfing_flagged_count": len(smurfing_candidates),
        "top_beneficiary_accounts": sorted(beneficiary_inflow.items(), key=lambda x: x[1], reverse=True)[:5],
    }

    full_text = (
        f"=== FINANCIAL INTELLIGENCE & HAWALA AUDIT TRAIL ===\n"
        f"Total Ingested Volume: ₹{summary['total_volume']:,.2f} across {len(records)} records. "
        f"Detected {len(smurfing_candidates)} structured deposits under regulatory thresholds.\n\n"
        + "\n".join(records)
    )

    return full_text, records, summary
