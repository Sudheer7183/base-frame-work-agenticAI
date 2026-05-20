"""
WC Audit Tables — Drop & Recreate Migration (v2)
=================================================
Drops the old tables (which used Postgres enum types that caused insertion
errors) and recreates them with plain VARCHAR columns.

Key changes from v1:
  • NO custom enum types — status, source, root_cause, recommendation are
    all VARCHAR.  Values are validated in Python, not in the DB.
  • wc_audit_cases.audit_reference (NOT NULL UNIQUE) is now present.
  • wc_policy_class_codes uses policy_id (INTEGER FK), not policy_number.
  • wc_payroll_records uses audit_case_id (INTEGER FK) as the parent key.
  • All constraints match exactly what db_persistence.py sends.

Usage:
    # All active tenants
    python scripts/create_wc_tables.py

    # Single tenant only
    python scripts/create_wc_tables.py tenant_demo

    # Force drop+recreate even if tables exist
    python scripts/create_wc_tables.py tenant_demo --force
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text

# ── Config ──────────────────────────────────────────────────────────────────
DB_URL      = "postgresql://postgres:postgres@localhost:5433/agenticbase2"
WC_REVISION = "wc_v2_varchar_20260319"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

FORCE = "--force" in sys.argv


# ── Drop old tables + old enum types ────────────────────────────────────────

def sql_drop_old(schema: str) -> str:
    """Drop the 9 WC tables and any stale enum types. Fully idempotent."""
    return f"""
        -- Drop tables in reverse FK order so constraints don't block
        DROP TABLE IF EXISTS {schema}.wc_audit_reports      CASCADE;
        DROP TABLE IF EXISTS {schema}.wc_hitl_reviews       CASCADE;
        DROP TABLE IF EXISTS {schema}.wc_agent_findings     CASCADE;
        DROP TABLE IF EXISTS {schema}.wc_variance_lines     CASCADE;
        DROP TABLE IF EXISTS {schema}.wc_payroll_records    CASCADE;
        DROP TABLE IF EXISTS {schema}.wc_audit_cases        CASCADE;
        DROP TABLE IF EXISTS {schema}.wc_policy_class_codes CASCADE;
        DROP TABLE IF EXISTS {schema}.wc_policy_officers    CASCADE;
        DROP TABLE IF EXISTS {schema}.wc_policies           CASCADE;

        -- Drop old enum types that caused "invalid input value for enum" errors
        DROP TYPE IF EXISTS {schema}.audit_status_enum   CASCADE;
        DROP TYPE IF EXISTS {schema}.variance_root_cause CASCADE;
        DROP TYPE IF EXISTS {schema}.recommendation_enum CASCADE;
        DROP TYPE IF EXISTS {schema}.data_source_enum    CASCADE;
    """


# ── Create tables ────────────────────────────────────────────────────────────

def sql_create_tables(schema: str) -> str:
    """
    Create all 9 WC tables with plain VARCHAR for all categorical fields.
    No Postgres enum types — no ALTER TYPE needed ever again.
    """
    return f"""

    -- ── 1. wc_policies ────────────────────────────────────────────────────
    CREATE TABLE {schema}.wc_policies (
        id                SERIAL          PRIMARY KEY,
        policy_number     VARCHAR(50)     NOT NULL UNIQUE,
        insured_name      VARCHAR(255)    NOT NULL,
        effective_date    DATE            NOT NULL,
        expiration_date   DATE            NOT NULL,
        estimated_premium NUMERIC(15,2)   DEFAULT 0.0,
        payroll_frequency VARCHAR(10)     DEFAULT '1W',
        state_code        VARCHAR(5)      NOT NULL,
        carrier_name      VARCHAR(255),
        broker_name       VARCHAR(255),
        is_active         BOOLEAN         DEFAULT TRUE,
        created_at        TIMESTAMP       DEFAULT now(),
        updated_at        TIMESTAMP       DEFAULT now()
    );
    CREATE INDEX ix_wc_policies_policy_number ON {schema}.wc_policies (policy_number);

    -- ── 2. wc_policy_class_codes ──────────────────────────────────────────
    -- FK: policy_id → wc_policies.id  (NOT policy_number string)
    CREATE TABLE {schema}.wc_policy_class_codes (
        id                  SERIAL          PRIMARY KEY,
        policy_id           INTEGER         NOT NULL
            REFERENCES {schema}.wc_policies(id) ON DELETE CASCADE,
        class_code          VARCHAR(10)     NOT NULL,
        class_desc          VARCHAR(255),
        state_code          VARCHAR(5)      NOT NULL,
        composite_rate      NUMERIC(10,6)   DEFAULT 0.0,
        exposure            NUMERIC(15,2)   DEFAULT 0.0,
        est_premium         NUMERIC(15,2)   DEFAULT 0.0,
        est_cc_premium      NUMERIC(15,2)   DEFAULT 0.0,
        endorsement_version VARCHAR(10)     DEFAULT 'V1',
        created_at          TIMESTAMP       DEFAULT now()
    );

    -- ── 3. wc_policy_officers ─────────────────────────────────────────────
    CREATE TABLE {schema}.wc_policy_officers (
        id            SERIAL          PRIMARY KEY,
        policy_id     INTEGER         NOT NULL
            REFERENCES {schema}.wc_policies(id) ON DELETE CASCADE,
        officer_name  VARCHAR(255)    NOT NULL,
        title         VARCHAR(100),
        is_on_payroll BOOLEAN         DEFAULT TRUE,
        ownership_pct NUMERIC(5,2)    DEFAULT 0.0,
        state_code    VARCHAR(5),
        created_at    TIMESTAMP       DEFAULT now()
    );

    -- ── 4. wc_audit_cases ─────────────────────────────────────────────────
    -- audit_reference: stable unique key generated as "WCA-{{policy}}-{{id}}"
    -- status: plain VARCHAR — pending|ingesting|processing|review|approved|completed|rejected
    -- recommendation: plain VARCHAR — refund|additional_premium|clarification|no_action
    CREATE TABLE {schema}.wc_audit_cases (
        id                    SERIAL          PRIMARY KEY,
        policy_id             INTEGER         NOT NULL
            REFERENCES {schema}.wc_policies(id) ON DELETE CASCADE,
        audit_reference       VARCHAR(150)    NOT NULL UNIQUE,
        status                VARCHAR(30)     DEFAULT 'pending',
        audit_period_start    DATE,
        audit_period_end      DATE,
        first_check_date      DATE,
        last_check_date       DATE,
        expected_submissions  FLOAT           DEFAULT 0.0,
        actual_submissions    FLOAT           DEFAULT 0.0,
        submitted_count       INTEGER         DEFAULT 0,
        total_earned_exposure NUMERIC(15,2)   DEFAULT 0.0,
        total_earned_premium  NUMERIC(15,2)   DEFAULT 0.0,
        total_est_exposure    NUMERIC(15,2)   DEFAULT 0.0,
        total_cc_premium    NUMERIC(15,2)   DEFAULT 0.0,
        total_est_ytd_premium NUMERIC(15,2)   DEFAULT 0.0,
        total_variance        NUMERIC(15,2)   DEFAULT 0.0,
        total_variance_pct    NUMERIC(8,4)    DEFAULT 0.0,
        ai_narrative          TEXT,
        risk_level            VARCHAR(20)     DEFAULT 'low',
        recommendation        VARCHAR(30),
        hitl_required         BOOLEAN         DEFAULT FALSE,
        hitl_approved_by      VARCHAR(255),
        hitl_notes            TEXT,
        hitl_approved_at      TIMESTAMP,
        auditor_override      BOOLEAN         DEFAULT FALSE,
        auditor_notes         TEXT,
        auditor_id            VARCHAR(100),
        payroll_file_path     VARCHAR(500),
        policy_xml_path       VARCHAR(500),
        audit_meta_file_path  VARCHAR(500),
        created_at            TIMESTAMP       DEFAULT now(),
        updated_at            TIMESTAMP       DEFAULT now(),
        completed_at          TIMESTAMP
    );
    CREATE INDEX ix_wc_audit_cases_policy_id      ON {schema}.wc_audit_cases (policy_id);
    CREATE INDEX ix_wc_audit_cases_audit_reference ON {schema}.wc_audit_cases (audit_reference);
    CREATE INDEX ix_wc_audit_cases_status          ON {schema}.wc_audit_cases (status);

    -- ── 5. wc_payroll_records ─────────────────────────────────────────────
    -- FK: audit_case_id → wc_audit_cases.id  (NOT NULL)
    -- source: plain VARCHAR — insured|payroll_provider|policy_config
    CREATE TABLE {schema}.wc_payroll_records (
        id             SERIAL          PRIMARY KEY,
        audit_case_id  INTEGER         NOT NULL
            REFERENCES {schema}.wc_audit_cases(id) ON DELETE CASCADE,
        source         VARCHAR(30)     NOT NULL DEFAULT 'insured',
        client_name    VARCHAR(255),
        policy_number  VARCHAR(50),
        check_date     DATE,
        ee_no          VARCHAR(50),
        employee_name  VARCHAR(255),
        state_code     VARCHAR(5),
        class_code     VARCHAR(10),
        wages          NUMERIC(15,2)   DEFAULT 0.0,
        overtime_pay   NUMERIC(15,2)   DEFAULT 0.0,
        double_time    NUMERIC(15,2)   DEFAULT 0.0,
        tips           NUMERIC(15,2)   DEFAULT 0.0,
        net_pay        NUMERIC(15,2)   DEFAULT 0.0,
        exposure       NUMERIC(15,2)   DEFAULT 0.0,
        net_rate       NUMERIC(10,6)   DEFAULT 0.0,
        earned_premium NUMERIC(15,2)   DEFAULT 0.0,
        census_rate    NUMERIC(10,6)   DEFAULT 0.0,
        census_premium NUMERIC(15,2)   DEFAULT 0.0,
        pol_eff_date   DATE,
        process_date   DATE,
        created_at     TIMESTAMP       DEFAULT now()
    );
    CREATE INDEX ix_wc_payroll_records_case  ON {schema}.wc_payroll_records (audit_case_id);
    CREATE INDEX ix_wc_payroll_records_date  ON {schema}.wc_payroll_records (check_date);

    -- ── 6. wc_variance_lines ──────────────────────────────────────────────
    -- root_cause: plain VARCHAR — officer_mismatch|class_code_mismatch|
    --             frequency_gap|payroll_variance|rate_discrepancy|none
    CREATE TABLE {schema}.wc_variance_lines (
        id                SERIAL          PRIMARY KEY,
        audit_case_id     INTEGER         NOT NULL
            REFERENCES {schema}.wc_audit_cases(id) ON DELETE CASCADE,
        policy_number     VARCHAR(50),
        state_code        VARCHAR(5),
        class_code        VARCHAR(10),
        class_desc        VARCHAR(255),
        earned_exposure   NUMERIC(15,2)   DEFAULT 0.0,
        earned_premium    NUMERIC(15,2)   DEFAULT 0.0,
        est_exposure      NUMERIC(15,2)   DEFAULT 0.0,
        est_ytd_premium   NUMERIC(15,2)   DEFAULT 0.0,
        variance          NUMERIC(15,2)   DEFAULT 0.0,
        variance_pct      NUMERIC(8,4)    DEFAULT 0.0,
        root_cause        VARCHAR(30)     DEFAULT 'none',
        root_cause_detail TEXT,
        is_flagged        BOOLEAN         DEFAULT FALSE,
        flag_reason       TEXT,
        created_at        TIMESTAMP       DEFAULT now()
    );
    CREATE INDEX ix_wc_variance_lines_case ON {schema}.wc_variance_lines (audit_case_id);

    -- ── 7. wc_agent_findings ──────────────────────────────────────────────
    -- agent_name: NOT NULL — OfficerAgent|ClassCodeAgent|FrequencyAgent
    -- severity: info|warning|critical
    CREATE TABLE {schema}.wc_agent_findings (
        id            SERIAL          PRIMARY KEY,
        audit_case_id INTEGER         NOT NULL
            REFERENCES {schema}.wc_audit_cases(id) ON DELETE CASCADE,
        agent_name    VARCHAR(100)    NOT NULL,
        finding_type  VARCHAR(100),
        severity      VARCHAR(20)     DEFAULT 'info',
        summary       TEXT,
        detail        JSONB,
        evidence_ref  TEXT,
        created_at    TIMESTAMP       DEFAULT now()
    );
    CREATE INDEX ix_wc_agent_findings_case ON {schema}.wc_agent_findings (audit_case_id);

    -- ── 8. wc_hitl_reviews ────────────────────────────────────────────────
    -- action: approve|reject|override|request_info|pending
    -- No status/risk_level columns — those live on wc_audit_cases
    CREATE TABLE {schema}.wc_hitl_reviews (
        id            SERIAL          PRIMARY KEY,
        audit_case_id INTEGER         NOT NULL
            REFERENCES {schema}.wc_audit_cases(id) ON DELETE CASCADE,
        reviewer_id   VARCHAR(100),
        reviewer_name VARCHAR(255),
        action        VARCHAR(50),
        notes         TEXT,
        override_data JSONB,
        reviewed_at   TIMESTAMP       DEFAULT now()
    );
    CREATE INDEX ix_wc_hitl_reviews_case ON {schema}.wc_hitl_reviews (audit_case_id);

    -- ── 9. wc_audit_reports ───────────────────────────────────────────────
    -- audit_case_id UNIQUE — one report per case
    CREATE TABLE {schema}.wc_audit_reports (
        id            SERIAL          PRIMARY KEY,
        audit_case_id INTEGER         NOT NULL UNIQUE
            REFERENCES {schema}.wc_audit_cases(id) ON DELETE CASCADE,
        report_ref    VARCHAR(150)    UNIQUE,
        generated_at  TIMESTAMP       DEFAULT now(),
        report_json   JSONB,
        report_file   VARCHAR(500),
        summary       TEXT,
        is_final      BOOLEAN         DEFAULT FALSE
    );
    """


# ── Migration logic ──────────────────────────────────────────────────────────

def tables_exist(conn, schema: str) -> bool:
    row = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :s AND table_name = 'wc_policies'
        )
    """), {"s": schema}).fetchone()
    return row and row[0]


