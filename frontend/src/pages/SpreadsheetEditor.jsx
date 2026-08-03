import { useState, useRef, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import AppNav from "@/components/AppNav";
import { LabActions } from "@/components/labs/LabActions";
import { exportNodeToPDF } from "@/lib/pdf";
import { Table2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from "recharts";

const COLS = ["A", "B", "C", "D", "E"];
const ROWS = 8;
const COLORS = ["#FB923C", "#22D3EE", "#A855F7", "#34D399", "#60A5FA"];

const seed = () => {
  const g = Array.from({ length: ROWS }, () => COLS.map(() => ""));
  const labels = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  const sales = [120, 200, 150, 260, 180];
  labels.forEach((l, i) => { g[i][0] = l; g[i][1] = String(sales[i]); });
  g[5][0] = "Total"; g[5][1] = "=SUM(B1:B5)";
  g[6][0] = "Average"; g[6][1] = "=AVERAGE(B1:B5)";
  g[7][0] = "Count"; g[7][1] = "=COUNT(B1:B5)";
  return g;
};

const colIndex = (c) => c.charCodeAt(0) - 65;
const numeric = (raw) => { const n = parseFloat(raw); return isNaN(n) ? null : n; };

function expandRange(a, b) {
  const c1 = colIndex(a[0]); const r1 = parseInt(a.slice(1)) - 1;
  const c2 = colIndex(b[0]); const r2 = parseInt(b.slice(1)) - 1;
  const cells = [];
  for (let r = Math.min(r1, r2); r <= Math.max(r1, r2); r++)
    for (let c = Math.min(c1, c2); c <= Math.max(c1, c2); c++) cells.push([r, c]);
  return cells;
}

function evalCell(grid, raw) {
  if (typeof raw !== "string" || !raw.startsWith("=")) return raw;
  const f = raw.trim().toUpperCase().replace(/\s+/g, "");
  const m = f.match(/^=(SUM|AVERAGE|COUNT)\(([A-E]\d+):([A-E]\d+)\)$/);
  if (!m) return "#ERR";
  const fn = m[1].toUpperCase();
  const cells = expandRange(m[2], m[3]);
  const nums = cells
    .filter(([r, c]) => r >= 0 && r < ROWS && c >= 0 && c < COLS.length)
    .map(([r, c]) => numeric(grid[r][c]))
    .filter((n) => n !== null);
  if (fn === "SUM") return String(nums.reduce((a, b) => a + b, 0));
  if (fn === "AVERAGE") return nums.length ? String(+(nums.reduce((a, b) => a + b, 0) / nums.length).toFixed(2)) : "0";
  if (fn === "COUNT") return String(nums.length);
  return "#ERR";
}

export default function SpreadsheetEditor() {
  const [params] = useSearchParams();
  const questId = params.get("quest") || "t2-q2";
  const exportRef = useRef(null);
  const [grid, setGrid] = useState(seed);
  const [active, setActive] = useState(null);

  const setCell = (r, c, v) => setGrid((g) => g.map((row, ri) => (ri === r ? row.map((cell, ci) => (ci === c ? v : cell)) : row)));

  const chartData = useMemo(() => {
    return grid.slice(0, 5).map((row) => ({ name: row[0] || "-", value: numeric(evalCell(grid, row[1])) || 0 }));
  }, [grid]);

  const exportPdf = () => exportNodeToPDF(exportRef.current, "spreadsheet.pdf");

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-11 h-11 rounded-xl bg-[#22D3EE]/15 flex items-center justify-center"><Table2 className="w-6 h-6 text-[#22D3EE]" /></div>
          <div>
            <h1 className="font-display text-3xl sm:text-4xl tracking-tight leading-none">Spreadsheet Lab</h1>
            <p className="text-sm text-muted-foreground mt-1">Try <span className="font-mono-data text-[#22D3EE]">=SUM</span>, <span className="font-mono-data text-[#22D3EE]">=AVERAGE</span>, <span className="font-mono-data text-[#22D3EE]">=COUNT</span> over a range like <span className="font-mono-data">B1:B5</span></p>
          </div>
        </div>

        <div ref={exportRef} style={{ background: "#ffffff", color: "#111", borderRadius: 12, padding: 20, marginTop: 16 }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", width: "100%", fontFamily: "monospace" }} data-testid="spreadsheet-grid">
              <thead>
                <tr>
                  <th style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", width: 32 }}></th>
                  {COLS.map((c) => (<th key={c} style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", padding: "6px 10px", color: "#334155" }}>{c}</th>))}
                </tr>
              </thead>
              <tbody>
                {grid.map((row, r) => (
                  <tr key={r}>
                    <td style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", textAlign: "center", color: "#334155", fontSize: 12 }}>{r + 1}</td>
                    {row.map((cell, c) => {
                      const isActive = active && active[0] === r && active[1] === c;
                      return (
                        <td key={c} style={{ border: "1px solid #e2e8f0", padding: 0 }}>
                          <input
                            data-testid={`cell-${COLS[c]}${r + 1}`}
                            value={isActive ? cell : evalCell(grid, cell)}
                            onFocus={() => setActive([r, c])}
                            onBlur={() => setActive(null)}
                            onChange={(e) => setCell(r, c, e.target.value)}
                            style={{ width: 110, border: "none", padding: "8px 10px", background: "transparent", color: "#111", outline: isActive ? "2px solid #22D3EE" : "none", fontFamily: "monospace" }}
                          />
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: 20 }}>
            <p style={{ color: "#334155", fontSize: 13, marginBottom: 8, fontFamily: "sans-serif" }}>Column B chart</p>
            <div style={{ width: "100%", height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <XAxis dataKey="name" tick={{ fill: "#334155", fontSize: 12 }} />
                  <YAxis tick={{ fill: "#334155", fontSize: 12 }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {chartData.map((d, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <LabActions questId={questId} onExport={exportPdf} />
      </div>
    </div>
  );
}
