"""wc_audit_tables

Revision ID: ff795386972a
Revises: 1db463364947
Create Date: 2026-03-16 05:24:08.981528

"""
from typing import Sequence, Union

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ff795386972a'
down_revision: Union[str, None] = '57ec5ea850a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _schema() -> str:
    return context.get_context().version_table_schema or "public"
 
 
def _create_enum_if_not_exists(conn, schema: str, type_name: str, values: list) -> None:
    """Idempotently create a PostgreSQL ENUM type via raw SQL."""
    values_sql = ", ".join(f"'{v}'" for v in values)
    conn.execute(sa.text(f"""
        DO $$ BEGIN
            CREATE TYPE {schema}.{type_name} AS ENUM ({values_sql});
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
 
 
def _cast_column_to_enum(
    conn,
    schema: str,
    table: str,
    column: str,
    type_name: str,
    restore_default: str = None,   # e.g. "pending"  →  sets default back as enum literal
) -> None:
    """
    Safely change a VARCHAR column to a PostgreSQL ENUM column.
 
    PostgreSQL raises DatatypeMismatch if the column still carries a string
    server_default when ALTER COLUMN TYPE is run, because it cannot
    automatically cast the default expression.  We must:
      1. Drop the default
      2. Alter the column type with an explicit USING cast
      3. Restore the default (now typed as the enum)
    """
    fq_type = f"{schema}.{type_name}"
 
    # Step 1 – remove the default so the ALTER TYPE can succeed
    conn.execute(sa.text(
        f"ALTER TABLE {schema}.{table} ALTER COLUMN {column} DROP DEFAULT;"
    ))
 
    # Step 2 – change the column type; USING clause handles existing row data
    conn.execute(sa.text(
        f"ALTER TABLE {schema}.{table} "
        f"ALTER COLUMN {column} TYPE {fq_type} "
        f"USING {column}::{fq_type};"
    ))
 
    # Step 3 – restore the default, now cast to the enum type
    if restore_default is not None:
        conn.execute(sa.text(
            f"ALTER TABLE {schema}.{table} "
            f"ALTER COLUMN {column} SET DEFAULT '{restore_default}'::{fq_type};"
        ))
 
 
# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------
 
def upgrade() -> None:
    schema = _schema()
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = inspector.get_table_names(schema=schema)
 
    print(f"[wc_audit_001] Running upgrade for schema: {schema}")
 
    # -----------------------------------------------------------------------
    # Step 1 – Create all ENUM types idempotently BEFORE creating any table.
    # -----------------------------------------------------------------------
    _create_enum_if_not_exists(conn, schema, "audit_status_enum", [
        "pending", "ingesting", "processing", "review",
        "approved", "completed", "rejected",
    ])
    _create_enum_if_not_exists(conn, schema, "variance_root_cause", [
        "officer_mismatch", "class_code_mismatch", "frequency_gap",
        "payroll_variance", "rate_discrepancy", "none",
    ])
    _create_enum_if_not_exists(conn, schema, "recommendation_enum", [
        "refund", "additional_premium", "clarification", "no_action",
    ])
    _create_enum_if_not_exists(conn, schema, "data_source_enum", [
        "insured", "payroll_provider", "policy_config",
    ])
 
    # -----------------------------------------------------------------------
    # 1. wc_policies  (no enum columns)
    # -----------------------------------------------------------------------
    if "wc_policies" not in existing:
        print(f"[wc_audit_001] Creating wc_policies in {schema}")
        op.create_table(
            "wc_policies",
            sa.Column("id",                sa.Integer(),      nullable=False),
            sa.Column("policy_number",     sa.String(50),     nullable=False),
            sa.Column("insured_name",      sa.String(255),    nullable=False),
            sa.Column("effective_date",    sa.Date(),         nullable=False),
            sa.Column("expiration_date",   sa.Date(),         nullable=False),
            sa.Column("estimated_premium", sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("payroll_frequency", sa.String(10),     server_default="1W"),
            sa.Column("state_code",        sa.String(5),      nullable=False),
            sa.Column("carrier_name",      sa.String(255)),
            sa.Column("broker_name",       sa.String(255)),
            sa.Column("is_active",         sa.Boolean(),      server_default=sa.text("true")),
            sa.Column("created_at",        sa.DateTime(),     server_default=sa.text("now()")),
            sa.Column("updated_at",        sa.DateTime(),     server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("policy_number", name="uq_wc_policies_policy_number"),
            schema=schema,
        )
        op.create_index("ix_wc_policies_id",            "wc_policies", ["id"],            schema=schema)
        op.create_index("ix_wc_policies_policy_number", "wc_policies", ["policy_number"], schema=schema)
 
    # -----------------------------------------------------------------------
    # 2. wc_policy_class_codes  (no enum columns)
    # -----------------------------------------------------------------------
    if "wc_policy_class_codes" not in existing:
        print(f"[wc_audit_001] Creating wc_policy_class_codes in {schema}")
        op.create_table(
            "wc_policy_class_codes",
            sa.Column("id",                  sa.Integer(),      nullable=False),
            sa.Column("policy_id",           sa.Integer(),      nullable=False),
            sa.Column("class_code",          sa.String(10),     nullable=False),
            sa.Column("class_desc",          sa.String(255)),
            sa.Column("state_code",          sa.String(5),      nullable=False),
            sa.Column("composite_rate",      sa.Numeric(10, 6), server_default="0.0"),
            sa.Column("exposure",            sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("est_premium",         sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("est_cc_premium",      sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("endorsement_version", sa.String(10),     server_default="V1"),
            sa.Column("created_at",          sa.DateTime(),     server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(
                ["policy_id"], [f"{schema}.wc_policies.id"],
                name="fk_wc_policy_class_codes_policy_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index("ix_wc_policy_class_codes_id", "wc_policy_class_codes", ["id"], schema=schema)
 
    # -----------------------------------------------------------------------
    # 3. wc_policy_officers  (no enum columns)
    # -----------------------------------------------------------------------
    if "wc_policy_officers" not in existing:
        print(f"[wc_audit_001] Creating wc_policy_officers in {schema}")
        op.create_table(
            "wc_policy_officers",
            sa.Column("id",            sa.Integer(),     nullable=False),
            sa.Column("policy_id",     sa.Integer(),     nullable=False),
            sa.Column("officer_name",  sa.String(255),   nullable=False),
            sa.Column("title",         sa.String(100)),
            sa.Column("is_on_payroll", sa.Boolean(),     server_default=sa.text("true")),
            sa.Column("ownership_pct", sa.Numeric(5, 2), server_default="0.0"),
            sa.Column("state_code",    sa.String(5)),
            sa.Column("created_at",    sa.DateTime(),    server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(
                ["policy_id"], [f"{schema}.wc_policies.id"],
                name="fk_wc_policy_officers_policy_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index("ix_wc_policy_officers_id", "wc_policy_officers", ["id"], schema=schema)
 
    # -----------------------------------------------------------------------
    # 4. wc_audit_cases  — enum columns: status, recommendation
    #    Declared as String() first; converted to enum via 3-step ALTER below.
    # -----------------------------------------------------------------------
    if "wc_audit_cases" not in existing:
        print(f"[wc_audit_001] Creating wc_audit_cases in {schema}")
        op.create_table(
            "wc_audit_cases",
            sa.Column("id",                    sa.Integer(),      nullable=False),
            sa.Column("policy_id",             sa.Integer(),      nullable=False),
            sa.Column("audit_reference",       sa.String(100),    nullable=False),
            # ↓ declared as String — converted to enum AFTER table creation
            sa.Column("status",                sa.String(20),     server_default="pending"),
            sa.Column("audit_period_start",    sa.Date()),
            sa.Column("audit_period_end",      sa.Date()),
            sa.Column("first_check_date",      sa.Date()),
            sa.Column("last_check_date",       sa.Date()),
            sa.Column("expected_submissions",  sa.Float(),        server_default="0.0"),
            sa.Column("actual_submissions",    sa.Float(),        server_default="0.0"),
            sa.Column("submitted_count",       sa.Integer(),      server_default="0"),
            sa.Column("total_earned_exposure", sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("total_earned_premium",  sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("total_est_exposure",    sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("total_est_ytd_premium", sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("total_variance",        sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("total_variance_pct",    sa.Numeric(8, 4),  server_default="0.0"),
            sa.Column("ai_narrative",          sa.Text()),
            sa.Column("risk_level",            sa.String(20),     server_default="low"),
            # ↓ declared as String — converted to enum AFTER table creation
            sa.Column("recommendation",        sa.String(30)),
            sa.Column("hitl_required",         sa.Boolean(),      server_default=sa.text("false")),
            sa.Column("hitl_approved_by",      sa.String(255)),
            sa.Column("hitl_notes",            sa.Text()),
            sa.Column("hitl_approved_at",      sa.DateTime()),
            sa.Column("auditor_override",      sa.Boolean(),      server_default=sa.text("false")),
            sa.Column("auditor_notes",         sa.Text()),
            sa.Column("auditor_id",            sa.String(100)),
            sa.Column("created_at",            sa.DateTime(),     server_default=sa.text("now()")),
            sa.Column("updated_at",            sa.DateTime(),     server_default=sa.text("now()")),
            sa.Column("completed_at",          sa.DateTime()),
            sa.Column("payroll_file_path",     sa.String(500)),
            sa.Column("policy_xml_path",       sa.String(500)),
            sa.Column("audit_meta_file_path",  sa.String(500)),
            sa.ForeignKeyConstraint(
                ["policy_id"], [f"{schema}.wc_policies.id"],
                name="fk_wc_audit_cases_policy_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("audit_reference", name="uq_wc_audit_cases_audit_reference"),
            schema=schema,
        )
        op.create_index("ix_wc_audit_cases_id", "wc_audit_cases", ["id"], schema=schema)
 
        # 3-step enum conversion: drop default → cast type → restore default
        _cast_column_to_enum(
            conn, schema, "wc_audit_cases", "status",
            "audit_status_enum",
            restore_default="pending",   # restore as enum literal
        )
        _cast_column_to_enum(
            conn, schema, "wc_audit_cases", "recommendation",
            "recommendation_enum",
            restore_default=None,        # no default on this column
        )
 
    # -----------------------------------------------------------------------
    # 5. wc_payroll_records  — enum column: source
    # -----------------------------------------------------------------------
    if "wc_payroll_records" not in existing:
        print(f"[wc_audit_001] Creating wc_payroll_records in {schema}")
        op.create_table(
            "wc_payroll_records",
            sa.Column("id",             sa.Integer(),      nullable=False),
            sa.Column("audit_case_id",  sa.Integer(),      nullable=False),
            # ↓ declared as String — converted to enum AFTER table creation
            sa.Column("source",         sa.String(30),     nullable=False),
            sa.Column("client_name",    sa.String(255)),
            sa.Column("policy_number",  sa.String(50),     nullable=False),
            sa.Column("check_date",     sa.Date()),
            sa.Column("ee_no",          sa.String(50)),
            sa.Column("employee_name",  sa.String(255)),
            sa.Column("state_code",     sa.String(5)),
            sa.Column("class_code",     sa.String(10)),
            sa.Column("wages",          sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("overtime_pay",   sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("double_time",    sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("tips",           sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("net_pay",        sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("exposure",       sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("net_rate",       sa.Numeric(10, 6), server_default="0.0"),
            sa.Column("earned_premium", sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("census_rate",    sa.Numeric(10, 6), server_default="0.0"),
            sa.Column("census_premium", sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("pol_eff_date",   sa.Date()),
            sa.Column("process_date",   sa.Date()),
            sa.Column("created_at",     sa.DateTime(),     server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(
                ["audit_case_id"], [f"{schema}.wc_audit_cases.id"],
                name="fk_wc_payroll_records_audit_case_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index("ix_wc_payroll_records_id", "wc_payroll_records", ["id"], schema=schema)
 
        _cast_column_to_enum(
            conn, schema, "wc_payroll_records", "source",
            "data_source_enum",
            restore_default=None,
        )
 
    # -----------------------------------------------------------------------
    # 6. wc_variance_lines  — enum column: root_cause
    # -----------------------------------------------------------------------
    if "wc_variance_lines" not in existing:
        print(f"[wc_audit_001] Creating wc_variance_lines in {schema}")
        op.create_table(
            "wc_variance_lines",
            sa.Column("id",                sa.Integer(),      nullable=False),
            sa.Column("audit_case_id",     sa.Integer(),      nullable=False),
            sa.Column("policy_number",     sa.String(50)),
            sa.Column("state_code",        sa.String(5)),
            sa.Column("class_code",        sa.String(10)),
            sa.Column("class_desc",        sa.String(255)),
            sa.Column("earned_exposure",   sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("earned_premium",    sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("est_exposure",      sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("est_ytd_premium",   sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("variance",          sa.Numeric(15, 2), server_default="0.0"),
            sa.Column("variance_pct",      sa.Numeric(8, 4),  server_default="0.0"),
            # ↓ declared as String — converted to enum AFTER table creation
            sa.Column("root_cause",        sa.String(30),     server_default="none"),
            sa.Column("root_cause_detail", sa.Text()),
            sa.Column("is_flagged",        sa.Boolean(),      server_default=sa.text("false")),
            sa.Column("flag_reason",       sa.Text()),
            sa.Column("created_at",        sa.DateTime(),     server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(
                ["audit_case_id"], [f"{schema}.wc_audit_cases.id"],
                name="fk_wc_variance_lines_audit_case_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index("ix_wc_variance_lines_id", "wc_variance_lines", ["id"], schema=schema)
 
        _cast_column_to_enum(
            conn, schema, "wc_variance_lines", "root_cause",
            "variance_root_cause",
            restore_default="none",
        )
 
    # -----------------------------------------------------------------------
    # 7. wc_agent_findings  (no enum columns)
    # -----------------------------------------------------------------------
    if "wc_agent_findings" not in existing:
        print(f"[wc_audit_001] Creating wc_agent_findings in {schema}")
        op.create_table(
            "wc_agent_findings",
            sa.Column("id",            sa.Integer(),    nullable=False),
            sa.Column("audit_case_id", sa.Integer(),    nullable=False),
            sa.Column("agent_name",    sa.String(100),  nullable=False),
            sa.Column("finding_type",  sa.String(100)),
            sa.Column("severity",      sa.String(20),   server_default="info"),
            sa.Column("summary",       sa.Text()),
            sa.Column("detail",        postgresql.JSONB()),
            sa.Column("evidence_ref",  sa.Text()),
            sa.Column("created_at",    sa.DateTime(),   server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(
                ["audit_case_id"], [f"{schema}.wc_audit_cases.id"],
                name="fk_wc_agent_findings_audit_case_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index("ix_wc_agent_findings_id", "wc_agent_findings", ["id"], schema=schema)
 
    # -----------------------------------------------------------------------
    # 8. wc_hitl_reviews  (no enum columns)
    # -----------------------------------------------------------------------
    if "wc_hitl_reviews" not in existing:
        print(f"[wc_audit_001] Creating wc_hitl_reviews in {schema}")
        op.create_table(
            "wc_hitl_reviews",
            sa.Column("id",            sa.Integer(),   nullable=False),
            sa.Column("audit_case_id", sa.Integer(),   nullable=False),
            sa.Column("reviewer_id",   sa.String(100)),
            sa.Column("reviewer_name", sa.String(255)),
            sa.Column("action",        sa.String(50)),
            sa.Column("notes",         sa.Text()),
            sa.Column("override_data", postgresql.JSONB()),
            sa.Column("reviewed_at",   sa.DateTime(),  server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(
                ["audit_case_id"], [f"{schema}.wc_audit_cases.id"],
                name="fk_wc_hitl_reviews_audit_case_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index("ix_wc_hitl_reviews_id", "wc_hitl_reviews", ["id"], schema=schema)
 
    # -----------------------------------------------------------------------
    # 9. wc_audit_reports  (no enum columns)
    # -----------------------------------------------------------------------
    if "wc_audit_reports" not in existing:
        print(f"[wc_audit_001] Creating wc_audit_reports in {schema}")
        op.create_table(
            "wc_audit_reports",
            sa.Column("id",            sa.Integer(),   nullable=False),
            sa.Column("audit_case_id", sa.Integer(),   nullable=False),
            sa.Column("report_ref",    sa.String(100)),
            sa.Column("generated_at",  sa.DateTime(),  server_default=sa.text("now()")),
            sa.Column("report_json",   postgresql.JSONB()),
            sa.Column("report_file",   sa.String(500)),
            sa.Column("summary",       sa.Text()),
            sa.Column("is_final",      sa.Boolean(),   server_default=sa.text("false")),
            sa.ForeignKeyConstraint(
                ["audit_case_id"], [f"{schema}.wc_audit_cases.id"],
                name="fk_wc_audit_reports_audit_case_id",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("audit_case_id", name="uq_wc_audit_reports_audit_case_id"),
            sa.UniqueConstraint("report_ref",    name="uq_wc_audit_reports_report_ref"),
            schema=schema,
        )
        op.create_index("ix_wc_audit_reports_id", "wc_audit_reports", ["id"], schema=schema)
 
    print(f"[wc_audit_001] ✅ Upgrade complete for schema: {schema}")
 
 
# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------
 
def downgrade() -> None:
    schema = _schema()
    conn = op.get_bind()
    print(f"[wc_audit_001] Running downgrade for schema: {schema}")
 
    for table in [
        "wc_audit_reports",
        "wc_hitl_reviews",
        "wc_agent_findings",
        "wc_variance_lines",
        "wc_payroll_records",
        "wc_audit_cases",
        "wc_policy_officers",
        "wc_policy_class_codes",
        "wc_policies",
    ]:
        op.drop_table(table, schema=schema)
 
    for enum_name in [
        "audit_status_enum",
        "variance_root_cause",
        "recommendation_enum",
        "data_source_enum",
    ]:
        conn.execute(sa.text(f"DROP TYPE IF EXISTS {schema}.{enum_name} CASCADE;"))
 
    print(f"[wc_audit_001] ✅ Downgrade complete for schema: {schema}")