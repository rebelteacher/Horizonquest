import { useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { KeyRound, ArrowLeft, ArrowRight, CheckCircle2, Gem, Trophy, Map, Lock, Shuffle, Sparkles } from "lucide-react";
import { toast } from "sonner";

const QUEST_ID = "t3-q6";
const PIGPEN_CHALLENGE = "cipher-pigpen";

// ---- cipher engines ----
const shiftChar = (c, shift) => {
  const code = c.charCodeAt(0);
  if (code >= 65 && code <= 90) return String.fromCharCode(((code - 65 + shift + 26) % 26) + 65);
  if (code >= 97 && code <= 122) return String.fromCharCode(((code - 97 + shift + 26) % 26) + 97);
  return c;
};
const caesar = (text, shift) => text.split("").map((c) => shiftChar(c, shift)).join("");

const SUB_KEY = "QWERTYUIOPASDFGHJKLZXCVBNM";
const subEncode = (text) =>
  text.toUpperCase().split("").map((c) => (c >= "A" && c <= "Z" ? SUB_KEY[c.charCodeAt(0) - 65] : c)).join("");

const norm = (s) => s.toUpperCase().replace(/\s+/g, " ").trim();

const CAESAR_CHALLENGES = [
  { plain: "SAIL", shift: 3 },
  { plain: "NORTH STAR", shift: 5 },
  { plain: "SET COURSE", shift: 7 },
];
const SUB_CHALLENGES = ["VIKING", "TREASURE", "OCEAN TIDE"];
const PIGPEN_WORD = "RUNES";

// ---- Pigpen glyph renderer ----
const SEG = { top: "M8,8 L32,8", right: "M32,8 L32,32", bottom: "M8,32 L32,32", left: "M8,8 L8,32" };
const GRID_SIDES = [
  ["right", "bottom"], ["left", "right", "bottom"], ["left", "bottom"],
  ["top", "right", "bottom"], ["top", "right", "bottom", "left"], ["top", "left", "bottom"],
  ["top", "right"], ["top", "left", "right"], ["top", "left"],
];
const WEDGES = { top: ["M20,20 L7,7", "M20,20 L33,7"], left: ["M20,20 L7,7", "M20,20 L7,33"], right: ["M20,20 L33,7", "M20,20 L33,33"], bottom: ["M20,20 L7,33", "M20,20 L33,33"] };
const WEDGE_OF = { S: "top", T: "left", U: "right", V: "bottom", W: "top", X: "left", Y: "right", Z: "bottom" };
const DOT_OF = { top: [20, 12], left: [12, 20], right: [28, 20], bottom: [20, 28] };

function PigpenGlyph({ letter, size = 34 }) {
  const L = (letter || "").toUpperCase();
  const strokes = [];
  let dot = null;
  if (L >= "A" && L <= "I") GRID_SIDES[L.charCodeAt(0) - 65].forEach((s) => strokes.push(SEG[s]));
  else if (L >= "J" && L <= "R") { GRID_SIDES[L.charCodeAt(0) - 74].forEach((s) => strokes.push(SEG[s])); dot = [20, 20]; }
  else if (L >= "S" && L <= "Z") {
    const w = WEDGE_OF[L];
    WEDGES[w].forEach((d) => strokes.push(d));
    if (L >= "W") dot = DOT_OF[w];
  } else {
    return <span style={{ width: size }} className="inline-block text-slate-500">·</span>;
  }
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" className="inline-block">
      {strokes.map((d, i) => (
        <path key={i} d={d} stroke="#22D3EE" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      ))}
      {dot && <circle cx={dot[0]} cy={dot[1]} r="2.4" fill="#22D3EE" />}
    </svg>
  );
}

