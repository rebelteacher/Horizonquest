import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Trophy, Gem, Anchor, Flag, Crown, Loader2, Users } from "lucide-react";

const MEDAL = ["#FB923C", "#C0C0C0", "#CD7F32"];

export default function Leaderboard() {
  const { user } = useAuth();
  const [scopes, setScopes] = useState({ classes: [], teacher: null, school: "" });
  const [scope, setScope] = useState("class");
  const [classId, setClassId] = useState("");
  const [period, setPeriod] = useState("total");
  const [fleetMode, setFleetMode] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get("/me/rank-scopes");
        setScopes(res.data);
        if (res.data.classes?.length) setClassId(res.data.classes[0].expedition_id);
        else setScope("global");
      } catch (e) {
        setScope("global");
      }
    })();
  }, []);

  const hasClasses = scopes.classes?.length > 0;

  const loadBoard = useCallback(async () => {
    setLoading(true);
    try {
      const params = { scope };
      if (scope === "class") { if (!classId) { setLoading(false); return; } params.expedition_id = classId; }
      else if (scope !== "global" && classId) params.expedition_id = classId;
      if (period === "week") params.period = "week";
      const res = await api.get("/leaderboard", { params });
      setData(res.data);
    } finally {
      setLoading(false);
    }
  }, [scope, classId, period]);

  useEffect(() => { loadBoard(); }, [loadBoard]);

  const metricLabel = period === "week" ? "This Week" : "Total";
  const scopeLabel = data?.scope_label || "";

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6 hq-fade-up">
          <div>
            <p className="text-xs uppercase tracking-widest font-mono-data text-primary">The horizon awaits</p>
            <h1 className="font-display text-5xl tracking-tight flex items-center gap-3"><Trophy className="w-9 h-9 text-primary" /> Explorer Rankings</h1>
            {scopeLabel && <p className="text-sm text-muted-foreground mt-1">Ranking <span className="text-[#22D3EE]">{scopeLabel}</span> by {metricLabel} points</p>}
          </div>
        </div>

        {/* Scope selector */}
        <div className="flex flex-col gap-4 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <Tabs value={scope} onValueChange={setScope} className={hasClasses ? "" : "hidden"}>
              <TabsList className="bg-white/5 border border-white/10">
                {hasClasses && <TabsTrigger value="class" data-testid="scope-class">My Class</TabsTrigger>}
                {hasClasses && <TabsTrigger value="teacher" data-testid="scope-teacher">By Teacher</TabsTrigger>}
                {hasClasses && <TabsTrigger value="school" data-testid="scope-school">By School</TabsTrigger>}
                <TabsTrigger value="global" data-testid="scope-global">Everybody</TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="flex items-center gap-4 flex-wrap">
              {scope === "class" && scopes.classes.length > 1 && (
                <Select value={classId} onValueChange={setClassId}>
                  <SelectTrigger data-testid="leaderboard-class-select" className="w-52 bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {scopes.classes.map((c) => <SelectItem key={c.expedition_id} value={c.expedition_id}>{c.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
              <Tabs value={period} onValueChange={setPeriod}>
                <TabsList className="bg-white/5 border border-white/10">
                  <TabsTrigger value="total" data-testid="period-total">Total</TabsTrigger>
                  <TabsTrigger value="week" data-testid="period-week">This Week</TabsTrigger>
                </TabsList>
              </Tabs>
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-[#22D3EE]" />
                <Label htmlFor="fleet-mode" className="text-sm cursor-pointer">Teams</Label>
                <Switch id="fleet-mode" data-testid="fleet-mode-toggle" checked={fleetMode} onCheckedChange={setFleetMode} />
              </div>
            </div>
          </div>
        </div>

        {loading || !data ? (
          <div className="flex justify-center py-32"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
        ) : fleetMode ? (
          /* -------- Team (Fleet) mode -------- */
          <div className="space-y-3" data-testid="fleet-standings">
            <p className="text-sm text-muted-foreground mb-4">Team standings across <span className="text-[#22D3EE]">{scopeLabel}</span> by {metricLabel} points — every Explorer's score adds to their Team.</p>
            {data.fleets.length === 0 && <p className="text-muted-foreground py-12 text-center">No team points here yet.</p>}
            {data.fleets.map((f, i) => {
              const max = data.fleets[0]?.points || 1;
              return (
                <div key={f.fleet} data-testid={`fleet-row-${i}`} className="hq-glass rounded-xl p-5 hq-fade-up" style={{ animationDelay: `${i * 0.05}s` }}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {i < 3 && <Crown className="w-5 h-5" style={{ color: MEDAL[i] }} />}
                      <span className="font-display text-2xl">{f.fleet}</span>
                    </div>
                    <span className="font-mono-data text-xl text-[#22D3EE]">{f.points}</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full rounded-full bg-[#22D3EE] transition-all duration-500" style={{ width: `${(f.points / max) * 100}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* -------- Individual rankings -------- */
          <div className="space-y-2" data-testid="individual-rankings">
            {data.entries.length === 0 && <p className="text-muted-foreground py-12 text-center">No Explorers here yet. Complete a mission or checkpoint to claim the top spot!</p>}
            {data.entries.map((e, i) => (
              <div
                key={e.user_id}
                data-testid={`leaderboard-row-${e.rank}`}
                style={{ animationDelay: `${Math.min(i, 10) * 0.04}s` }}
                className={`hq-fade-up flex items-center gap-4 p-4 rounded-xl border transition-colors duration-200 ${
                  e.is_me ? "border-primary/50 bg-primary/10" : "border-white/10 hover:bg-white/5"
                }`}
              >
                <div className="w-10 text-center shrink-0">
                  {e.rank <= 3 ? <Crown className="w-6 h-6 mx-auto" style={{ color: MEDAL[e.rank - 1] }} /> : <span className="font-mono-data text-lg text-muted-foreground">{e.rank}</span>}
                </div>
                <Avatar className="w-11 h-11">
                  <AvatarImage src={e.picture} />
                  <AvatarFallback className="bg-secondary">{(e.name || "E")[0]}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{e.name}{e.is_me && <span className="text-primary text-xs ml-2">(you)</span>}</p>
                  <p className="text-xs text-muted-foreground flex items-center gap-2">
                    <span className="flex items-center gap-1"><Flag className="w-3 h-3" />{e.fleet || "Unaligned"}</span>
                    {e.tier && <span className="px-2 py-0.5 rounded-full bg-white/5 text-[10px] uppercase tracking-wider font-mono-data text-[#22D3EE] border border-[#22D3EE]/20">{e.tier}</span>}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <div className="flex items-center gap-1.5 justify-end text-primary"><Gem className="w-4 h-4" /><span className="font-mono-data text-lg">{e.score}</span></div>
                  <div className="flex items-center gap-1 justify-end text-[#22D3EE] text-xs"><Anchor className="w-3 h-3" />{e.compass_marks}</div>
                </div>
              </div>
            ))}
            {data.entries.length > 0 && (
              <p className="text-xs text-muted-foreground text-center pt-3">Ranked by <span className="text-primary">{metricLabel}</span> points</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
