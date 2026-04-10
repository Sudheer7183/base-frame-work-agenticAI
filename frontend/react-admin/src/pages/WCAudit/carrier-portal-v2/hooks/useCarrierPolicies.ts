// frontend/react-admin/src/pages/WCAudit/carrier-portal/hooks/useCarrierPolicies.ts

import { useState, useEffect, useCallback } from 'react'
import { listAuditCases } from '../../../../api/wcAuditAPI'
import type {
  Policy, ClassCode, AuditStatus, RiskLevel, PolicyStatus,
  BookSummary, DistributionEntry, StateRiskEntry, TargetVariance,
  CarrierPortalData,
} from '../types'

const THRESHOLD = 30

// ─── Status maps ──────────────────────────────────────────────────────────────
const AUDIT_STATUS_MAP: Record<string, AuditStatus> = {
  completed:    'Complete',
  pending:      'Pending',
  running:      'In Progress',
  hitl_pending: 'In Progress',
  error:        'N/A',
}

const RISK_MAP: Record<string, RiskLevel> = {
  high:    'High',
  medium:  'Medium',
  low:     'Low',
  unknown: 'Low',
}

function derivePolicyStatus(c: any): PolicyStatus {
  if (c.expiration_date) {
    try {
      const d = new Date(c.expiration_date)
      if (!isNaN(d.getTime()) && d < new Date()) return 'Expired'
    } catch { /* ignore */ }
  }
  if (c.recommendation === 'refund') return 'Pending Cancel'
  return 'Active'
}

// ─── Core transform: one raw API case → Policy ────────────────────────────────
function transformCase(c: any): Policy {

  console.log("c data value in new screens",c);
  
  const ov = c.overall_variance ?? {}
  const monthly = ov.monthly_trend ?? []
  
  const estPremium      = Number(ov.est_ytd_premium ?? 0)
  const estCCPremium = Number(ov.total_cc_premium   ?? 0)
  const actualEarned    = Number(ov.earned_premium  ?? 0)
  const variance        = Number(c.variance         ?? ov.variance     ?? 0)
  const variancePercent = Number(c.variance_pct     ?? ov.variance_pct ?? 0)

  // ── Payroll counts: round to integers, never negative ────────────────────
  const periodsExpected = Math.max(0, Math.round(Number(c.expected_submissions ?? 0)))
  const periodsReceived = Math.max(0, Math.round(Number(c.submitted_count      ?? 0)))
  // Clamp missing to 0..periodsExpected so we never show negatives
  const missingPayrolls = Math.max(0, periodsExpected - periodsReceived)

  // ── Class codes: capitalised keys from _db_case_to_dict ──────────────────
  const classCodes: ClassCode[] = (c.class_code_variance ?? []).map((cc: any) => {
    const earnedExp  = Number(cc.earned_exposure  ?? 0)
    const earnedPrem = Number(cc.earned_premium   ?? 0)
    const estExp     = Number(cc.est_exposure     ?? 0)
    // net_rate = earned_premium / earned_exposure (rate per unit of exposure)
    const netRate    = earnedExp > 0 ? earnedPrem / earnedExp : 0
    return {
      code:           String(cc.ClassCode  ?? cc.class_code  ?? ''),
      description:    String(cc.class_desc ?? cc.ClassCode   ?? cc.class_code ?? ''),
      estExposure:    estExp,
      earnedExposure: earnedExp,
      netRate,
      estYtdPremium:  Number(cc.est_ytd_premium ?? 0),
    }
  })

  const Statecodes:ClassCode[] = (c.class_code_variance ?? []).map((cc:any)=>{
    const state_code = String(cc.StateCode ?? "")

    return state_code
  })

  console.log("state codes from funct",Statecodes);
  

  return {
    policyNumber:        String(c.policy_number ?? c.audit_case_id ?? ''),
    insuredName:         String(c.insured_name  ?? ''),
    state:               String(Statecodes),
    effectiveDate:       String(c.effective_date  ?? ''),
    expirationDate:      String(c.expiration_date ?? ''),
    policyStatus:        derivePolicyStatus(c),
    estPremium,
    estCCPremium,
    estEarnedPremium:    estPremium,
    actualEarnedPremium: actualEarned,
    variance,
    variancePercent,
    risk:         RISK_MAP[String(c.risk_level ?? 'low').toLowerCase()] ?? 'Low',
    auditStatus:  AUDIT_STATUS_MAP[String(c.status ?? 'pending')]       ?? 'Pending',
    periodsExpected,
    periodsReceived,
    missingPayrolls,
    classCodes,
    aiNarrative:  String(c.ai_narrative ?? ''),
    monthlyTrend: monthly.map((m: any) => ({
    month: m.month,
    earned: Number(m.earned ?? 0),
    est: Number(m.est ?? 0),
    variance: Number(m.variance ?? 0),
  })),
  }
}

