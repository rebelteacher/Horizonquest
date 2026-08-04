import { useState } from "react";
import { motion } from "framer-motion";
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Image as ImageIcon, BarChart3, Plus, Trash2, X, Play, Sparkles, ArrowRightLeft } from "lucide-react";

const CHART_SAMPLE = [{ name: "Mon", value: 8 }, { name: "Tue", value: 14 }, { name: "Wed", value: 6 }, { name: "Thu", value: 11 }];
const PIE_COLORS = ["#22D3EE", "#F59E0B", "#34D399", "#818CF8"];

const ANIM_VARIANTS = {
  none: { hidden: { opacity: 1 }, show: { opacity: 1 } },
  fade: { hidden: { opacity: 0 }, show: { opacity: 1, transition: { duration: 0.6 } } },
  fly: { hidden: { opacity: 0, x: -40 }, show: { opacity: 1, x: 0, transition: { duration: 0.5 } } },
  zoom: { hidden: { opacity: 0, scale: 0.85 }, show: { opacity: 1, scale: 1, transition: { duration: 0.5 } } },
};

function Sel({ label, value, onChange, options, testid }) {
  return (
    <label className="flex items-center gap-1.5 text-xs text-slate-600">
      <span className="hidden sm:inline">{label}</span>
      <select data-testid={testid} value={value} onChange={(e) => onChange(e.target.value)}
        className="h-9 rounded-md border border-slate-300 bg-white text-slate-700 text-sm px-2">
        {options.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
      </select>
    </label>
  );
}

export default function SlideEditorCore({ doc, setDoc, config, pageRef }) {
  const active = doc.activeSlide || 0;
  const slide = doc.slides[active];
  const [menu, setMenu] = useState(null); // 'image' | 'chart'
  const [playKey, setPlayKey] = useState(0);

  const theme = config.themes.find((t) => t.id === slide.theme) || config.themes[0];

  const updateSlide = (patch) => setDoc({ ...doc, slides: doc.slides.map((s, i) => (i === active ? { ...s, ...patch } : s)) });
  const setBullet = (i, val) => { const b = [...(slide.bullets || [])]; b[i] = val; updateSlide({ bullets: b }); };
  const addBullet = () => updateSlide({ bullets: [...(slide.bullets || []), ""] });
  const removeBullet = (i) => updateSlide({ bullets: (slide.bullets || []).filter((_, idx) => idx !== i) });

  const addSlide = () => setDoc({ ...doc, slides: [...doc.slides, { id: `s${Date.now()}`, layout: "title-content", theme: slide.theme, title: "", bullets: [], image: null, chart: null, animation: "none", transition: "none", notes: "" }], activeSlide: doc.slides.length });
  const deleteSlide = () => { if (doc.slides.length <= 1) return; const slides = doc.slides.filter((_, i) => i !== active); setDoc({ ...doc, slides, activeSlide: Math.max(0, active - 1) }); };

  const bullets = slide.bullets || [];
  const anim = ANIM_VARIANTS[slide.animation] || ANIM_VARIANTS.none;

  const renderMedia = () => (
    <>
      {slide.image && (
        <div className="relative rounded-lg overflow-hidden">
          <img src={slide.image.url} alt={slide.image.label} className="w-full h-full object-cover max-h-48" crossOrigin="anonymous" />
        </div>
      )}
      {slide.chart && (
        <div className="bg-white/95 rounded-lg p-2" style={{ height: 190 }}>
          <ResponsiveContainer width="100%" height="100%">
            {slide.chart.type === "bar" ? (
              <BarChart data={CHART_SAMPLE}><XAxis dataKey="name" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="value" fill={theme.accent} radius={[4, 4, 0, 0]} /></BarChart>
            ) : (
              <PieChart><Pie data={CHART_SAMPLE} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60}>{CHART_SAMPLE.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}</Pie><Legend wrapperStyle={{ fontSize: 10 }} /></PieChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </>
  );

  return (
    <div className="rounded-2xl overflow-hidden border border-white/10">
      {/* Toolbar */}
      <div className="bg-slate-100 border-b border-slate-300 px-2 py-2 flex flex-wrap items-center gap-2 relative">
        <Sel testid="slide-layout-select" label="Layout" value={slide.layout} onChange={(v) => updateSlide({ layout: v })} options={config.layouts} />
        <Sel testid="slide-theme-select" label="Theme" value={slide.theme} onChange={(v) => updateSlide({ theme: v })} options={config.themes} />
        <div className="w-px h-6 bg-slate-300" />
        <div className="relative">
          <button data-testid="slide-image-btn" onClick={() => setMenu(menu === "image" ? null : "image")} className="h-9 px-2.5 rounded-md text-slate-700 hover:bg-slate-200 flex items-center gap-1.5 text-sm"><ImageIcon className="w-4 h-4" /> Image</button>
          {menu === "image" && (
            <div className="absolute z-30 top-11 left-0 bg-white border border-slate-300 rounded-lg p-2 shadow-xl grid grid-cols-3 gap-2 w-72">
              {config.gallery.map((g) => (
                <button key={g.id} data-testid={`slide-image-${g.id}`} onClick={() => { updateSlide({ image: g }); setMenu(null); }} className="rounded overflow-hidden border border-slate-200 hover:ring-2 hover:ring-[#22D3EE]">
                  <img src={g.url} alt={g.label} className="w-full h-14 object-cover" />
                  <span className="block text-[10px] text-slate-600 py-0.5">{g.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="relative">
          <button data-testid="slide-chart-btn" onClick={() => setMenu(menu === "chart" ? null : "chart")} className="h-9 px-2.5 rounded-md text-slate-700 hover:bg-slate-200 flex items-center gap-1.5 text-sm"><BarChart3 className="w-4 h-4" /> Chart</button>
          {menu === "chart" && (
            <div className="absolute z-30 top-11 left-0 bg-white border border-slate-300 rounded-lg p-2 shadow-xl w-40">
              {config.chartTypes.map((t) => (
                <button key={t.id} data-testid={`slide-chart-${t.id}`} onClick={() => { updateSlide({ chart: { type: t.id } }); setMenu(null); }} className="w-full text-left px-2 py-1.5 rounded hover:bg-slate-100 text-sm text-slate-700">{t.name}</button>
              ))}
            </div>
          )}
        </div>
        <div className="w-px h-6 bg-slate-300" />
        <Sel testid="slide-anim-select" label="Animate" value={slide.animation} onChange={(v) => { updateSlide({ animation: v }); setPlayKey((k) => k + 1); }} options={config.animations} />
        <Sel testid="slide-transition-select" label="Transition" value={slide.transition} onChange={(v) => updateSlide({ transition: v })} options={config.transitions} />
        <button data-testid="slide-play-btn" title="Preview animation" onClick={() => setPlayKey((k) => k + 1)} className="h-9 px-2.5 rounded-md text-slate-700 hover:bg-slate-200 flex items-center gap-1 text-sm"><Play className="w-4 h-4" /></button>
      </div>

      <div className="bg-slate-200 p-3 sm:p-5 flex flex-col lg:flex-row gap-4 max-h-[600px] overflow-auto hq-scrollbar" onClick={() => setMenu(null)}>
        {/* Thumbnail rail */}
        <div className="flex lg:flex-col gap-2 lg:w-28 shrink-0 overflow-x-auto">
          {doc.slides.map((s, i) => {
            const th = config.themes.find((t) => t.id === s.theme) || config.themes[0];
            return (
              <button key={s.id} data-testid={`slide-thumb-${i}`} onClick={() => setDoc({ ...doc, activeSlide: i })}
                className={`shrink-0 w-24 lg:w-full aspect-video rounded-md border-2 text-[9px] p-1.5 text-left overflow-hidden ${i === active ? "border-[#22D3EE]" : "border-transparent"}`}
                style={{ background: th.bg, color: th.fg }}>
                <span className="font-bold block truncate">{s.title || `Slide ${i + 1}`}</span>
              </button>
            );
          })}
          <div className="flex lg:flex-col gap-2">
            <button data-testid="slide-add" onClick={addSlide} className="w-24 lg:w-full h-9 rounded-md bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 flex items-center justify-center gap-1 text-xs"><Plus className="w-3.5 h-3.5" /> Slide</button>
            <button data-testid="slide-delete" onClick={deleteSlide} disabled={doc.slides.length <= 1} className="w-24 lg:w-full h-9 rounded-md bg-white text-slate-500 border border-slate-300 hover:text-red-500 disabled:opacity-40 flex items-center justify-center gap-1 text-xs"><Trash2 className="w-3.5 h-3.5" /> Delete</button>
          </div>
        </div>

        {/* Canvas + notes */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            {slide.animation !== "none" && <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-primary/15 text-primary"><Sparkles className="w-3 h-3" /> {slide.animation} in</span>}
            {slide.transition !== "none" && <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-[#22D3EE]/15 text-[#0e7490]"><ArrowRightLeft className="w-3 h-3" /> {slide.transition}</span>}
          </div>

          <div ref={pageRef} data-testid="slide-canvas" className="aspect-video rounded-lg shadow-2xl p-6 sm:p-8 flex flex-col" style={{ background: theme.bg, color: theme.fg }}>
            {slide.layout === "title" ? (
              <div className="m-auto text-center w-full">
                <input data-testid="slide-title-input" value={slide.title} onChange={(e) => updateSlide({ title: e.target.value })} placeholder="Presentation Title"
                  className="w-full bg-transparent outline-none text-3xl sm:text-4xl font-bold text-center placeholder:opacity-40" style={{ color: theme.fg }} />
                <input data-testid="slide-bullet-0" value={bullets[0] || ""} onChange={(e) => setBullet(0, e.target.value)} placeholder="Subtitle / your name"
                  className="w-full bg-transparent outline-none text-lg text-center mt-3 placeholder:opacity-40" style={{ color: theme.accent }} />
              </div>
            ) : (
              <>
                <input data-testid="slide-title-input" value={slide.title} onChange={(e) => updateSlide({ title: e.target.value })} placeholder="Slide title"
                  className="w-full bg-transparent outline-none text-2xl sm:text-3xl font-bold placeholder:opacity-40 mb-4" style={{ color: theme.accent }} />
                <motion.div key={playKey} variants={anim} initial="hidden" animate="show" className={`flex-1 grid gap-4 ${slide.layout === "two-content" || slide.image || slide.chart ? "sm:grid-cols-2" : "grid-cols-1"}`}>
                  <div className="space-y-1.5">
                    {bullets.map((b, i) => (
                      <div key={i} className="flex items-center gap-2 group">
                        <span style={{ color: theme.accent }}>•</span>
                        <input data-testid={`slide-bullet-${i}`} value={b} onChange={(e) => setBullet(i, e.target.value)} placeholder="Bullet point"
                          className="flex-1 bg-transparent outline-none placeholder:opacity-40" style={{ color: theme.fg }} />
                        <button data-testid={`slide-bullet-remove-${i}`} onClick={() => removeBullet(i)} className="opacity-0 group-hover:opacity-100 text-current/50 hover:text-red-400"><X className="w-3.5 h-3.5" /></button>
                      </div>
                    ))}
                    <button data-testid="slide-bullet-add" onClick={addBullet} className="text-sm inline-flex items-center gap-1 opacity-60 hover:opacity-100"><Plus className="w-3.5 h-3.5" /> Add bullet</button>
                  </div>
                  {(slide.image || slide.chart) && (
                    <div className="space-y-2">
                      {renderMedia()}
                      <div className="flex gap-2">
                        {slide.image && <button data-testid="slide-image-remove" onClick={() => updateSlide({ image: null })} className="text-[11px] opacity-70 hover:opacity-100 underline">Remove image</button>}
                        {slide.chart && <button data-testid="slide-chart-remove" onClick={() => updateSlide({ chart: null })} className="text-[11px] opacity-70 hover:opacity-100 underline">Remove chart</button>}
                      </div>
                    </div>
                  )}
                </motion.div>
              </>
            )}
          </div>

          {/* Speaker notes */}
          <div className="mt-3 bg-white rounded-lg border border-slate-300 p-3">
            <p className="text-xs font-medium text-slate-500 mb-1">Speaker notes (what you'll say — audience can't see these)</p>
            <textarea data-testid="slide-notes-input" value={slide.notes} onChange={(e) => updateSlide({ notes: e.target.value })} rows={2}
              placeholder="Type the words you'd say when presenting this slide…"
              className="w-full bg-transparent outline-none resize-none text-sm text-slate-800 placeholder:text-slate-400" />
          </div>
        </div>
      </div>
    </div>
  );
}
