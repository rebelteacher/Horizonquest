import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, CheckCircle2, XCircle, Trophy, RotateCcw, AlertTriangle, Gem } from "lucide-react";

const LETTERS = ["A", "B", "C", "D"];

export default function AssessmentRunner() {
  const { assessmentId } = useParams();
  const navigate = useNavigate();
  const { user, refresh } = useAuth();
  const isGuide = user?.role === "guide";

  const [phase, setPhase] = useState("loading"); // loading | error | quiz | result
  const [errorMsg, setErrorMsg] = useState("");
  const [attempt, setAttempt] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const start = useCallback(async () => {
    setPhase("loading"); setAnswers({}); setResult(null);
    try {
      const r = await api.post(`/assessments/${assessmentId}/start`);
      setAttempt(r.data);
      setPhase("quiz");
    } catch (e) {
      setErrorMsg(e?.response?.data?.detail || "Could not start this test.");
      setPhase("error");
    }
  }, [assessmentId]);

  useEffect(() => { start(); }, [start]);

  const answered = attempt ? Object.keys(answers).length : 0;
  const totalQ = attempt?.questions?.length || 0;

  const submit = async () => {
    if (answered < totalQ) { toast.error(`Answer all ${totalQ} questions first (${answered}/${totalQ} done).`); return; }
    setSubmitting(true);
    try {
      const r = await api.post(`/assessments/attempts/${attempt.attempt_id}/submit`, { answers });
      setResult(r.data);
      setPhase("result");
      if (!r.data.preview) await refresh();
      if (r.data.preview) toast.info(`Preview: ${r.data.score}% — not saved.`);
      else if (r.data.passed) toast.success(`Passed with ${r.data.score}%!${r.data.points_awarded ? ` +${r.data.points_awarded} HP` : ""}`);
      else toast.warning(`Scored ${r.data.score}%. ${r.data.attempts_remaining > 0 ? "You have a retake left." : "No attempts remaining."}`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not submit.");
    } finally { setSubmitting(false); }
  };

  const backToStudio = () => navigate(isGuide ? "/guide" : "/studio/email");

  if (phase === "loading") return (<div className="min-h-screen"><AppNav /><div className="flex justify-center py-40"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div></div>);

  if (phase === "error") return (
    <div className="min-h-screen"><AppNav />
      <div className="max-w-xl mx-auto px-6 py-24 text-center">
        <AlertTriangle className="w-10 h-10 text-[#FB923C] mx-auto mb-4" />
        <h1 className="font-display text-2xl mb-2">Can't start this test</h1>
        <p className="text-muted-foreground mb-6" data-testid="assessment-error-msg">{errorMsg}</p>
        <Button data-testid="assessment-back-btn" onClick={backToStudio} variant="outline">Back to Skill Studio</Button>
      </div>
    </div>
  );

  if (phase === "result") {
    const pct = result.score;
    const color = result.passed ? "#34D399" : "#FB923C";
    return (
      <div className="min-h-screen"><AppNav />
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
          <div className="hq-glass rounded-2xl p-8 text-center mb-6">
            {result.passed ? <Trophy className="w-12 h-12 mx-auto mb-3" style={{ color }} /> : <XCircle className="w-12 h-12 mx-auto mb-3" style={{ color }} />}
            <h1 className="font-display text-3xl" data-testid="assessment-result-score" style={{ color }}>{pct}%</h1>
            <p className="text-slate-300 mt-1">{result.correct}/{result.total} correct · {result.passed ? "Passed" : "Not passed"}</p>
            {result.preview ? (
              <p className="text-sm text-[#22D3EE] mt-4">Teaching preview — not saved to any gradebook.</p>
            ) : (
              <div className="mt-4 space-y-1">
                {result.points_awarded > 0 && <p className="flex items-center justify-center gap-2 text-primary"><Gem className="w-5 h-5" /><span className="font-mono-data text-xl">+{result.points_awarded} Horizon Points</span></p>}
                <p className="text-sm text-muted-foreground">Attempts remaining: <b data-testid="assessment-attempts-remaining">{result.attempts_remaining}</b></p>
              </div>
            )}
            <div className="flex flex-wrap gap-3 justify-center mt-6">
              {!result.passed && result.attempts_remaining > 0 && (
                <Button data-testid="assessment-retake-btn" onClick={start} className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]"><RotateCcw className="w-4 h-4 mr-2" />Retake</Button>
              )}
              <Button data-testid="assessment-done-btn" onClick={backToStudio} variant="outline">Back to Skill Studio</Button>
            </div>
          </div>

          <h2 className="font-display text-xl mb-3">Review</h2>
          <div className="space-y-3">
            {result.review.map((r, i) => {
              const gotIt = r.chosen === r.correct;
              return (
                <div key={i} data-testid={`review-q-${i}`} className="hq-glass rounded-xl p-4">
                  <div className="flex items-start gap-2">
                    {gotIt ? <CheckCircle2 className="w-5 h-5 text-[#34D399] shrink-0 mt-0.5" /> : <XCircle className="w-5 h-5 text-[#E11D48] shrink-0 mt-0.5" />}
                    <p className="text-sm text-white font-medium">{i + 1}. {r.question}</p>
                  </div>
                  <div className="mt-2 ml-7 space-y-1">
                    {r.options.map((opt, oi) => {
                      const isCorrect = oi === r.correct;
                      const isChosen = oi === r.chosen;
                      return (
                        <div key={oi} className={`text-sm px-2 py-1 rounded ${isCorrect ? "bg-[#34D399]/15 text-[#34D399]" : isChosen ? "bg-[#E11D48]/15 text-[#fca5a5]" : "text-slate-400"}`}>
                          {LETTERS[oi]}. {opt}{isCorrect ? " ✓" : isChosen ? " (your answer)" : ""}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // quiz phase
  return (
    <div className="min-h-screen"><AppNav />
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <button data-testid="assessment-quiz-back" onClick={backToStudio} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4"><ArrowLeft className="w-4 h-4" /> Leave test</button>
        <div className="hq-glass rounded-2xl p-5 mb-6 sticky top-16 z-10">
          <h1 className="font-display text-2xl" data-testid="assessment-title">{attempt.title}</h1>
          <p className="text-sm text-muted-foreground mt-1">Answer all questions. You need {attempt.pass}% to pass. Questions and answer choices are shuffled for every student.</p>
          <div className="mt-3 h-2 rounded-full bg-white/10 overflow-hidden"><div className="h-full bg-[#22D3EE] transition-all" style={{ width: `${totalQ ? (answered / totalQ) * 100 : 0}%` }} /></div>
          <p className="text-xs text-muted-foreground mt-1" data-testid="assessment-progress">{answered}/{totalQ} answered</p>
        </div>

        <div className="space-y-4">
          {attempt.questions.map((q, i) => (
            <div key={q.qid} data-testid={`quiz-q-${i}`} className="hq-glass rounded-xl p-4">
              <p className="text-sm text-white font-medium mb-3">{i + 1}. {q.question}</p>
              <div className="grid gap-2">
                {q.options.map((opt, oi) => {
                  const selected = answers[q.qid] === oi;
                  return (
                    <button key={oi} data-testid={`quiz-q-${i}-opt-${oi}`} onClick={() => setAnswers((a) => ({ ...a, [q.qid]: oi }))}
                      className={`text-left text-sm px-3 py-2 rounded-lg border transition-colors flex items-center gap-2 ${selected ? "border-[#22D3EE] bg-[#22D3EE]/15 text-white" : "border-white/10 text-slate-300 hover:bg-white/5"}`}>
                      <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${selected ? "bg-[#22D3EE] text-[#04121f]" : "bg-white/10"}`}>{LETTERS[oi]}</span>
                      {opt}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="sticky bottom-4 mt-6">
          <Button data-testid="assessment-submit-btn" onClick={submit} disabled={submitting} className="w-full h-12 bg-[#818CF8] hover:bg-[#6366F1] text-white text-base">
            {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : `Submit test (${answered}/${totalQ})`}
          </Button>
        </div>
      </div>
    </div>
  );
}