// ─── Derived summary builders ─────────────────────────────────────────────────
function buildBookSummary(active: Policy[]): BookSummary {
  return {
    totalActiveBookPremium:   active.reduce((s, p) => s + p.estCCPremium,          0),
    totalEstEarnedPremium:    active.reduce((s, p) => s + p.estEarnedPremium,    0),
    totalActualEarnedPremium: active.reduce((s, p) => s + p.actualEarnedPremium, 0),
    get variance() { return this.totalActualEarnedPremium - this.totalEstEarnedPremium },
  }
}

function buildStatusDist(all: Policy[]): DistributionEntry[] {
  return [
    { name: 'Active',         value: all.filter(p => p.policyStatus === 'Active').length,         color: '#10B981' },
    { name: 'Pending Cancel', value: all.filter(p => p.policyStatus === 'Pending Cancel').length,  color: '#F59E0B' },
    { name: 'Cancelled',      value: all.filter(p => p.policyStatus === 'Cancelled').length,       color: '#EF4444' },
    { name: 'Expired',        value: all.filter(p => p.policyStatus === 'Expired').length,         color: '#9CA3AF' },
  ].filter(d => d.value > 0)
}

function buildRiskDist(active: Policy[]): DistributionEntry[] {
  return [
    { name: 'High',   value: active.filter(p => p.risk === 'High').length,   color: '#EF4444' },
    { name: 'Medium', value: active.filter(p => p.risk === 'Medium').length, color: '#F59E0B' },
    { name: 'Low',    value: active.filter(p => p.risk === 'Low').length,    color: '#10B981' },
  ].filter(d => d.value > 0)
}

function buildStateRisk(active: Policy[]): StateRiskEntry[] {
  const states = [...new Set(active.map(p => p.state).filter(s => s && s !== '—'))].sort()
  return states.map(state => ({
    state,
    High:   active.filter(p => p.state === state && p.risk === 'High').length,
    Medium: active.filter(p => p.state === state && p.risk === 'Medium').length,
    Low:    active.filter(p => p.state === state && p.risk === 'Low').length,
  }))
}

function buildTargetVariance(active: Policy[]): TargetVariance {
  const over  = active.filter(p => Math.abs(p.variancePercent) >  THRESHOLD)
  const under = active.filter(p => Math.abs(p.variancePercent) <= THRESHOLD)
  return {
    threshold: THRESHOLD,
    over:  { count: over.length,  dollarVariance: over.reduce((s, p)  => s + p.variance, 0) },
    under: { count: under.length, dollarVariance: under.reduce((s, p) => s + p.variance, 0) },
  }
}

// ─── Hook ─────────────────────────────────────────────────────────────────────
export function useCarrierPolicies(): CarrierPortalData {
  const [policies, setPolicies] = useState<Policy[]>([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const raw: any[] = await listAuditCases()
      setPolicies(raw.map(transformCase))
    } catch (err: any) {
      setError(err?.message ?? 'Failed to load audit cases')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const activePolicies = policies.filter(
    p => p.policyStatus === 'Active' || p.policyStatus === 'Pending Cancel',
  )

  console.log("active policy data", activePolicies);
  

  return {
    policies,
    bookSummary:        buildBookSummary(activePolicies),
    statusDistribution: buildStatusDist(policies),
    riskDistribution:   buildRiskDist(activePolicies),
    stateRiskData:      buildStateRisk(activePolicies),
    targetVariance:     buildTargetVariance(activePolicies),
    loading,
    error,
    refresh: fetchData,
  }
}
