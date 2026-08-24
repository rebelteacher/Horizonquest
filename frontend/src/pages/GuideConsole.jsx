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
import { Anchor, Plus, Copy, Users, ClipboardCheck, BarChart3, Trophy, Loader2, Check, Compass, BookOpen, Target, Download, ListChecks, Trash2, X as XIcon, BookMarked, Printer, Pencil, Search, UserCog } from "lucide-react";
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
            <TabsTrigger value="assignments" data-testid="tab-assignments"><ListChecks className="w-4 h-4 mr-2" />Assignments</TabsTrigger>
            <TabsTrigger value="reports" data-testid="tab-reports"><ClipboardCheck className="w-4 h-4 mr-2" />Reports</TabsTrigger>
            <TabsTrigger value="testscores" data-testid="tab-testscores"><Target className="w-4 h-4 mr-2" />Test Scores</TabsTrigger>
            <TabsTrigger value="questionbank" data-testid="tab-questionbank"><BookMarked className="w-4 h-4 mr-2" />Question Bank</TabsTrigger>
            <TabsTrigger value="leaderboard" data-testid="tab-leaderboard"><Trophy className="w-4 h-4 mr-2" />Rankings</TabsTrigger>
          </TabsList>

          <TabsContent value="expeditions" className="mt-6">
            <ExpeditionsTab expeditions={expeditions} loading={loading} reload={loadExpeditions} />
          </TabsContent>
          <TabsContent value="reviews" className="mt-6"><ReviewsTab /></TabsContent>
          <TabsContent value="mastery" className="mt-6"><MasteryTab expeditions={expeditions} /></TabsContent>
          <TabsContent value="curriculum" className="mt-6"><CurriculumTab /></TabsContent>
          <TabsContent value="assignments" className="mt-6"><AssignmentsTab expeditions={expeditions} /></TabsContent>
          <TabsContent value="reports" className="mt-6"><ReportsTab /></TabsContent>
          <TabsContent value="testscores" className="mt-6"><TestScoresTab /></TabsContent>
          <TabsContent value="questionbank" className="mt-6"><QuestionBankTab /></TabsContent>
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
  const [rename, setRename] = useState(null);
  const [rName, setRName] = useState("");
  const [rDesc, setRDesc] = useState("");
  const [savingRename, setSavingRename] = useState(false);

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

  const openRename = (e) => { setRename(e); setRName(e.name); setRDesc(e.description || ""); };
  const saveRename = async () => {
    if (!rName.trim()) { toast.error("Class name cannot be empty."); return; }
    setSavingRename(true);
    try {
      await api.patch(`/expeditions/${rename.expedition_id}`, { name: rName.trim(), description: rDesc });
      toast.success("Class renamed.");
      setRename(null);
      await reload();
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not rename the class."); }
    finally { setSavingRename(false); }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="space-y-6 h-fit">
        <div className="hq-glass rounded-2xl p-6 border-t border-t-[#22D3EE]/30">
          <h2 className="font-display text-2xl mb-4 flex items-center gap-2"><Plus className="w-5 h-5 text-[#22D3EE]" /> New Expedition</h2>
          <div className="space-y-3">
            <Input data-testid="expedition-name-input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Expedition name (e.g. Period 3 Voyage)" className="bg-white/5 border-white/10" />
            <Textarea data-testid="expedition-desc-input" value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Description (optional)" className="bg-white/5 border-white/10" />
            <Button data-testid="create-expedition-btn" onClick={create} disabled={creating} className="w-full bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]">
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Expedition"}
            </Button>
          </div>
        </div>
        <RoleFixPanel />
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
                  <Button variant="outline" size="sm" className="border-white/15 gap-1.5" data-testid={`rename-expedition-${e.join_code}`} onClick={() => openRename(e)}><Pencil className="w-3.5 h-3.5" /> Rename</Button>
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

      <Dialog open={!!rename} onOpenChange={(o) => !o && setRename(null)}>
        <DialogContent className="hq-glass border-white/10">
          <DialogHeader><DialogTitle className="font-display text-2xl">Rename class</DialogTitle><DialogDescription>The join code stays the same — Explorers won't need to rejoin.</DialogDescription></DialogHeader>
          <div className="space-y-3">
            <Input data-testid="rename-name-input" value={rName} onChange={(e) => setRName(e.target.value)} placeholder="Class name" className="bg-white/5 border-white/10" />
            <Textarea data-testid="rename-desc-input" value={rDesc} onChange={(e) => setRDesc(e.target.value)} placeholder="Description (optional)" className="bg-white/5 border-white/10" />
            <div className="flex gap-2 justify-end">
              <Button variant="outline" className="border-white/15" onClick={() => setRename(null)}>Cancel</Button>
              <Button data-testid="rename-save-btn" onClick={saveRename} disabled={savingRename} className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]">{savingRename ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save"}</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function RoleFixPanel() {
  const { user } = useAuth();
  const [q, setQ] = useState("");
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [savingId, setSavingId] = useState(null);

  const search = async () => {
    if (q.trim().length < 3) { toast.error("Type at least 3 characters of the email or name."); return; }
    setSearching(true);
    try {
      const res = await api.get(`/admin/users`, { params: { q: q.trim() } });
      setResults(res.data.users || []);
    } catch (e) { toast.error(e?.response?.data?.detail || "Search failed."); }
    finally { setSearching(false); }
  };

  const setRole = async (u, role) => {
    setSavingId(u.user_id);
    try {
      await api.post(`/admin/users/${u.user_id}/role`, { role });
      toast.success(`${u.name || u.email} is now ${role === "guide" ? "a Guide" : "an Explorer"}.`);
      setResults((r) => r.map((x) => (x.user_id === u.user_id ? { ...x, role } : x)));
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not update role."); }
    finally { setSavingId(null); }
  };

  return (
    <div className="hq-glass rounded-2xl p-6 border-t border-t-primary/30" data-testid="role-fix-panel">
      <h2 className="font-display text-2xl mb-1 flex items-center gap-2"><UserCog className="w-5 h-5 text-primary" /> Fix account role</h2>
      <p className="text-sm text-muted-foreground mb-4">A student who signed up as a Guide by mistake? Find them and switch them to Explorer.</p>
      <div className="flex gap-2">
        <Input data-testid="role-fix-search-input" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && search()} placeholder="Search email or name…" className="bg-white/5 border-white/10" />
        <Button data-testid="role-fix-search-btn" onClick={search} disabled={searching} className="bg-primary text-primary-foreground hover:bg-[#FDBA74] shrink-0">{searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}</Button>
      </div>
      {results && (
        <div className="mt-4 space-y-2 max-h-80 overflow-y-auto hq-scrollbar">
          {results.length === 0 && <p className="text-sm text-muted-foreground">No matching accounts.</p>}
          {results.map((u) => (
            <div key={u.user_id} data-testid={`role-fix-user-${u.user_id}`} className="flex items-center justify-between gap-2 p-3 rounded-lg bg-white/5">
              <div className="min-w-0">
                <p className="text-sm truncate">{u.name}</p>
                <p className="text-xs text-muted-foreground truncate">{u.email}</p>
                <span className={`text-[11px] font-mono-data uppercase tracking-wider ${u.role === "guide" ? "text-[#22D3EE]" : "text-primary"}`}>{u.role || "no role"}</span>
              </div>
              {u.user_id === user?.user_id ? (
                <span className="text-[11px] text-muted-foreground shrink-0">You</span>
              ) : (
                <div className="flex gap-1.5 shrink-0">
                  <Button size="sm" variant={u.role === "explorer" ? "default" : "outline"} className={u.role === "explorer" ? "bg-primary text-primary-foreground" : "border-white/15"} disabled={savingId === u.user_id} data-testid={`set-explorer-${u.user_id}`} onClick={() => setRole(u, "explorer")}>{savingId === u.user_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Explorer"}</Button>
                  <Button size="sm" variant={u.role === "guide" ? "default" : "outline"} className={u.role === "guide" ? "bg-[#22D3EE] text-[#04121f]" : "border-white/15"} disabled={savingId === u.user_id} data-testid={`set-guide-${u.user_id}`} onClick={() => setRole(u, "guide")}>Guide</Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const STUDIO_TRACKS = [{ id: "docs", name: "Word Processing" }, { id: "sheets", name: "Spreadsheets" }, { id: "slides", name: "Presentations" }, { id: "email", name: "Email & Communication" }];

function AssignmentsTab({ expeditions }) {
  const [expId, setExpId] = useState("");
  const [track, setTrack] = useState("email");
  const [missions, setMissions] = useState([]);
  const [selected, setSelected] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const loadAssignments = useCallback(async () => {
    setLoading(true);
    try { const res = await api.get("/assignments"); setAssignments(res.data); } catch (e) { /* noop */ }
    setLoading(false);
  }, []);
  useEffect(() => { loadAssignments(); }, [loadAssignments]);

  useEffect(() => {
    setSelected([]);
    api.get(`/studio/${track}`).then((r) => setMissions([...r.data.missions].sort((a, b) => a.order - b.order))).catch(() => setMissions([]));
  }, [track]);

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const create = async () => {
    if (!expId) { toast.error("Pick a class (Expedition)."); return; }
    if (selected.length === 0) { toast.error("Select at least one mission."); return; }
    setCreating(true);
    try {
      await api.post("/assignments", { expedition_id: expId, track, mission_ids: selected });
      toast.success("Missions assigned! ⛵");
      setSelected([]);
      await loadAssignments();
    } catch (e) { toast.error("Could not create assignment."); }
    finally { setCreating(false); }
  };

  const remove = async (id) => {
    await api.delete(`/assignments/${id}`);
    toast.success("Assignment removed.");
    await loadAssignments();
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="hq-glass rounded-2xl p-6 border-t border-t-[#22D3EE]/30 h-fit">
        <h2 className="font-display text-2xl mb-4 flex items-center gap-2"><ListChecks className="w-5 h-5 text-[#22D3EE]" /> New Assignment</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-muted-foreground">Class (Expedition)</label>
            <Select value={expId} onValueChange={setExpId}>
              <SelectTrigger data-testid="assign-expedition-select" className="bg-white/5 border-white/10 mt-1"><SelectValue placeholder="Choose a class…" /></SelectTrigger>
              <SelectContent>
                {expeditions.length === 0 && <div className="px-3 py-2 text-sm text-muted-foreground">Create an Expedition first.</div>}
                {expeditions.map((e) => <SelectItem key={e.expedition_id} value={e.expedition_id} data-testid={`assign-exp-opt-${e.join_code}`}>{e.name} · {e.member_count} Explorers</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Studio track</label>
            <Select value={track} onValueChange={setTrack}>
              <SelectTrigger data-testid="assign-track-select" className="bg-white/5 border-white/10 mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>{STUDIO_TRACKS.map((t) => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Missions ({selected.length} selected)</label>
            <div className="mt-1 max-h-72 overflow-y-auto hq-scrollbar space-y-1 rounded-lg border border-white/10 p-2">
              {missions.map((m) => (
                <button key={m.id} data-testid={`assign-mission-${m.id}`} onClick={() => toggle(m.id)}
                  className={`w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors ${selected.includes(m.id) ? "bg-[#22D3EE]/15 text-white" : "text-slate-300 hover:bg-white/5"}`}>
                  <span className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 ${selected.includes(m.id) ? "bg-[#22D3EE] border-[#22D3EE]" : "border-white/25"}`}>{selected.includes(m.id) && <Check className="w-3 h-3 text-[#04121f]" />}</span>
                  <span className="truncate">{m.order}. {m.title}</span>
                </button>
              ))}
            </div>
          </div>
          <Button data-testid="create-assignment-btn" onClick={create} disabled={creating} className="w-full bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]">
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Assign to class"}
          </Button>
        </div>
      </div>

      <div className="lg:col-span-2">
        {loading ? <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div> : (
          <div className="space-y-4">
            {assignments.length === 0 && <p className="text-muted-foreground py-12 text-center">No assignments yet. Assign missions to a class to track who's finished.</p>}
            {assignments.map((a) => {
              const mids = a.mission_ids;
              return (
                <div key={a.assignment_id} data-testid={`assignment-card-${a.assignment_id}`} className="hq-glass rounded-2xl p-5">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="min-w-0">
                      <h3 className="font-display text-xl truncate">{a.expedition_name}</h3>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {mids.map((mid) => <span key={mid} className="text-xs bg-white/5 rounded px-2 py-0.5 text-slate-300">{a.mission_titles[mid] || mid}</span>)}
                      </div>
                    </div>
                    <button data-testid={`delete-assignment-${a.assignment_id}`} onClick={() => remove(a.assignment_id)} className="text-slate-400 hover:text-[#E11D48] shrink-0"><Trash2 className="w-4 h-4" /></button>
                  </div>
                  {a.students.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No Explorers have joined this class yet.</p>
                  ) : (
                    <div className="overflow-x-auto hq-scrollbar">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-xs text-muted-foreground">
                            <th className="py-1 pr-3 font-medium">Explorer</th>
                            {mids.map((mid) => <th key={mid} className="py-1 px-2 font-medium text-center"><span className="block max-w-[90px] truncate mx-auto" title={a.mission_titles[mid]}>{a.mission_titles[mid] || mid}</span></th>)}
                            <th className="py-1 pl-2 font-medium text-center">Done</th>
                          </tr>
                        </thead>
                        <tbody>
                          {a.students.map((s) => (
                            <tr key={s.user_id} data-testid={`assign-row-${s.user_id}`} className="border-t border-white/10">
                              <td className="py-1.5 pr-3 truncate max-w-[160px]">{s.name || s.email}</td>
                              {mids.map((mid) => (
                                <td key={mid} className="py-1.5 px-2 text-center">
                                  {s.done[mid] ? <Check className="w-4 h-4 text-[#34D399] mx-auto" /> : <XIcon className="w-4 h-4 text-slate-600 mx-auto" />}
                                </td>
                              ))}
                              <td className="py-1.5 pl-2 text-center font-mono-data" style={{ color: s.done_count === mids.length ? "#34D399" : "#FB923C" }}>{s.done_count}/{mids.length}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
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

const QB_SECTIONS = [
  { id: "docs", name: "Word Processing" },
  { id: "sheets", name: "Spreadsheets" },
  { id: "slides", name: "Presentations" },
  { id: "email", name: "Email" },
  { id: "final", name: "Final Exam" },
];

function QuestionBankTab() {
  const [bank, setBank] = useState(null);
  const [loading, setLoading] = useState(true);
  const [section, setSection] = useState("email");
  useEffect(() => {
    api.get("/assessments/bank").then((r) => setBank(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (!bank) return <p className="text-sm text-muted-foreground py-10 text-center">Could not load the question bank.</p>;

  const assessments = section === "final" ? [bank.final] : (bank.tracks[section] || []);
  const totalQ = assessments.reduce((n, a) => n + a.questions.length, 0);

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-4 flex-wrap">
        <p className="text-sm text-muted-foreground max-w-2xl">Review every question and its correct answer (shown in green). To change one, just tell me its reference like <span className="text-[#22D3EE] font-mono-data">email-cp1 #5</span> and the new wording. Students see the answer choices in a shuffled order.</p>
      </div>
      <div className="flex flex-wrap gap-2 mb-6">
        {QB_SECTIONS.map((s) => (
          <button key={s.id} data-testid={`qb-section-${s.id}`} onClick={() => setSection(s.id)}
            className={`px-3 h-9 rounded-full text-sm transition-colors ${section === s.id ? "bg-[#818CF8] text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>{s.name}</button>
        ))}
      </div>

      <p className="text-xs text-muted-foreground mb-4 font-mono-data">{totalQ} questions in this section</p>

      <div className="space-y-8">
        {assessments.map((a) => (
          <div key={a.id} data-testid={`qb-assessment-${a.id}`}>
            <div className="flex items-center gap-2 mb-3 sticky top-16 bg-background/80 backdrop-blur py-2 z-10">
              <h3 className="font-display text-xl">{a.title}</h3>
              <span className="text-xs font-mono-data text-muted-foreground bg-white/5 rounded px-2 py-0.5">{a.id}</span>
              <span className="text-xs text-muted-foreground">· {a.questions.length} in pool</span>
            </div>
            <div className="space-y-3">
              {a.questions.map((q) => (
                <div key={q.n} data-testid={`qb-q-${a.id}-${q.n}`} className="hq-glass rounded-xl p-4">
                  <p className="text-sm text-white font-medium flex gap-2">
                    <span className="font-mono-data text-[#22D3EE] shrink-0">{a.id} #{q.n}</span>
                    <span>{q.q}</span>
                  </p>
                  <div className="mt-2 grid gap-1 sm:grid-cols-2">
                    {q.options.map((opt, oi) => {
                      const correct = opt === q.correct;
                      return (
                        <div key={oi} className={`text-sm px-2 py-1 rounded flex items-center gap-1.5 ${correct ? "bg-[#34D399]/15 text-[#34D399]" : "text-slate-400"}`}>
                          {correct ? <Check className="w-3.5 h-3.5 shrink-0" /> : <span className="w-3.5 shrink-0" />}{opt}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TestScoresTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api.get("/assessments/reports").then((r) => setData(r.data)).finally(() => setLoading(false));
  }, []);
  const color = (s) => (s == null ? "#64748b" : s >= 90 ? "#34D399" : s >= 70 ? "#22D3EE" : "#E11D48");
  const SHORT = { docs: "Docs", sheets: "Sheets", slides: "Slides", email: "Email" };
  const label = (id) => (id === "final" ? "Final" : `${SHORT[id.split("-")[0]] || id} C${id.slice(-1)}`);

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (!data || data.students.length === 0) return <p className="text-sm text-muted-foreground py-10 text-center">No Explorers have joined your Expeditions yet. Test scores will appear here once students join and take a checkpoint or the final.</p>;

  const exportCSV = () => {
    const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const rows = [["Explorer", "Email", ...data.columns.map((c) => c.title)].map(esc).join(",")];
    data.students.forEach((s) => rows.push([s.name || s.email, s.email, ...data.columns.map((c) => (s.scores[c.id] != null ? `${s.scores[c.id]}%` : ""))].map(esc).join(",")));
    const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `test-scores-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-4 flex-wrap">
        <p className="text-sm text-muted-foreground">Best checkpoint & final scores per Explorer. Blank = not attempted yet.</p>
        <button data-testid="testscores-export-csv-btn" onClick={exportCSV} className="inline-flex items-center gap-2 shrink-0 px-3 h-9 rounded-md bg-[#22D3EE] text-[#04121f] text-sm font-medium hover:bg-[#22D3EE]/90"><Download className="w-4 h-4" /> Export CSV</button>
      </div>
      <div className="overflow-x-auto hq-scrollbar">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted-foreground">
              <th className="py-2 pr-3 font-medium sticky left-0 bg-transparent">Explorer</th>
              {data.columns.map((c) => <th key={c.id} className="py-2 px-2 font-medium text-center whitespace-nowrap"><span title={c.title}>{label(c.id)}</span></th>)}
              <th className="py-2 pl-3 font-medium text-center whitespace-nowrap">Report</th>
            </tr>
          </thead>
          <tbody>
            {data.students.map((s) => (
              <tr key={s.user_id} data-testid={`testscore-row-${s.user_id}`} className="border-t border-white/10">
                <td className="py-2 pr-3 truncate max-w-[160px]">{s.name || s.email}</td>
                {data.columns.map((c) => (
                  <td key={c.id} className="py-2 px-2 text-center font-mono-data" style={{ color: color(s.scores[c.id]) }}>{s.scores[c.id] != null ? `${s.scores[c.id]}%` : "—"}</td>
                ))}
                <td className="py-2 pl-3 text-center"><Link to={`/report/${s.user_id}`} data-testid={`report-link-${s.user_id}`} className="inline-flex items-center gap-1 text-[#22D3EE] hover:underline whitespace-nowrap"><Printer className="w-3.5 h-3.5" /> Report</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
