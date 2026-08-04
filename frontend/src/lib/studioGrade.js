// Client mirror of backend skillstudio grading (for live task ticking).
const getBlock = (doc, bid) => (doc.blocks || []).find((b) => b.id === bid);
const firstTable = (doc) => (doc.blocks || []).find((b) => b.type === "table");
const LIST_TYPES = ["paragraph", "bullet", "number", "heading"];

export function checkTask(check, doc) {
  const k = check.kind;
  try {
    if (k === "fmt") { const b = getBlock(doc, check.block); return !!b && b.fmt?.[check.attr] === check.equals; }
    if (k === "fmt_all") { const bs = (doc.blocks || []).filter((b) => LIST_TYPES.includes(b.type)); return bs.length > 0 && bs.every((b) => b.fmt?.[check.attr] === check.equals); }
    if (k === "fmt_multi") { return check.blocks.every((id) => getBlock(doc, id)?.fmt?.[check.attr] === check.equals); }
    if (k === "fmt_and") { const b = getBlock(doc, check.block); return !!b && check.checks.every(([a, v]) => b.fmt?.[a] === v); }
    if (k === "type") { const b = getBlock(doc, check.block); return !!b && b.type === check.equals; }
    if (k === "type_multi") { return check.blocks.every((id) => getBlock(doc, id)?.type === check.equals); }
    if (k === "text_contains") { const b = getBlock(doc, check.block); return !!b && (b.text || "").includes(check.value); }
    if (k === "text_replaced") { const b = getBlock(doc, check.block); if (!b) return false; const t = (b.text || "").toLowerCase(); return !t.includes(check.remove.toLowerCase()) && t.includes(check.add.toLowerCase()); }
    if (k === "link") { const b = getBlock(doc, check.block); return (b?.fmt?.link || "").startsWith("http"); }
    if (k === "header_contains") { return (doc.header || "").toLowerCase().includes(check.value.toLowerCase()); }
    if (k === "footer_pagenum") { return !!doc.footerPageNumber; }
    if (k === "table") { const t = firstTable(doc); return !!t && t.cols === check.cols && t.rows === check.rows; }
    if (k === "table_cell_filled") { const t = firstTable(doc); if (!t) return false; const cells = t.cells || []; const { row, col } = check; return row < cells.length && col < cells[row].length && !!(cells[row][col] || "").trim(); }
    if (k === "exported") { return !!doc.exported; }
  } catch (e) { return false; }
  return false;
}
