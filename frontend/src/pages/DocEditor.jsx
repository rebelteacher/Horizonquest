import { useState, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import AppNav from "@/components/AppNav";
import { LabActions } from "@/components/labs/LabActions";
import { exportNodeToPDF } from "@/lib/pdf";
import { Input } from "@/components/ui/input";
import { Bold, Italic, Underline, Heading, List, FileText } from "lucide-react";

export default function DocEditor() {
  const [params] = useSearchParams();
  const questId = params.get("quest") || "t2-q1";
  const pageRef = useRef(null);
  const bodyRef = useRef(null);
  const [title, setTitle] = useState("My Business Report");
  const [header, setHeader] = useState("HorizonQuest · Productivity Peaks");
  const [footer, setFooter] = useState("Confidential draft");

  const cmd = (command, value = null) => {
    document.execCommand(command, false, value);
    bodyRef.current?.focus();
  };

  const tools = [
    { icon: Bold, label: "Bold", action: () => cmd("bold") },
    { icon: Italic, label: "Italic", action: () => cmd("italic") },
    { icon: Underline, label: "Underline", action: () => cmd("underline") },
    { icon: Heading, label: "Heading", action: () => cmd("formatBlock", "H2") },
    { icon: List, label: "Bullet list", action: () => cmd("insertUnorderedList") },
  ];

  const exportPdf = () => exportNodeToPDF(pageRef.current, "document.pdf");

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-11 h-11 rounded-xl bg-[#22D3EE]/15 flex items-center justify-center"><FileText className="w-6 h-6 text-[#22D3EE]" /></div>
          <div>
            <h1 className="font-display text-3xl sm:text-4xl tracking-tight leading-none">Document Builder</h1>
            <p className="text-sm text-muted-foreground mt-1">Format a document, then export it to PDF</p>
          </div>
        </div>

        {/* Meta fields */}
        <div className="grid sm:grid-cols-3 gap-3 mb-4">
          <div>
            <label className="text-xs text-muted-foreground">Header</label>
            <Input data-testid="doc-header-input" value={header} onChange={(e) => setHeader(e.target.value)} className="bg-white/5 border-white/10 mt-1" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Title</label>
            <Input data-testid="doc-title-input" value={title} onChange={(e) => setTitle(e.target.value)} className="bg-white/5 border-white/10 mt-1" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Footer</label>
            <Input data-testid="doc-footer-input" value={footer} onChange={(e) => setFooter(e.target.value)} className="bg-white/5 border-white/10 mt-1" />
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap gap-1 p-2 rounded-t-xl hq-glass border border-white/10">
          {tools.map((t) => (
            <button key={t.label} data-testid={`doc-tool-${t.label.toLowerCase().replace(" ", "-")}`} title={t.label} onMouseDown={(e) => { e.preventDefault(); t.action(); }} className="w-9 h-9 rounded-lg hover:bg-white/10 flex items-center justify-center transition-colors">
              <t.icon className="w-4 h-4" />
            </button>
          ))}
        </div>

        {/* Paper page (export target) */}
        <div className="rounded-b-xl overflow-hidden border-x border-b border-white/10 bg-white/5 p-4 sm:p-8">
          <div ref={pageRef} style={{ background: "#ffffff", color: "#1a1a1a", padding: "48px", minHeight: "700px", maxWidth: "720px", margin: "0 auto", fontFamily: "Georgia, serif", boxShadow: "0 10px 40px rgba(0,0,0,0.4)" }}>
            <div style={{ borderBottom: "1px solid #ddd", paddingBottom: 8, marginBottom: 24, fontSize: 12, color: "#888", display: "flex", justifyContent: "space-between" }}>
              <span>{header}</span>
              <span>Page 1</span>
            </div>
            <h1 style={{ fontSize: 28, marginBottom: 20, color: "#111" }}>{title}</h1>
            <div
              ref={bodyRef}
              data-testid="doc-body"
              contentEditable
              suppressContentEditableWarning
              style={{ outline: "none", lineHeight: 1.7, fontSize: 16, minHeight: 420, color: "#1a1a1a" }}
              dangerouslySetInnerHTML={{ __html: "<p>Start typing your report here. Use the toolbar to add <b>bold</b>, <i>italic</i>, headings, and bullet lists.</p><h2>Key Points</h2><ul><li>Point one</li><li>Point two</li></ul>" }}
            />
            <div style={{ borderTop: "1px solid #ddd", paddingTop: 8, marginTop: 24, fontSize: 12, color: "#888", textAlign: "center" }}>{footer}</div>
          </div>
        </div>

        <LabActions questId={questId} onExport={exportPdf} />
      </div>
    </div>
  );
}
