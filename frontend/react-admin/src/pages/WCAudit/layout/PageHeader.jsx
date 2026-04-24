import C from "../constants/colors";

function PageHeader({ title, sub }) {
  return (
    <div style={{ background:C.card, borderBottom:`1px solid ${C.border}`,
      padding:"16px 28px", flexShrink:0 }}>
      <h1 style={{ margin:0, fontSize:20, fontWeight:800, color:C.text }}>{title}</h1>
      <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>{sub}</p>
    </div>
  );
}

export default PageHeader;