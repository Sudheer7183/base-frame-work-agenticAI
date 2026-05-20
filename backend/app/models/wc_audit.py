"""
Workers' Compensation Audit — SQLAlchemy Models (v2 — simplified)
==================================================================
Redesigned to match the db_persistence.py node exactly:

• NO Postgres custom enum types — all status/source/root_cause fields
  are plain VARCHAR.  This means:
    - No enum casting errors on INSERT
    - Values like "pending","review","approved","completed","rejected"
      just work without a migration-managed enum type
    - Adding new values never requires an ALTER TYPE

• FK chain uses INTEGER ids (not policy_number strings):
    wc_policies.id  →  wc_policy_class_codes.policy_id
                    →  wc_policy_officers.policy_id
                    →  wc_audit_cases.policy_id
                         ↓
                    →  wc_payroll_records.audit_case_id
                    →  wc_variance_lines.audit_case_id
                    →  wc_agent_findings.audit_case_id
                    →  wc_hitl_reviews.audit_case_id
                    →  wc_audit_reports.audit_case_id

• wc_audit_cases.audit_reference is NOT NULL UNIQUE — generated as
  "WCA-{policy_number}-{audit_case_id}" by the persistence node.

File: backend/app/agent_langgraph/wc_nodes/wc_models.py
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, Numeric, Date, JSON
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ─────────────────────────────────────────────
# 1. Policy Master
# ─────────────────────────────────────────────

class Policy(Base):
    __tablename__ = "wc_policies"

    id                = Column(Integer, primary_key=True, index=True)
    policy_number     = Column(String(50),  nullable=False, unique=True, index=True)
    insured_name      = Column(String(255), nullable=False)
    effective_date    = Column(Date,        nullable=False)
    expiration_date   = Column(Date,        nullable=False)
    estimated_premium = Column(Numeric(15, 2), default=0.0)
    payroll_frequency = Column(String(10),  default="1W")
    state_code        = Column(String(5),   nullable=False)
    carrier_name      = Column(String(255))
    broker_name       = Column(String(255))
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime, default=datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class_codes = relationship("PolicyClassCode", back_populates="policy", cascade="all, delete-orphan")
    officers    = relationship("PolicyOfficer",   back_populates="policy", cascade="all, delete-orphan")
    audit_cases = relationship("AuditCase",       back_populates="policy", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# 2. Policy Class Codes
# ─────────────────────────────────────────────

class PolicyClassCode(Base):
    __tablename__ = "wc_policy_class_codes"

    id                  = Column(Integer, primary_key=True, index=True)
    policy_id           = Column(Integer, ForeignKey("wc_policies.id", ondelete="CASCADE"), nullable=False)
    class_code          = Column(String(10), nullable=False)
    class_desc          = Column(String(255))
    state_code          = Column(String(5),  nullable=False)
    composite_rate      = Column(Numeric(10, 6), default=0.0)
    exposure            = Column(Numeric(15, 2), default=0.0)
    est_premium         = Column(Numeric(15, 2), default=0.0)
    est_cc_premium      = Column(Numeric(15, 2), default=0.0)
    endorsement_version = Column(String(10), default="V1")
    created_at          = Column(DateTime, default=datetime.utcnow)

    policy = relationship("Policy", back_populates="class_codes")


# ─────────────────────────────────────────────
# 3. Policy Officers
# ─────────────────────────────────────────────

class PolicyOfficer(Base):
    __tablename__ = "wc_policy_officers"

    id            = Column(Integer, primary_key=True, index=True)
    policy_id     = Column(Integer, ForeignKey("wc_policies.id", ondelete="CASCADE"), nullable=False)
    officer_name  = Column(String(255), nullable=False)
    title         = Column(String(100))
    is_on_payroll = Column(Boolean, default=True)
    ownership_pct = Column(Numeric(5, 2), default=0.0)
    state_code    = Column(String(5))
    created_at    = Column(DateTime, default=datetime.utcnow)

    policy = relationship("Policy", back_populates="officers")


# ─────────────────────────────────────────────
# 4. Audit Case
# ─────────────────────────────────────────────

class AuditCase(Base):
    __tablename__ = "wc_audit_cases"

    id                    = Column(Integer, primary_key=True, index=True)
    policy_id             = Column(Integer, ForeignKey("wc_policies.id", ondelete="CASCADE"), nullable=False)
    monthly_variances = relationship(
        "MonthlyVariance",
        back_populates="audit_case",
        cascade="all, delete-orphan"
    )
    # Stable unique identifier generated by persistence node
    # Format: "WCA-{policy_number}-{in_memory_case_id}"
    audit_reference       = Column(String(150), nullable=False, unique=True)

    # VARCHAR — no enum type. Valid values:
    # pending | ingesting | processing | review | approved | completed | rejected
    status                = Column(String(30), default="pending")

    audit_period_start    = Column(Date)
    audit_period_end      = Column(Date)
    first_check_date      = Column(Date)
    last_check_date       = Column(Date)
    expected_submissions  = Column(Float, default=0.0)
    actual_submissions    = Column(Float, default=0.0)
    submitted_count       = Column(Integer, default=0)

    total_earned_exposure = Column(Numeric(15, 2), default=0.0)
    total_earned_premium  = Column(Numeric(15, 2), default=0.0)
    total_est_exposure    = Column(Numeric(15, 2), default=0.0)
    total_cc_premium = Column(Numeric(15,12), default = 0.0)
    total_est_ytd_premium = Column(Numeric(15, 2), default=0.0)
    total_variance        = Column(Numeric(15, 2), default=0.0)
    total_variance_pct    = Column(Numeric(8, 4),  default=0.0)

    ai_narrative          = Column(Text)
    risk_level            = Column(String(20), default="low")
    # VARCHAR — valid values: refund | additional_premium | clarification | no_action
    recommendation        = Column(String(30))

    hitl_required         = Column(Boolean, default=False)
    hitl_approved_by      = Column(String(255))
    hitl_notes            = Column(Text)
    hitl_approved_at      = Column(DateTime)

    auditor_override      = Column(Boolean, default=False)
    auditor_notes         = Column(Text)
    auditor_id            = Column(String(100))

    payroll_file_path     = Column(String(500))
    policy_xml_path       = Column(String(500))
    audit_meta_file_path  = Column(String(500))

    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at          = Column(DateTime)

    policy          = relationship("Policy",       back_populates="audit_cases")
    payroll_records = relationship("PayrollRecord", back_populates="audit_case", cascade="all, delete-orphan")
    variance_lines  = relationship("VarianceLine",  back_populates="audit_case", cascade="all, delete-orphan")
    agent_findings  = relationship("AgentFinding",  back_populates="audit_case", cascade="all, delete-orphan")
    hitl_reviews    = relationship("HITLReview",    back_populates="audit_case", cascade="all, delete-orphan")
    report          = relationship("AuditReport",   back_populates="audit_case", uselist=False, cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# 5. Payroll Records
# ─────────────────────────────────────────────

class PayrollRecord(Base):
    __tablename__ = "wc_payroll_records"

    id             = Column(Integer, primary_key=True, index=True)
    audit_case_id  = Column(Integer, ForeignKey("wc_audit_cases.id", ondelete="CASCADE"), nullable=False)
    # VARCHAR — valid values: insured | payroll_provider | policy_config
    source         = Column(String(30), nullable=False, default="insured")
    client_name    = Column(String(255))
    policy_number  = Column(String(50))
    check_date     = Column(Date)
    ee_no          = Column(String(50))
    employee_name  = Column(String(255))
    state_code     = Column(String(5))
    class_code     = Column(String(10))
    wages          = Column(Numeric(15, 2), default=0.0)
    overtime_pay   = Column(Numeric(15, 2), default=0.0)
    double_time    = Column(Numeric(15, 2), default=0.0)
    tips           = Column(Numeric(15, 2), default=0.0)
    net_pay        = Column(Numeric(15, 2), default=0.0)
    exposure       = Column(Numeric(15, 2), default=0.0)
    net_rate       = Column(Numeric(10, 6), default=0.0)
    earned_premium = Column(Numeric(15, 2), default=0.0)
    census_rate    = Column(Numeric(10, 6), default=0.0)
    census_premium = Column(Numeric(15, 2), default=0.0)
    pol_eff_date   = Column(Date)
    process_date   = Column(Date)
    created_at     = Column(DateTime, default=datetime.utcnow)

    audit_case = relationship("AuditCase", back_populates="payroll_records")


# ─────────────────────────────────────────────
# 6. Variance Lines
# ─────────────────────────────────────────────

class VarianceLine(Base):
    __tablename__ = "wc_variance_lines"

    id               = Column(Integer, primary_key=True, index=True)
    audit_case_id    = Column(Integer, ForeignKey("wc_audit_cases.id", ondelete="CASCADE"), nullable=False)
    policy_number    = Column(String(50))
    state_code       = Column(String(5))
    class_code       = Column(String(10))
    class_desc       = Column(String(255))
    earned_exposure  = Column(Numeric(15, 2), default=0.0)
    earned_premium   = Column(Numeric(15, 2), default=0.0)
    est_exposure     = Column(Numeric(15, 2), default=0.0)
    est_ytd_premium  = Column(Numeric(15, 2), default=0.0)
    variance         = Column(Numeric(15, 2), default=0.0)
    variance_pct     = Column(Numeric(8, 4),  default=0.0)
    # VARCHAR — valid values: officer_mismatch | class_code_mismatch |
    #           frequency_gap | payroll_variance | rate_discrepancy | none
    root_cause       = Column(String(30), default="none")
    root_cause_detail = Column(Text)
    is_flagged       = Column(Boolean, default=False)
    flag_reason      = Column(Text)
    created_at       = Column(DateTime, default=datetime.utcnow)

    audit_case = relationship("AuditCase", back_populates="variance_lines")


# ─────────────────────────────────────────────
# 7. Agent Findings
# ─────────────────────────────────────────────

class AgentFinding(Base):
    __tablename__ = "wc_agent_findings"

    id            = Column(Integer, primary_key=True, index=True)
    audit_case_id = Column(Integer, ForeignKey("wc_audit_cases.id", ondelete="CASCADE"), nullable=False)
    agent_name    = Column(String(100), nullable=False)   # OfficerAgent | ClassCodeAgent | FrequencyAgent
    finding_type  = Column(String(100))
    severity      = Column(String(20), default="info")    # info | warning | critical
    summary       = Column(Text)
    detail        = Column(JSON)                           # All raw finding fields
    evidence_ref  = Column(Text)
    created_at    = Column(DateTime, default=datetime.utcnow)

    audit_case = relationship("AuditCase", back_populates="agent_findings")


# ─────────────────────────────────────────────
# 8. HITL Reviews
# ─────────────────────────────────────────────

class HITLReview(Base):
    __tablename__ = "wc_hitl_reviews"

    id            = Column(Integer, primary_key=True, index=True)
    audit_case_id = Column(Integer, ForeignKey("wc_audit_cases.id", ondelete="CASCADE"), nullable=False)
    reviewer_id   = Column(String(100))
    reviewer_name = Column(String(255))
    action        = Column(String(50))    # approve | reject | override | request_info | pending
    notes         = Column(Text)
    override_data = Column(JSON)
    reviewed_at   = Column(DateTime, default=datetime.utcnow)

    audit_case = relationship("AuditCase", back_populates="hitl_reviews")


# ─────────────────────────────────────────────
# 9. Audit Report
# ─────────────────────────────────────────────

class AuditReport(Base):
    __tablename__ = "wc_audit_reports"

    id            = Column(Integer, primary_key=True, index=True)
    audit_case_id = Column(Integer, ForeignKey("wc_audit_cases.id", ondelete="CASCADE"),
                           nullable=False, unique=True)
    report_ref    = Column(String(150), unique=True)
    generated_at  = Column(DateTime, default=datetime.utcnow)
    report_json   = Column(JSON)
    report_file   = Column(String(500))   # Path to Excel/PDF
    summary       = Column(Text)          # AI narrative goes here
    is_final      = Column(Boolean, default=False)

    audit_case = relationship("AuditCase", back_populates="report")


class MonthlyVariance(Base):
    __tablename__ = "wc_monthly_variance"

    id = Column(Integer, primary_key=True, index=True)

    audit_case_id = Column(
        Integer,
        ForeignKey("wc_audit_cases.id", ondelete="CASCADE"),
        nullable=False
    )

    policy_number = Column(String(50))
    state_code    = Column(String(5))
    class_code    = Column(String(10))

    month = Column(String(7))  # "YYYY-MM"

    earned_premium = Column(Numeric(15, 2), default=0.0)
    est_premium    = Column(Numeric(15, 2), default=0.0)

    variance     = Column(Numeric(15, 2), default=0.0)
    variance_pct = Column(Numeric(8, 4), default=0.0)

    payroll_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ ONLY THIS (ONE relationship)
    audit_case = relationship(
        "AuditCase",
        back_populates="monthly_variances"
    )