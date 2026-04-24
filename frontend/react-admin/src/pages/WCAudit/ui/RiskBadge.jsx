const RiskBadge = ({ risk }) => {
  const map = {
    high:   { bg:"#FEE2E2", color:"#DC2626", label:"High Risk" },
    High:   { bg:"#FEE2E2", color:"#DC2626", label:"High Risk" },
    medium: { bg:"#FEF3C7", color:"#D97706", label:"Medium" },
    Medium: { bg:"#FEF3C7", color:"#D97706", label:"Medium" },
    low:    { bg:"#D1FAE5", color:"#059669", label:"Low" },
    Low:    { bg:"#D1FAE5", color:"#059669", label:"Low" },
  };
  const s = map[risk] || map.Low;
  return (
    <span style={{ background:s.bg, color:s.color, padding:"2px 10px",
      borderRadius:20, fontSize:11, fontWeight:700, whiteSpace:"nowrap" }}>
      {s.label}
    </span>
  );
};

export default RiskBadge;