from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING

from pibody_match.audit.trail import AuditRecord
from pibody_match.domain.constraints import HumanDecision
from pibody_match.domain.opportunities import Opportunity
from pibody_match.domain.profiles import Profile
from pibody_match.domain.skills import SeniorityLevel, SkillClaim, SkillRequirement
from pibody_match.domain.universal import Capability, EntityKind, Universe, UserEntity

if TYPE_CHECKING:
    from pathlib import Path


class SqliteMatchRepository:
    """Persistance SQLite locale pour profils, opportunites, entites universelles et audits."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    profile_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS opportunities (
                    opportunity_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS universal_entities (
                    entity_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS consent_logs (
                    consent_id TEXT PRIMARY KEY,
                    accepted INTEGER NOT NULL,
                    scope TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS consent_logs (
                    consent_id TEXT PRIMARY KEY,
                    accepted INTEGER NOT NULL,
                    scope TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    match_id TEXT NOT NULL,
                    profile_id TEXT NOT NULL,
                    opportunity_id TEXT NOT NULL,
                    total_score REAL NOT NULL,
                    weights_snapshot TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reviewer_note TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL
                );
                """
            )

    def save_profile(self, profile: Profile) -> None:
        data = {
            "profile_id": profile.profile_id,
            "display_name": profile.display_name,
            "headline": profile.headline,
            "seniority": profile.seniority.value,
            "objectives_text": profile.objectives_text,
            "total_experience_years": profile.total_experience_years,
            "availability_ratio": profile.availability_ratio,
            "public_tags": list(profile.public_tags),
            "skills": [
                {
                    "skill_id": s.skill_id,
                    "raw_name": s.raw_name,
                    "canonical_name": s.canonical_name,
                    "family": s.family,
                    "proficiency": s.proficiency,
                    "years_experience": s.years_experience,
                    "verified": s.verified,
                }
                for s in profile.skills
            ],
        }
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO profiles (profile_id, payload) VALUES (?, ?)",
                (profile.profile_id, json.dumps(data, ensure_ascii=False)),
            )

    def list_profiles(self) -> list[Profile]:
        rows = self._conn.execute("SELECT payload FROM profiles ORDER BY profile_id").fetchall()
        result: list[Profile] = []
        for row in rows:
            d = json.loads(row["payload"])
            result.append(
                Profile(
                    profile_id=d["profile_id"],
                    display_name=d["display_name"],
                    headline=d["headline"],
                    seniority=SeniorityLevel(d["seniority"]),
                    skills=tuple(
                        SkillClaim(
                            raw_name=s.get("raw_name", s["canonical_name"]),
                            **{k: v for k, v in s.items() if k != "raw_name"},
                        )
                        for s in d["skills"]
                    ),
                    objectives_text=d["objectives_text"],
                    total_experience_years=d["total_experience_years"],
                    availability_ratio=d["availability_ratio"],
                    public_tags=tuple(d["public_tags"]),
                )
            )
        return result

    def save_opportunity(self, opp: Opportunity) -> None:
        pref = opp.preferred_seniority.value if opp.preferred_seniority else None
        data = {
            "opportunity_id": opp.opportunity_id,
            "title": opp.title,
            "organization": opp.organization,
            "description_text": opp.description_text,
            "objectives_text": opp.objectives_text,
            "min_total_experience": opp.min_total_experience,
            "preferred_seniority": pref,
            "capacity": opp.capacity,
            "domain_tags": list(opp.domain_tags),
            "requirements": [
                {
                    "skill_id": r.skill_id,
                    "canonical_name": r.canonical_name,
                    "family": r.family,
                    "min_proficiency": r.min_proficiency,
                    "min_years": r.min_years,
                    "weight": r.weight,
                    "mandatory": r.mandatory,
                }
                for r in opp.requirements
            ],
        }
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO opportunities (opportunity_id, payload) VALUES (?, ?)",
                (opp.opportunity_id, json.dumps(data, ensure_ascii=False)),
            )

    def list_opportunities(self) -> list[Opportunity]:
        rows = self._conn.execute(
            "SELECT payload FROM opportunities ORDER BY opportunity_id"
        ).fetchall()
        result: list[Opportunity] = []
        for row in rows:
            d = json.loads(row["payload"])
            pref = (
                SeniorityLevel(d["preferred_seniority"]) if d.get("preferred_seniority") else None
            )
            result.append(
                Opportunity(
                    opportunity_id=d["opportunity_id"],
                    title=d["title"],
                    organization=d["organization"],
                    description_text=d["description_text"],
                    objectives_text=d["objectives_text"],
                    requirements=tuple(SkillRequirement(**r) for r in d["requirements"]),
                    min_total_experience=d["min_total_experience"],
                    preferred_seniority=pref,
                    capacity=d["capacity"],
                    domain_tags=tuple(d["domain_tags"]),
                )
            )
        return result

    def save_universal_entity(self, entity: UserEntity) -> None:
        data = {
            "entity_id": entity.entity_id,
            "name": entity.name,
            "kind": entity.kind.value,
            "universe": entity.universe.value,
            "headline": entity.headline,
            "bio_and_goals": entity.bio_and_goals,
            "experience_years": entity.experience_years,
            "availability_hours_week": entity.availability_hours_week,
            "open_to_mentor": entity.open_to_mentor,
            "open_to_collaborate": entity.open_to_collaborate,
            "verified": entity.verified,
            "capabilities": [
                {
                    "skill_id": c.skill_id,
                    "canonical_name": c.canonical_name,
                    "family": c.family,
                    "level": c.level,
                    "years": c.years,
                    "can_teach": c.can_teach,
                }
                for c in entity.capabilities
            ],
        }
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO universal_entities (entity_id, payload) VALUES (?, ?)",
                (entity.entity_id, json.dumps(data, ensure_ascii=False)),
            )

    def list_universal_entities(self) -> list[UserEntity]:
        rows = self._conn.execute(
            "SELECT payload FROM universal_entities ORDER BY entity_id"
        ).fetchall()
        result: list[UserEntity] = []
        for row in rows:
            d = json.loads(row["payload"])
            result.append(
                UserEntity(
                    entity_id=d["entity_id"],
                    name=d["name"],
                    kind=EntityKind(d["kind"]),
                    universe=Universe(d["universe"]),
                    headline=d["headline"],
                    bio_and_goals=d["bio_and_goals"],
                    capabilities=tuple(Capability(**c) for c in d["capabilities"]),
                    experience_years=d["experience_years"],
                    availability_hours_week=d["availability_hours_week"],
                    open_to_mentor=d["open_to_mentor"],
                    open_to_collaborate=d["open_to_collaborate"],
                    verified=d.get("verified", True),
                )
            )
        return result

    def clear_all(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                DELETE FROM profiles;
                DELETE FROM opportunities;
                DELETE FROM universal_entities;
                DELETE FROM audit_logs;
                """
            )

    def save_audit(self, record: AuditRecord) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO audit_logs (
                    audit_id, match_id, profile_id, opportunity_id, total_score,
                    weights_snapshot, decision, reviewer_note, timestamp_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.match_id,
                    record.profile_id,
                    record.opportunity_id,
                    record.total_score,
                    json.dumps(record.weights_snapshot, ensure_ascii=False),
                    record.decision.value,
                    record.reviewer_note,
                    record.timestamp_utc,
                ),
            )

    def list_audits(self) -> list[AuditRecord]:
        rows = self._conn.execute("SELECT * FROM audit_logs ORDER BY timestamp_utc").fetchall()
        return [
            AuditRecord(
                audit_id=row["audit_id"],
                match_id=row["match_id"],
                profile_id=row["profile_id"],
                opportunity_id=row["opportunity_id"],
                total_score=row["total_score"],
                weights_snapshot=json.loads(row["weights_snapshot"]),
                decision=HumanDecision(row["decision"]),
                reviewer_note=row["reviewer_note"],
                timestamp_utc=row["timestamp_utc"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()

    def record_consent(
        self, consent_id: str, accepted: bool, scope: str, timestamp_utc: str
    ) -> None:
        with self._conn:
            self._conn.execute(
                (
                    "INSERT OR REPLACE INTO consent_logs "
                    "(consent_id, accepted, scope, timestamp_utc) VALUES (?, ?, ?, ?)"
                ),
                (consent_id, 1 if accepted else 0, scope, timestamp_utc),
            )

    def get_latest_consent(self) -> dict[str, object] | None:
        row = self._conn.execute(
            "SELECT consent_id, accepted, scope, timestamp_utc "
            "FROM consent_logs ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return {
            "consent_id": str(row["consent_id"]),
            "accepted": bool(row["accepted"]),
            "scope": str(row["scope"]),
            "timestamp_utc": str(row["timestamp_utc"]),
        }
