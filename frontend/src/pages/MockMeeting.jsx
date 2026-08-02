import { useState, useRef, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { Button } from "@/components/ui/button";
import { Gavel, ArrowLeft, ArrowRight, CheckCircle2, XCircle, Gem, Trophy, Map, RotateCcw, Anchor } from "lucide-react";
import { toast } from "sonner";

const SCENES = [
  {
    id: "call_to_order",
    phase: "Call to Order",
    narration: "The clock strikes 9:00. Members are seated and still chatting. You are the Chair.",
    prompt: "How do you begin the meeting?",
    options: [
      { text: "Rap the gavel and say, “I call this meeting to order.”", correct: true, feedback: "Exactly — the Chair officially opens the meeting so everyone knows business has begun." },
      { text: "Wait quietly until everyone stops talking on their own.", correct: false, feedback: "A Chair sets the tone. You must officially call the meeting to order." },
      { text: "Jump straight into the first vote.", correct: false, feedback: "You can't vote before the meeting is opened and the agenda is set." },
    ],
  },
  {
    id: "quorum",
    phase: "Quorum",
    narration: "Before conducting business, you glance around the room to count who's present.",
    prompt: "What must be present to legally conduct business?",
    options: [
      { text: "A quorum — the minimum number of members required.", correct: true, feedback: "Right. Without a quorum, any decisions you make wouldn't be official." },
      { text: "A guest speaker.", correct: false, feedback: "A guest is nice to have, but it's a quorum that lets you conduct business." },
      { text: "Snacks for everyone.", correct: false, feedback: "Tempting — but it's a quorum you need, not snacks." },
    ],
  },
  {
    id: "agenda",
    phase: "Agenda",
    narration: "The meeting is open and a quorum is confirmed.",
    prompt: "What is the correct next step?",
    options: [
      { text: "Present and approve the agenda.", correct: true, feedback: "Yes — the agenda is the plan; approving it keeps the meeting on track." },
      { text: "Adjourn immediately.", correct: false, feedback: "You just started! Adjourning now skips all the business." },
      { text: "Skip the agenda and improvise.", correct: false, feedback: "Without an agenda the meeting loses structure and focus." },
    ],
  },
  {
    id: "motion_make",
    phase: "Motion",
    narration: "During new business, a member wants the club to host a fundraiser.",
    prompt: "What should that member do?",
    options: [
      { text: "Make a motion: “I move that we host a fundraiser.”", correct: true, feedback: "Correct — formal proposals are introduced as motions." },
      { text: "Just start planning it without a vote.", correct: false, feedback: "Group decisions need a motion and a vote, not solo action." },
      { text: "Email you about it after the meeting.", correct: false, feedback: "This is the moment to raise it — as a motion." },
    ],
  },
  {
    id: "motion_second",
    phase: "Second",
    narration: "The motion to host a fundraiser has been made.",
    prompt: "Before it can be discussed, the motion needs a…",
    options: [
      { text: "Second from another member.", correct: true, feedback: "Right — a second shows at least two members want to discuss it." },
      { text: "Full budget attached.", correct: false, feedback: "Budgets can come later; first it needs a second." },
      { text: "Round of applause.", correct: false, feedback: "Nice energy, but a motion needs a second, not applause." },
    ],
  },
  {
    id: "discuss_vote",
    phase: "Discussion & Vote",
    narration: "The motion has been made and seconded.",
    prompt: "As Chair, what do you do now?",
    options: [
      { text: "Open discussion, then call for a vote.", correct: true, feedback: "Exactly — members debate, then you put it to a vote." },
      { text: "Declare it passed automatically.", correct: false, feedback: "Every motion must be voted on — you can't just declare it passed." },
      { text: "Table it forever.", correct: false, feedback: "Tabling ends discussion; here the group wants to decide now." },
    ],
  },
  {
    id: "vote_result",
    phase: "Result",
    narration: "The votes are counted: 8 in favor, 3 against.",
    prompt: "What is the result of the motion?",
    options: [
      { text: "It passes by majority vote.", correct: true, feedback: "Correct — more than half voted yes, so it carries." },
      { text: "It fails.", correct: false, feedback: "8 beats 3 — that's a majority in favor." },
      { text: "It needs everyone to agree.", correct: false, feedback: "Most motions pass with a simple majority, not unanimity." },
    ],
  },
  {
    id: "adjourn",
    phase: "Adjourn",
    narration: "All items on the agenda are complete.",
    prompt: "How do you properly end the meeting?",
    options: [
      { text: "Entertain a motion to adjourn, then close the meeting.", correct: true, feedback: "Perfectly done, Chair — the meeting adjourns in good order." },
      { text: "Just get up and walk out.", correct: false, feedback: "A meeting is closed formally by adjourning, not by walking off." },
      { text: "Start brand-new business.", correct: false, feedback: "Business is finished — it's time to adjourn." },
    ],
  },
];

export default function MockMeeting() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const questId = params.get("quest") || "t1-q8";
  const { refresh } = useAuth();

  const [idx, setIdx] = useState(0);
  const [picked, setPicked] = useState(null);
  const [solved, setSolved] = useState(false);
  const [wrongPicks, setWrongPicks] = useState([]);
  const [mistakes, setMistakes] = useState(0);
  const [finished, setFinished] = useState(false);
  const [award, setAward] = useState(null);
  const awardedRef = useRef(false);

  const scene = SCENES[idx];
  const progress = Math.round(((idx + (solved ? 1 : 0)) / SCENES.length) * 100);

  const choose = (oi) => {
    if (solved) return;
    const opt = scene.options[oi];
    if (opt.correct) {
      setPicked(oi);
      setSolved(true);
    } else {
      if (!wrongPicks.includes(oi)) {
        setWrongPicks((w) => [...w, oi]);
        setMistakes((m) => m + 1);
      }
      setPicked(oi);
    }
  };

  const next = () => {
    if (idx < SCENES.length - 1) {
      setIdx((i) => i + 1);
      setPicked(null);
      setSolved(false);
      setWrongPicks([]);
    } else {
      finish();
    }
  };

  const finish = async () => {
    setFinished(true);
    if (awardedRef.current) return;
    awardedRef.current = true;
    try {
      const res = await api.post(`/labs/${questId}/complete`);
      setAward(res.data);
      await refresh();
      if (res.data.bonus > 0) toast.success(`Meeting adjourned! +${res.data.bonus} Horizon Points`);
      else toast.info("Meeting adjourned! (bonus already earned)");
    } catch (e) {
      toast.error("Could not save your lab result.");
    }
  };

  const restart = () => {
    setIdx(0); setPicked(null); setSolved(false); setWrongPicks([]); setMistakes(0); setFinished(false);
  };

  const accuracy = Math.round((SCENES.length / (SCENES.length + mistakes)) * 100);

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <button data-testid="mm-back-btn" onClick={() => navigate(`/quest/${questId}`)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to the quest
        </button>

        <div className="flex items-center gap-3 mb-2">
          <div className="w-11 h-11 rounded-xl bg-primary/15 flex items-center justify-center hq-glow-gold"><Gavel className="w-6 h-6 text-primary" /></div>
          <div>
            <h1 data-testid="mock-meeting-title" className="font-display text-3xl sm:text-4xl tracking-tight leading-none">Mock Meeting Simulator</h1>
            <p className="text-sm text-muted-foreground mt-1">Summit of Leadership · You are the Chair</p>
          </div>
        </div>

        {/* progress */}
        <div className="mt-6 mb-8">
          <div className="flex justify-between text-xs font-mono-data text-muted-foreground mb-2">
            <span>{finished ? "Adjourned" : scene.phase}</span>
            <span>{finished ? 100 : progress}%</span>
          </div>
          <div className="h-2 rounded-full bg-white/5 overflow-hidden">
            <div className="h-full rounded-full bg-primary transition-all duration-500" style={{ width: `${finished ? 100 : progress}%` }} />
          </div>
        </div>

        {!finished ? (
          <AnimatePresence mode="wait">
            <motion.div
              key={scene.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.35 }}
              className="hq-glass rounded-2xl p-6 sm:p-8 border-t border-t-primary/30"
            >
              <p className="text-slate-400 italic mb-4">{scene.narration}</p>
              <h2 className="font-display text-2xl mb-6">{scene.prompt}</h2>

              <div className="space-y-3">
                {scene.options.map((opt, oi) => {
                  const isPicked = picked === oi;
                  const isWrong = wrongPicks.includes(oi);
                  const showCorrect = solved && opt.correct;
                  return (
                    <div key={oi}>
                      <button
                        data-testid={`mm-option-${scene.id}-${oi}`}
                        onClick={() => choose(oi)}
                        disabled={solved || isWrong}
                        className={`w-full text-left p-4 rounded-xl border transition-colors duration-200 flex items-start gap-3 ${
                          showCorrect
                            ? "border-emerald-400/60 bg-emerald-400/10"
                            : isWrong
                            ? "border-[#E11D48]/50 bg-[#E11D48]/10 opacity-70"
                            : "border-white/10 hover:bg-white/5"
                        } ${solved && !opt.correct ? "opacity-50" : ""}`}
                      >
                        <span className="mt-0.5 shrink-0">
                          {showCorrect ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : isWrong ? <XCircle className="w-5 h-5 text-[#E11D48]" /> : <span className="block w-5 h-5 rounded-full border border-white/25" />}
                        </span>
                        <span className="flex-1 text-slate-200">{opt.text}</span>
                      </button>
                      {isPicked && (
                        <p className={`mt-2 text-sm px-1 ${opt.correct ? "text-emerald-300" : "text-[#fca5b5]"}`}>{opt.feedback}</p>
                      )}
                    </div>
                  );
                })}
              </div>

              {solved && (
                <Button data-testid="mm-next-btn" onClick={next} className="mt-6 w-full py-6 bg-primary text-primary-foreground hover:bg-[#FDBA74]">
                  {idx < SCENES.length - 1 ? <>Continue <ArrowRight className="w-4 h-4 ml-2" /></> : <>Adjourn the meeting <Gavel className="w-4 h-4 ml-2" /></>}
                </Button>
              )}
            </motion.div>
          </AnimatePresence>
        ) : (
          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="hq-glass rounded-2xl p-8 text-center border-t border-t-primary/30">
            <div className="mx-auto w-20 h-20 rounded-full bg-primary/15 hq-glow-gold flex items-center justify-center mb-5"><Gavel className="w-9 h-9 text-primary" /></div>
            <h2 className="font-display text-3xl mb-2">Meeting Adjourned!</h2>
            <p className="text-slate-300">You ran the meeting from call to order to adjournment.</p>

            <div className="flex justify-center gap-8 mt-6">
              <div>
                <p className="font-mono-data text-3xl text-primary">{accuracy}%</p>
                <p className="text-xs text-muted-foreground mt-1">Accuracy</p>
              </div>
              <div>
                <p className="font-mono-data text-3xl text-slate-200">{mistakes}</p>
                <p className="text-xs text-muted-foreground mt-1">Missteps</p>
              </div>
              {award && (
                <div>
                  <p className="font-mono-data text-3xl text-primary flex items-center gap-1 justify-center"><Gem className="w-6 h-6" />+{award.bonus}</p>
                  <p className="text-xs text-muted-foreground mt-1">Bonus Points</p>
                </div>
              )}
            </div>

            <div className="mt-8 space-y-3">
              <div className="flex gap-3">
                <Button data-testid="mm-restart-btn" variant="outline" className="flex-1 border-white/15" onClick={restart}><RotateCcw className="w-4 h-4 mr-2" /> Run again</Button>
                <Button data-testid="mm-quest-btn" variant="outline" className="flex-1 border-white/15" onClick={() => navigate(`/quest/${questId}`)}><ArrowLeft className="w-4 h-4 mr-2" /> Back to quest</Button>
              </div>
              <div className="flex gap-3">
                <Button data-testid="mm-map-btn" variant="outline" className="flex-1 border-white/15" onClick={() => navigate("/map")}><Map className="w-4 h-4 mr-2" /> Map</Button>
                <Button data-testid="mm-rankings-btn" className="flex-1 bg-primary text-primary-foreground hover:bg-[#FDBA74]" onClick={() => navigate("/leaderboard")}><Trophy className="w-4 h-4 mr-2" /> Rankings</Button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
