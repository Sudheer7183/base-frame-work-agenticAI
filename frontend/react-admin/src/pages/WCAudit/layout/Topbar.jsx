import C from "../constants/colors";

function Topbar({ notifications, notifOpen, setNotifOpen }) {
  return (
    <div style={{ background:C.card, borderBottom:`1px solid ${C.border}`, padding:"0 28px",
      height:64, display:"flex", alignItems:"center", justifyContent:"space-between", flexShrink:0 }}>

      {/* Search */}
      <div style={{ position:"relative" }}>
        <input placeholder="Search policy number, insured name, class code..."
          style={{ border:`1px solid ${C.border}`, borderRadius:10,
            padding:"8px 14px 8px 38px", fontSize:13, width:320, outline:"none",
            color:C.text, background:C.bg }} />
        <span style={{ position:"absolute", left:12, top:"50%", transform:"translateY(-50%)",
          color:C.muted, fontSize:14 }}>🔍</span>
      </div>

      {/* Right controls */}
      <div style={{ display:"flex", alignItems:"center", gap:16 }}>

        {/* Notifications */}
        <div style={{ position:"relative" }}>
          <button onClick={() => setNotifOpen(!notifOpen)}
            style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:10,
              width:38, height:38, cursor:"pointer", fontSize:16, position:"relative" }}>
            🔔
            {notifications.length > 0 && (
              <span style={{ position:"absolute", top:2, right:2, width:16, height:16,
                background:C.red, borderRadius:"50%", fontSize:9, color:"#fff",
                display:"flex", alignItems:"center", justifyContent:"center", fontWeight:700 }}>
                {notifications.length}
              </span>
            )}
          </button>

          {notifOpen && (
            <div style={{ position:"absolute", right:0, top:48, width:340, background:C.card,
              border:`1px solid ${C.border}`, borderRadius:12,
              boxShadow:"0 8px 32px rgba(0,0,0,0.12)", zIndex:100 }}>
              <div style={{ padding:"14px 18px", borderBottom:`1px solid ${C.border}`,
                fontWeight:700, fontSize:14, color:C.text }}>Notifications</div>
              {notifications.length === 0 ? (
                <div style={{ padding:"20px 18px", color:C.muted, fontSize:13 }}>No new notifications</div>
              ) : notifications.map((n, i) => (
                <div key={i} style={{ padding:"12px 18px", borderBottom:`1px solid ${C.border}`,
                  display:"flex", gap:10 }}>
                  <span>{n.type === "alert" ? "🔴" : n.type === "warning" ? "🟡" : "🔵"}</span>
                  <div>
                    <div style={{ fontSize:12, color:C.text, lineHeight:1.4 }}>{n.msg}</div>
                    <div style={{ fontSize:11, color:C.muted, marginTop:3 }}>{n.time}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* User avatar */}
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ width:36, height:36, borderRadius:"50%",
            background:"linear-gradient(135deg, #1E6FD9, #0ABFBC)",
            display:"flex", alignItems:"center", justifyContent:"center",
            color:"#fff", fontWeight:700, fontSize:14 }}>WC</div>
          <div>
            <div style={{ fontSize:13, fontWeight:700, color:C.text }}>WC Auditor</div>
            <div style={{ fontSize:11, color:C.muted }}>Senior Analyst</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Topbar;