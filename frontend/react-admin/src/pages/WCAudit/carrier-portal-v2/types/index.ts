// frontend/react-admin/src/pages/WCAudit/carrier-portal/types/index.ts

export type AuditStatus  = 'In Progress' | 'Complete' | 'Pending' | 'N/A'
export type RiskLevel    = 'Low' | 'Medium' | 'High'
export type PolicyStatus = 'Active' | 'Pending Cancel' | 'Cancelled' | 'Expired'

export interface ClassCode {
  code: string
  description: string
  estExposure: number
  earnedExposure: number
  netRate: number
  estYtdPremium: number
}
export interface MonthlyTrend {
  month: string
  earned: number
  est: number
  variance: number
}
export interface Policy {
  policyNumber: string
  insuredName: string
  state: string
  payment_frequency:string
  effectiveDate: string
  expirationDate: string
  completed_at:String
  policyStatus: PolicyStatus
  estPremium: number
  estimated_premium:number
  estCCPremium: number
  estEarnedPremium: number
  actualEarnedPremium: number
  variance: number
  variancePercent: number
  risk: RiskLevel
  auditStatus: AuditStatus
  // ── Payroll submission counts (always integers) ──
  periodsExpected: number   // Math.round(expected_submissions) from API
  periodsReceived: number   // Math.round(submitted_count) from API
  actualPeriodsRecevied:number
  missingPayrolls: number   // periodsExpected - periodsReceived, clamped ≥ 0
  classCodes: ClassCode[]
  aiNarrative: string
  monthlyTrend?: MonthlyTrend[]
  
}

export interface BookSummary {
  totalActiveBookPremium: number
  totalEstEarnedPremium: number
  totalActualEarnedPremium: number
  variance: number
}

export interface DistributionEntry {
  name: string
  value: number
  color: string
}

export interface StateRiskEntry {
  state: string
  High: number
  Medium: number
  Low: number
}

export interface TargetVariance {
  threshold: number
  over:  { count: number; dollarVariance: number }
  under: { count: number; dollarVariance: number }
}

export interface CarrierPortalData {
  policies: Policy[]
  bookSummary: BookSummary
  statusDistribution: DistributionEntry[]
  riskDistribution: DistributionEntry[]
  stateRiskData: StateRiskEntry[]
  targetVariance: TargetVariance
  loading: boolean
  error: string | null
  refresh: () => void
}
