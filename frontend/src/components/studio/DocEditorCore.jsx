import { useRef, useEffect, useState } from "react";
import {
  Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight, AlignJustify,
  List, ListOrdered, Link2, Table2, Sigma, Hash,
} from "lucide-react";

function AutoTextarea({ value, onChange, style, onFocus, testid, placeholder }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (el) { el.style.height = "auto"; el.style.height = el.scrollHeight + "px"; }
  }, [value, style.fontSize, style.fontFamily, style.lineHeight]);
  return (
    <textarea
      ref={ref} data-testid={testid} rows={1} value={value} placeholder={placeholder}
      onFocus={onFocus} onChange={(e) => onChange(e.target.value)}
      style={style}
      className="w-full bg-transparent resize-none outline-none border-none overflow-hidden placeholder:text-slate-400"
    />
  );
}

const TBtn = ({ active, onClick, title, testid, children, disabled }) => (
  <button
    type="button" data-testid={testid} title={title} onClick={onClick} disabled={disabled}
    className={`h-9 w-9 flex items-center justify-center rounded-md transition-colors disabled:opacity-30 ${
      active ? "bg-[#22D3EE] text-[#04121f]" : "text-slate-700 hover:bg-slate-200"
    }`}
  >
    {children}
  </button>
);

export default function DocEditorCore({ doc, setDoc, config, pageRef }) {
  const [selectedId, setSelectedId] = useState(doc.blocks[0]?.id || null);
  const [menu, setMenu] = useState(null); // 'color' | 'symbol' | 'table'
  const selected = doc.blocks.find((b) => b.id === selectedId);

  const patchBlock = (id, patch, fmtPatch) =>
    setDoc({
      ...doc,
      blocks: doc.blocks.map((b) => (b.id === id ? { ...b, ...patch, fmt: { ...b.fmt, ...(fmtPatch || {}) } } : b)),
    });

  const setFmt = (attr, val) => { if (selectedId) patchBlock(selectedId, {}, { [attr]: val }); };
  const toggleFmt = (attr) => { if (selected) setFmt(attr, !selected.fmt[attr]); };
  const toggleType = (type) => {
    if (!selected) return;
    patchBlock(selectedId, { type: selected.type === type ? "paragraph" : type });
  };
  const setText = (id, text) => patchBlock(id, { text });

  const insertSymbol = (sym) => {
    if (!selected) return;
    patchBlock(selectedId, { text: (selected.text || "") + sym });
    setMenu(null);
  };
  const addLink = () => {
    if (!selected) return;
    const url = window.prompt("Enter the full URL (https://…)", "https://");
    if (url) patchBlock(selectedId, {}, { link: url });
  };
  const insertTable = (cols, rows) => {
    const cells = Array.from({ length: rows }, () => Array.from({ length: cols }, () => ""));
    const tbl = { id: `tbl_${Date.now()}`, type: "table", text: "", cols, rows, cells, fmt: { ...doc.blocks[0].fmt } };
    setDoc({ ...doc, blocks: [...doc.blocks, tbl] });
    setMenu(null);
  };
  const setCell = (tid, r, c, val) =>
    setDoc({
      ...doc,
      blocks: doc.blocks.map((b) => {
        if (b.id !== tid) return b;
        const cells = b.cells.map((row, ri) => row.map((cell, ci) => (ri === r && ci === c ? val : cell)));
        return { ...b, cells };
      }),
    });

  const blockStyle = (b) => ({
    fontWeight: b.fmt.bold ? 700 : 400,
    fontStyle: b.fmt.italic ? "italic" : "normal",
    textDecoration: b.fmt.underline || b.fmt.link ? "underline" : "none",
    fontFamily: b.fmt.fontFamily,
    fontSize: `${b.fmt.fontSize}px`,
    color: b.fmt.link ? "#2563eb" : b.fmt.color,
    textAlign: b.fmt.align,
    lineHeight: b.fmt.lineSpacing,
  });

  let numberCount = 0;

  return (
    <div className="rounded-2xl overflow-hidden border border-white/10">
      {/* Toolbar (the "ribbon") */}
      <div className="bg-slate-100 border-b border-slate-300 px-2 py-2 flex flex-wrap items-center gap-1 relative">
        <TBtn testid="studio-bold" title="Bold" active={selected?.fmt.bold} onClick={() => toggleFmt("bold")} disabled={!selected}><Bold className="w-4 h-4" /></TBtn>
        <TBtn testid="studio-italic" title="Italic" active={selected?.fmt.italic} onClick={() => toggleFmt("italic")} disabled={!selected}><Italic className="w-4 h-4" /></TBtn>
        <TBtn testid="studio-underline" title="Underline" active={selected?.fmt.underline} onClick={() => toggleFmt("underline")} disabled={!selected}><Underline className="w-4 h-4" /></TBtn>
        <div className="w-px h-6 bg-slate-300 mx-1" />

        <select data-testid="studio-font" value={selected?.fmt.fontFamily || "Arial"} disabled={!selected}
          onChange={(e) => setFmt("fontFamily", e.target.value)}
          className="h-9 rounded-md border border-slate-300 bg-white text-slate-700 text-sm px-2 disabled:opacity-30">
          {config.fonts.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
        <select data-testid="studio-size" value={selected?.fmt.fontSize || 11} disabled={!selected}
          onChange={(e) => setFmt("fontSize", Number(e.target.value))}
          className="h-9 rounded-md border border-slate-300 bg-white text-slate-700 text-sm px-2 w-16 disabled:opacity-30">
          {config.sizes.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>

        {/* color */}
        <div className="relative">
          <TBtn testid="studio-color" title="Text color" active={menu === "color"} onClick={() => setMenu(menu === "color" ? null : "color")} disabled={!selected}>
            <span className="flex flex-col items-center justify-center leading-none">
              <span className="text-[13px] font-bold">A</span>
              <span className="w-3.5 h-[3px] rounded-sm mt-0.5" style={{ background: selected?.fmt.color || "#dc2626" }} />
            </span>
          </TBtn>
          {menu === "color" && (
            <div className="absolute z-30 top-11 left-0 bg-white border border-slate-300 rounded-lg p-2 grid grid-cols-3 gap-2 shadow-xl w-32">
              {config.colors.map((c) => (
                <button key={c.hex} data-testid={`studio-color-${c.name.toLowerCase()}`} title={c.name}
                  onClick={() => { setFmt("color", c.hex); setMenu(null); }}
                  className="w-7 h-7 rounded-full ring-1 ring-slate-300" style={{ background: c.hex }} />
              ))}
            </div>
          )}
        </div>
        <div className="w-px h-6 bg-slate-300 mx-1" />

        <TBtn testid="studio-align-left" title="Align left" active={selected?.fmt.align === "left"} onClick={() => setFmt("align", "left")} disabled={!selected}><AlignLeft className="w-4 h-4" /></TBtn>
        <TBtn testid="studio-align-center" title="Center" active={selected?.fmt.align === "center"} onClick={() => setFmt("align", "center")} disabled={!selected}><AlignCenter className="w-4 h-4" /></TBtn>
        <TBtn testid="studio-align-right" title="Align right" active={selected?.fmt.align === "right"} onClick={() => setFmt("align", "right")} disabled={!selected}><AlignRight className="w-4 h-4" /></TBtn>
        <TBtn testid="studio-align-justify" title="Justify" active={selected?.fmt.align === "justify"} onClick={() => setFmt("align", "justify")} disabled={!selected}><AlignJustify className="w-4 h-4" /></TBtn>

        <select data-testid="studio-spacing" title="Line spacing" value={selected?.fmt.lineSpacing || 1} disabled={!selected}
          onChange={(e) => setFmt("lineSpacing", Number(e.target.value))}
          className="h-9 rounded-md border border-slate-300 bg-white text-slate-700 text-sm px-2 ml-1 disabled:opacity-30">
          {config.spacings.map((s) => <option key={s} value={s}>{s.toFixed(2).replace(/0$/, "")}×</option>)}
        </select>
        <div className="w-px h-6 bg-slate-300 mx-1" />

        <TBtn testid="studio-bullet" title="Bulleted list" active={selected?.type === "bullet"} onClick={() => toggleType("bullet")} disabled={!selected}><List className="w-4 h-4" /></TBtn>
        <TBtn testid="studio-number" title="Numbered list" active={selected?.type === "number"} onClick={() => toggleType("number")} disabled={!selected}><ListOrdered className="w-4 h-4" /></TBtn>
        <TBtn testid="studio-link" title="Insert link" active={!!selected?.fmt.link} onClick={addLink} disabled={!selected}><Link2 className="w-4 h-4" /></TBtn>

        {/* symbol */}
        <div className="relative">
          <TBtn testid="studio-symbol" title="Special character" active={menu === "symbol"} onClick={() => setMenu(menu === "symbol" ? null : "symbol")} disabled={!selected}><Sigma className="w-4 h-4" /></TBtn>
          {menu === "symbol" && (
            <div className="absolute z-30 top-11 left-0 bg-white border border-slate-300 rounded-lg p-2 grid grid-cols-5 gap-1 shadow-xl w-48">
              {config.symbols.map((s) => (
                <button key={s} data-testid={`studio-symbol-${s}`} onClick={() => insertSymbol(s)}
                  className="w-8 h-8 rounded hover:bg-slate-100 text-slate-800 text-lg">{s}</button>
              ))}
            </div>
          )}
        </div>

        {/* table */}
        <div className="relative">
          <TBtn testid="studio-table" title="Insert table" active={menu === "table"} onClick={() => setMenu(menu === "table" ? null : "table")}><Table2 className="w-4 h-4" /></TBtn>
          {menu === "table" && (
            <div className="absolute z-30 top-11 left-0 bg-white border border-slate-300 rounded-lg p-3 shadow-xl">
              <p className="text-xs text-slate-600 mb-2">Insert table</p>
              <div className="flex flex-wrap gap-1.5">
                {[[3, 2], [2, 3], [3, 3], [4, 2], [2, 2]].map(([c, r]) => (
                  <button key={`${c}x${r}`} data-testid={`studio-table-${c}x${r}`} onClick={() => insertTable(c, r)}
                    className="px-2.5 py-1.5 rounded bg-slate-100 hover:bg-[#22D3EE] hover:text-[#04121f] text-slate-700 text-xs font-mono">
                    {c}×{r}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <TBtn testid="studio-footer-toggle" title="Page numbers (footer)" active={doc.footerPageNumber} onClick={() => setDoc({ ...doc, footerPageNumber: !doc.footerPageNumber })}><Hash className="w-4 h-4" /></TBtn>
      </div>

      {/* The page */}
      <div className="bg-slate-200 p-4 sm:p-8 max-h-[560px] overflow-y-auto hq-scrollbar" onClick={() => setMenu(null)}>
        <div ref={pageRef} className="mx-auto bg-white text-slate-900 shadow-2xl rounded-sm p-8 sm:p-10" style={{ maxWidth: 640 }}>
          {/* header */}
          <input
            data-testid="studio-header-input" value={doc.header}
            onChange={(e) => setDoc({ ...doc, header: e.target.value })}
            placeholder="Header (optional)…"
            className="w-full text-xs text-slate-400 border-b border-dashed border-slate-200 pb-2 mb-4 outline-none placeholder:text-slate-300"
          />

          {doc.blocks.map((b) => {
            if (b.type === "table") {
              return (
                <div key={b.id} className="my-4">
                  <table className="border-collapse w-full">
                    <tbody>
                      {b.cells.map((row, ri) => (
                        <tr key={ri}>
                          {row.map((cell, ci) => (
                            <td key={ci} className="border border-slate-400 p-0">
                              <input data-testid={`studio-cell-${ri}-${ci}`} value={cell}
                                onChange={(e) => setCell(b.id, ri, ci, e.target.value)}
                                className="w-full px-2 py-1.5 text-sm outline-none text-slate-800" />
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            }
            let prefix = null;
            if (b.type === "bullet") prefix = <span className="mt-0.5 select-none text-slate-700">•</span>;
            if (b.type === "number") { numberCount += 1; prefix = <span className="mt-0.5 select-none text-slate-700 font-mono">{numberCount}.</span>; }
            const isSel = b.id === selectedId;
            return (
              <div
                key={b.id}
                onClick={() => setSelectedId(b.id)}
                className={`flex gap-2 rounded px-2 -mx-2 py-0.5 mb-1 cursor-text transition-colors ${isSel ? "ring-2 ring-[#22D3EE]/60 bg-[#22D3EE]/5" : "hover:bg-slate-50"}`}
              >
                {prefix}
                <AutoTextarea
                  testid={`studio-block-${b.id}`}
                  value={b.text}
                  onChange={(t) => setText(b.id, t)}
                  onFocus={() => setSelectedId(b.id)}
                  style={blockStyle(b)}
                />
              </div>
            );
          })}

          {doc.footerPageNumber && (
            <div className="mt-8 pt-2 border-t border-dashed border-slate-200 text-center text-xs text-slate-400">Page 1</div>
          )}
        </div>
      </div>
    </div>
  );
}
