// Spreadsheet formula engine — mirrors backend skillstudio.py (SUM/AVERAGE/COUNT/MAX/MIN).
export const colToIdx = (col) => { let i = 0; for (const ch of col) i = i * 26 + (ch.toUpperCase().charCodeAt(0) - 64); return i - 1; };
export const idxToCol = (i) => { let s = ""; i += 1; while (i > 0) { const r = (i - 1) % 26; s = String.fromCharCode(65 + r) + s; i = Math.floor((i - 1) / 26); } return s; };
export const parseRef = (ref) => { const m = /^([A-Za-z]+)(\d+)$/.exec((ref || "").trim()); if (!m) return null; return [colToIdx(m[1]), parseInt(m[2], 10) - 1]; };

export const expandRange = (rng) => {
  rng = (rng || "").trim();
  if (rng.includes(":")) {
    const [a, b] = rng.split(":");
    const pa = parseRef(a), pb = parseRef(b);
    if (!pa || !pb) return [];
    const refs = [];
    for (let r = Math.min(pa[1], pb[1]); r <= Math.max(pa[1], pb[1]); r++)
      for (let c = Math.min(pa[0], pb[0]); c <= Math.max(pa[0], pb[0]); c++)
        refs.push(idxToCol(c) + (r + 1));
    return refs;
  }
  return [rng];
};

// grid of refs for a range (rows of columns), for chart rendering
export const rangeGrid = (rng) => {
  if (!rng || !rng.includes(":")) return null;
  const [a, b] = rng.split(":");
  const pa = parseRef(a), pb = parseRef(b);
  if (!pa || !pb) return null;
  const grid = [];
  for (let r = Math.min(pa[1], pb[1]); r <= Math.max(pa[1], pb[1]); r++) {
    const row = [];
    for (let c = Math.min(pa[0], pb[0]); c <= Math.max(pa[0], pb[0]); c++) row.push(idxToCol(c) + (r + 1));
    grid.push(row);
  }
  return grid;
};

const num = (v) => { if (v === "" || v === null || v === undefined) return null; const n = Number(v); return Number.isNaN(n) ? null : n; };

export function evalRef(cells, ref, seen) {
  seen = seen || new Set();
  if (seen.has(ref)) return null;
  const raw = (cells[ref] || "").trim();
  if (raw === "") return null;
  if (raw.startsWith("=")) { const s = new Set(seen); s.add(ref); return evalFormula(cells, raw, s); }
  const n = num(raw);
  return n === null ? raw : n;
}

function evalFormula(cells, raw, seen) {
  const m = /^=\s*([A-Za-z]+)\s*\((.*)\)\s*$/.exec(raw);
  if (!m) return "#ERR";
  const fn = m[1].toUpperCase();
  const refs = [];
  m[2].split(",").forEach((p) => { p = p.trim(); if (p) refs.push(...expandRange(p)); });
  const vals = [];
  refs.forEach((r) => { const v = evalRef(cells, r, seen); const n = typeof v === "number" ? v : num(v); if (typeof n === "number") vals.push(n); });
  if (fn === "SUM") return vals.reduce((a, b) => a + b, 0);
  if (fn === "COUNT") return vals.length;
  if (fn === "AVERAGE") return vals.length ? Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 10000) / 10000 : 0;
  if (fn === "MAX") return vals.length ? Math.max(...vals) : 0;
  if (fn === "MIN") return vals.length ? Math.min(...vals) : 0;
  return "#ERR";
}

export function cellDisplay(cells, ref) {
  const v = evalRef(cells, ref);
  if (v === null || v === undefined) return "";
  return String(v);
}
