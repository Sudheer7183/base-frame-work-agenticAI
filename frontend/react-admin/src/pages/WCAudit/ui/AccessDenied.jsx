import C from "../constants/colors";

function AccessDenied({ requiredRole }) {
  return (
    <div style={{ display:"flex", flexDirection:"column", alignItems:"center",
      justifyContent:"center", height:300, gap:16, color:C.muted }}>
      <span style={{ fontSize:48 }}>🔒</span>
      <div style={{ textAlign:"center" }}>
        <div style={{ fontSize:16, fontWeight:700, color:C.text, marginBottom:6 }}>
          Access Restricted
        </div>
        <div style={{ fontSize:13 }}>
          This section requires <strong>{requiredRole}</strong> access.
          Contact your administrator to request the appropriate role.
        </div>
      </div>
    </div>
  );
}

export default AccessDenied;