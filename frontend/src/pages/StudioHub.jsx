import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { Button } from "@/components/ui/button";
import { ArrowLeft, FileText, CheckCircle2, Loader2, ArrowRight, Award, Sparkles, GraduationCap, ClipboardCheck, Lock, Trophy } from "lucide-react";

const GRADE_COLOR = { A: "#34D399", B: "#22D3EE", C: "#FB923C", D: "#F59E0B", F: "#E11D48" };

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
  useEffect(() => {
    api.get(`/assessments/track/${track}`).then((r) => setCheckpoints(r.data.checkpoints || [])).catch(() => setCheckpoints([]));
    api.get(`/assessments/final/meta`).then((r) => setFinalMeta(r.data)).catch(() => setFinalMeta(null));
  }, [track]);

  if (loading || !data) return (<div className="min-h-screen"><AppNav /><div className="flex justify-center py-40"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div></div>);

  const missions = [...data.missions].sort((a, b) => a.order - b.order);
  const progress = data.progress || {};
  const mastered = missions.filter((m) => progress[m.id]?.mastery).length;
  const firstUndone = missions.find((m) => !progress[m.id]?.mastery) || missions[0];

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

        <div className="grid gap-3 sm:grid-cols-2 mt-8">
          {missions.map((m, i) => {
            const p = progress[m.id];
            const isCapstone = m.points > 100;
            return (
              <button
                key={m.id}
                data-testid={`studio-mission-card-${m.id}`}
                onClick={() => navigate(`/studio/${track}/${m.id}`)}
                style={{ animationDelay: `${i * 0.03}s` }}
                className="hq-fade-up text-left hq-glass rounded-2xl p-5 border border-white/10 hover:border-[#22D3EE]/50 hover:-translate-y-0.5 transition-all"
              >
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
          })}
        </div>

        <div className="mt-10">
          <h2 className="font-display text-2xl flex items-center gap-2"><ClipboardCheck className="w-5 h-5 text-[#22D3EE]" /> Checkpoint Tests</h2>
          <p className="text-sm text-muted-foreground mt-1">A 20-question test at the end of each block of lessons. You get one retake. Questions and answers are shuffled for each Explorer.</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mt-4">
            {checkpoints.map((c, i) => {
              const noAttempts = c.attempts_used >= c.max_attempts;
              const remaining = Math.max(0, c.max_attempts - c.attempts_used);
              return (
                <div key={c.id} data-testid={`checkpoint-card-${c.id}`} className={`hq-glass rounded-2xl p-5 border ${c.passed ? "border-[#34D399]/40" : "border-white/10"}`}>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-display text-lg leading-tight">Checkpoint {i + 1}</h3>
                    {c.best_score != null && <span className="font-display text-xl shrink-0" style={{ color: c.passed ? "#34D399" : "#FB923C" }} data-testid={`checkpoint-score-${c.id}`}>{c.best_score}%</span>}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Covers {c.covers.length} lessons · {c.question_count} questions · pass {c.pass}%</p>
                  <p className="text-[11px] text-slate-500 mt-2">{c.attempts_used}/{c.max_attempts} attempts used{c.passed ? " · Passed ✓" : ""}</p>
                  {!c.unlocked ? (
                    <div className="mt-3 flex items-center gap-2 text-xs text-slate-400"><Lock className="w-4 h-4" /> {c.locked_reason}</div>
                  ) : noAttempts ? (
                    <Button data-testid={`checkpoint-review-${c.id}`} disabled variant="outline" className="w-full mt-3 opacity-60">No attempts left</Button>
                  ) : (
                    <Button data-testid={`checkpoint-take-${c.id}`} onClick={() => navigate(`/assessment/${c.id}`)} className="w-full mt-3 bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]">
                      {c.attempts_used === 0 ? "Take test" : `Retake (${remaining} left)`}
                    </Button>
                  )}
                </div>
              );
            })}
          </div>

          {finalMeta && (
            <div data-testid="final-exam-card" className="hq-glass rounded-2xl p-5 mt-4 border border-primary/40 flex flex-col sm:flex-row sm:items-center gap-4">
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
      </div>
    </div>
  );
}
