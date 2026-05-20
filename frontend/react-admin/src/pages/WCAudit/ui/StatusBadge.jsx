const StatusBadge = ({ status }) => {
  const map = {
    "Under Review": { bg:"#EDE9FE", color:"#7C3AED" },
    "Pending":       { bg:"#FEF9C3", color:"#B45309" },
    "pending":       { bg:"#FEF9C3", color:"#B45309" },
    "Completed":     { bg:"#DCFCE7", color:"#16A34A" },
    "completed":     { bg:"#DCFCE7", color:"#16A34A" },
    "In Progress":   { bg:"#DBEAFE", color:"#1D4ED8" },
    "running":       { bg:"#DBEAFE", color:"#1D4ED8" },
    "processing":    { bg:"#DBEAFE", color:"#1D4ED8" },
    "error":         { bg:"#FEE2E2", color:"#DC2626" },
    "hitl_pending":  { bg:"#EDE9FE", color:"#7C3AED" },
    "rejected":      { bg:"#FEE2E2", color:"#DC2626" },
  };
  const s = map[status] || { bg:"#F3F4F6", color:"#374151" };
  return (
    <span style={{ background:s.bg, color:s.color, padding:"2px 10px",
      borderRadius:20, fontSize:11, fontWeight:600 }}>
      {status}
    </span>
  );
};

export default StatusBadge;