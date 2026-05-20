import C from "../constants/colors";

function Sidebar({ screen, setScreen, collapsed, setCollapsed, navItems }) {
  return (
    <div style={{ width:collapsed ? 68 : 240, background:C.navy, display:"flex",
      flexDirection:"column", transition:"width 0.25s ease", flexShrink:0, overflow:"hidden" }}>

      {/* Logo */}
      <div style={{ padding:"24px 20px 20px", display:"flex", alignItems:"center", gap:12,
        borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
        <div style={{ width:36, height:36,
          background:"linear-gradient(135deg, #1E6FD9, #0ABFBC)", borderRadius:10,
          display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, flexShrink:0 }}>
          🛡
        </div>
        {!collapsed && (
          <div>
            <div style={{ color:"#fff", fontWeight:800, fontSize:14, lineHeight:1.2 }}>Workers' Comp</div>
            <div style={{ color:"rgba(255,255,255,0.45)", fontSize:11, fontWeight:500 }}>Audit Platform</div>
          </div>
        )}
      </div>

      {/* Nav items */}
      <nav style={{ flex:1, padding:"16px 10px", overflow:"hidden" }}>
        {navItems.map(item => (
          <button key={item.id} onClick={() => setScreen(item.id)}
            style={{ display:"flex", alignItems:"center", gap:12, width:"100%",
              padding:"11px 12px", border:"none", borderRadius:10, cursor:"pointer", marginBottom:4,
              background: screen === item.id || (screen === "audit-detail" && item.id === "policies")
                ? "rgba(30,111,217,0.25)" : "transparent",
              color: screen === item.id || (screen === "audit-detail" && item.id === "policies")
                ? "#fff" : "rgba(255,255,255,0.55)",
              borderLeft: screen === item.id || (screen === "audit-detail" && item.id === "policies")
                ? `3px solid ${C.accentLt}` : "3px solid transparent",
              transition:"all 0.15s", textAlign:"left" }}>
            <span style={{ fontSize:16, width:20, textAlign:"center", flexShrink:0 }}>{item.icon}</span>
            {!collapsed && <span style={{ fontSize:13, fontWeight:600, whiteSpace:"nowrap" }}>{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div style={{ padding:"12px 10px", borderTop:"1px solid rgba(255,255,255,0.07)" }}>
        <button onClick={() => setCollapsed(!collapsed)}
          style={{ display:"flex", alignItems:"center", gap:12, width:"100%", padding:"10px 12px",
            border:"none", borderRadius:10, cursor:"pointer", background:"transparent",
            color:"rgba(255,255,255,0.4)", transition:"all 0.15s" }}
          onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.06)"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
          <span style={{ fontSize:16 }}>{collapsed ? "▶" : "◀"}</span>
          {!collapsed && <span style={{ fontSize:12 }}>Collapse</span>}
        </button>
      </div>
    </div>
  );
}

export default Sidebar;