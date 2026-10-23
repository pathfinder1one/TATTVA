import csv
import json
from pathlib import Path
from typing import Any


def is_cdr_csv(fieldnames: list[str]) -> bool:
    """Heuristic to detect if a CSV represents telecom Call Detail Records (CDR)."""
    normalized = [f.strip().lower().replace(" ", "_") for f in fieldnames if f]
    caller_indicators = {"caller", "calling", "a_party", "calling_number", "caller_msisdn", "source_number", "anumber", "a_num"}
    receiver_indicators = {"called", "receiver", "b_party", "called_number", "dialed_number", "bnumber", "b_num", "destination"}
    
    has_caller = any(any(ind in f for ind in caller_indicators) for f in normalized)
    has_receiver = any(any(ind in f for ind in receiver_indicators) for f in normalized)
    return has_caller and has_receiver


def parse_cdr_file(path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """
    Parses a Call Detail Record (CDR) CSV into structured forensic intelligence text,
    retaining individual records and calculating telecommunications summary metrics.
    """
    records = []
    contact_counter: dict[str, int] = {}
    imei_to_sim: dict[str, set[str]] = {}
    sim_to_imei: dict[str, set[str]] = {}
    night_calls_count = 0

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError("CDR CSV must have a header row.")

        field_map = {}
        for f in reader.fieldnames:
            norm = f.strip().lower().replace(" ", "_")
            if any(k in norm for k in ["calling", "caller", "a_party", "a_num", "source"]):
                field_map["caller"] = f
            elif any(k in norm for k in ["called", "receiver", "b_party", "b_num", "dialed"]):
                field_map["receiver"] = f
            elif any(k in norm for k in ["date", "time", "timestamp"]):
                field_map["timestamp"] = f
            elif any(k in norm for k in ["duration", "dur", "sec"]):
                field_map["duration"] = f
            elif any(k in norm for k in ["imei", "handset", "device"]):
                field_map["imei"] = f
            elif any(k in norm for k in ["imsi"]):
                field_map["imsi"] = f
            elif any(k in norm for k in ["tower", "cell", "cell_id", "cgi", "bts"]):
                field_map["tower"] = f
            elif any(k in norm for k in ["type", "call_type"]):
                field_map["call_type"] = f

        caller_col = field_map.get("caller")
        receiver_col = field_map.get("receiver")
        time_col = field_map.get("timestamp")
        dur_col = field_map.get("duration")
        imei_col = field_map.get("imei")
        imsi_col = field_map.get("imsi")
        tower_col = field_map.get("tower")
        type_col = field_map.get("call_type")

        for row_idx, row in enumerate(reader, start=1):
            caller = (row.get(caller_col) or "").strip()
            receiver = (row.get(receiver_col) or "").strip()
            timestamp = (row.get(time_col) or "").strip()
            duration = (row.get(dur_col) or "0").strip()
            imei = (row.get(imei_col) or "").strip()
            imsi = (row.get(imsi_col) or "").strip()
            tower = (row.get(tower_col) or "").strip()
            call_type = (row.get(type_col) or "VOICE_CALL").strip()

            if not caller or not receiver:
                continue

            # Update contact pairs
            pair = f"{caller} <-> {receiver}"
            contact_counter[pair] = contact_counter.get(pair, 0) + 1

            # Update IMEI / SIM mapping for burner phone detection
            if imei and caller:
                imei_to_sim.setdefault(imei, set()).add(caller)
                sim_to_imei.setdefault(caller, set()).add(imei)

            # Check night calling (between 23:00 and 05:00)
            if any(t in timestamp for t in [" 23:", " 00:", " 01:", " 02:", " 03:", " 04:"]):
                night_calls_count += 1

            formatted_line = (
                f"[TELECOM CDR LOG #{row_idx}] "
                f"CALLER: {caller} | RECEIVER: {receiver} | "
                f"TIMESTAMP: {timestamp or 'N/A'} | DURATION: {duration}s | "
                f"CALL_TYPE: {call_type} | CELL_TOWER_ID: {tower or 'UNKNOWN'} | "
                f"DEVICE_IMEI: {imei or 'UNKNOWN'} | SIM_IMSI: {imsi or 'UNKNOWN'}"
            )
            records.append(formatted_line)

    # Detect burner phone anomalies
    burner_imeis = [imei for imei, sims in imei_to_sim.items() if len(sims) >= 2]
    sim_swaps = [sim for sim, imeis in sim_to_imei.items() if len(imeis) >= 2]

    telecom_summary = {
        "total_calls": len(records),
        "unique_contact_pairs": len(contact_counter),
        "night_calls_count": night_calls_count,
        "suspicious_burner_imeis": burner_imeis,
        "sim_swapping_numbers": sim_swaps,
        "top_frequent_contacts": sorted(contact_counter.items(), key=lambda x: x[1], reverse=True)[:5],
    }

    full_text = (
        f"=== TELECOMMUNICATIONS CALL DETAIL RECORD (CDR) FORENSIC DUMP ===\n"
        f"Summary: {len(records)} calls recorded. "
        f"Detected {len(burner_imeis)} potential burner devices (multiple SIMs per IMEI) "
        f"and {len(sim_swaps)} SIMs swapped across multiple devices.\n\n"
        + "\n".join(records)
    )

    return full_text, records, telecom_summary
