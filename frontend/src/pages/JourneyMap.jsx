import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import AICopilot from "@/components/AICopilot";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Compass, Gem, Anchor, CheckCircle2, Lock, MapPin, Loader2, Star, Flag } from "lucide-react";
import { toast } from "sonner";
import { ASSETS } from "@/lib/assets";

const MAP_BG = ASSETS.worldMap;
const TERRITORY_ICONS = [Compass, MapPin, Star, Flag];

export default function JourneyMap() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [curriculum, setCurriculum] = useState(null);
  const [progress, setProgress] = useState({});
  const [expeditions, setExpeditions] = useState([]);
  const [activeTerritory, setActiveTerritory] = useState(null);
  const [joinCode, setJoinCode] = useState("");
  const [joining, setJoining] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [cur, prog, exps] = await Promise.all([
        api.get("/curriculum"),
        api.get("/me/progress"),
        api.get("/me/expeditions"),
      ]);
      setCurriculum(cur.data);
      const pmap = {};
      prog.data.progress.forEach((p) => (pmap[p.quest_id] = p));
      setProgress(pmap);
      setExpeditions(exps.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const join = async () => {
    if (!joinCode.trim()) return;
    setJoining(true);
    try {
      const res = await api.post("/expeditions/join", { join_code: joinCode });
      if (res.data.already_member) toast.info("You're already sailing with this Expedition.");
      else toast.success(`Joined ${res.data.expedition.name}! Fleet: ${res.data.fleet}`);
      setJoinCode("");
      await Promise.all([load(), refresh()]);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Invalid join code.");
    } finally {
      setJoining(false);
    }
  };

  if (loading || !curriculum) {
    return (
      <div className="min-h-screen">
        <AppNav />
        <div className="flex items-center justify-center py-40"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
      </div>
    );
  }

  const questsByTerritory = (tid) =>
    curriculum.quests.filter((q) => q.territory_id === tid).sort((a, b) => a.order - b.order);

  const territoryDone = (tid) => {
    const qs = questsByTerritory(tid);
    const done = qs.filter((q) => progress[q.id]?.mastery).length;
    return { done, total: qs.length };
  };

  return (
    <div className="min-h-screen">
      <AppNav />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Dashboard header */}
        <div className="grid gap-4 md:grid-cols-12 mb-8">
          <div className="md:col-span-5 hq-glass rounded-2xl p-6 border-t border-t-primary/30 hq-fade-up">
            <p className="text-xs uppercase tracking-widest text-muted-foreground font-mono-data">Explorer's Log</p>
            <h1 className="font-display text-4xl mt-1">Ahoy, {(user.name || "Explorer").split(" ")[0]}</h1>
            <div className="flex gap-6 mt-5">
              <div>
                <div className="flex items-center gap-2 text-primary"><Gem className="w-5 h-5" /><span className="font-mono-data text-2xl">{user.horizon_points ?? 0}</span></div>
                <p className="text-xs text-muted-foreground mt-1">Horizon Points</p>
              </div>
              <div>
                <div className="flex items-center gap-2 text-[#22D3EE]"><Anchor className="w-5 h-5" /><span className="font-mono-data text-2xl">{user.compass_marks ?? 0}</span></div>
                <p className="text-xs text-muted-foreground mt-1">Compass Marks</p>
              </div>
              {user.fleet && (
                <div>
                  <div className="flex items-center gap-2 text-slate-200"><Flag className="w-5 h-5" /><span className="font-mono-data text-lg">{user.fleet}</span></div>
                  <p className="text-xs text-muted-foreground mt-1">Your Fleet</p>
                </div>
              )}
            </div>
          </div>

          <div className="md:col-span-7 hq-glass rounded-2xl p-6 hq-fade-up" style={{ animationDelay: "0.1s" }}>
            <p className="text-xs uppercase tracking-widest text-muted-foreground font-mono-data mb-3">Expeditions</p>
            {expeditions.length > 0 ? (
              <div className="flex flex-wrap gap-2 mb-4">
                {expeditions.map((e) => (
                  <span key={e.expedition_id} data-testid={`joined-expedition-${e.join_code}`} className="px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm border border-primary/20">
                    {e.name}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground mb-4">You haven't joined an Expedition yet. Enter a Guide's join code to appear on the leaderboard.</p>
            )}
            <div className="flex gap-2 max-w-md">
              <Input
                data-testid="join-code-input"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                placeholder="Enter join code (e.g. AB12CD)"
                className="bg-white/5 border-white/10 font-mono-data uppercase"
                maxLength={6}
              />
              <Button data-testid="join-expedition-btn" onClick={join} disabled={joining} className="bg-primary text-primary-foreground hover:bg-[#FDBA74]">
                {joining ? <Loader2 className="w-4 h-4 animate-spin" /> : "Join"}
              </Button>
            </div>
          </div>
        </div>

        {/* Journey Map */}
        <div className="hq-fade-up" style={{ animationDelay: "0.2s" }}>
          <h2 className="font-display text-3xl mb-4 flex items-center gap-3"><Compass className="w-7 h-7 text-primary" /> The Journey Map</h2>
          <div className="relative w-full rounded-3xl overflow-hidden border border-white/10" style={{ aspectRatio: "16 / 8" }}>
            <img src={MAP_BG} alt="" className="absolute inset-0 w-full h-full object-cover opacity-60" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#060B19] via-[#060B19]/30 to-transparent" />

            <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
              <polyline
                points={curriculum.territories.map((t) => `${t.position.x},${t.position.y}`).join(" ")}
                fill="none"
                stroke="rgba(212,175,55,0.5)"
                strokeWidth="0.5"
                strokeDasharray="2 2"
              />
            </svg>

            {curriculum.territories.map((t, i) => {
              const { done, total } = territoryDone(t.id);
              const complete = done === total;
              const Icon = TERRITORY_ICONS[i % TERRITORY_ICONS.length];
              const isNext = !complete && (i === 0 || territoryDone(curriculum.territories[i - 1].id).done > 0);
              return (
                <button
                  key={t.id}
                  data-testid={`territory-node-${t.id}`}
                  onClick={() => setActiveTerritory(t)}
                  className="absolute -translate-x-1/2 -translate-y-1/2 group"
                  style={{ left: `${t.position.x}%`, top: `${t.position.y}%` }}
                >
                  <div
                    className={`w-14 h-14 sm:w-16 sm:h-16 rounded-full flex items-center justify-center border-2 transition-transform duration-200 group-hover:scale-110 ${isNext ? "hq-pulse" : ""}`}
                    style={{ borderColor: t.color, background: `${t.color}22`, boxShadow: `0 0 20px ${t.color}55` }}
                  >
                    {complete ? <CheckCircle2 className="w-7 h-7" style={{ color: t.color }} /> : <Icon className="w-7 h-7" style={{ color: t.color }} />}
                  </div>
                  <div className="mt-2 text-center whitespace-nowrap">
                    <p className="font-display text-base sm:text-lg leading-tight">{t.name}</p>
                    <p className="text-[10px] sm:text-xs font-mono-data text-muted-foreground">{done}/{total} quests</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Territory quest panel */}
      <Sheet open={!!activeTerritory} onOpenChange={(o) => !o && setActiveTerritory(null)}>
        <SheetContent side="right" className="w-full sm:max-w-lg hq-glass overflow-y-auto hq-scrollbar">
          {activeTerritory && (
            <>
              <SheetHeader className="text-left">
                <p className="text-xs uppercase tracking-widest font-mono-data" style={{ color: activeTerritory.color }}>Territory {activeTerritory.order}</p>
                <SheetTitle className="font-display text-3xl">{activeTerritory.name}</SheetTitle>
                <p className="text-sm text-muted-foreground">{activeTerritory.subtitle}</p>
                <p className="text-sm text-slate-400 italic mt-1">“{activeTerritory.lore}”</p>
              </SheetHeader>

              <div className="mt-6 space-y-3">
                {questsByTerritory(activeTerritory.id).map((q, idx) => {
                  const p = progress[q.id];
                  const done = p?.mastery;
                  const attempted = !!p;
                  const prevQuests = questsByTerritory(activeTerritory.id).slice(0, idx);
                  const locked = idx > 0 && !progress[prevQuests[idx - 1].id];
                  return (
                    <button
                      key={q.id}
                      data-testid={`quest-item-${q.id}`}
                      disabled={locked}
                      onClick={() => navigate(`/quest/${q.id}`)}
                      className={`w-full text-left flex items-center gap-4 p-4 rounded-xl border transition-colors duration-200 ${
                        locked ? "border-white/5 opacity-50 cursor-not-allowed" : "border-white/10 hover:bg-white/5"
                      }`}
                    >
                      <div className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center border" style={{ borderColor: done ? activeTerritory.color : "rgba(255,255,255,0.15)" }}>
                        {locked ? <Lock className="w-4 h-4 text-muted-foreground" /> : done ? <CheckCircle2 className="w-5 h-5" style={{ color: activeTerritory.color }} /> : <span className="font-mono-data text-sm">{q.order}</span>}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{q.title}</p>
                        <p className="text-xs text-muted-foreground font-mono-data">DOK {q.dok} · {q.standard.code} · {q.points} pts</p>
                      </div>
                      {attempted && !done && <span className="text-xs font-mono-data text-primary">{p.score}%</span>}
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      <AICopilot />
    </div>
  );
}
