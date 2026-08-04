import { useEffect, useRef, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import DocEditorCore from "@/components/studio/DocEditorCore";
import SheetEditorCore from "@/components/studio/SheetEditorCore";
import { checkTask } from "@/lib/studioGrade";
import { exportNodeToPDF } from "@/lib/pdf";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ArrowLeft, ArrowRight, ScrollText, CheckCircle2, Circle, Loader2, Download, Gem, Anchor, ListChecks, Trophy } from "lucide-react";
import { toast } from "sonner";

function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i} className="text-white font-semibold">{p.slice(2, -2)}</strong>;
    if (p.startsWith("`") && p.endsWith("`")) return <code key={i} className="px-1.5 py-0.5 rounded bg-white/10 font-mono-data text-[#22D3EE] text-[0.85em]">{p.slice(1, -1)}</code>;
    if (p.startsWith("*") && p.endsWith("*")) return <em key={i} className="text-slate-200">{p.slice(1, -1)}</em>;
    return <span key={i}>{p}</span>;
  });
}

function Instruction({ blocks }) {
  return (
    <div className="space-y-2">
      {blocks.map((b, i) => {
        if (b.startsWith("## ")) return <h3 key={i} className="font-display text-lg text-primary mt-4 first:mt-0">{renderInline(b.slice(3))}</h3>;
        if (b.startsWith("- ")) return (
          <div key={i} className="flex gap-2.5 text-slate-300 text-sm leading-relaxed">
            <span className="mt-2 w-1.5 h-1.5 rounded-full bg-[#22D3EE] shrink-0" />
            <p className="flex-1">{renderInline(b.slice(2))}</p>
          </div>
        );
        return <p key={i} className="text-slate-300 text-sm leading-relaxed">{renderInline(b)}</p>;
      })}
    </div>
  );
}

const GRADE_COLOR = { A: "#34D399", B: "#22D3EE", C: "#FB923C", D: "#F59E0B", F: "#E11D48" };