def stamp_version(conn, schema: str) -> None:
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {schema}.alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        )
    """))
    existing = conn.execute(
        text(f"SELECT version_num FROM {schema}.alembic_version")
    ).fetchall()
    if existing:
        conn.execute(
            text(f"UPDATE {schema}.alembic_version SET version_num = :v"),
            {"v": WC_REVISION}
        )
    else:
        conn.execute(
            text(f"INSERT INTO {schema}.alembic_version (version_num) VALUES (:v)"),
            {"v": WC_REVISION}
        )


def migrate_schema(conn, schema: str) -> None:
    log.info(f"  → {schema}")
    already = tables_exist(conn, schema)

    if already and not FORCE:
        log.info(f"  ✓ Tables already exist in {schema}. Use --force to drop+recreate.")
        stamp_version(conn, schema)
        return

    if already and FORCE:
        log.info(f"  ⚠ --force: dropping old tables + enums in {schema}...")
        conn.execute(text(sql_drop_old(schema)))
        log.info(f"  ✓ Dropped.")

    log.info(f"  Creating 9 WC tables (v2 VARCHAR) in {schema}...")
    conn.execute(text(sql_create_tables(schema)))
    stamp_version(conn, schema)
    log.info(f"  ✅ {schema} done.")


def verify(conn, schema: str) -> None:
    rows = conn.execute(text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = :s AND table_name LIKE 'wc_%'
        ORDER BY table_name
    """), {"s": schema}).fetchall()
    names = [r[0] for r in rows]
    log.info(f"  {schema}: {len(names)} tables — {', '.join(names)}")


