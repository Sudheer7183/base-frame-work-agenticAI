import C from "../constants/colors";

/**
 * Drag-and-drop / click-to-browse file picker.
 *
 * Props:
 *  label    — display label
 *  file     — currently selected File object (or null)
 *  setFile  — setter for the file
 *  accept   — accepted MIME/extension string (e.g. ".xlsx")
 *  dragKey  — unique string key used for drag-over state and the hidden <input> id
 *  dragging — current dragging key held in parent state
 *  setDragging — setter for dragging in parent
 */
function FileDropZone({ label, file, setFile, accept, dragKey, dragging, setDragging }) {
  return (
    <div
      style={{ background:dragging === dragKey ? "#EEF2FF" : C.bg,
        border:`2px dashed ${dragging === dragKey ? C.accent : C.border}`,
        borderRadius:12, padding:"20px 24px", cursor:"pointer", transition:"all 0.2s",
        display:"flex", alignItems:"center", gap:14 }}
      onDragOver={e => { e.preventDefault(); setDragging(dragKey); }}
      onDragLeave={() => setDragging(null)}
      onDrop={e => { e.preventDefault(); setDragging(null);
        const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
      onClick={() => document.getElementById(`inp-${dragKey}`).click()}>
      <span style={{ fontSize:28 }}>{file ? "✅" : "📂"}</span>
      <div>
        <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{label}</div>
        <div style={{ fontSize:12, color:C.muted }}>
          {file ? file.name : `Drop or click to select — ${accept}`}
        </div>
      </div>
      <input id={`inp-${dragKey}`} type="file" accept={accept} style={{ display:"none" }}
        onChange={e => e.target.files[0] && setFile(e.target.files[0])} />
    </div>
  );
}

export default FileDropZone;