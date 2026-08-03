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
  const [expeditions, setExpeditions] = useState([]);
  const [territories, setTerritories] = useState([]);
  const [scope, setScope] = useState("global");
  const [tab, setTab] = useState("class");
  const [territoryId, setTerritoryId] = useState("");
  const [fleetMode, setFleetMode] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const path = user.role === "guide" ? "/expeditions" : "/me/expeditions";
      const [exps, cur] = await Promise.all([api.get(path), api.get("/curriculum")]);
      setExpeditions(exps.data);
      setTerritories(cur.data.territories);
      setTerritoryId(cur.data.territories[0]?.id || "");
      if (exps.data.length > 0) setScope(exps.data[0].expedition_id);
    })();
  }, [user.role]);

  const loadBoard = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (scope !== "global") params.expedition_id = scope;
      if (tab === "territory" && territoryId) params.territory_id = territoryId;
      if (tab === "week") params.period = "week";
      const res = await api.get("/leaderboard", { params });
      setData(res.data);
    } finally {
      setLoading(false);
    }
  }, [scope, tab, territoryId]);

  useEffect(() => { loadBoard(); }, [loadBoard]);

  const metricLabel = tab === "week" ? "This Week" : tab === "territory" ? (territories.find((t) => t.id === territoryId)?.name || "Territory") : "Total";

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6 hq-fade-up">
          <div>
            <p className="text-xs uppercase tracking-widest font-mono-data text-primary">The horizon awaits</p>
            <h1 className="font-display text-5xl tracking-tight flex items-center gap-3"><Trophy className="w-9 h-9 text-primary" /> Explorer Rankings</h1>
          </div>
          <Select value={scope} onValueChange={setScope}>
            <SelectTrigger data-testid="leaderboard-scope-select" className="w-64 bg-white/5 border-white/10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="global">All Explorers</SelectItem>
              {expeditions.map((e) => (<SelectItem key={e.expedition_id} value={e.expedition_id}>{e.name}</SelectItem>))}
            </SelectContent>
          </Select>
        </div>

        {/* Tabs + fleet toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="bg-white/5 border border-white/10">
              <TabsTrigger value="class" data-testid="tab-my-class">My Class</TabsTrigger>
              <TabsTrigger value="territory" data-testid="tab-by-territory">By Territory</TabsTrigger>
              <TabsTrigger value="week" data-testid="tab-this-week">This Week</TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="flex items-center gap-4">
            {tab === "territory" && (
              <Select value={territoryId} onValueChange={setTerritoryId}>
                <SelectTrigger data-testid="territory-select" className="w-48 bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {territories.map((t) => (<SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>))}
                </SelectContent>
              </Select>
            )}
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-[#22D3EE]" />
              <Label htmlFor="fleet-mode" className="text-sm cursor-pointer">Fleets</Label>
              <Switch id="fleet-mode" data-testid="fleet-mode-toggle" checked={fleetMode} onCheckedChange={setFleetMode} />
            </div>
          </div>
        </div>

        {loading || !data ? (
          <div className="flex justify-center py-32"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
        ) : fleetMode ? (
          /* -------- Fleet team mode -------- */
          <div className="space-y-3" data-testid="fleet-standings">
            <p className="text-sm text-muted-foreground mb-4">Team standings by <span className="text-[#22D3EE]">{metricLabel}</span> points — every Explorer's score adds to their Fleet.</p>
            {data.fleets.length === 0 && <p className="text-muted-foreground py-12 text-center">No fleets yet.</p>}
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
            {data.entries.length === 0 && <p className="text-muted-foreground py-12 text-center">No Explorers here yet. Complete a Trial to claim the top spot!</p>}
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
