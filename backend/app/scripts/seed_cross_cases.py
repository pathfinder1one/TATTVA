"""Seed rich cross-case criminal network test dataset into MongoDB."""

import asyncio
from datetime import datetime, timezone
from pymongo import AsyncMongoClient
from app.config import get_settings


async def seed():
    settings = get_settings()
    mongo = AsyncMongoClient(settings.mongodb_uri)
    db = mongo[settings.mongodb_database]
    tenant_id = "local-tenant"
    now = datetime.now(timezone.utc).isoformat()

    now_dt = datetime.now(timezone.utc)

    cases = [
        {
            "case_id": "case_2024_023_golden_trident",
            "case_number": "CASE-2024-023",
            "tenant_id": tenant_id,
            "created_by": "local-investigator",
            "title": "Operation Golden Trident: Inter-State Narcotics & Hawala Cartel",
            "crime_type": "NARCOTICS & HAWALA",
            "description": "Cross-border narcotics trafficking syndicate operating via Punjab border and laundering funds via Hawala brokers in Delhi.",
            "status": "active",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
        {
            "case_id": "case_2024_041_delhi_homicide",
            "case_number": "CASE-2024-041",
            "tenant_id": tenant_id,
            "created_by": "local-investigator",
            "title": "South Delhi Real-Estate Homicide: Murder of Rajesh Malhotra",
            "crime_type": "HOMICIDE / CONTRACT KILLING",
            "description": "Real estate developer Rajesh Malhotra fatally stabbed at his Chattarpur farmhouse driveway. Autopsy reveals specialized serrated tactical knife blade.",
            "status": "active",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
        {
            "case_id": "case_2024_055_noida_stabbing",
            "case_number": "CASE-2024-055",
            "tenant_id": tenant_id,
            "created_by": "local-investigator",
            "title": "Noida Sector-128 Cold-Case Double Stabbing",
            "crime_type": "SERIAL HOMICIDE / STABBING",
            "description": "Double homicide at Sector-128 basement parking. Autopsy confirms wound profile matching identical serrated tactical knife used in Delhi homicide.",
            "status": "active",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
        {
            "case_id": "case_2024_088_cyber_syndicate",
            "case_number": "CASE-2024-088",
            "tenant_id": tenant_id,
            "created_by": "local-investigator",
            "title": "Cyber-Syndicate Jamtara-Mewat Phishing Cartel",
            "crime_type": "CYBER CRIME & HAWALA LAUNDERING",
            "description": "Inter-state phishing and digital arrest racket laundering extorted funds via shell bullions.",
            "status": "active",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    ]

    for c in cases:
        await db.cases.replace_one({"case_id": c["case_id"]}, c, upsert=True)
        await db.memberships.replace_one(
            {"case_id": c["case_id"], "tenant_id": tenant_id, "user_id": "local-investigator"},
            {"case_id": c["case_id"], "tenant_id": tenant_id, "user_id": "local-investigator", "role": "lead_investigator", "created_at": now},
            upsert=True
        )

    # Entities for CASE-2024-041
    await db.entities.delete_many({"case_id": "case_2024_041_delhi_homicide"})
    entities_41 = [
        {
            "entity_id": "ent_vikramaditya_041",
            "case_id": "case_2024_041_delhi_homicide",
            "tenant_id": tenant_id,
            "name": "Vikramaditya Singhania",
            "display_name": "Vikramaditya Singhania",
            "entity_type": "PERSON",
            "role": "KINGPIN",
            "risk_level": "CRITICAL",
            "confidence": 0.96,
            "metadata": {
                "notes": "Primary suspect and mastermind. Dispute over 45-acre Gurugram land parcel with victim Rajesh Malhotra.",
                "phone": "+91-98110-44921",
                "vehicle": "Land Cruiser DL-3C-AZ-9901",
            },
        },
        {
            "entity_id": "ent_farhan_041",
            "case_id": "case_2024_041_delhi_homicide",
            "tenant_id": tenant_id,
            "name": "Farhan Qureshi",
            "display_name": "Farhan Qureshi",
            "entity_type": "PERSON",
            "role": "BROKER",
            "risk_level": "HIGH",
            "confidence": 0.92,
            "metadata": {
                "notes": "Hawala operator who arranged contract payment of Rs 25 Lakhs from Al-Madina Trading to local shooters.",
                "phone": "+91-98712-88210",
            },
        },
        {
            "entity_id": "ent_knife_041",
            "case_id": "case_2024_041_delhi_homicide",
            "tenant_id": tenant_id,
            "name": "Japanese Tanto Serrated Tactical Knife (12cm)",
            "display_name": "Japanese Tanto Serrated Tactical Knife (12cm)",
            "entity_type": "WEAPON",
            "role": "EVIDENCE",
            "risk_level": "CRITICAL",
            "confidence": 0.99,
            "metadata": {
                "weapon_type": "KNIFE",
                "blade_length_cm": 12.0,
                "blade_profile": "Tanto Serrated Blade",
                "notch_pattern": "4-Groove Cross-Hilt Serration",
                "fsl_ref": "FSL-KNIFE-092",
            },
        },
        {
            "entity_id": "ent_almadina_041",
            "case_id": "case_2024_041_delhi_homicide",
            "tenant_id": tenant_id,
            "name": "Al-Madina Trading & Bullion Co.",
            "display_name": "Al-Madina Trading & Bullion Co.",
            "entity_type": "ORGANIZATION",
            "role": "SHELL_ENTITY",
            "risk_level": "HIGH",
            "confidence": 0.95,
            "metadata": {"notes": "Chandni Chowk bullion firm used to clear wire funds for contract killing."},
        },
    ]
    await db.entities.insert_many(entities_41)

    # Findings for CASE-2024-041
    await db.findings.delete_many({"case_id": "case_2024_041_delhi_homicide"})
    findings_41 = [
        {
            "finding_id": "find_alibi_vikramaditya_41",
            "case_id": "case_2024_041_delhi_homicide",
            "tenant_id": tenant_id,
            "category": "ALIBI_CONTRADICTION",
            "severity": "CRITICAL",
            "title": "Vikramaditya Singhania Alibi Fabrication vs CDR Tower Ping",
            "statement": "Vikramaditya claimed in police interrogation that he was in Dubai on October 12, but his primary iPhone IMEI was logged pinging Chattarpur and Faridabad toll towers at 22:45 IST on the night of Rajesh Malhotra murder.",
            "entities_involved": ["Vikramaditya Singhania"],
            "created_at": now,
        },
        {
            "finding_id": "find_weapon_41",
            "case_id": "case_2024_041_delhi_homicide",
            "tenant_id": tenant_id,
            "category": "FORENSIC_BALLISTICS",
            "severity": "CRITICAL",
            "title": "Autopsy Weapon Signature: Japanese Tanto Serrated Blade",
            "statement": "Forensic autopsy report DL-41 confirms fatal thoracic puncture caused by a 12cm Japanese Tanto tactical blade with 4-groove micro-serrations.",
            "entities_involved": ["Japanese Tanto Serrated Tactical Knife (12cm)"],
            "created_at": now,
        },
    ]
    await db.findings.insert_many(findings_41)

    # Entities for CASE-2024-055
    await db.entities.delete_many({"case_id": "case_2024_055_noida_stabbing"})
    entities_55 = [
        {
            "entity_id": "ent_vikramaditya_055",
            "case_id": "case_2024_055_noida_stabbing",
            "tenant_id": tenant_id,
            "name": "Vikramaditya Singhania",
            "display_name": "Vikramaditya Singhania",
            "entity_type": "PERSON",
            "role": "KINGPIN",
            "risk_level": "CRITICAL",
            "confidence": 0.94,
            "metadata": {
                "notes": "Identified by ANPR camera driving Land Cruiser DL-3C-AZ-9901 passing Noida Toll 14 minutes before crime.",
                "phone": "+91-98110-44921",
            },
        },
        {
            "entity_id": "ent_knife_055",
            "case_id": "case_2024_055_noida_stabbing",
            "tenant_id": tenant_id,
            "name": "Japanese Tanto Serrated Tactical Knife (12cm)",
            "display_name": "Japanese Tanto Serrated Tactical Knife (12cm)",
            "entity_type": "WEAPON",
            "role": "EVIDENCE",
            "risk_level": "CRITICAL",
            "confidence": 0.98,
            "metadata": {
                "weapon_type": "KNIFE",
                "blade_length_cm": 12.0,
                "blade_profile": "Tanto Serrated Blade",
                "notch_pattern": "4-Groove Cross-Hilt Serration",
                "fsl_ref": "FSL-BLADE-104",
            },
        },
        {
            "entity_id": "ent_vehicle_055",
            "case_id": "case_2024_055_noida_stabbing",
            "tenant_id": tenant_id,
            "name": "Land Cruiser DL-3C-AZ-9901",
            "display_name": "Land Cruiser DL-3C-AZ-9901",
            "entity_type": "VEHICLE",
            "role": "OPERATIVE",
            "risk_level": "HIGH",
            "confidence": 0.96,
            "metadata": {"owner": "Vikramaditya Singhania", "anpr_timestamp": "23:18:00"},
        },
    ]
    await db.entities.insert_many(entities_55)

    # Findings for CASE-2024-055
    await db.findings.delete_many({"case_id": "case_2024_055_noida_stabbing"})
    findings_55 = [
        {
            "finding_id": "find_knife_cross_match_55",
            "case_id": "case_2024_055_noida_stabbing",
            "tenant_id": tenant_id,
            "category": "CROSS_CASE_WEAPON_MATCH",
            "severity": "CRITICAL",
            "title": "Exact Weapon Striation Match with South Delhi Homicide (CASE-2024-041)",
            "statement": "Central Forensic Science Laboratory (CFSL) comparison proves identical 12cm Tanto blade striations and 4-groove serration pitch in both Noida stabbing and South Delhi murder, confirming the same serial contract weapon was used.",
            "entities_involved": ["Japanese Tanto Serrated Tactical Knife (12cm)", "Vikramaditya Singhania"],
            "created_at": now,
        }
    ]
    await db.findings.insert_many(findings_55)

    # Entities for CASE-2024-088
    await db.entities.delete_many({"case_id": "case_2024_088_cyber_syndicate"})
    entities_88 = [
        {
            "entity_id": "ent_almadina_088",
            "case_id": "case_2024_088_cyber_syndicate",
            "tenant_id": tenant_id,
            "name": "Al-Madina Trading & Bullion Co.",
            "display_name": "Al-Madina Trading & Bullion Co.",
            "entity_type": "ORGANIZATION",
            "role": "SHELL_ENTITY",
            "risk_level": "CRITICAL",
            "confidence": 0.97,
            "metadata": {"notes": "Primary money-mule laundering hub where cyber extortion victim funds are converted to gold bullion."},
        },
        {
            "entity_id": "ent_farhan_088",
            "case_id": "case_2024_088_cyber_syndicate",
            "tenant_id": tenant_id,
            "name": "Farhan Qureshi",
            "display_name": "Farhan Qureshi",
            "entity_type": "PERSON",
            "role": "BROKER",
            "risk_level": "HIGH",
            "confidence": 0.93,
            "metadata": {"notes": "Coordinates WhatsApp call-spoofing cashouts with Mewat scam operatives."},
        },
    ]
    await db.entities.insert_many(entities_88)

    print("SUCCESS: 4 Inter-connected cases seeded with cross-case links!")


if __name__ == "__main__":
    asyncio.run(seed())
