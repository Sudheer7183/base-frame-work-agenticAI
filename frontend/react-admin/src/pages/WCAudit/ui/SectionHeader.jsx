import C from "../constants/colors";

const SectionHeader = ({ title, sub, action, onAction }) => (
  <div style={{ display:"flex", justifyContent:"space-between",
    alignItems:"center", marginBottom:18 }}>
    <div>
      <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>{title}</h2>
      {sub && <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>{sub}</p>}
    </div>
    {action && (
      <button onClick={onAction} style={{ background:C.accent, color:"#fff", border:"none",
        borderRadius:8, padding:"7px 16px", fontSize:13, fontWeight:600, cursor:"pointer" }}>
        {action}
      </button>
    )}
  </div>
);

export default SectionHeader;