export default function StudioMission() {
  const { track, missionId } = useParams();
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const pageRef = useRef(null);

  const [config, setConfig] = useState(null);
  const [mission, setMission] = useState(null);
  const [nextId, setNextId] = useState(null);
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    setLoading(true); setResult(null);
    (async () => {
      const res = await api.get(`/studio/${track}`);
      setConfig(res.data.config);
      const missions = res.data.missions.sort((a, b) => a.order - b.order);
      const m = missions.find((x) => x.id === missionId);
      setMission(m || null);
      if (m) {
        setDoc(JSON.parse(JSON.stringify(m.doc)));
        const idx = missions.findIndex((x) => x.id === missionId);
        setNextId(idx >= 0 && idx < missions.length - 1 ? missions[idx + 1].id : null);
      }
      setLoading(false);
    })();
  }, [track, missionId]);

  const taskStatus = useMemo(() => {
    if (!mission || !doc) return [];
    return mission.tasks.map((t) => ({ ...t, passed: checkTask(t.check, doc) }));
  }, [mission, doc]);

  const passedCount = taskStatus.filter((t) => t.passed).length;
  const allDone = mission && passedCount === mission.tasks.length;

  const doExport = async () => {
    if (!pageRef.current) return;
    try {
      await exportNodeToPDF(pageRef.current, `${mission.id}.pdf`);
      setDoc((d) => ({ ...d, exported: true }));
      toast.success("Exported to PDF ⛵");
    } catch (e) {
      toast.error("Export failed. Try again.");
    }
  };

  const submit = async () => {
    setSubmitting(true);
    try {
      const res = await api.post(`/studio/${track}/${missionId}/submit`, { doc });
      setResult(res.data);
      await refresh();
      if (res.data.mastery) toast.success(`Graded ${res.data.grade} · +${res.data.points_awarded} Horizon Points`);
      else toast.info(`Graded ${res.data.grade} (${res.data.score}%). Reach 90% for mastery.`);
    } catch (e) {
      toast.error("Could not submit for grading.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (<div className="min-h-screen"><AppNav /><div className="flex justify-center py-40"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div></div>);
  if (!mission || !doc) return (<div className="min-h-screen"><AppNav /><div className="text-center py-40 text-muted-foreground">Mission not found. <button className="text-primary underline" onClick={() => navigate(`/studio/${track}`)}>Back to Studio</button></div></div>);

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <button data-testid="studio-back-btn" onClick={() => navigate(`/studio/${track}`)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-5">
          <ArrowLeft className="w-4 h-4" /> Back to Skill Studio
        </button>

        <p className="text-xs uppercase tracking-widest font-mono-data text-[#22D3EE]">Mission {mission.order} · {mission.chunk}</p>
        <h1 data-testid="studio-mission-title" className="font-display text-3xl sm:text-4xl mt-1 tracking-tight">{mission.title}</h1>

        <div className="grid lg:grid-cols-3 gap-6 mt-6">
          {/* Editor */}
          <div className="lg:col-span-2 order-2 lg:order-1">
            {track === "sheets"
              ? <SheetEditorCore doc={doc} setDoc={setDoc} config={config} pageRef={pageRef} />
              : <DocEditorCore doc={doc} setDoc={setDoc} config={config} pageRef={pageRef} />}
            <div className="flex flex-wrap gap-3 mt-4">
              <Button data-testid="studio-export-btn" variant="outline" className="border-white/15" onClick={doExport}>
                <Download className="w-4 h-4 mr-2" /> Export PDF
              </Button>
              <Button data-testid="studio-submit-btn" onClick={submit} disabled={submitting} className="bg-primary text-primary-foreground hover:bg-[#FDBA74]">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Submit for a grade{allDone ? " ✓" : ""}</>}
              </Button>
            </div>
          </div>

          {/* Instruction + tasks */}
          <div className="order-1 lg:order-2 space-y-6">
            <div className="hq-glass rounded-2xl p-5 border-t border-t-[#22D3EE]/30">
              <h2 className="font-display text-xl flex items-center gap-2 mb-3"><ScrollText className="w-4 h-4 text-[#22D3EE]" /> Instruction</h2>
              <div className="max-h-64 overflow-y-auto hq-scrollbar pr-2 -mr-2">
                <Instruction blocks={mission.instruction} />
              </div>
            </div>

            <div className="hq-glass rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-display text-xl flex items-center gap-2"><ListChecks className="w-4 h-4 text-primary" /> Your Tasks</h2>
                <span className="font-mono-data text-sm text-muted-foreground">{passedCount}/{mission.tasks.length}</span>
              </div>
              <div className="space-y-2.5">
                {taskStatus.map((t) => (
                  <div key={t.id} data-testid={`studio-task-${t.id}`} className="flex items-start gap-2.5">
                    {t.passed
                      ? <CheckCircle2 data-testid={`studio-task-${t.id}-done`} className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                      : <Circle className="w-5 h-5 text-slate-500 shrink-0 mt-0.5" />}
                    <span className={`text-sm ${t.passed ? "text-emerald-300 line-through/0" : "text-slate-300"}`}>{t.label}</span>
                  </div>
                ))}
              </div>
              {allDone && <p className="mt-4 text-sm text-emerald-300">All tasks complete — submit for your grade!</p>}
            </div>
          </div>
        </div>
      </div>

      {/* Result dialog */}
      <Dialog open={!!result} onOpenChange={(o) => !o && setResult(null)}>
        <DialogContent className="hq-glass border-white/10 max-w-md">
          {result && (
            <>
              <DialogHeader>
                <DialogTitle className="font-display text-3xl text-center">Mission Graded</DialogTitle>
                <DialogDescription className="text-center">{mission.title}</DialogDescription>
              </DialogHeader>
              <div className="text-center py-4">
                <div className="mx-auto w-24 h-24 rounded-full flex items-center justify-center mb-3" style={{ background: `${GRADE_COLOR[result.grade]}22`, boxShadow: `0 0 40px ${GRADE_COLOR[result.grade]}33` }}>
                  <span className="font-display text-5xl" style={{ color: GRADE_COLOR[result.grade] }} data-testid="studio-result-grade">{result.grade}</span>
                </div>
                <p className="text-slate-300">Score <b>{result.score}%</b> · {result.passed}/{result.total} tasks</p>
                <div className="flex justify-center gap-6 mt-5">
                  <div className="flex items-center gap-2 text-primary"><Gem className="w-5 h-5" /><span className="font-mono-data text-xl">+{result.points_awarded}</span></div>
                  {result.compass_mark_earned && <div className="flex items-center gap-2 text-[#22D3EE]"><Anchor className="w-5 h-5" /><span className="font-mono-data text-xl">+1 Mark</span></div>}
                </div>
                {!result.mastery && <p className="text-sm text-muted-foreground mt-4">Fix any red tasks and resubmit to raise your grade (90%+ earns mastery).</p>}
              </div>
              <div className="space-y-3">
                <div className="flex gap-3">
                  <Button data-testid="studio-result-review-btn" variant="outline" className="flex-1 border-white/15" onClick={() => setResult(null)}>Keep editing</Button>
                  <Button data-testid="studio-result-hub-btn" variant="outline" className="flex-1 border-white/15" onClick={() => navigate(`/studio/${track}`)}>Studio</Button>
                </div>
                {nextId ? (
                  <Button data-testid="studio-result-next-btn" className="w-full bg-primary text-primary-foreground hover:bg-[#FDBA74]" onClick={() => navigate(`/studio/${track}/${nextId}`)}>
                    Next mission <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                ) : (
                  <Button data-testid="studio-result-rankings-btn" className="w-full bg-primary text-primary-foreground hover:bg-[#FDBA74]" onClick={() => navigate("/leaderboard")}>
                    <Trophy className="w-4 h-4 mr-2" /> See rankings
                  </Button>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
