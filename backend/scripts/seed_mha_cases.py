"""Seed rich MHA / NCRB criminal cases for Problem Statement #26189."""

import asyncio
from datetime import datetime, timezone
from pymongo import AsyncMongoClient

MONGODB_URI = "mongodb://mongodb:27017"
DB_NAME = "tattva_dev"

async def seed():
    client = AsyncMongoClient(MONGODB_URI)
    db = client[DB_NAME]

    tenant_id = "local-tenant"
    user_id = "local-investigator"
    now = datetime.now(timezone.utc)

    # ══════════════════════════════════════════════════════════════════
    # CASE 23: Operation Golden Trident (Narcotics & Hawala Syndicate)
    # ══════════════════════════════════════════════════════════════════
    case_23_id = "case_2024_023_golden_trident"
    case_23 = {
        "case_id": case_23_id,
        "tenant_id": tenant_id,
        "case_number": "CASE-2024-023",
        "title": "Operation Golden Trident: Inter-State Narcotics & Hawala Cartel",
        "description": "Cross-border multi-tiered criminal syndicate operating narcotics distribution pipelines and structured Hawala money laundering across Punjab, Delhi-NCR, and Mumbai.",
        "created_by": user_id,
        "created_at": now,
        "updated_at": now,
    }

    await db.cases.update_one({"case_id": case_23_id}, {"$set": case_23}, upsert=True)
    await db.case_memberships.update_one(
        {"case_id": case_23_id, "tenant_id": tenant_id, "user_id": user_id},
        {"$set": {"role": "owner", "created_at": now}},
        upsert=True,
    )

    # Case 23 Entities
    entities_23 = [
        {
            "entity_id": "ent_23_vikram",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "entity_type": "person",
            "display_name": "Vikramaditya 'Vikram' Singhania",
            "created_by": user_id,
            "created_at": now,
            "role": "KINGPIN",
            "influence_score": 98,
            "sub_gang_module": "CELL-01 (Apex Command)",
            "evidence_ids": ["ev_fir_114"],
        },
        {
            "entity_id": "ent_23_farhan",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "entity_type": "person",
            "display_name": "Farhan Qureshi",
            "created_by": user_id,
            "created_at": now,
            "role": "BROKER",
            "influence_score": 88,
            "sub_gang_module": "CELL-02 (Hawala & Logistics)",
            "evidence_ids": ["ev_hawala_ledger"],
        },
        {
            "entity_id": "ent_23_garry",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "entity_type": "person",
            "display_name": "Gurpreet 'Garry' Sodhi",
            "created_by": user_id,
            "created_at": now,
            "role": "COORDINATOR",
            "influence_score": 76,
            "sub_gang_module": "CELL-03 (Border Smuggling)",
            "evidence_ids": ["ev_cdr_amritsar"],
        },
        {
            "entity_id": "ent_23_sanjay",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "entity_type": "person",
            "display_name": "Sanjay 'Chhotu' Verma",
            "created_by": user_id,
            "created_at": now,
            "role": "OPERATIVE",
            "influence_score": 42,
            "sub_gang_module": "CELL-04 (Retail Supply)",
            "evidence_ids": ["ev_fir_114"],
        },
        {
            "entity_id": "ent_23_al_madina",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "entity_type": "organization",
            "display_name": "Al-Madina Trading & Bullion Co.",
            "created_by": user_id,
            "created_at": now,
            "role": "SHELL_ENTITY",
            "influence_score": 82,
            "sub_gang_module": "CELL-02 (Hawala & Logistics)",
            "evidence_ids": ["ev_hawala_ledger"],
        },
        {
            "entity_id": "ent_23_burner",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "entity_type": "device",
            "display_name": "Burner IMEI: 864201048829103",
            "created_by": user_id,
            "created_at": now,
            "role": "BURNER_DEVICE",
            "influence_score": 68,
            "sub_gang_module": "CELL-03 (Border Smuggling)",
            "evidence_ids": ["ev_cdr_amritsar"],
        },
        {
            "entity_id": "ent_23_hub",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "entity_type": "location",
            "display_name": "Amritsar Sector-7 Border Hub",
            "created_by": user_id,
            "created_at": now,
            "role": "CRIME_LOCATION",
            "influence_score": 55,
            "sub_gang_module": "CELL-03 (Border Smuggling)",
            "evidence_ids": ["ev_cdr_amritsar"],
        },
    ]

    for ent in entities_23:
        await db.entities.update_one(
            {"entity_id": ent["entity_id"], "case_id": case_23_id},
            {"$set": ent},
            upsert=True,
        )

    # Case 23 Relationships
    relationships_23 = [
        {
            "relationship_id": "rel_23_01",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "subject_entity_id": "ent_23_vikram",
            "predicate": "commands_and_finances",
            "object_entity_id": "ent_23_garry",
            "evidence_ids": ["ev_fir_114"],
            "verification_status": "supported",
            "verification_rationale": "Direct command hierarchy established via intercepted communications.",
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
        {
            "relationship_id": "rel_23_02",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "subject_entity_id": "ent_23_vikram",
            "predicate": "beneficial_owner_of",
            "object_entity_id": "ent_23_al_madina",
            "evidence_ids": ["ev_hawala_ledger"],
            "verification_status": "supported",
            "verification_rationale": "Financial beneficiary logs identify Vikram Singhania.",
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
        {
            "relationship_id": "rel_23_03",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "subject_entity_id": "ent_23_vikram",
            "predicate": "instructs_hawala_channel",
            "object_entity_id": "ent_23_farhan",
            "evidence_ids": ["ev_hawala_ledger"],
            "verification_status": "supported",
            "verification_rationale": "Hawala transaction tokens matched in communication logs.",
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
        {
            "relationship_id": "rel_23_04",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "subject_entity_id": "ent_23_garry",
            "predicate": "coordinates_shipments_to",
            "object_entity_id": "ent_23_farhan",
            "evidence_ids": ["ev_cdr_amritsar"],
            "verification_status": "supported",
            "verification_rationale": "Tower triangulation places both suspect devices at handoff node.",
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
        {
            "relationship_id": "rel_23_05",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "subject_entity_id": "ent_23_farhan",
            "predicate": "supplies_narcotics_to",
            "object_entity_id": "ent_23_sanjay",
            "evidence_ids": ["ev_fir_114"],
            "verification_status": "supported",
            "verification_rationale": "Recovery memo dated Aug 15 matches intercepted consignment lot.",
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
        {
            "relationship_id": "rel_23_06",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "subject_entity_id": "ent_23_garry",
            "predicate": "operates_at_location",
            "object_entity_id": "ent_23_hub",
            "evidence_ids": ["ev_cdr_amritsar"],
            "verification_status": "supported",
            "verification_rationale": "Amritsar Sector-7 tower pings.",
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
        {
            "relationship_id": "rel_23_07",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "subject_entity_id": "ent_23_garry",
            "predicate": "uses_burner_device",
            "object_entity_id": "ent_23_burner",
            "evidence_ids": ["ev_cdr_amritsar"],
            "verification_status": "supported",
            "verification_rationale": "Multiple SIMs active on single hardware IMEI.",
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
    ]

    for rel in relationships_23:
        await db.relationships.update_one(
            {"relationship_id": rel["relationship_id"], "case_id": case_23_id},
            {"$set": rel},
            upsert=True,
        )

    # Case 23 Findings (Contradictions & Anomalies)
    findings_23 = [
        {
            "finding_id": "fnd_23_01",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "finding_type": "contradiction",
            "statement": "Critical Alibi Contradiction: Vikram Singhania's immigration passport stamp claims presence in Dubai on Aug 14, 2024, yet intercepted CDR Tower ID #TR-401 connects his personal phone in Amritsar Sector-7 at 02:14 AM during the consignment drop.",
            "evidence_ids": ["ev_fir_114", "ev_cdr_amritsar"],
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
        {
            "finding_id": "fnd_23_02",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "finding_type": "hawala_structuring",
            "statement": "Hawala Structuring Alert: 18 consecutive NEFT/IMPS transfers of exactly ₹49,200 each were credited to Al-Madina Trading within 4 hours to deliberately circumvent the mandatory ₹50,000 PAN reporting threshold.",
            "evidence_ids": ["ev_hawala_ledger"],
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
        {
            "finding_id": "fnd_23_03",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "finding_type": "burner_phone",
            "statement": "Burner Phone Detection: IMEI 864201048829103 cycled through 5 distinct SIM IMSIs across Punjab, Delhi, and Haryana within 18 days, maintaining active encrypted communications exclusively with Farhan Qureshi.",
            "evidence_ids": ["ev_cdr_amritsar"],
            "review_status": "not_reviewed",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        },
    ]

    for fnd in findings_23:
        await db.findings.update_one(
            {"finding_id": fnd["finding_id"], "case_id": case_23_id},
            {"$set": fnd},
            upsert=True,
        )

    # Case 23 Documents
    docs_23 = [
        {
            "document_id": "doc_23_fir_114",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "filename": "FIR_114_2024_NDPS_SPECIAL_CELL.pdf",
            "status": "indexed",
            "chunk_count": 8,
            "size_bytes": 18420,
            "created_by": user_id,
            "created_at": now,
        },
        {
            "document_id": "doc_23_cdr_dump",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "filename": "CDR_Telecom_Dump_Amritsar_Hub.csv",
            "status": "indexed",
            "chunk_count": 14,
            "size_bytes": 42100,
            "created_by": user_id,
            "created_at": now,
        },
        {
            "document_id": "doc_23_hawala_ledger",
            "case_id": case_23_id,
            "tenant_id": tenant_id,
            "filename": "Hawala_Ledger_Al_Madina_Trading.xlsx",
            "status": "indexed",
            "chunk_count": 6,
            "size_bytes": 15800,
            "created_by": user_id,
            "created_at": now,
        },
    ]

    for doc in docs_23:
        await db.documents.update_one(
            {"document_id": doc["document_id"], "case_id": case_23_id},
            {"$set": doc},
            upsert=True,
        )

    # ══════════════════════════════════════════════════════════════════
    # CASE 88: Jamtara-Mewat Cyber Cartel
    # ══════════════════════════════════════════════════════════════════
    case_88_id = "case_2024_088_cyber_syndicate"
    case_88 = {
        "case_id": case_88_id,
        "tenant_id": tenant_id,
        "case_number": "CASE-2024-088",
        "title": "Cyber-Syndicate Jamtara-Mewat Phishing Cartel",
        "description": "Multi-state organized digital extortion, SIM-swap cloning, and bank mule distribution network targeting senior citizens across 6 states.",
        "created_by": user_id,
        "created_at": now,
        "updated_at": now,
    }

    await db.cases.update_one({"case_id": case_88_id}, {"$set": case_88}, upsert=True)
    await db.case_memberships.update_one(
        {"case_id": case_88_id, "tenant_id": tenant_id, "user_id": user_id},
        {"$set": {"role": "owner", "created_at": now}},
        upsert=True,
    )

    docs_88 = [
        {
            "document_id": "doc_88_mule_accounts",
            "case_id": case_88_id,
            "tenant_id": tenant_id,
            "filename": "Bank_Mule_Account_Trace_Mewat.csv",
            "status": "indexed",
            "chunk_count": 9,
            "size_bytes": 28400,
            "created_by": user_id,
            "created_at": now,
        },
    ]
    for doc in docs_88:
        await db.documents.update_one(
            {"document_id": doc["document_id"], "case_id": case_88_id},
            {"$set": doc},
            upsert=True,
        )

    # Also update Case 1 so it has verified syndicate roles
    await db.entities.update_many(
        {"case_id": "case_0bbea9fdca3b42409d2a5a9ca2c1a719", "display_name": "Apex Holdings LLC"},
        {"$set": {"role": "SHELL_ENTITY", "sub_gang_module": "CELL-01", "influence_score": 75}}
    )
    await db.entities.update_many(
        {"case_id": "case_0bbea9fdca3b42409d2a5a9ca2c1a719", "display_name": "John Doe"},
        {"$set": {"role": "KINGPIN", "sub_gang_module": "CELL-01", "influence_score": 92}}
    )

    print("Successfully seeded CASE-2024-001, CASE-2024-023, and CASE-2024-088 into MongoDB!")

if __name__ == "__main__":
    asyncio.run(seed())
