import { useEffect, useRef, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import DocEditorCore from "@/components/studio/DocEditorCore";
import SheetEditorCore from "@/components/studio/SheetEditorCore";
import SlideEditorCore from "@/components/studio/SlideEditorCore";
import EmailClientCore from "@/components/studio/EmailClientCore";
import { checkTask } from "@/lib/studioGrade";
import { findBoundaryIndex } from "@/components/studio/Squiggly";
import { exportNodeToPDF } from "@/lib/pdf";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ArrowLeft, ArrowRight, ScrollText, CheckCircle2, Circle, Loader2, Download, Gem, Anchor, ListChecks, Trophy, ClipboardCheck, SpellCheck, AlertTriangle, Wand2 } from "lucide-react";
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
  const { refresh, user } = useAuth();
  const isGuide = user?.role === "guide";
  const pageRef = useRef(null);

  const [config, setConfig] = useState(null);
  const [mission, setMission] = useState(null);
  const [nextId, setNextId] = useState(null);
  const [nextCheckpoint, setNextCheckpoint] = useState(null);
  const [nextTask, setNextTask] = useState(null);
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [gate, setGate] = useState(true);
  const [checking, setChecking] = useState(false);
  const [docIssues, setDocIssues] = useState([]);
  const [emailIssues, setEmailIssues] = useState([]);
  const [review, setReview] = useState(null); // { issues, blocking }
  const writable = track === "docs" || track === "email";

  useEffect(() => {
    setLoading(true); setResult(null); setDocIssues([]); setEmailIssues([]); setReview(null);
    api.get("/studio/writing-gate").then((r) => setGate(r.data.gate !== false)).catch(() => setGate(true));
    (async () => {
      const res = await api.get(`/studio/${track}`);
      setConfig(res.data.config);
      const missions = res.data.missions.sort((a, b) => a.order - b.order);
      const blockTasks = res.data.block_tasks || [];
      const drills = res.data.drills || [];
      const m = missions.find((x) => x.id === missionId) || blockTasks.find((x) => x.id === missionId) || drills.find((x) => x.id === missionId);
      setMission(m || null);
      if (m) {
        let freshDoc = JSON.parse(JSON.stringify(m.doc));
        if (track === "email" && !isGuide) {
          try {
            const dr = await api.get(`/studio/email/${missionId}/drafts`);
            const drafts = dr.data.drafts || [];
            if (drafts.length) freshDoc = { ...freshDoc, messages: [...(freshDoc.messages || []), ...drafts] };
          } catch (e) { /* no saved drafts */ }
        }
        setDoc(freshDoc);
        const idx = missions.findIndex((x) => x.id === missionId);
        setNextId(!m.is_block_task && idx >= 0 && idx < missions.length - 1 ? missions[idx + 1].id : null);
        // Route to the block's checkpoint after the block task, or after the last lesson of the block.
        try {
          const ar = await api.get(`/assessments/track/${track}`);
          const cps = ar.data.checkpoints || [];
          if (m.is_block_task) {
            const cp = cps.find((c) => c.id === m.block_cp);
            setNextCheckpoint(cp ? { id: cp.id, unlocked: !!cp.unlocked } : null);
          } else {
            const cp = cps.find((c) => (c.covers || []).includes(missionId));
            const blockMissions = cp ? missions.filter((x) => cp.covers.includes(x.id)) : [];
            const isLastOfBlock = blockMissions.length > 0 && blockMissions[blockMissions.length - 1].id === missionId;
            // After the last lesson, send them to the Block Task if one exists, else the checkpoint.
            if (cp && isLastOfBlock) {
              const bt = blockTasks.find((t) => t.block_cp === cp.id);
              if (bt) setNextTask({ id: bt.id, title: bt.title });
              else setNextCheckpoint({ id: cp.id, unlocked: !!cp.unlocked });
            }
          }
        } catch (e) { setNextCheckpoint(null); }
      }
      setLoading(false);
    })();
  }, [track, missionId, isGuide]);

  // Persist email drafts so students can finish them later (explorers only, debounced).
  useEffect(() => {
    if (track !== "email" || !doc || isGuide) return;
    const drafts = (doc.messages || []).filter((m) => m.folder === "drafts");
    const t = setTimeout(() => { api.put(`/studio/email/${missionId}/drafts`, { drafts }).catch(() => {}); }, 800);
    return () => clearTimeout(t);
  }, [doc, track, missionId, isGuide]);

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

  const proofread = async (text) => {
    if (!text || !text.trim()) return [];
    const res = await api.post("/ai/proofread", { text });
    return res.data.issues || [];
  };

  // Docs is proofread per block so every issue is tied to its exact block (blockId).
  const getDocSegments = () => (doc.blocks || [])
    .filter((b) => b.type !== "table" && (b.text || "").trim())
    .map((b) => ({ id: b.id, text: b.text }));

  const proofreadDoc = async () => {
    const segs = getDocSegments();
    const lists = await Promise.all(segs.map(async (s) => {
      try {
        const res = await api.post("/ai/proofread", { text: s.text });
        return (res.data.issues || []).map((i) => ({ ...i, blockId: s.id }));
      } catch (e) { return []; }
    }));
    return lists.flat();
  };

  const getLatestSent = () => {
    const sent = (doc.messages || []).filter((m) => m.folder === "sent");
    const m = sent[sent.length - 1];
    if (!m) return { body: "", msgId: null };
    return { body: m.bodyStudent != null ? m.bodyStudent : (m.body || ""), msgId: m.id };
  };

  const proofreadEmail = async () => {
    const { body } = getLatestSent();
    if (!body.trim()) return [];
    const issues = await proofread(body);
    return issues.map((i) => ({ ...i, blockId: "__email__" }));
  };

  const runIssueCheck = () => (track === "docs" ? proofreadDoc() : proofreadEmail());
  const hasCheckText = () => (track === "docs" ? getDocSegments().length > 0 : !!getLatestSent().body.trim());

  const replaceOnce = (str, needle, repl) => {
    const idx = findBoundaryIndex(str, needle);
    if (idx < 0) return { str, done: false };
    return { str: str.slice(0, idx) + repl + str.slice(idx + needle.length), done: true };
  };

  const applyIssueToDoc = (d, issue) => {
    if (!issue.suggestion) return d;
    if (track === "docs") {
      return {
        ...d,
        blocks: (d.blocks || []).map((b) => {
          if (b.id !== issue.blockId || b.type === "table") return b;
          const { str, done } = replaceOnce(b.text || "", issue.text, issue.suggestion);
          return done ? { ...b, text: str } : b;
        }),
      };
    }
    const { msgId } = getLatestSent();
    return {
      ...d,
      messages: (d.messages || []).map((m) => {
        if (m.id !== msgId) return m;
        const nb = replaceOnce(m.body || "", issue.text, issue.suggestion);
        const ns = replaceOnce(m.bodyStudent != null ? m.bodyStudent : (m.body || ""), issue.text, issue.suggestion);
        return { ...m, body: nb.str, bodyStudent: ns.str };
      }),
    };
  };

  const applyFix = (issue) => {
    setDoc((d) => applyIssueToDoc(d, issue));
    const drop = (arr) => arr.filter((i) => i !== issue);
    if (track === "docs") setDocIssues(drop); else setEmailIssues(drop);
    setReview((r) => (r ? { ...r, issues: drop(r.issues) } : r));
  };

  const applyAllFixes = () => {
    const issues = (review?.issues || []).filter((i) => i.suggestion);
    setDoc((d) => issues.reduce((acc, iss) => applyIssueToDoc(acc, iss), d));
    if (track === "docs") setDocIssues([]); else setEmailIssues([]);
    setReview(null);
    toast.success("Applied the suggested fixes — give it one more read! ⚓");
  };

  const runCheck = async () => {
    if (!hasCheckText()) {
      toast.info(track === "email" ? "Send your email first, then I can check the writing." : "Write something first, then I can check it.");
      return;
    }
    setChecking(true);
    try {
      const issues = await runIssueCheck();
      if (track === "docs") setDocIssues(issues); else setEmailIssues(issues);
      if (!issues.length) toast.success("Nice writing — no spelling or grammar issues found! ⚓");
      else { setReview({ issues, blocking: false }); toast.warning(`Found ${issues.length} thing${issues.length > 1 ? "s" : ""} to fix.`); }
    } catch (e) {
      toast.error("The Writing Coach was unavailable. Try again in a moment.");
    } finally {
      setChecking(false);
    }
  };

  const doSubmit = async (writingCount = 0) => {
    setSubmitting(true);
    try {
      const res = await api.post(`/studio/${track}/${missionId}/submit`, { doc, writing_issues: writingCount });
      setResult(res.data);
      if (!res.data.preview) await refresh();
      if (nextCheckpoint) {
        try {
          const ar = await api.get(`/assessments/track/${track}`);
          const cp = (ar.data.checkpoints || []).find((c) => c.id === nextCheckpoint.id);
          if (cp) setNextCheckpoint((nc) => (nc ? { ...nc, unlocked: !!cp.unlocked } : nc));
        } catch (e) { /* keep prior state */ }
      }
      if (res.data.blank_send) toast.warning("That email was blank — write a real message (greeting, a few sentences, and a sign-off) to earn points.");
      else if (res.data.preview) toast.info(`Preview graded ${res.data.grade} (${res.data.score}%). Not saved.`);
      else if (res.data.mastery) toast.success(`Graded ${res.data.grade} · +${res.data.points_awarded} Horizon Points`);
      else toast.info(`Graded ${res.data.grade} (${res.data.score}%). Reach 90% for mastery.`);
    } catch (e) {
      toast.error("Could not submit for grading.");
    } finally {
      setSubmitting(false);
    }
  };

  const submit = async () => {
    // AI writing gate for Docs & Email — auto-check before grading.
    if (writable && !isGuide && hasCheckText()) {
      setChecking(true);
      let issues = [];
      try { issues = await runIssueCheck(); } catch (e) { issues = []; }
      setChecking(false);
      if (track === "docs") setDocIssues(issues); else setEmailIssues(issues);
      if (issues.length) {
        if (gate) {
          setReview({ issues, blocking: true });
          toast.error(`Fix ${issues.length} writing issue${issues.length > 1 ? "s" : ""} before submitting.`);
          return;
        }
        toast.warning(`Submitted with ${issues.length} unresolved writing issue${issues.length > 1 ? "s" : ""} — flagged for your teacher.`);
        await doSubmit(issues.length);
        return;
      }
    }
    await doSubmit(0);
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
          <div className="lg:col-span-2 order-2 lg:order-1 min-w-0">
            {track === "sheets"
              ? <SheetEditorCore doc={doc} setDoc={setDoc} config={config} pageRef={pageRef} />
              : track === "slides"
                ? <SlideEditorCore doc={doc} setDoc={setDoc} config={config} pageRef={pageRef} />
                : track === "email"
                  ? <EmailClientCore doc={doc} setDoc={setDoc} config={config} proofread={isGuide ? null : proofread} readingIssues={emailIssues} />
                  : <DocEditorCore doc={doc} setDoc={setDoc} config={config} pageRef={pageRef} issues={docIssues} />}
            <div className="flex flex-wrap gap-3 mt-4">
              {track !== "email" && (
                <Button data-testid="studio-export-btn" variant="outline" className="border-white/15" onClick={doExport}>
                  <Download className="w-4 h-4 mr-2" /> Export PDF
                </Button>
              )}
              {track === "docs" && !isGuide && (
                <Button data-testid="studio-check-writing-btn" variant="outline" className="border-[#818CF8]/40 text-[#a5b4fc] hover:bg-[#818CF8]/10" onClick={runCheck} disabled={checking}>
                  {checking ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <SpellCheck className="w-4 h-4 mr-2" />} Check my writing
                </Button>
              )}
              <Button data-testid="studio-submit-btn" onClick={submit} disabled={submitting || checking} className="bg-primary text-primary-foreground hover:bg-[#FDBA74]">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : checking ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Checking…</> : <>Submit for a grade{allDone ? " ✓" : ""}</>}
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
                {result.preview ? (
                  <p data-testid="studio-result-preview-note" className="text-sm text-[#22D3EE] mt-4">Teaching preview — this attempt was not graded or saved to any gradebook.</p>
                ) : (
                  <>
                    <div className="flex justify-center gap-6 mt-5">
                      <div className="flex items-center gap-2 text-primary"><Gem className="w-5 h-5" /><span className="font-mono-data text-xl">+{result.points_awarded}</span></div>
                      {result.compass_mark_earned && <div className="flex items-center gap-2 text-[#22D3EE]"><Anchor className="w-5 h-5" /><span className="font-mono-data text-xl">+1 Mark</span></div>}
                    </div>
                    {result.blank_send && <p data-testid="studio-result-blank-note" className="text-sm text-[#FB923C] mt-4">You sent a blank email, so it earned <b>0 points</b>. Write a real message — a greeting, a few sentences, and a sign-off — then resubmit.</p>}
                    {!result.mastery && !result.blank_send && <p className="text-sm text-muted-foreground mt-4">Fix any red tasks and resubmit to raise your grade (90%+ earns mastery).</p>}
                  </>
                )}
              </div>
              {result.ai_feedback && (
                <div data-testid="studio-ai-feedback" className="rounded-xl border border-[#818CF8]/40 bg-[#818CF8]/10 p-4 mb-4 text-left">
                  <p className="text-xs uppercase tracking-widest font-mono-data text-[#a5b4fc] mb-1">AI Coach {result.ai_rating ? `· ${result.ai_rating}` : ""}</p>
                  <p className="text-sm text-slate-200">{result.ai_feedback}</p>
                </div>
              )}
              <div className="space-y-3">
                <div className="flex gap-3">
                  <Button data-testid="studio-result-review-btn" variant="outline" className="flex-1 border-white/15" onClick={() => setResult(null)}>Keep editing</Button>
                  <Button data-testid="studio-result-hub-btn" variant="outline" className="flex-1 border-white/15" onClick={() => navigate(`/studio/${track}`)}>Studio</Button>
                </div>
                {nextTask ? (
                  <Button data-testid="studio-result-blocktask-btn" className="w-full bg-[#a5b4fc] text-[#04121f] hover:bg-[#c7d2fe]" onClick={() => navigate(`/studio/${track}/${nextTask.id}`)}>
                    <ClipboardCheck className="w-4 h-4 mr-2" /> Start the Block Task
                  </Button>
                ) : nextCheckpoint ? (
                  nextCheckpoint.unlocked ? (
                    <Button data-testid="studio-result-checkpoint-btn" className="w-full bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9] hq-glow-teal" onClick={() => navigate(`/assessment/${nextCheckpoint.id}`)}>
                      <ClipboardCheck className="w-4 h-4 mr-2" /> Take the Checkpoint
                    </Button>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-xs text-muted-foreground text-center">Pass all lessons in this block to unlock the Checkpoint.</p>
                      <Button data-testid="studio-result-finishblock-btn" variant="outline" className="w-full border-[#22D3EE]/40 text-[#22D3EE] hover:bg-[#22D3EE]/10" onClick={() => navigate(`/studio/${track}`)}>
                        Back to this block's lessons <ArrowRight className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  )
                ) : nextId ? (
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

      {/* AI Writing Coach review dialog */}
      <Dialog open={!!review} onOpenChange={(o) => !o && setReview(null)}>
        <DialogContent className="hq-glass border-white/10 max-w-lg">
          {review && (
            <>
              <DialogHeader>
                <DialogTitle className="font-display text-2xl flex items-center gap-2">
                  <SpellCheck className="w-5 h-5 text-[#a5b4fc]" /> Writing Coach
                </DialogTitle>
                <DialogDescription>
                  {review.blocking
                    ? `Fix these ${review.issues.length} thing${review.issues.length > 1 ? "s" : ""} before you can submit. Tap "Apply fix" or edit it yourself.`
                    : `Found ${review.issues.length} thing${review.issues.length > 1 ? "s" : ""} to review. Red underlines mark them in your work.`}
                </DialogDescription>
              </DialogHeader>
              {review.blocking && (
                <div data-testid="studio-writing-halt-note" className="flex items-start gap-2 rounded-lg border border-[#E11D48]/40 bg-[#E11D48]/10 p-3 text-sm text-[#fecdd3]">
                  <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>Your teacher requires clean writing before submitting. Fix each item, then submit again.</span>
                </div>
              )}
              <div className="max-h-72 overflow-y-auto hq-scrollbar space-y-2.5 pr-1">
                {review.issues.length === 0 && <p className="text-sm text-emerald-300 py-4 text-center">All fixed — submit when you're ready! ⚓</p>}
                {review.issues.map((iss, i) => (
                  <div key={i} data-testid={`writing-issue-${i}`} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-[10px] uppercase tracking-widest font-mono-data px-1.5 py-0.5 rounded bg-[#E11D48]/15 text-[#fb7185]">{iss.type}</span>
                      <span className="text-sm text-white line-through decoration-[#E11D48]/70">{iss.text}</span>
                      {iss.suggestion && <><ArrowRight className="w-3.5 h-3.5 text-slate-500" /><span className="text-sm text-emerald-300 font-medium">{iss.suggestion}</span></>}
                    </div>
                    <p className="text-xs text-slate-400">{iss.message}</p>
                    {iss.suggestion && (
                      <button data-testid={`writing-apply-${i}`} onClick={() => applyFix(iss)} className="mt-2 inline-flex items-center gap-1.5 text-xs text-[#22D3EE] hover:underline">
                        <Wand2 className="w-3.5 h-3.5" /> Apply fix
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <div className="flex gap-3 pt-1">
                {review.issues.some((i) => i.suggestion) && (
                  <Button data-testid="writing-apply-all-btn" onClick={applyAllFixes} className="flex-1 bg-[#a5b4fc] text-[#04121f] hover:bg-[#c7d2fe]">
                    <Wand2 className="w-4 h-4 mr-2" /> Apply all fixes
                  </Button>
                )}
                <Button data-testid="writing-close-btn" variant="outline" className="flex-1 border-white/15" onClick={() => setReview(null)}>
                  {review.blocking ? "I'll fix these" : "Done"}
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
