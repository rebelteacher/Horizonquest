import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import AICopilot from "@/components/AICopilot";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ArrowLeft, ScrollText, Swords, Gem, Anchor, Loader2, Trophy, Map, ArrowRight, FlaskConical, Target } from "lucide-react";
import { toast } from "sonner";
import { QUEST_LABS } from "@/lib/labs";

function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i} className="text-white font-semibold">{p.slice(2, -2)}</strong>;
    if (p.startsWith("`") && p.endsWith("`")) return <code key={i} className="px-1.5 py-0.5 rounded bg-white/10 font-mono-data text-[#22D3EE] text-[0.85em]">{p.slice(1, -1)}</code>;
    if (p.startsWith("*") && p.endsWith("*")) return <em key={i} className="text-slate-200">{p.slice(1, -1)}</em>;
    return <span key={i}>{p}</span>;
  });
}

function LessonContent({ blocks }) {
  return (
    <div className="space-y-2.5">
      {blocks.map((b, i) => {
        if (b.startsWith("## ")) return <h3 key={i} className="font-display text-xl text-primary mt-5 first:mt-0">{renderInline(b.slice(3))}</h3>;
        if (b.startsWith("- ")) return (
          <div key={i} className="flex gap-3 text-slate-300 leading-relaxed">
            <span className="mt-2 w-1.5 h-1.5 rounded-full bg-[#22D3EE] shrink-0" />
            <p className="flex-1">{renderInline(b.slice(2))}</p>
          </div>
        );
        return <p key={i} className="text-slate-300 leading-relaxed">{renderInline(b)}</p>;
      })}
    </div>
  );
}

