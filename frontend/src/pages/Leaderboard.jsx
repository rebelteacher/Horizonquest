import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Trophy, Gem, Anchor, Flag, Crown, Loader2 } from "lucide-react";

const MEDAL = ["#D4AF37", "#C0C0C0", "#CD7F32"];

export default function Leaderboard() {
  const { user } = useAuth();
  const [expeditions, setExpeditions] = useState([]);
  const [selected, setSelected] = useState("global");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const path = user.role === "guide" ? "/expeditions" : "/me/expeditions";
      const res = await api.get(path);
      setExpeditions(res.data);
      if (res.data.length > 0) setSelected(res.data[0].expedition_id);
      else setSelected("global");
    })();
  }, [user.role]);

  const loadBoard = useCallback(async () => {
    setLoading(true);
    try {
      const params = selected !== "global" ? { expedition_id: selected } : {};
      const res = await api.get("/leaderboard", { params });
      setData(res.data);
    } finally {
      setLoading(false);
    }
  }, [selected]);

  useEffect(() => { loadBoard(); }, [loadBoard]);

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8 hq-fade-up">
          <div>
            <p className="text-xs uppercase tracking-widest font-mono-data text-primary">The horizon awaits</p>
            <h1 className="font-display text-5xl tracking-tight flex items-center gap-3"><Trophy className="w-9 h-9 text-primary" /> Explorer Rankings</h1>
          </div>
          <Select value={selected} onValueChange={setSelected}>
            <SelectTrigger data-testid="leaderboard-scope-select" className="w-64 bg-white/5 border-white/10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="global">All Explorers</SelectItem>
              {expeditions.map((e) => (<SelectItem key={e.expedition_id} value={e.expedition_id}>{e.name}</SelectItem>))}
            </SelectContent>
          </Select>
        </div>

        {loading || !data ? (
          <div className="flex justify-center py-32"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Rankings */}
            <div className="lg:col-span-2 space-y-2">
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
                    {e.rank <= 3 ? (
                      <Crown className="w-6 h-6 mx-auto" style={{ color: MEDAL[e.rank - 1] }} />
                    ) : (
                      <span className="font-mono-data text-lg text-muted-foreground">{e.rank}</span>
                    )}
                  </div>
                  <Avatar className="w-11 h-11">
                    <AvatarImage src={e.picture} />
                    <AvatarFallback className="bg-secondary">{(e.name || "E")[0]}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{e.name}{e.is_me && <span className="text-primary text-xs ml-2">(you)</span>}</p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1"><Flag className="w-3 h-3" />{e.fleet || "Unaligned"}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="flex items-center gap-1.5 justify-end text-primary"><Gem className="w-4 h-4" /><span className="font-mono-data text-lg">{e.horizon_points}</span></div>
                    <div className="flex items-center gap-1 justify-end text-[#06B6D4] text-xs"><Anchor className="w-3 h-3" />{e.compass_marks}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Fleet standings */}
            <div className="hq-glass rounded-2xl p-6 h-fit border-t border-t-[#06B6D4]/30 hq-fade-up">
              <h2 className="font-display text-2xl flex items-center gap-2 mb-5"><Flag className="w-5 h-5 text-[#06B6D4]" /> Fleet Standings</h2>
              <div className="space-y-4">
                {data.fleets.map((f, i) => {
                  const max = data.fleets[0]?.points || 1;
                  return (
                    <div key={f.fleet} data-testid={`fleet-${i}`}>
                      <div className="flex justify-between text-sm mb-1.5">
                        <span>{f.fleet}</span>
                        <span className="font-mono-data text-[#06B6D4]">{f.points}</span>
                      </div>
                      <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full rounded-full bg-[#06B6D4] transition-all duration-500" style={{ width: `${(f.points / max) * 100}%` }} />
                      </div>
                    </div>
                  );
                })}
                {data.fleets.length === 0 && <p className="text-sm text-muted-foreground">No fleets yet.</p>}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
