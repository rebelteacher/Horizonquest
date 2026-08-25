import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { SlideCarousel } from "@/components/studio/SlideCarousel";
import { Button } from "@/components/ui/button";
import { ArrowLeft, FileText, CheckCircle2, Loader2, ArrowRight, Award, Sparkles, GraduationCap, ClipboardCheck, Lock, Trophy, Presentation, Upload, ExternalLink, Trash2 } from "lucide-react";

const GRADE_COLOR = { A: "#34D399", B: "#22D3EE", C: "#FB923C", D: "#F59E0B", F: "#E11D48" };
const BACKEND = process.env.REACT_APP_BACKEND_URL;

export default function StudioHub() {
  const { track } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isGuide = user?.role === "guide";
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [assignedIds, setAssignedIds] = useState([]);

  useEffect(() => {
    setLoading(true);
    api.get(`/studio/${track}`).then((r) => setData(r.data)).finally(() => setLoading(false));
  }, [track]);

  useEffect(() => {
    if (isGuide) { setAssignedIds([]); return; }
    api.get("/me/assignments")
      .then((r) => setAssignedIds((r.data || []).filter((a) => a.track === track).flatMap((a) => a.mission_ids)))
      .catch(() => setAssignedIds([]));
  }, [track, isGuide]);

  const [checkpoints, setCheckpoints] = useState([]);
  const [finalMeta, setFinalMeta] = useState(null);
  const [blockSlides, setBlockSlides] = useState({});
  const [deckImages, setDeckImages] = useState({});
  const [editingBlock, setEditingBlock] = useState(null);
  const [urlInput, setUrlInput] = useState("");
  const [uploadingBlock, setUploadingBlock] = useState(null);
  useEffect(() => {
    api.get(`/assessments/track/${track}`).then((r) => setCheckpoints(r.data.checkpoints || [])).catch(() => setCheckpoints([]));
    api.get(`/assessments/final/meta`).then((r) => setFinalMeta(r.data)).catch(() => setFinalMeta(null));
    api.get(`/block-slides/${track}`).then((r) => setBlockSlides(r.data || {})).catch(() => setBlockSlides({}));
  }, [track]);

  const refreshBlockSlides = () => api.get(`/block-slides/${track}`).then((r) => setBlockSlides(r.data || {})).catch(() => {});

  useEffect(() => {
    fetch(`${process.env.PUBLIC_URL || ""}/decks/img/manifest.json`)
      .then((r) => (r.ok ? r.json() : {}))
      .then((m) => setDeckImages(m || {}))
      .catch(() => setDeckImages({}));
  }, []);

  const saveBlockSlides = async (blockId, url) => {
    try {
      await api.put(`/block-slides/${blockId}`, { embed_url: url });
      await refreshBlockSlides();
      setEditingBlock(null);
      toast.success(url ? "Google Slides linked!" : "Google Slides link removed.");
    } catch (e) { toast.error(e?.response?.data?.detail || "Please paste a valid Google Slides embed link."); }
  };

  const uploadPptx = async (blockId, file) => {
    if (!file) return;
    if (!/\.pptx?$/i.test(file.name)) { toast.error("Please choose a PowerPoint file (.pptx or .ppt)."); return; }
    setUploadingBlock(blockId);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api.post(`/block-slides/${blockId}/upload-pptx`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      await refreshBlockSlides();
      setEditingBlock(null);
      if (res.data?.pptx?.status === "ready") toast.success("PowerPoint converted — students will see your slides.");
      else { toast.success("PowerPoint uploaded — converting slides…"); pollPptx(blockId); }
    } catch (e) { toast.error(e?.response?.data?.detail || "Upload failed. Please try again."); }
    finally { setUploadingBlock(null); }
  };

  const pollPptx = (blockId, tries = 0) => {
    if (tries > 12) return;
    setTimeout(async () => {
      try {
        const r = await api.get(`/block-slides/${blockId}/pptx-status`);
        if (r.data?.status === "ready") { await refreshBlockSlides(); toast.success("Slides are ready!"); return; }
      } catch (e) { /* keep trying */ }
      pollPptx(blockId, tries + 1);
    }, 3000);
  };

  const deletePptx = async (blockId) => {
    try {
      await api.delete(`/block-slides/${blockId}/pptx`);
      await refreshBlockSlides();
      toast.success("Removed your PowerPoint — showing the starter deck.");
    } catch (e) { toast.error("Could not remove the PowerPoint."); }
  };

  if (loading || !data) return (<div className="min-h-screen"><AppNav /><div className="flex justify-center py-40"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div></div>);

  const missions = [...data.missions].sort((a, b) => a.order - b.order);
  const progress = data.progress || {};
  const mastered = missions.filter((m) => progress[m.id]?.mastery).length;
  const firstUndone = missions.find((m) => !progress[m.id]?.mastery) || missions[0];

  const missionCard = (m, i) => {
    const p = progress[m.id];
    const isCapstone = m.points > 100;
    return (
      <button key={m.id} data-testid={`studio-mission-card-${m.id}`} onClick={() => navigate(`/studio/${track}/${m.id}`)} style={{ animationDelay: `${i * 0.03}s` }}
        className="hq-fade-up text-left hq-glass rounded-2xl p-5 border border-white/10 hover:border-[#22D3EE]/50 hover:-translate-y-0.5 transition-all">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 font-mono-data ${isCapstone ? "bg-primary/15 text-primary" : "bg-[#22D3EE]/15 text-[#22D3EE]"}`}>
              {isCapstone ? <Award className="w-5 h-5" /> : m.order}
            </div>
            <div className="min-w-0">
              <h3 className="font-display text-lg leading-tight truncate flex items-center gap-2">{m.title}{isCapstone && <Sparkles className="w-4 h-4 text-primary shrink-0" />}</h3>
              <div className="flex items-center gap-2 mt-0.5">
                <p className="text-xs text-muted-foreground truncate">{m.chunk}</p>
                {assignedIds.includes(m.id) && <span data-testid={`assigned-badge-${m.id}`} className="text-[10px] font-semibold uppercase tracking-wide bg-[#FB923C]/20 text-[#FB923C] rounded px-1.5 py-0.5 shrink-0">Assigned</span>}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">{m.tasks.length} tasks · {m.points} pts</p>
            </div>
          </div>
          {p && (
            <div className="text-right shrink-0">
              <span className="font-display text-2xl" style={{ color: GRADE_COLOR[p.grade] }}>{p.grade}</span>
              {p.mastery && <CheckCircle2 className="w-4 h-4 text-emerald-400 ml-auto mt-1" />}
            </div>
          )}
        </div>
      </button>
    );
  };

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <button data-testid="studio-hub-back-btn" onClick={() => navigate(isGuide ? "/guide" : "/map")} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6">
          <ArrowLeft className="w-4 h-4" /> {isGuide ? "Back to the console" : "Back to the map"}
        </button>

        {isGuide && (
          <div data-testid="studio-guide-preview-banner" className="hq-glass rounded-xl px-4 py-3 mb-5 flex items-center gap-3 border border-[#22D3EE]/30">
            <GraduationCap className="w-5 h-5 text-[#22D3EE] shrink-0" />
            <p className="text-sm text-slate-200">Teaching preview — try any mission just like your Explorers do. Your attempts here are <span className="text-[#22D3EE]">not graded or saved</span> to any gradebook.</p>
          </div>
        )}

        <div className="hq-fade-up flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest font-mono-data text-[#22D3EE]">Skill Studio</p>
            <h1 data-testid="studio-hub-title" className="font-display text-4xl sm:text-5xl mt-1 tracking-tight">{data.track.name}</h1>
            <p className="text-slate-300 mt-2 max-w-xl">{data.track.intro}</p>
          </div>
          <div className="hq-glass rounded-2xl px-5 py-4 text-center shrink-0">
            <p className="font-mono-data text-3xl text-primary">{mastered}/{missions.length}</p>
            <p className="text-xs text-muted-foreground mt-1">Missions mastered</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-6">
          {[{ id: "docs", name: "Word Processing" }, { id: "sheets", name: "Spreadsheets" }, { id: "slides", name: "Presentations" }, { id: "email", name: "Email & Communication" }].map((t) => (
            <button
              key={t.id}
              data-testid={`studio-track-pill-${t.id}`}
              onClick={() => navigate(`/studio/${t.id}`)}
              className={`px-4 py-1.5 rounded-full text-sm transition-colors border ${
                t.id === track ? "bg-[#22D3EE] text-[#04121f] border-[#22D3EE]" : "border-white/15 text-slate-300 hover:border-[#22D3EE]/50"
              }`}
            >
              {t.name}
            </button>
          ))}
        </div>

        <Button data-testid="studio-continue-btn" onClick={() => navigate(`/studio/${track}/${firstUndone.id}`)} className="mt-6 bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9] hq-glow-teal">
          {mastered === 0 ? "Start Mission 1" : "Continue"} · {firstUndone.title} <ArrowRight className="w-4 h-4 ml-2" />
        </Button>

        {(() => {
          const blocks = checkpoints
            .map((c) => ({ cp: c, missions: missions.filter((m) => c.covers.includes(m.id)).sort((a, b) => a.order - b.order) }))
            .filter((b) => b.missions.length > 0);
          if (blocks.length === 0) {
            return <div className="grid gap-3 sm:grid-cols-2 mt-8">{missions.map((m, i) => missionCard(m, i))}</div>;
          }
          return (
            <div className="mt-8 space-y-10">
              {blocks.map((b, bi) => {
                const c = b.cp;
                const noAttempts = c.attempts_used >= c.max_attempts;
                const remaining = Math.max(0, c.max_attempts - c.attempts_used);
                const bs = blockSlides[c.id] || {};
                const url = bs.embed_url || "";
                const pptx = bs.pptx || null;
                const first = b.missions[0].order, last = b.missions[b.missions.length - 1].order;
                return (
                  <section key={c.id} data-testid={`block-${c.id}`}>
                    <h2 className="font-display text-2xl">Block {bi + 1} <span className="text-sm text-muted-foreground">· Lessons {first}–{last}</span></h2>
                    <p className="text-sm text-muted-foreground mt-1 mb-3">Watch the teaching slides, complete the {b.missions.length} skills, then take the checkpoint.</p>

                    <div className="hq-glass rounded-2xl p-4 mb-4 border border-white/10">
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <p className="text-sm font-medium flex items-center gap-2"><Presentation className="w-4 h-4 text-[#818CF8]" /> Teaching Slides</p>
                        {isGuide && <button data-testid={`slides-edit-${c.id}`} onClick={() => { setEditingBlock(editingBlock === c.id ? null : c.id); setUrlInput(url || ""); }} className="text-xs text-[#a5b4fc] hover:underline">{editingBlock === c.id ? "Close" : "Manage slides"}</button>}
                      </div>
                      {isGuide && editingBlock === c.id && (
                        <div className="mb-3 space-y-3 rounded-lg bg-slate-900/50 border border-white/10 p-3">
                          <div>
                            <p className="text-xs text-slate-300 mb-1.5">Option 1 · Paste a published <span className="text-[#a5b4fc]">Google Slides</span> link (fully editable, live-updating)</p>
                            <div className="flex flex-col sm:flex-row gap-2">
                              <input data-testid={`slides-input-${c.id}`} value={urlInput} onChange={(e) => setUrlInput(e.target.value)} placeholder="https://docs.google.com/presentation/d/.../embed" className="flex-1 h-9 rounded-md bg-slate-800 border border-slate-600 px-2 text-sm text-white placeholder:text-slate-400 outline-none focus:border-[#818CF8]" />
                              <Button size="sm" data-testid={`slides-save-${c.id}`} onClick={() => saveBlockSlides(c.id, urlInput.trim())} className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]">Save link</Button>
                              {url && <Button size="sm" variant="outline" data-testid={`slides-remove-link-${c.id}`} onClick={() => saveBlockSlides(c.id, "")}>Remove link</Button>}
                            </div>
                          </div>
                          <div className="border-t border-white/10 pt-3">
                            <p className="text-xs text-slate-300 mb-1.5">Option 2 · Upload your own <span className="text-[#a5b4fc]">PowerPoint</span> (.pptx)</p>
                            <div className="flex flex-wrap items-center gap-2">
                              <label data-testid={`pptx-upload-label-${c.id}`} className={`inline-flex items-center gap-2 h-9 px-3 rounded-md text-sm cursor-pointer border border-slate-600 bg-slate-800 hover:border-[#818CF8] text-white ${uploadingBlock === c.id ? "opacity-60 pointer-events-none" : ""}`}>
                                {uploadingBlock === c.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                                {uploadingBlock === c.id ? "Uploading…" : (pptx ? "Replace PowerPoint" : "Upload PowerPoint")}
                                <input data-testid={`pptx-upload-input-${c.id}`} type="file" accept=".pptx,.ppt,application/vnd.openxmlformats-officedocument.presentationml.presentation" className="hidden" onChange={(e) => { uploadPptx(c.id, e.target.files?.[0]); e.target.value = ""; }} />
                              </label>
                              {pptx && <span className="text-xs text-slate-400 truncate max-w-[180px]" title={pptx.filename}>{pptx.filename}</span>}
                              {pptx && <Button size="sm" variant="outline" data-testid={`pptx-remove-${c.id}`} onClick={() => deletePptx(c.id)} className="gap-1"><Trash2 className="w-3.5 h-3.5" /> Remove</Button>}
                            </div>
                            <p className="text-[11px] text-muted-foreground mt-1.5">Tip: a Google Slides link always wins over an uploaded PowerPoint. Remove the link to show your PowerPoint.</p>
                          </div>
                        </div>
                      )}
                      {(() => {
                        const deckKey = `horizonquest_${track}_block${bi + 1}`;
                        const deckUrl = `/decks/${deckKey}.pptx`;
                        const images = deckImages[deckKey] || [];
                        if (url) {
                          return (
                            <>
                              <div className="aspect-video w-full rounded-lg overflow-hidden bg-black" data-testid={`slides-embed-${c.id}`}>
                                <iframe src={url} title={`Teaching slides block ${bi + 1}`} className="w-full h-full" allowFullScreen frameBorder="0" />
                              </div>
                              {isGuide && <p className="text-[11px] text-muted-foreground mt-1">Showing your custom Google Slides.</p>}
                            </>
                          );
                        }
                        if (pptx) {
                          if (pptx.provider === "cloudinary") {
                            if (pptx.status === "ready" && (pptx.images || []).length) {
                              return (
                                <div data-testid={`slides-embed-${c.id}`}>
                                  <SlideCarousel images={pptx.images} title={`Block ${bi + 1} teaching slides`} />
                                  <p className="text-[11px] text-muted-foreground mt-1">Showing {isGuide ? "your uploaded" : "the class"} PowerPoint.</p>
                                </div>
                              );
                            }
                            return (
                              <div className="aspect-video w-full rounded-lg bg-slate-900/60 border border-white/10 flex flex-col items-center justify-center gap-2 text-sm text-muted-foreground" data-testid={`slides-embed-${c.id}`}>
                                <Loader2 className="w-6 h-6 animate-spin text-[#22D3EE]" />
                                Converting your PowerPoint into slides…
                              </div>
                            );
                          }
                          // legacy object-storage upload → Office viewer
                          const fileUrl = `${BACKEND}/api/decks/pptx/${c.id}.pptx?v=${pptx.version}`;
                          const officeSrc = `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(fileUrl)}`;
                          return (
                            <div data-testid={`slides-embed-${c.id}`}>
                              <div className="aspect-video w-full rounded-lg overflow-hidden bg-black">
                                <iframe src={officeSrc} title={`Teaching slides block ${bi + 1}`} className="w-full h-full" allowFullScreen frameBorder="0" />
                              </div>
                              <div className="flex items-center justify-between gap-2 mt-1.5 flex-wrap">
                                <p className="text-[11px] text-muted-foreground">Showing {isGuide ? "your uploaded" : "the class"} PowerPoint. If it doesn't load, use the link →</p>
                                <a href={fileUrl} target="_blank" rel="noopener noreferrer" data-testid={`pptx-open-${c.id}`} className="inline-flex items-center gap-1.5 text-xs text-[#22D3EE] hover:underline"><ExternalLink className="w-3.5 h-3.5" /> Open / Download slides</a>
                              </div>
                            </div>
                          );
                        }
                        if (images.length === 0) {
                          return <div className="aspect-video w-full rounded-lg bg-slate-900/60 border border-white/10 flex items-center justify-center text-sm text-muted-foreground" data-testid={`slides-embed-${c.id}`}>Teaching slides are loading…</div>;
                        }
                        return (
                          <div data-testid={`slides-embed-${c.id}`}>
                            <SlideCarousel images={images} title={`Block ${bi + 1} teaching slides`} deckUrl={deckUrl} />
                            <p className="text-[11px] text-muted-foreground mt-1">{isGuide ? "Showing the HorizonQuest starter deck. Click ‘Manage slides’ to use your own Google Slides or PowerPoint." : "Use the arrows to move through the slides."}</p>
                          </div>
                        );
                      })()}
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">{b.missions.map((m, i) => missionCard(m, i))}</div>

                    <div className={`hq-glass rounded-2xl p-5 mt-4 border ${c.passed ? "border-[#34D399]/40" : "border-white/10"}`} data-testid={`checkpoint-card-${c.id}`}>
                      <div className="flex items-center justify-between gap-3 flex-wrap">
                        <div>
                          <h3 className="font-display text-lg flex items-center gap-2"><ClipboardCheck className="w-4 h-4 text-[#22D3EE]" /> Checkpoint {bi + 1} Test</h3>
                          <p className="text-xs text-muted-foreground mt-1">{c.question_count} questions · pass {c.pass}% · 1 retake · {c.attempts_used}/{c.max_attempts} used{c.passed ? " · Passed ✓" : ""}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          {c.best_score != null && <span className="font-display text-2xl" style={{ color: c.passed ? "#34D399" : "#FB923C" }} data-testid={`checkpoint-score-${c.id}`}>{c.best_score}%</span>}
                          {!c.unlocked ? (
                            <span className="flex items-center gap-2 text-xs text-slate-400"><Lock className="w-4 h-4" /> {c.locked_reason}</span>
                          ) : noAttempts ? (
                            <Button data-testid={`checkpoint-review-${c.id}`} disabled variant="outline" className="opacity-60">No attempts left</Button>
                          ) : (
                            <Button data-testid={`checkpoint-take-${c.id}`} onClick={() => navigate(`/assessment/${c.id}`)} className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]">
                              {c.attempts_used === 0 ? "Take Checkpoint" : `Retake (${remaining} left)`}
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  </section>
                );
              })}

              {finalMeta && (
                <div data-testid="final-exam-card" className="hq-glass rounded-2xl p-5 border border-primary/40 flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="w-12 h-12 rounded-xl bg-primary/15 text-primary flex items-center justify-center shrink-0"><Trophy className="w-6 h-6" /></div>
                    <div className="min-w-0">
                      <h3 className="font-display text-xl">{finalMeta.title}</h3>
                      <p className="text-xs text-muted-foreground">{finalMeta.question_count} questions across all skills · pass {finalMeta.pass}% · <span className="text-[#FB923C]">no retakes</span>{finalMeta.best_score != null ? ` · Best: ${finalMeta.best_score}%` : ""}</p>
                    </div>
                  </div>
                  {finalMeta.attempts_used >= finalMeta.max_attempts ? (
                    <Button data-testid="final-exam-done" disabled variant="outline" className="opacity-60 shrink-0">Completed ({finalMeta.best_score}%)</Button>
                  ) : (
                    <Button data-testid="final-exam-start" onClick={() => navigate(`/assessment/final`)} className="bg-primary text-primary-foreground hover:bg-primary/90 shrink-0">Start Final Exam</Button>
                  )}
                </div>
              )}
            </div>
          );
        })()}
      </div>
    </div>
  );
}
