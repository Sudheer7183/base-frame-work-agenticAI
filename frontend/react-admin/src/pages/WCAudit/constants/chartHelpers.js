// ── Chart data helpers ────────────────────────────────────────────────────────

export function buildVarianceTrendData(cases) {
  const byMonth = {};
  cases
    .filter(c => c.created_at && c.overall_variance?.earned_premium != null)
    .forEach(c => {
      const d = new Date(c.created_at);
      // Sort key: "YYYY-MM" for correct chronological ordering
      const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      const label = d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      if (!byMonth[key]) byMonth[key] = { date: label, variance: 0, premium: 0, estPremium: 0, count: 0, _key: key };
      byMonth[key].variance   += Math.abs(c.overall_variance?.variance || 0);
      byMonth[key].premium    += c.overall_variance?.earned_premium || 0;
      byMonth[key].estPremium += c.overall_variance?.est_premium || 0;
      byMonth[key].count      += 1;
    });
  return Object.values(byMonth).sort((a, b) => a._key.localeCompare(b._key));
}

export function buildMonthlyAuditData(cases) {
  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"];
  const byMonth = {};
  cases.forEach(c => {
    if (!c.created_at) return;
    const m = MONTHS[new Date(c.created_at).getMonth()];
    if (!byMonth[m]) byMonth[m] = { month:m, completed:0, pending:0, highRisk:0 };
    if (c.status === "completed" || c.status === "rejected") byMonth[m].completed += 1;
    else if (["pending","processing","running","hitl_pending"].includes(c.status)) byMonth[m].pending += 1;
    if (c.risk_level === "high") byMonth[m].highRisk += 1;
  });
  return MONTHS.filter(m => byMonth[m]).map(m => byMonth[m]);
}