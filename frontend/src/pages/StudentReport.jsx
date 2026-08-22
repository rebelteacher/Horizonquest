import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import AppNav from "@/components/AppNav";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Printer, Loader2, Gem, Anchor, Award } from "lucide-react";

const scoreColor = (s, pass = 70) => (s == null ? "#94a3b8" : s >= 90 ? "#059669" : s >= pass ? "#0891b2" : "#dc2626");

export default function StudentReport() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/reports/student/${userId}`).then((r) => setData(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Could not load report"))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return (<div className="min-h-screen"><AppNav /><div className="flex justify-center py-40"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div></div>);
  if (err) return (<div className="min-h-screen"><AppNav /><div className="max-w-xl mx-auto px-6 py-24 text-center"><p className="text-muted-foreground mb-6" data-testid="report-error">{err}</p><Button onClick={() => navigate("/guide")} variant="outline">Back to Console</Button></div></div>);

  const s = data.student;
  const date = new Date(data.generated_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });

  return (
    <div className="min-h-screen bg-[#04121f] report-root">
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body, .report-root { background: #ffffff !important; }
          .report-sheet { box-shadow: none !important; margin: 0 !important; }
          @page { margin: 14mm; }
        }
      `}</style>
      <div className="no-print"><AppNav /></div>

      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="no-print flex items-center justify-between mb-4">
          <button data-testid="report-back" onClick={() => navigate("/guide")} className="flex items-center gap-2 text-sm text-slate-300 hover:text-white"><ArrowLeft className="w-4 h-4" /> Back to Console</button>
          <Button data-testid="report-print-btn" onClick={() => window.print()} className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]"><Printer className="w-4 h-4 mr-2" /> Print / Save PDF</Button>
        </div>

        {/* printable sheet */}
        <div className="report-sheet bg-white text-slate-900 rounded-xl shadow-2xl p-8" data-testid="student-report">
          <div className="flex items-start justify-between border-b-2 border-slate-800 pb-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">HorizonQuest — Progress Report</h1>
              <p className="text-sm text-slate-500 mt-0.5">CTE Skill Studio · Checkpoints & Final</p>
            </div>
            <div className="text-right text-xs text-slate-500">
              <p>Generated {date}</p>
              {data.guide_name && <p>Guide: {data.guide_name}</p>}
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-2 mt-4 text-sm">
            <p><span className="text-slate-500">Explorer:</span> <b className="text-slate-900" data-testid="report-name">{s.name || s.email}</b></p>
            <p><span className="text-slate-500">Email:</span> {s.email}</p>
            <p><span className="text-slate-500">Class:</span> {data.classes.join(", ") || "—"}</p>
            <p><span className="text-slate-500">Fleet / Rank:</span> {s.fleet || "—"}{s.tier ? ` · ${s.tier}` : ""}</p>
          </div>

          <div className="flex flex-wrap gap-4 mt-4">
            <div className="flex items-center gap-2 text-sm"><Award className="w-4 h-4 text-slate-700" /> Level <b>{s.level}</b></div>
            <div className="flex items-center gap-2 text-sm"><Gem className="w-4 h-4 text-indigo-600" /> <b>{s.horizon_points}</b> Horizon Points</div>
            <div className="flex items-center gap-2 text-sm"><Anchor className="w-4 h-4 text-cyan-600" /> <b>{s.compass_marks}</b> Compass Marks</div>
          </div>

          {/* Skill Studio */}
          <h2 className="text-lg font-bold mt-6 mb-2 text-slate-900">Skill Studio</h2>
          <table className="w-full text-sm border border-slate-200">
            <thead className="bg-slate-100 text-left">
              <tr><th className="py-1.5 px-2 font-semibold">Track</th><th className="py-1.5 px-2 font-semibold text-center">Mastered</th><th className="py-1.5 px-2 font-semibold text-center">Attempted</th><th className="py-1.5 px-2 font-semibold text-center">Average</th></tr>
            </thead>
            <tbody>
              {data.studio.map((t) => (
                <tr key={t.track} data-testid={`report-studio-${t.track}`} className="border-t border-slate-200">
                  <td className="py-1.5 px-2">{t.name}</td>
                  <td className="py-1.5 px-2 text-center">{t.mastered}/{t.total}</td>
                  <td className="py-1.5 px-2 text-center">{t.attempted}/{t.total}</td>
                  <td className="py-1.5 px-2 text-center font-semibold" style={{ color: scoreColor(t.avg, 90) }}>{t.avg != null ? `${t.avg}%` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Checkpoints & Final */}
          <h2 className="text-lg font-bold mt-6 mb-2 text-slate-900">Checkpoint Tests & Final Exam</h2>
          <table className="w-full text-sm border border-slate-200">
            <thead className="bg-slate-100 text-left">
              <tr><th className="py-1.5 px-2 font-semibold">Assessment</th><th className="py-1.5 px-2 font-semibold text-center">Best Score</th><th className="py-1.5 px-2 font-semibold text-center">Result</th></tr>
            </thead>
            <tbody>
              {data.checkpoints.map((c) => (
                <tr key={c.id} data-testid={`report-cp-${c.id}`} className="border-t border-slate-200">
                  <td className="py-1.5 px-2">{c.title}</td>
                  <td className="py-1.5 px-2 text-center font-semibold" style={{ color: scoreColor(c.best, c.pass) }}>{c.best != null ? `${c.best}%` : "—"}</td>
                  <td className="py-1.5 px-2 text-center text-xs">{c.best == null ? "Not taken" : c.best >= c.pass ? "Passed" : "Not passed"}</td>
                </tr>
              ))}
              <tr data-testid="report-final" className="border-t-2 border-slate-300 bg-amber-50">
                <td className="py-1.5 px-2 font-semibold">{data.final.title}</td>
                <td className="py-1.5 px-2 text-center font-bold" style={{ color: scoreColor(data.final.best, data.final.pass) }}>{data.final.best != null ? `${data.final.best}%` : "—"}</td>
                <td className="py-1.5 px-2 text-center text-xs">{data.final.best == null ? "Not taken" : data.final.best >= data.final.pass ? "Passed" : "Not passed"}</td>
              </tr>
            </tbody>
          </table>

          <p className="text-xs text-slate-400 mt-6 border-t border-slate-200 pt-3">Skill Studio "Mastered" = 90%+. Checkpoints & Final pass at 70%. Generated by HorizonQuest.</p>
        </div>
      </div>
    </div>
  );
}
