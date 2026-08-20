// Client mirror of backend skillstudio grading (for live task ticking).
import { evalRef } from "@/lib/sheetEngine";

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
    // ---- sheets kinds ----
    if (k === "cell_text" || k === "cell_formula" || k === "cell_value" || k === "sorted") {
      const sheets = doc.sheets || [];
      const si = check.sheet || 0;
      if (si >= sheets.length) return false;
      const cells = sheets[si].cells || {};
      if (k === "cell_text") return (cells[check.cell] || "").trim().toLowerCase() === check.equals.toLowerCase();
      if (k === "cell_formula") { const raw = (cells[check.cell] || "").replace(/\s/g, "").toUpperCase(); const exp = `=${check.fn}(${check.range})`.replace(/\s/g, "").toUpperCase(); return raw === exp; }
      if (k === "cell_value") { const v = evalRef(cells, check.cell); return typeof v === "number" && Math.abs(v - check.equals) < 0.001; }
      if (k === "sorted") {
        const col = check.col.toUpperCase(); const nums = [];
        for (let r = check.from; r <= check.to; r++) { const n = Number((cells[`${col}${r}`] || "").trim()); if (!Number.isNaN(n) && (cells[`${col}${r}`] || "").trim() !== "") nums.push(n); }
        if (nums.length < 2) return false;
        if (check.order === "asc") return nums.every((n, i) => i === 0 || nums[i - 1] <= n);
        return nums.every((n, i) => i === 0 || nums[i - 1] >= n);
      }
    }
    if (k === "chart") return (doc.charts || []).some((c) => c.type === check.type);
    if (k === "chart_range") { const want = check.range.replace(/\s/g, "").toUpperCase(); return (doc.charts || []).some((c) => c.type === check.type && (c.range || "").replace(/\s/g, "").toUpperCase() === want); }
    if (k === "sheet_count") return (doc.sheets || []).length === check.equals;
    if (k === "sheet_named") { const s = doc.sheets || []; return check.index < s.length && (s[check.index].name || "").trim().toLowerCase() === check.name.toLowerCase(); }
    // ---- slides kinds ----
    if (k === "slide_count") return (doc.slides || []).length === check.equals;
    if (k.startsWith("slide_") || k === "five_by_five") {
      const slides = doc.slides || [];
      const si = check.slide || 0;
      if (si >= slides.length) return false;
      const sl = slides[si];
      const bullets = (sl.bullets || []).filter((b) => (b || "").trim());
      if (k === "slide_title_nonempty") return !!(sl.title || "").trim();
      if (k === "slide_title_contains") return (sl.title || "").toLowerCase().includes(check.value.toLowerCase());
      if (k === "slide_bullets_min") return bullets.length >= check.min;
      if (k === "five_by_five") return bullets.length >= 1 && bullets.length <= 5 && bullets.every((b) => b.trim().split(/\s+/).length <= 5);
      if (k === "slide_layout") return sl.layout === check.equals;
      if (k === "slide_theme") return sl.theme === check.equals;
      if (k === "slide_has_image") return !!sl.image;
      if (k === "slide_has_chart") return !!sl.chart && (!("type" in check) || sl.chart.type === check.type);
      if (k === "slide_animation") return (sl.animation || "none") !== "none";
      if (k === "slide_transition") return (sl.transition || "none") !== "none";
      if (k === "slide_notes_min_words") return (sl.notes || "").trim().split(/\s+/).filter(Boolean).length >= check.min;
    }
    // ---- email kinds ----
    if (k === "email_opened") return (doc.messages || []).some((m) => m.id === check.id && m.read);
    if (k === "searched") return !!doc.searched;
    if (["sent_exists", "subject_prefix", "subject_nonempty", "subject_and_to", "to_includes", "cc_includes", "bcc_includes", "cc_min", "has_greeting", "has_signoff", "has_greeting_signoff", "has_attachment", "body_min_words", "formatting"].includes(k)) {
      const sent = (doc.messages || []).filter((m) => m.folder === "sent" && m.kind === check.sentKind);
      const m = sent[sent.length - 1];
      if (k === "sent_exists") return !!m;
      if (!m) return false;
      const body = m.body || "", bl = body.toLowerCase(), subj = (m.subject || "").trim();
      const inList = (arr, e) => (arr || []).map((x) => x.toLowerCase()).includes(e.toLowerCase());
      const GRE = ["dear ", "hi ", "hi,", "hello", "good morning", "good afternoon", "hey ", "greetings"];
      const SIG = ["thanks", "thank you", "sincerely", "best,", "best regards", "regards", "cheers", "respectfully", "yours"];
      if (k === "subject_prefix") return subj.toLowerCase().startsWith(check.prefix.toLowerCase());
      if (k === "subject_nonempty") return !!subj;
      if (k === "subject_and_to") return !!subj && inList(m.to, check.email);
      if (k === "to_includes") return inList(m.to, check.email);
      if (k === "cc_includes") return inList(m.cc, check.email);
      if (k === "bcc_includes") return inList(m.bcc, check.email);
      if (k === "cc_min") return (m.cc || []).length >= check.min;
      if (k === "has_greeting") return GRE.some((g) => bl.includes(g));
      if (k === "has_signoff") return SIG.some((s) => bl.includes(s));
      if (k === "has_greeting_signoff") return GRE.some((g) => bl.includes(g)) && SIG.some((s) => bl.includes(s));
      if (k === "has_attachment") return (m.attachments || []).length > 0 && (!check.name || (m.attachments || []).some((a) => a.name === check.name));
      if (k === "body_min_words") return body.split(/\s+/).filter(Boolean).length >= check.min;
      if (k === "formatting") return { bold: m.hasBold, bullets: m.hasBullets, signature: m.hasSignature }[check.feature] || false;
    }
  } catch (e) { return false; }
  return false;
}
