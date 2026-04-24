import C from "../constants/colors";

const KpiCard = ({ label, value, sub, subColor = "#10B981", icon, accent }) => (
  <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14,
    padding:"20px 24px", flex:1, minWidth:180, position:"relative", overflow:"hidden" }}>
    <div style={{ position:"absolute", top:0, left:0, width:4, height:"100%",
      background:accent || C.accent, borderRadius:"14px 0 0 14px" }} />
    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
      <div>
        <div style={{ fontSize:12, color:C.muted, fontWeight:600, textTransform:"uppercase",
          letterSpacing:1, marginBottom:6 }}>{label}</div>
        <div style={{ fontSize:28, fontWeight:800, color:C.text, lineHeight:1 }}>{value}</div>
        {sub && <div style={{ fontSize:12, color:subColor, fontWeight:600, marginTop:6 }}>{sub}</div>}
      </div>
      {icon && <div style={{ fontSize:28, opacity:0.15, color:accent || C.accent }}>{icon}</div>}
    </div>
  </div>
);

export default KpiCard;