function ChallengeRow({ index, cipher, solved, onSolve }) {
  const [val, setVal] = useState("");
  const [shake, setShake] = useState(false);
  const check = () => {
    if (norm(val) === norm(cipher.plain)) onSolve();
    else { setShake(true); toast.error("Not quite — check your decoding and try again."); setTimeout(() => setShake(false), 400); }
  };
  return (
    <div className={`rounded-xl border p-4 transition-colors ${solved ? "border-emerald-400/50 bg-emerald-400/5" : "border-white/10"}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono-data text-muted-foreground">Secret message {index + 1}{cipher.shift != null ? ` · shift +${cipher.shift}` : ""}</span>
        {solved && <span className="flex items-center gap-1 text-emerald-400 text-xs font-mono-data"><CheckCircle2 className="w-4 h-4" /> Cracked</span>}
      </div>
      <p className="font-mono-data text-xl tracking-widest text-[#22D3EE] mb-3 break-words">{cipher.cipher}</p>
      {!solved && (
        <motion.div animate={shake ? { x: [0, -6, 6, -4, 4, 0] } : {}} transition={{ duration: 0.4 }} className="flex gap-2">
          <Input data-testid={`cipher-input-${index}`} value={val} onChange={(e) => setVal(e.target.value)} onKeyDown={(e) => e.key === "Enter" && check()} placeholder="Type the decoded message…" className="bg-white/5 border-white/10 uppercase" />
          <Button data-testid={`cipher-check-${index}`} onClick={check} className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9] shrink-0">Decode</Button>
        </motion.div>
      )}
      {solved && <p className="font-mono-data text-lg tracking-widest text-emerald-300">{cipher.plain}</p>}
    </div>
  );
}

export default function CipherPlayground() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const questId = params.get("quest") || QUEST_ID;
  const { refresh } = useAuth();

  const [encInput, setEncInput] = useState("MEET AT DAWN");
  const [encShift, setEncShift] = useState(3);
  const [caesarSolved, setCaesarSolved] = useState({});
  const [subSolved, setSubSolved] = useState({});
  const [pigpenVal, setPigpenVal] = useState("");
  const [pigpenSolved, setPigpenSolved] = useState(false);
  const [pigpenAward, setPigpenAward] = useState(null);
  const [labAward, setLabAward] = useState(null);
  const [completing, setCompleting] = useState(false);
  const labAwardedRef = useRef(false);
  const pigpenRef = useRef(false);

  const caesarData = useMemo(() => CAESAR_CHALLENGES.map((c) => ({ ...c, cipher: caesar(c.plain, c.shift) })), []);
  const subData = useMemo(() => SUB_CHALLENGES.map((plain) => ({ plain, shift: null, cipher: subEncode(plain) })), []);

  const caesarDone = caesarData.every((_, i) => caesarSolved[i]);
  const subDone = subData.every((_, i) => subSolved[i]);
  const coreDone = caesarDone && subDone;
  const solvedCount = Object.keys(caesarSolved).length + Object.keys(subSolved).length;

  const completeLab = async () => {
    if (labAwardedRef.current) return;
    labAwardedRef.current = true;
    setCompleting(true);
    try {
      const res = await api.post(`/labs/${questId}/complete`);
      setLabAward(res.data);
      await refresh();
      if (res.data.bonus > 0) toast.success(`Ciphers cracked! +${res.data.bonus} Horizon Points`);
      else toast.info("Lab already completed — sharp work!");
    } catch (e) {
      labAwardedRef.current = false;
      toast.error("Could not save your lab result.");
    } finally {
      setCompleting(false);
    }
  };

  const solvePigpen = async () => {
    if (norm(pigpenVal) !== norm(PIGPEN_WORD)) {
      toast.error("Not decoded yet — use the chart to match each symbol.");
      return;
    }
    setPigpenSolved(true);
    if (pigpenRef.current) return;
    pigpenRef.current = true;
    try {
      const res = await api.post(`/challenges/${PIGPEN_CHALLENGE}/complete`);
      setPigpenAward(res.data);
      await refresh();
      if (res.data.bonus > 0) toast.success(`Pigpen bonus! +${res.data.bonus} Horizon Points`);
      else toast.info("Pigpen already solved — nicely done!");
    } catch (e) {
      toast.error("Could not save the bonus.");
    }
  };

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <button data-testid="cipher-back-btn" onClick={() => navigate(`/quest/${questId}`)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to the quest
        </button>

        <div className="flex items-center gap-3 mb-2">
          <div className="w-11 h-11 rounded-xl bg-[#22D3EE]/15 flex items-center justify-center hq-glow-teal"><KeyRound className="w-6 h-6 text-[#22D3EE]" /></div>
          <div>
            <h1 data-testid="cipher-title" className="font-display text-3xl sm:text-4xl tracking-tight leading-none">Cipher Playground</h1>
            <p className="text-sm text-muted-foreground mt-1">The Cyber Frontier · Encode & decode secret messages</p>
          </div>
        </div>

        <div className="mt-6 mb-6">
          <div className="flex justify-between text-xs font-mono-data text-muted-foreground mb-2">
            <span>Messages cracked</span><span>{solvedCount}/{caesarData.length + subData.length}</span>
          </div>
          <div className="h-2 rounded-full bg-white/5 overflow-hidden">
            <div className="h-full rounded-full bg-[#22D3EE] transition-all duration-500" style={{ width: `${(solvedCount / (caesarData.length + subData.length)) * 100}%` }} />
          </div>
        </div>

        <Tabs defaultValue="caesar">
          <TabsList className="bg-white/5 border border-white/10">
            <TabsTrigger value="caesar" data-testid="tab-caesar"><Lock className="w-4 h-4 mr-2" />Caesar</TabsTrigger>
            <TabsTrigger value="substitution" data-testid="tab-substitution"><Shuffle className="w-4 h-4 mr-2" />Substitution</TabsTrigger>
            <TabsTrigger value="pigpen" data-testid="tab-pigpen"><Sparkles className="w-4 h-4 mr-2" />Pigpen +50</TabsTrigger>
          </TabsList>

          {/* Caesar */}
          <TabsContent value="caesar" className="mt-6 space-y-6">
            <div className="hq-glass rounded-2xl p-6 border-t border-t-[#22D3EE]/30">
              <h2 className="font-display text-2xl mb-1">Caesar wheel · encode a message</h2>
              <p className="text-sm text-muted-foreground mb-4">A Caesar cipher shifts every letter by a fixed amount. Slide to change the shift and watch your message transform.</p>
              <Input data-testid="caesar-encode-input" value={encInput} onChange={(e) => setEncInput(e.target.value)} className="bg-white/5 border-white/10 uppercase mb-4" placeholder="Type a message to encode…" />
              <div className="flex items-center gap-4 mb-4">
                <span className="text-sm text-muted-foreground w-16">Shift +{encShift}</span>
                <input data-testid="caesar-shift-slider" type="range" min="0" max="25" value={encShift} onChange={(e) => setEncShift(Number(e.target.value))} className="flex-1 accent-[#22D3EE]" />
              </div>
              <div className="rounded-xl bg-[#04121f] border border-white/10 p-4">
                <p className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Encoded</p>
                <p data-testid="caesar-encode-output" className="font-mono-data text-2xl tracking-widest text-[#22D3EE] break-words">{caesar(encInput, encShift) || "…"}</p>
              </div>
            </div>

            <div>
              <h2 className="font-display text-2xl mb-1">Crack these Caesar messages</h2>
              <p className="text-sm text-muted-foreground mb-4">Each message tells you its shift. Shift the letters back to reveal the plain text.</p>
              <div className="space-y-3">
                {caesarData.map((c, i) => (
                  <ChallengeRow key={i} index={i} cipher={c} solved={!!caesarSolved[i]} onSolve={() => setCaesarSolved((s) => ({ ...s, [i]: true }))} />
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Substitution */}
          <TabsContent value="substitution" className="mt-6 space-y-6">
            <div className="hq-glass rounded-2xl p-6 border-t border-t-[#22D3EE]/30">
              <h2 className="font-display text-2xl mb-1">The substitution key</h2>
              <p className="text-sm text-muted-foreground mb-4">A substitution cipher swaps each letter for another using a fixed key. Use this key to decode the messages below.</p>
              <div className="overflow-x-auto hq-scrollbar">
                <div className="inline-grid grid-flow-col grid-rows-2 gap-x-1.5 gap-y-1 text-center">
                  {SUB_KEY.split("").map((c, i) => (
                    <div key={i} className="contents">
                      <div className="font-mono-data text-xs text-muted-foreground w-7">{String.fromCharCode(65 + i)}</div>
                      <div className="font-mono-data text-sm text-[#22D3EE] w-7">{c}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <h2 className="font-display text-2xl mb-1">Crack these substitution messages</h2>
              <p className="text-sm text-muted-foreground mb-4">Match each cipher letter back to its plain letter using the key above.</p>
              <div className="space-y-3">
                {subData.map((c, i) => (
                  <ChallengeRow key={i} index={i} cipher={c} solved={!!subSolved[i]} onSolve={() => setSubSolved((s) => ({ ...s, [i]: true }))} />
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Pigpen bonus */}
          <TabsContent value="pigpen" className="mt-6 space-y-6">
            <div className="rounded-2xl p-6 border border-primary/30 bg-primary/5">
              <div className="flex items-center gap-2 mb-1"><Sparkles className="w-5 h-5 text-primary" /><h2 className="font-display text-2xl">Bonus Challenge · Pigpen</h2></div>
              <p className="text-sm text-muted-foreground">The Pigpen cipher hides each letter inside a symbol. Decode the secret word below using the chart to earn <b className="text-primary">+50 bonus Horizon Points</b>.</p>
            </div>

            <div className="hq-glass rounded-2xl p-6">
              <h3 className="font-display text-xl mb-4">Pigpen chart</h3>
              <div className="grid grid-cols-6 sm:grid-cols-9 gap-3">
                {"ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").map((L) => (
                  <div key={L} className="flex flex-col items-center gap-0.5">
                    <PigpenGlyph letter={L} />
                    <span className="font-mono-data text-xs text-muted-foreground">{L}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className={`rounded-2xl border p-6 ${pigpenSolved ? "border-emerald-400/50 bg-emerald-400/5" : "border-white/10 hq-glass"}`}>
              <h3 className="font-display text-xl mb-3">Decode the secret word</h3>
              <div className="flex flex-wrap items-center gap-2 p-4 rounded-xl bg-[#04121f] border border-white/10 mb-4">
                {PIGPEN_WORD.split("").map((L, i) => <PigpenGlyph key={i} letter={L} size={40} />)}
              </div>
              {pigpenSolved ? (
                <p data-testid="pigpen-solved" className="font-mono-data text-2xl tracking-widest text-emerald-300 flex items-center gap-2"><CheckCircle2 className="w-6 h-6" /> {PIGPEN_WORD}{pigpenAward?.bonus > 0 && <span className="text-primary text-lg">+{pigpenAward.bonus}</span>}</p>
              ) : (
                <div className="flex gap-2">
                  <Input data-testid="pigpen-input" value={pigpenVal} onChange={(e) => setPigpenVal(e.target.value)} onKeyDown={(e) => e.key === "Enter" && solvePigpen()} placeholder="Type the decoded word…" className="bg-white/5 border-white/10 uppercase" />
                  <Button data-testid="pigpen-check" onClick={solvePigpen} className="bg-primary text-primary-foreground hover:bg-[#FDBA74] shrink-0">Decode</Button>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Completion */}
        <div className="mt-8 hq-glass rounded-2xl p-6 text-center border-t border-t-[#22D3EE]/30">
          {labAward ? (
            <>
              <div className="mx-auto w-16 h-16 rounded-full bg-[#22D3EE]/15 hq-glow-teal flex items-center justify-center mb-4"><CheckCircle2 className="w-8 h-8 text-[#22D3EE]" /></div>
              <h2 className="font-display text-2xl mb-1">Cipher Lab Complete!</h2>
              <p className="text-slate-300 flex items-center justify-center gap-1"><Gem className="w-5 h-5 text-primary" /> +{labAward.bonus} points earned{pigpenSolved && pigpenAward?.bonus > 0 ? ` · +${pigpenAward.bonus} pigpen bonus` : ""}</p>
              <div className="flex justify-center gap-3 mt-6">
                <Button data-testid="cipher-map-btn" variant="outline" className="border-white/15" onClick={() => navigate("/map")}><Map className="w-4 h-4 mr-2" /> Map</Button>
                <Button data-testid="cipher-rankings-btn" className="bg-primary text-primary-foreground hover:bg-[#FDBA74]" onClick={() => navigate("/leaderboard")}><Trophy className="w-4 h-4 mr-2" /> Rankings</Button>
              </div>
            </>
          ) : (
            <>
              <p className="text-sm text-muted-foreground mb-4">{coreDone ? "All messages cracked — claim your reward, Explorer!" : "Crack every Caesar and Substitution message to complete the lab."}</p>
              <Button data-testid="cipher-complete-btn" onClick={completeLab} disabled={!coreDone || completing} className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9] disabled:opacity-40">
                {completing ? "Saving…" : <><Gem className="w-4 h-4 mr-2" /> Complete Lab (+75)</>}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
