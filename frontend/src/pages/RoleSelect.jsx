import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { Compass, Ship, Anchor, Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function RoleSelect() {
  const { user, loading, setUser } = useAuth();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(null);

  useEffect(() => {
    if (!loading && !user) navigate("/", { replace: true });
    if (!loading && user?.role) navigate(user.role === "guide" ? "/guide" : "/map", { replace: true });
  }, [user, loading, navigate]);

  const choose = async (role) => {
    setSaving(role);
    try {
      const res = await api.post("/auth/role", { role });
      setUser(res.data);
      toast.success(role === "guide" ? "Welcome aboard, Guide!" : "Set sail, Explorer!");
      navigate(role === "guide" ? "/guide" : "/map", { replace: true });
    } catch (e) {
      toast.error("Could not save your role. Try again.");
      setSaving(null);
    }
  };

  const cards = [
    {
      role: "explorer",
      icon: Ship,
      title: "Explorer",
      tag: "Student",
      desc: "Set out across the world map, complete Trials, earn Horizon Points, and rise through the Fleet rankings.",
      accent: "primary",
    },
    {
      role: "guide",
      icon: Anchor,
      title: "Guide",
      tag: "Teacher",
      desc: "Create Expeditions, share join codes, track standards mastery, and steer the leaderboard.",
      accent: "teal",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16">
      <Compass className="w-10 h-10 text-primary hq-float mb-6" />
      <h1 className="font-display text-4xl sm:text-5xl text-center tracking-tight">Choose your path</h1>
      <p className="text-muted-foreground mt-3 mb-12 text-center">How will you journey through HorizonQuest?</p>

      <div className="grid gap-6 md:grid-cols-2 w-full max-w-3xl">
        {cards.map((c, i) => (
          <button
            key={c.role}
            data-testid={`role-${c.role}-btn`}
            disabled={!!saving}
            onClick={() => choose(c.role)}
            style={{ animationDelay: `${0.1 * (i + 1)}s` }}
            className={`hq-fade-up text-left hq-glass rounded-2xl p-8 border transition-all duration-200 hover:-translate-y-1 disabled:opacity-60 ${
              c.accent === "primary"
                ? "border-primary/25 hover:border-primary/60 hover:hq-glow-gold"
                : "border-[#06B6D4]/25 hover:border-[#06B6D4]/60 hover:hq-glow-teal"
            }`}
          >
            <div className="flex items-center justify-between mb-6">
              <c.icon className={`w-10 h-10 ${c.accent === "primary" ? "text-primary" : "text-[#06B6D4]"}`} />
              <span className="text-xs font-mono-data uppercase tracking-widest text-muted-foreground">{c.tag}</span>
            </div>
            <h2 className="font-display text-3xl mb-2">{c.title}</h2>
            <p className="text-slate-400 text-sm leading-relaxed">{c.desc}</p>
            {saving === c.role && <Loader2 className="w-5 h-5 mt-4 animate-spin text-primary" />}
          </button>
        ))}
      </div>
    </div>
  );
}
