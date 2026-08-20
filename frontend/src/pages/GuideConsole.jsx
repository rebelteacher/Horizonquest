import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Anchor, Plus, Copy, Users, ClipboardCheck, BarChart3, Trophy, Loader2, Check, Compass, BookOpen, Target, Download } from "lucide-react";
import { toast } from "sonner";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from "recharts";

export default function GuideConsole() {
  const { user } = useAuth();
  const [expeditions, setExpeditions] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadExpeditions = useCallback(async () => {
    const res = await api.get("/expeditions");
    setExpeditions(res.data);
    setLoading(false);
  }, []);

  useEffect(() => { loadExpeditions(); }, [loadExpeditions]);

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="mb-8 hq-fade-up">
          <p className="text-xs uppercase tracking-widest font-mono-data text-[#22D3EE]">Guide Console</p>
          <h1 className="font-display text-5xl tracking-tight">Chart the course, {(user.name || "Guide").split(" ")[0]}</h1>
        </div>

        <Tabs defaultValue="expeditions">
          <TabsList className="bg-white/5 border border-white/10">
            <TabsTrigger value="expeditions" data-testid="tab-expeditions"><Anchor className="w-4 h-4 mr-2" />Expeditions</TabsTrigger>
            <TabsTrigger value="reviews" data-testid="tab-reviews"><ClipboardCheck className="w-4 h-4 mr-2" />Review Queue</TabsTrigger>
            <TabsTrigger value="mastery" data-testid="tab-mastery"><BarChart3 className="w-4 h-4 mr-2" />Mastery</TabsTrigger>
            <TabsTrigger value="curriculum" data-testid="tab-curriculum"><BookOpen className="w-4 h-4 mr-2" />Curriculum</TabsTrigger>
            <TabsTrigger value="reports" data-testid="tab-reports"><ClipboardCheck className="w-4 h-4 mr-2" />Reports</TabsTrigger>
            <TabsTrigger value="leaderboard" data-testid="tab-leaderboard"><Trophy className="w-4 h-4 mr-2" />Rankings</TabsTrigger>
          </TabsList>

          <TabsContent value="expeditions" className="mt-6">
            <ExpeditionsTab expeditions={expeditions} loading={loading} reload={loadExpeditions} />
          </TabsContent>
          <TabsContent value="reviews" className="mt-6"><ReviewsTab /></TabsContent>
          <TabsContent value="mastery" className="mt-6"><MasteryTab expeditions={expeditions} /></TabsContent>
          <TabsContent value="curriculum" className="mt-6"><CurriculumTab /></TabsContent>
          <TabsContent value="reports" className="mt-6"><ReportsTab /></TabsContent>
          <TabsContent value="leaderboard" className="mt-6"><LeaderboardControlsTab expeditions={expeditions} reload={loadExpeditions} /></TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function ExpeditionsTab({ expeditions, loading, reload }) {
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [creating, setCreating] = useState(false);
  const [members, setMembers] = useState(null);

  const create = async () => {
    if (!name.trim()) { toast.error("Give your Expedition a name."); return; }
    setCreating(true);
    try {
      const res = await api.post("/expeditions", { name, description: desc });
      toast.success(`Expedition created! Join code: ${res.data.join_code}`);
      setName(""); setDesc("");
      await reload();
    } catch (e) { toast.error("Could not create Expedition."); }
    finally { setCreating(false); }
  };

  const copyCode = (code) => { navigator.clipboard?.writeText(code); toast.success(`Copied ${code}`); };

  const viewMembers = async (id) => {
    const res = await api.get(`/expeditions/${id}`);
    setMembers({ name: res.data.expedition.name, list: res.data.members });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="hq-glass rounded-2xl p-6 border-t border-t-[#22D3EE]/30 h-fit">
        <h2 className="font-display text-2xl mb-4 flex items-center gap-2"><Plus className="w-5 h-5 text-[#22D3EE]" /> New Expedition</h2>
        <div className="space-y-3">
          <Input data-testid="expedition-name-input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Expedition name (e.g. Period 3 Voyage)" className="bg-white/5 border-white/10" />
          <Textarea data-testid="expedition-desc-input" value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Description (optional)" className="bg-white/5 border-white/10" />
          <Button data-testid="create-expedition-btn" onClick={create} disabled={creating} className="w-full bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]">
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Expedition"}
          </Button>
        </div>
      </div>

      <div className="lg:col-span-2">
        {loading ? <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div> : (
          <div className="space-y-3">
            {expeditions.length === 0 && <p className="text-muted-foreground py-12 text-center">No Expeditions yet. Create your first voyage!</p>}
            {expeditions.map((e) => (
              <div key={e.expedition_id} data-testid={`expedition-card-${e.join_code}`} className="hq-glass rounded-2xl p-5 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <h3 className="font-display text-2xl truncate">{e.name}</h3>
                  {e.description && <p className="text-sm text-muted-foreground truncate">{e.description}</p>}
                  <div className="flex items-center gap-3 mt-2 text-sm">
                    <span className="flex items-center gap-1 text-muted-foreground"><Users className="w-4 h-4" />{e.member_count} Explorers</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <button data-testid={`copy-code-${e.join_code}`} onClick={() => copyCode(e.join_code)} className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-primary/30 bg-primary/10 hover:bg-primary/20 transition-colors">
                    <span className="font-mono-data text-lg text-primary tracking-widest">{e.join_code}</span>
                    <Copy className="w-4 h-4 text-primary" />
                  </button>
                  <Button variant="outline" size="sm" className="border-white/15" data-testid={`view-members-${e.join_code}`} onClick={() => viewMembers(e.expedition_id)}>Members</Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={!!members} onOpenChange={(o) => !o && setMembers(null)}>
        <DialogContent className="hq-glass border-white/10">
          <DialogHeader><DialogTitle className="font-display text-2xl">{members?.name} · Crew</DialogTitle><DialogDescription>Explorers who have joined this Expedition.</DialogDescription></DialogHeader>
          <div className="space-y-2 max-h-96 overflow-y-auto hq-scrollbar">
            {members?.list.length === 0 && <p className="text-muted-foreground text-sm">No Explorers have joined yet.</p>}
            {members?.list.map((m) => (
              <div key={m.user_id} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                <span>{m.name} <span className="text-xs text-muted-foreground">· {m.fleet}</span></span>
                <span className="font-mono-data text-primary">{m.horizon_points} pts</span>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ReviewsTab() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.get("/guide/reviews");
    setReviews(res.data);
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  const approve = async (id) => {
    await api.post(`/guide/reviews/${id}/approve`);
    toast.success("Reflection approved · +25 bonus points awarded");
    load();
  };

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div className="space-y-3">
      {reviews.length === 0 && <p className="text-muted-foreground py-12 text-center">The review queue is clear. 🎉</p>}
      {reviews.map((r, i) => (
        <div key={r.review_id} data-testid={`review-item-${i}`} className="hq-glass rounded-2xl p-5 flex items-start justify-between gap-4 hq-fade-up" style={{ animationDelay: `${i * 0.04}s` }}>
          <div>
            <p className="text-sm"><b>{r.user_name}</b> · <span className="text-muted-foreground">{r.quest_title}</span></p>
            <p className="mt-2 text-slate-300 italic">“{r.reflection}”</p>
          </div>
          <Button data-testid={`approve-review-${i}`} onClick={() => approve(r.review_id)} className="shrink-0 bg-primary text-primary-foreground hover:bg-[#FDBA74]">
            <Check className="w-4 h-4 mr-1" /> Approve
          </Button>
        </div>
      ))}
    </div>
  );
}

function MasteryTab({ expeditions }) {
  const [selected, setSelected] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { if (expeditions.length && !selected) setSelected(expeditions[0].expedition_id); }, [expeditions, selected]);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    api.get(`/guide/mastery/${selected}`).then((r) => setData(r.data)).finally(() => setLoading(false));
  }, [selected]);

  if (expeditions.length === 0) return <p className="text-muted-foreground py-12 text-center">Create an Expedition to track standards mastery.</p>;

  return (
    <div>
      <Select value={selected} onValueChange={setSelected}>
        <SelectTrigger data-testid="mastery-expedition-select" className="w-64 bg-white/5 border-white/10 mb-6"><SelectValue /></SelectTrigger>
        <SelectContent>{expeditions.map((e) => <SelectItem key={e.expedition_id} value={e.expedition_id}>{e.name}</SelectItem>)}</SelectContent>
      </Select>

      {loading || !data ? <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div> : (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="hq-glass rounded-2xl p-6">
            <h3 className="font-display text-2xl mb-1">Mastery by Territory</h3>
            <p className="text-sm text-muted-foreground mb-5">{data.member_count} Explorers · % achieving 80%+ mastery</p>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data.territory_summary}>
                <XAxis dataKey="territory" tick={{ fill: "#94A3B8", fontSize: 11 }} axisLine={{ stroke: "#334155" }} />
                <YAxis domain={[0, 100]} tick={{ fill: "#94A3B8", fontSize: 11 }} axisLine={{ stroke: "#334155" }} />
                <Tooltip contentStyle={{ background: "#0A1128", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                <Bar dataKey="mastery" radius={[6, 6, 0, 0]}>
                  {data.territory_summary.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="hq-glass rounded-2xl p-6 overflow-x-auto">
            <h3 className="font-display text-2xl mb-4">Standards Detail</h3>
            <Table>
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead>Standard</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Mastery</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.standards.map((s) => (
                  <TableRow key={s.code} className="border-white/5 hover:bg-white/5">
                    <TableCell className="font-mono-data text-primary">{s.code}</TableCell>
                    <TableCell className="text-sm text-slate-300 max-w-xs">{s.description}</TableCell>
                    <TableCell className="text-right font-mono-data">{s.mastery_pct}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
}

function ReportsTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const TRACKS = [{ id: "docs", name: "Docs" }, { id: "sheets", name: "Sheets" }, { id: "slides", name: "Slides" }, { id: "email", name: "Email" }];

  useEffect(() => {
    api.get("/studio/reports/all").then((r) => setData(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (!data || data.students.length === 0) return <p className="text-sm text-muted-foreground py-10 text-center">No Skill Studio activity yet. Once Explorers complete missions, their grades appear here.</p>;

  const gradeColor = (s) => (s >= 90 ? "#34D399" : s >= 80 ? "#22D3EE" : s >= 70 ? "#FB923C" : s >= 60 ? "#F59E0B" : "#E11D48");

  const exportCSV = () => {
    const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const header = ["Explorer", "Email"];
    TRACKS.forEach((t) => { header.push(`${t.name} Avg %`, `${t.name} Mastered`, `${t.name} Total`); });
    const rows = [header.map(esc).join(",")];
    data.students.forEach((s) => {
      const row = [s.name || s.email, s.email];
      TRACKS.forEach((t) => {
        const tr = s.tracks[t.id];
        row.push(tr ? tr.avg : "", tr ? tr.mastered : "", data.totals[t.id] ?? "");
      });
      rows.push(row.map(esc).join(","));
    });
    const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `skill-studio-grades-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-4 flex-wrap">
        <p className="text-sm text-muted-foreground">Skill Studio scores per Explorer. Each cell shows missions mastered / total and the average score.</p>
        <button data-testid="reports-export-csv-btn" onClick={exportCSV} className="inline-flex items-center gap-2 shrink-0 px-3 h-9 rounded-md bg-[#22D3EE] text-[#04121f] text-sm font-medium hover:bg-[#22D3EE]/90 transition-colors">
          <Download className="w-4 h-4" /> Export CSV
        </button>
      </div>
      <div className="overflow-x-auto hq-scrollbar">
        <table className="w-full text-sm border-collapse" data-testid="reports-table">
          <thead>
            <tr className="text-left text-xs uppercase tracking-widest text-muted-foreground">
              <th className="py-2 pr-4">Explorer</th>
              {TRACKS.map((t) => <th key={t.id} className="py-2 px-3 text-center">{t.name} <span className="opacity-50">/{data.totals[t.id]}</span></th>)}
            </tr>
          </thead>
          <tbody>
            {data.students.map((s) => (
              <tr key={s.user_id} data-testid={`report-row-${s.user_id}`} className="border-t border-white/10">
                <td className="py-2.5 pr-4">
                  <p className="text-slate-200">{s.name || s.email}</p>
                  <p className="text-xs text-muted-foreground">{s.email}</p>
                </td>
                {TRACKS.map((t) => {
                  const tr = s.tracks[t.id];
                  return (
                    <td key={t.id} className="py-2.5 px-3 text-center">
                      {tr ? (
                        <div>
                          <span className="font-mono-data" style={{ color: gradeColor(tr.avg) }}>{tr.avg}%</span>
                          <p className="text-[11px] text-muted-foreground">{tr.mastered}/{tr.total} mastered</p>
                        </div>
                      ) : <span className="text-slate-600">—</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CurriculumTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/curriculum").then((r) => setData(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading || !data) return <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div className="space-y-8">
      <p className="text-sm text-muted-foreground">Every quest with its teaching objective, learner goal, and mapped standard. Use these to plan lessons and align assessments.</p>
      {data.territories.sort((a, b) => a.order - b.order).map((t) => {
        const quests = data.quests.filter((q) => q.territory_id === t.id).sort((a, b) => a.order - b.order);
        return (
          <div key={t.id} data-testid={`curriculum-territory-${t.id}`}>
            <div className="flex items-center gap-3 mb-3">
              <span className="w-3 h-3 rounded-full" style={{ background: t.color }} />
              <h3 className="font-display text-2xl">{t.name}</h3>
              <span className="text-xs font-mono-data text-muted-foreground">{t.subtitle} · {quests.length} quests</span>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {quests.map((q) => (
                <div key={q.id} data-testid={`curriculum-quest-${q.id}`} className="hq-glass rounded-2xl p-5">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <h4 className="font-display text-lg leading-tight">{q.title}</h4>
                    <span className="font-mono-data text-[11px] text-primary shrink-0">DOK {q.dok}</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <p className="text-slate-300"><span className="text-[11px] uppercase tracking-widest text-muted-foreground mr-1.5">Objective</span>{q.objective}</p>
                    <p className="flex items-start gap-2 text-[#8be9f0]"><Target className="w-4 h-4 mt-0.5 shrink-0 text-[#22D3EE]" /><span>{q.learner_goal}</span></p>
                    <p className="text-xs"><span className="font-mono-data text-primary">{q.standard.code}</span> <span className="text-muted-foreground">· {q.standard.description}</span></p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function LeaderboardControlsTab({ expeditions, reload }) {
  const toggle = async (id) => {
    const res = await api.patch(`/expeditions/${id}/leaderboard`);
    toast.success(res.data.leaderboard_visible ? "Leaderboard shown to Explorers" : "Leaderboard hidden");
    reload();
  };

  return (
    <div className="space-y-4">
      <Link to="/leaderboard" className="inline-flex items-center gap-2 text-primary hover:underline" data-testid="view-full-leaderboard-link">
        <Trophy className="w-4 h-4" /> Open the full Rankings view
      </Link>
      {expeditions.length === 0 && <p className="text-muted-foreground py-8">Create an Expedition to manage its leaderboard.</p>}
      {expeditions.map((e) => (
        <div key={e.expedition_id} className="hq-glass rounded-2xl p-5 flex items-center justify-between">
          <div>
            <h3 className="font-display text-xl">{e.name}</h3>
            <p className="text-sm text-muted-foreground">Leaderboard {e.leaderboard_visible ? "visible" : "hidden"} to Explorers</p>
          </div>
          <Switch data-testid={`toggle-leaderboard-${e.join_code}`} checked={e.leaderboard_visible} onCheckedChange={() => toggle(e.expedition_id)} />
        </div>
      ))}
    </div>
  );
}