def get_tenants(conn) -> list:
    try:
        rows = conn.execute(text(
            "SELECT schema_name FROM public.tenants WHERE status = 'active' ORDER BY schema_name"
        )).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    # Parse CLI args (skip --force)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = args[0] if args else None

    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        schemas = [target] if target else get_tenants(conn)

        if not schemas:
            log.warning("No schemas found. Pass a schema name as argument.")
            log.info("  Example: python scripts/create_wc_tables.py tenant_demo --force")
            return

        force_note = " (--force: DROP+RECREATE)" if FORCE else ""
        log.info("=" * 60)
        log.info(f"WC Tables Migration v2{force_note}")
        log.info(f"Schemas: {schemas}")
        log.info("=" * 60)

        ok, fail = [], []
        for schema in schemas:
            try:
                migrate_schema(conn, schema)
                ok.append(schema)
            except Exception as e:
                log.error(f"  ❌ {schema}: {e}")
                fail.append(schema)

        log.info("\n" + "=" * 60)
        log.info("VERIFICATION")
        log.info("=" * 60)
        for schema in ok:
            verify(conn, schema)

        log.info("\n" + "=" * 60)
        log.info(f"✅ Success: {ok}")
        if fail:
            log.error(f"❌ Failed:  {fail}")
        log.info("=" * 60)


if __name__ == "__main__":
    main()