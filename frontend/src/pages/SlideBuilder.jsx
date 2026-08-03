import { useState, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import AppNav from "@/components/AppNav";
import { LabActions } from "@/components/labs/LabActions";
import { exportNodesToPDF } from "@/lib/pdf";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Presentation, Plus, Trash2, ChevronLeft, ChevronRight, AlertTriangle, CheckCircle2 } from "lucide-react";

const initialSlides = [
  { title: "Our Fundraiser Plan", bullets: "Goal: raise $500\nEvent: bake sale\nDate: next Friday\nTeam: 6 members\nBudget: $80" },
  { title: "Why It Matters", bullets: "Supports the robotics club\nBuilds teamwork\nFun for the whole school" },
];

const SlideCard = ({ slide, index, total, forExport = false }) => (
  <div
    style={{
      background: "#0b1120",
      color: "#ffffff",
      width: forExport ? 960 : "100%",
      aspectRatio: "16 / 9",
      borderRadius: forExport ? 0 : 16,
      padding: forExport ? 64 : 40,
      display: "flex",
      flexDirection: "column",
      fontFamily: "sans-serif",
      border: "1px solid rgba(255,255,255,0.1)",
      backgroundImage: "linear-gradient(135deg, #0b1120 0%, #111a33 100%)",
    }}
  >
    <div style={{ height: 6, width: 64, background: "#FB923C", borderRadius: 4, marginBottom: 24 }} />
    <h2 style={{ fontSize: forExport ? 44 : 30, fontWeight: 700, marginBottom: 24, lineHeight: 1.1 }}>{slide.title || "Untitled slide"}</h2>
    <ul style={{ fontSize: forExport ? 26 : 18, lineHeight: 1.9, listStyle: "none", padding: 0, margin: 0, flex: 1 }}>
      {slide.bullets.split("\n").filter((b) => b.trim()).map((b, i) => (
        <li key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
          <span style={{ color: "#22D3EE", marginTop: forExport ? 10 : 8 }}>▸</span>
          <span>{b}</span>
        </li>
      ))}
    </ul>
    <div style={{ textAlign: "right", fontSize: 13, color: "rgba(255,255,255,0.4)" }}>{index + 1} / {total}</div>
  </div>
);

export default function SlideBuilder() {
  const [params] = useSearchParams();
  const questId = params.get("quest") || "t2-q4";
  const [slides, setSlides] = useState(initialSlides);
  const [cur, setCur] = useState(0);
  const exportContainerRef = useRef(null);

  const slide = slides[cur];
  const update = (field, value) => setSlides((s) => s.map((sl, i) => (i === cur ? { ...sl, [field]: value } : sl)));

  const addSlide = () => { setSlides((s) => [...s, { title: "New Slide", bullets: "First point" }]); setCur(slides.length); };
  const delSlide = () => {
    if (slides.length === 1) return;
    const next = slides.filter((_, i) => i !== cur);
    setSlides(next);
    setCur(Math.max(0, cur - 1));
  };

  const bulletLines = slide.bullets.split("\n").filter((b) => b.trim());
  const tooManyLines = bulletLines.length > 5;
  const longLine = bulletLines.some((l) => l.trim().split(/\s+/).length > 5);
  const followsRule = !tooManyLines && !longLine;

  const exportPdf = async () => {
    const nodes = Array.from(exportContainerRef.current.children);
    await exportNodesToPDF(nodes, "slides.pdf");
  };

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-11 h-11 rounded-xl bg-[#22D3EE]/15 flex items-center justify-center"><Presentation className="w-6 h-6 text-[#22D3EE]" /></div>
          <div>
            <h1 className="font-display text-3xl sm:text-4xl tracking-tight leading-none">Slide Builder</h1>
            <p className="text-sm text-muted-foreground mt-1">Follow the 5×5 rule — ~5 lines per slide, ~5 words per line</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Editor */}
          <div className="hq-glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Button data-testid="slide-prev-btn" size="icon" variant="outline" className="border-white/15 h-8 w-8" disabled={cur === 0} onClick={() => setCur(cur - 1)}><ChevronLeft className="w-4 h-4" /></Button>
                <span className="font-mono-data text-sm">Slide {cur + 1} / {slides.length}</span>
                <Button data-testid="slide-next-btn" size="icon" variant="outline" className="border-white/15 h-8 w-8" disabled={cur === slides.length - 1} onClick={() => setCur(cur + 1)}><ChevronRight className="w-4 h-4" /></Button>
              </div>
              <div className="flex gap-2">
                <Button data-testid="slide-add-btn" size="sm" variant="outline" className="border-white/15" onClick={addSlide}><Plus className="w-4 h-4 mr-1" /> Add</Button>
                <Button data-testid="slide-delete-btn" size="sm" variant="outline" className="border-[#E11D48]/40 text-[#f43f5e]" onClick={delSlide} disabled={slides.length === 1}><Trash2 className="w-4 h-4" /></Button>
              </div>
            </div>

            <label className="text-xs text-muted-foreground">Slide title</label>
            <Input data-testid="slide-title-input" value={slide.title} onChange={(e) => update("title", e.target.value)} className="bg-white/5 border-white/10 mt-1 mb-4" />

            <label className="text-xs text-muted-foreground">Bullet points (one per line)</label>
            <Textarea data-testid="slide-bullets-input" value={slide.bullets} onChange={(e) => update("bullets", e.target.value)} className="bg-white/5 border-white/10 mt-1 min-h-[160px] font-mono-data text-sm" />

            <div className={`mt-4 flex items-center gap-2 text-sm ${followsRule ? "text-emerald-400" : "text-[#FB923C]"}`} data-testid="slide-5x5-hint">
              {followsRule ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              {followsRule ? "Great — this slide follows the 5×5 rule." : tooManyLines ? "Too many lines — keep it to about 5." : "A line has more than 5 words — tighten it up."}
            </div>
          </div>

          {/* Live preview */}
          <div>
            <p className="text-xs uppercase tracking-widest font-mono-data text-muted-foreground mb-2">Preview</p>
            <SlideCard slide={slide} index={cur} total={slides.length} />
          </div>
        </div>

        <LabActions questId={questId} onExport={exportPdf} exportLabel="Export deck (PDF)" />
      </div>

      {/* Hidden export nodes (all slides at fixed size) */}
      <div ref={exportContainerRef} style={{ position: "fixed", left: -10000, top: 0 }}>
        {slides.map((s, i) => (<SlideCard key={i} slide={s} index={i} total={slides.length} forExport />))}
      </div>
    </div>
  );
}
