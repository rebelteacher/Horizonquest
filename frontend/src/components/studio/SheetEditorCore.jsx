import { useState } from "react";
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid,
} from "recharts";
import { ArrowDownAZ, ArrowUpAZ, BarChart3, Plus, Trash2 } from "lucide-react";
import { evalRef, cellDisplay, idxToCol, rangeGrid } from "@/lib/sheetEngine";

const PIE_COLORS = ["#22D3EE", "#F59E0B", "#34D399", "#818CF8", "#FB7185", "#A78BFA", "#38BDF8", "#FBBF24"];

export default function SheetEditorCore({ doc, setDoc, config, pageRef }) {
  const active = doc.activeSheet || 0;
  const sheet = doc.sheets[active];
  const cells = sheet.cells || {};
  const [sel, setSel] = useState("A1");
  const [focused, setFocused] = useState(null);
  const [chartOpen, setChartOpen] = useState(false);
  const [chartType, setChartType] = useState((config.chartTypes && config.chartTypes[0]?.id) || "bar");
  const [chartRange, setChartRange] = useState("");

  const updateSheet = (patch) => setDoc({ ...doc, sheets: doc.sheets.map((s, i) => (i === active ? { ...s, ...patch } : s)) });
  const setCell = (ref, val) => updateSheet({ cells: { ...cells, [ref]: val } });

  const selCol = sel.replace(/\d+/, "");
  const selRaw = cells[sel] || "";

  const sortCol = (order) => {
    const entries = [];
    for (let r = 1; r <= sheet.rows; r++) {
      const ref = `${selCol}${r}`;
      const raw = (cells[ref] || "").trim();
      const n = Number(raw);
      if (raw !== "" && !raw.startsWith("=") && !Number.isNaN(n)) entries.push({ ref, n });
    }
    if (entries.length < 2) return;
    const sorted = [...entries].map((e) => e.n).sort((a, b) => (order === "asc" ? a - b : b - a));
    const newCells = { ...cells };
    entries.forEach((e, i) => { newCells[e.ref] = String(sorted[i]); });
    updateSheet({ cells: newCells });
  };

  const addChart = () => {
    if (!chartRange.includes(":")) return;
    const chart = { id: `ch_${Date.now()}`, type: chartType, range: chartRange.toUpperCase(), title: `${sheet.name} chart` };
    setDoc({ ...doc, charts: [...(doc.charts || []), chart] });
    setChartOpen(false); setChartRange("");
  };
  const removeChart = (id) => setDoc({ ...doc, charts: (doc.charts || []).filter((c) => c.id !== id) });

  const addSheet = () => {
    const name = `Sheet${doc.sheets.length + 1}`;
    setDoc({ ...doc, sheets: [...doc.sheets, { name, rows: 8, cols: 4, cells: {} }], activeSheet: doc.sheets.length });
  };
  const renameSheet = (i) => {
    const name = window.prompt("Rename worksheet", doc.sheets[i].name);
    if (name) setDoc({ ...doc, sheets: doc.sheets.map((s, idx) => (idx === i ? { ...s, name } : s)) });
  };

  const chartData = (range) => {
    const grid = rangeGrid(range);
    if (!grid) return [];
    return grid.map((row) => {
      const name = cellDisplay(cells, row[0]) || row[0];
      const valRef = row.length > 1 ? row[1] : row[0];
      const v = evalRef(cells, valRef);
      return { name, value: typeof v === "number" ? v : Number(v) || 0 };
    });
  };

  return (
    <div className="rounded-2xl overflow-hidden border border-white/10">
      {/* Toolbar */}
      <div className="bg-slate-100 border-b border-slate-300 px-2 py-2 flex flex-wrap items-center gap-2 relative">
        <span className="font-mono-data text-xs bg-slate-800 text-white rounded px-2 py-1.5 min-w-[40px] text-center">{sel}</span>
        <input
          data-testid="sheet-formula-input"
          value={selRaw}
          onFocus={() => setFocused("fx")} onBlur={() => setFocused(null)}
          onChange={(e) => setCell(sel, e.target.value)}
          placeholder="Enter a value or =SUM(B2:B5)…"
          className="flex-1 min-w-[180px] h-9 rounded-md border border-slate-300 bg-white px-2 text-sm text-slate-800 outline-none focus:border-[#22D3EE]"
        />
        <div className="w-px h-6 bg-slate-300" />
        <button data-testid="sheet-sort-asc" title="Sort column A→Z (ascending)" onClick={() => sortCol("asc")} className="h-9 px-2.5 rounded-md text-slate-700 hover:bg-slate-200 flex items-center gap-1 text-sm"><ArrowDownAZ className="w-4 h-4" /></button>
        <button data-testid="sheet-sort-desc" title="Sort column Z→A (descending)" onClick={() => sortCol("desc")} className="h-9 px-2.5 rounded-md text-slate-700 hover:bg-slate-200 flex items-center gap-1 text-sm"><ArrowUpAZ className="w-4 h-4" /></button>
        <div className="relative">
          <button data-testid="sheet-chart-btn" onClick={() => setChartOpen((o) => !o)} className="h-9 px-2.5 rounded-md text-slate-700 hover:bg-slate-200 flex items-center gap-1.5 text-sm"><BarChart3 className="w-4 h-4" /> Chart</button>
          {chartOpen && (
            <div className="absolute z-30 top-11 left-0 bg-white border border-slate-300 rounded-lg p-3 shadow-xl w-56">
              <p className="text-xs text-slate-600 mb-2">Insert chart</p>
              <select data-testid="sheet-chart-type" value={chartType} onChange={(e) => setChartType(e.target.value)} className="w-full h-9 rounded-md border border-slate-300 bg-white text-slate-700 text-sm px-2 mb-2">
                {config.chartTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
              <input data-testid="sheet-chart-range" value={chartRange} onChange={(e) => setChartRange(e.target.value)} placeholder="Data range e.g. A1:B4" className="w-full h-9 rounded-md border border-slate-300 bg-white px-2 text-sm text-slate-800 outline-none mb-2" />
              <button data-testid="sheet-chart-add" onClick={addChart} className="w-full h-9 rounded-md bg-[#22D3EE] text-[#04121f] text-sm font-medium hover:bg-[#67E8F9]">Add chart</button>
            </div>
          )}
        </div>
      </div>

      {/* Grid + charts (export area) */}
      <div className="bg-slate-200 p-3 sm:p-5 max-h-[560px] overflow-auto hq-scrollbar" onClick={() => setChartOpen(false)}>
        <div ref={pageRef} className="bg-white rounded-sm p-3 sm:p-4 inline-block min-w-full">
          <table className="border-collapse">
            <thead>
              <tr>
                <th className="w-10 h-7 bg-slate-100 border border-slate-300 sticky left-0" />
                {Array.from({ length: sheet.cols }).map((_, c) => (
                  <th key={c} className="min-w-[90px] h-7 bg-slate-100 border border-slate-300 text-xs font-mono-data text-slate-600">{idxToCol(c)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: sheet.rows }).map((_, r) => (
                <tr key={r}>
                  <td className="w-10 h-8 bg-slate-100 border border-slate-300 text-center text-xs font-mono-data text-slate-600">{r + 1}</td>
                  {Array.from({ length: sheet.cols }).map((_, c) => {
                    const ref = `${idxToCol(c)}${r + 1}`;
                    const isSel = ref === sel;
                    const raw = cells[ref] || "";
                    const display = focused === ref ? raw : cellDisplay(cells, ref);
                    const isNum = raw !== "" && !raw.startsWith("=") && !Number.isNaN(Number(raw));
                    const isFormula = raw.startsWith("=");
                    return (
                      <td key={c} className={`border border-slate-300 p-0 ${isSel ? "ring-2 ring-[#22D3EE] ring-inset" : ""}`}>
                        <input
                          data-testid={`sheet-cell-${ref}`}
                          value={display}
                          onFocus={() => { setSel(ref); setFocused(ref); }}
                          onBlur={() => setFocused(null)}
                          onChange={(e) => setCell(ref, e.target.value)}
                          className={`w-full h-8 px-1.5 text-sm outline-none bg-transparent ${isNum || isFormula ? "text-right" : "text-left"} ${isFormula && focused !== ref ? "text-emerald-700 font-medium" : "text-slate-800"}`}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>

          {/* charts */}
          {(doc.charts || []).length > 0 && (
            <div className="mt-5 grid sm:grid-cols-2 gap-4">
              {(doc.charts || []).map((c) => {
                const data = chartData(c.range);
                return (
                  <div key={c.id} data-testid={`sheet-chart-${c.type}`} className="border border-slate-200 rounded-lg p-3 relative">
                    <button data-testid={`sheet-chart-remove-${c.id}`} onClick={() => removeChart(c.id)} className="absolute top-2 right-2 text-slate-400 hover:text-red-500 z-10"><Trash2 className="w-3.5 h-3.5" /></button>
                    <p className="text-xs text-slate-500 mb-2 font-mono-data">{c.type === "bar" ? "Bar" : "Pie"} · {c.range}</p>
                    <ResponsiveContainer width="100%" height={200}>
                      {c.type === "bar" ? (
                        <BarChart data={data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#475569" }} />
                          <YAxis tick={{ fontSize: 11, fill: "#475569" }} />
                          <Tooltip />
                          <Bar dataKey="value" fill="#22D3EE" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      ) : (
                        <PieChart>
                          <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={{ fontSize: 10 }}>
                            {data.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                          </Pie>
                          <Legend wrapperStyle={{ fontSize: 11 }} />
                          <Tooltip />
                        </PieChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Sheet tabs */}
      <div className="bg-slate-100 border-t border-slate-300 px-2 py-1.5 flex items-center gap-1">
        {doc.sheets.map((s, i) => (
          <button
            key={i} data-testid={`sheet-tab-${i}`}
            onClick={() => setDoc({ ...doc, activeSheet: i })}
            onDoubleClick={() => renameSheet(i)}
            title="Double-click to rename"
            className={`px-3 py-1.5 rounded-md text-sm transition-colors ${i === active ? "bg-white text-slate-900 shadow-sm font-medium" : "text-slate-600 hover:bg-slate-200"}`}
          >
            {s.name}
          </button>
        ))}
        <button data-testid="sheet-add-tab" onClick={addSheet} title="Add worksheet" className="w-7 h-7 flex items-center justify-center rounded-md text-slate-600 hover:bg-slate-200"><Plus className="w-4 h-4" /></button>
      </div>
    </div>
  );
}