export default function QuestView() {
  const { questId } = useParams();
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [quest, setQuest] = useState(null);
  const [nextQuestId, setNextQuestId] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAnswers({});
    setResult(null);
    setSubmitting(false);
    setLoading(true);
    (async () => {
      const cur = await api.get("/curriculum");
      const q = cur.data.quests.find((x) => x.id === questId);
      setQuest(q || null);
      if (q) {
        const sameTerritory = cur.data.quests
          .filter((x) => x.territory_id === q.territory_id)
          .sort((a, b) => a.order - b.order);
        const next = sameTerritory.find((x) => x.order === q.order + 1);
        setNextQuestId(next ? next.id : null);
      }
      setLoading(false);
    })();
  }, [questId]);

  const allAnswered = quest && quest.trial.questions.every((q) => answers[q.id]);

  const submit = async () => {
    if (!allAnswered) {
      toast.error("Answer every question before submitting the Trial.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post(`/trials/${questId}/submit`, { answers });
      setResult(res.data);
      await refresh();
      if (res.data.mastery) {
        toast.success(res.data.points_awarded > 0 ? `Mastery! +${res.data.points_awarded} Horizon Points` : "Mastery preserved ⚓");
      } else {
        toast.info(`Trial scored ${res.data.score}%. Keep pushing for mastery (80%+).`);
      }
    } catch (e) {
      toast.error("Could not submit the Trial. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (<div className="min-h-screen"><AppNav /><div className="flex justify-center py-40"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div></div>);
  }
  if (!quest) {
    return (<div className="min-h-screen"><AppNav /><div className="text-center py-40 text-muted-foreground">Quest not found. <button className="text-primary underline" onClick={() => navigate("/map")}>Back to map</button></div></div>);
  }

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <button data-testid="back-to-map-btn" onClick={() => navigate("/map")} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to the map
        </button>

        <div className="hq-fade-up">
          <p className="text-xs uppercase tracking-widest font-mono-data text-primary">DOK {quest.dok} · {quest.standard.code} · {quest.points} pts</p>
          <h1 className="font-display text-4xl sm:text-5xl mt-2 tracking-tight">{quest.title}</h1>
          <p className="text-sm text-muted-foreground mt-2">{quest.standard.description}</p>
          {quest.learner_goal && (
            <div data-testid="quest-learner-goal" className="mt-4 flex items-start gap-3 rounded-xl border border-[#22D3EE]/30 bg-[#22D3EE]/5 px-4 py-3">
              <Target className="w-5 h-5 text-[#22D3EE] shrink-0 mt-0.5" />
              <p className="text-slate-200"><span className="text-[11px] uppercase tracking-widest font-mono-data text-[#22D3EE] mr-2">Your Goal</span>{quest.learner_goal}</p>
            </div>
          )}
        </div>

        {/* Lesson */}
        <section className="mt-8 hq-glass rounded-2xl p-6 border-t border-t-primary/30 hq-fade-up" style={{ animationDelay: "0.1s" }}>
          <h2 className="font-display text-2xl flex items-center gap-2 mb-4"><ScrollText className="w-5 h-5 text-primary" /> The Lesson</h2>
          <LessonContent blocks={quest.lesson} />
        </section>

        {/* Hands-on lab callout */}
        {QUEST_LABS[quest.id] && (
          <section className="mt-6 rounded-2xl p-6 border border-[#22D3EE]/30 bg-[#22D3EE]/5 hq-fade-up" style={{ animationDelay: "0.15s" }}>
            <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
              <div className="flex items-start gap-3">
                <div className="w-11 h-11 rounded-xl bg-[#22D3EE]/15 flex items-center justify-center shrink-0"><FlaskConical className="w-6 h-6 text-[#22D3EE]" /></div>
                <div>
                  <h2 className="font-display text-2xl">{QUEST_LABS[quest.id].title}</h2>
                  <p className="text-sm text-muted-foreground mt-0.5">{QUEST_LABS[quest.id].desc}</p>
                </div>
              </div>
              <Button
                data-testid="launch-lab-btn"
                onClick={() => navigate(QUEST_LABS[quest.id].path ? QUEST_LABS[quest.id].path : `/lab/${QUEST_LABS[quest.id].tool}?quest=${quest.id}`)}
                className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9] shrink-0 hq-glow-teal"
              >
                Launch Hands-On Lab <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </section>
        )}

        {/* Trial */}
        <section className="mt-6 hq-fade-up" style={{ animationDelay: "0.2s" }}>
          <h2 className="font-display text-2xl flex items-center gap-2 mb-4"><Swords className="w-5 h-5 text-[#E11D48]" /> The Trial</h2>
          <div className="space-y-5">
            {quest.trial.questions.map((q, idx) => (
              <div key={q.id} className="hq-glass rounded-2xl p-6" data-testid={`trial-question-${q.id}`}>
                <p className="font-medium mb-4"><span className="font-mono-data text-primary mr-2">{idx + 1}.</span>{q.prompt}</p>
                <RadioGroup value={answers[q.id] || ""} onValueChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}>
                  {q.options.map((opt, oi) => (
                    <div key={oi} className="flex items-center gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors">
                      <RadioGroupItem value={opt} id={`${q.id}-${oi}`} data-testid={`option-${q.id}-${oi}`} />
                      <Label htmlFor={`${q.id}-${oi}`} className="flex-1 cursor-pointer text-slate-200 font-normal">{opt}</Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            ))}
          </div>
        </section>

        <Button
          data-testid="submit-trial-btn"
          onClick={submit}
          disabled={submitting}
          className="mt-8 w-full py-6 text-base bg-primary text-primary-foreground hover:bg-[#FDBA74] hq-glow-gold"
        >
          {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : "Complete the Trial ⚔️"}
        </Button>
      </div>

      {/* Result dialog */}
      <Dialog open={!!result} onOpenChange={(o) => !o && setResult(null)}>
        <DialogContent className="hq-glass border-white/10 max-w-md">
          {result && (
            <>
              <DialogHeader>
                <DialogTitle className="font-display text-3xl text-center">
                  {result.mastery ? "Territory Conquered!" : "Trial Complete"}
                </DialogTitle>
                <DialogDescription className="text-center">Your Trial results are in, Explorer.</DialogDescription>
              </DialogHeader>
              <div className="text-center py-4">
                <div className={`mx-auto w-24 h-24 rounded-full flex items-center justify-center mb-4 ${result.mastery ? "bg-primary/15 hq-glow-gold" : "bg-white/5"}`}>
                  <span className={`font-mono-data text-3xl ${result.mastery ? "text-primary" : "text-slate-300"}`}>{result.score}%</span>
                </div>
                <p className="text-slate-300">You answered <b>{result.correct}/{result.total}</b> correctly.</p>

                <div className="flex justify-center gap-6 mt-6">
                  <div className="flex items-center gap-2 text-primary"><Gem className="w-5 h-5" /><span className="font-mono-data text-xl">+{result.points_awarded}</span></div>
                  {result.compass_mark_earned && <div className="flex items-center gap-2 text-[#22D3EE]"><Anchor className="w-5 h-5" /><span className="font-mono-data text-xl">+1 Mark</span></div>}
                </div>

                {!result.mastery && <p className="text-sm text-muted-foreground mt-5">Reach 80% to earn full points and a Compass Mark. Retry anytime!</p>}
              </div>
              <div className="space-y-3">
                <div className="flex gap-3">
                  <Button data-testid="result-retry-btn" variant="outline" className="flex-1 border-white/15" onClick={() => setResult(null)}>Review answers</Button>
                  <Button data-testid="result-map-btn" variant="outline" className="flex-1 border-white/15" onClick={() => navigate("/map")}>
                    <Map className="w-4 h-4 mr-2" /> Back to Map
                  </Button>
                </div>
                {result.mastery && nextQuestId ? (
                  <Button data-testid="result-next-quest-btn" className="w-full bg-primary text-primary-foreground hover:bg-[#FDBA74]" onClick={() => navigate(`/quest/${nextQuestId}`)}>
                    Continue to next quest <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                ) : (
                  <Button data-testid="result-rankings-btn" className="w-full bg-primary text-primary-foreground hover:bg-[#FDBA74]" onClick={() => navigate("/leaderboard")}>
                    <Trophy className="w-4 h-4 mr-2" /> See rankings
                  </Button>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      <AICopilot questId={quest.id} questTitle={quest.title} />
    </div>
  );
}
