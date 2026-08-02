import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Compass, Map, Trophy, Sparkles, Anchor, ArrowRight } from "lucide-react";

const HERO = "https://images.unsplash.com/photo-1608924066819-930edc42986a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwyfHxuYXV0aWNhbCUyMGNhcnRvZ3JhcGh5JTIwcGFyY2htZW50JTIwbWFwfGVufDB8fHx8MTc4NTcwMzE3MXww&ixlib=rb-4.1.0&q=85";

export default function Landing() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      if (!user.role) navigate("/welcome", { replace: true });
      else navigate(user.role === "guide" ? "/guide" : "/map", { replace: true });
    }
  }, [user, loading, navigate]);

  const signIn = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const features = [
    { icon: Map, title: "Chart 4 Territories", desc: "33 quests across a living world map, from the Coding Coast to the Frontier Peaks." },
    { icon: Trophy, title: "Climb the Rankings", desc: "Earn Horizon Points, win Compass Marks, and rally your Fleet up the leaderboard." },
    { icon: Sparkles, title: "AI Copilot", desc: "A Claude-powered guide gives hints — never the answer — so every discovery is yours." },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0">
        <img src={HERO} alt="" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-[#060B19]/80 via-[#060B19]/90 to-[#060B19]" />
      </div>

      <div className="relative z-10">
        <header className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Compass className="w-8 h-8 text-primary hq-float" />
            <span className="font-display text-3xl tracking-tight">HorizonQuest</span>
          </div>
          <button
            data-testid="header-signin-btn"
            onClick={signIn}
            className="px-5 py-2.5 rounded-full border border-white/15 text-sm hover:bg-white/5 transition-colors duration-200"
          >
            Sign in
          </button>
        </header>

        <main className="max-w-7xl mx-auto px-6 pt-16 sm:pt-24 pb-24">
          <div className="max-w-3xl hq-fade-up">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/30 text-primary text-xs mb-8 font-mono-data uppercase tracking-widest">
              <Anchor className="w-3.5 h-3.5" /> The learning voyage begins
            </div>
            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl leading-[1.02] tracking-tight">
              Conquer knowledge like <span className="hq-gold-text">uncharted lands.</span>
            </h1>
            <p className="mt-8 text-lg text-slate-300 max-w-xl leading-relaxed">
              HorizonQuest turns your curriculum into an epic expedition. Explorers sail from quest to
              quest, Guides chart the course — and every trial earns a place on the horizon.
            </p>

            <div className="mt-10 flex flex-col sm:flex-row gap-4">
              <button
                data-testid="hero-google-signin-btn"
                onClick={signIn}
                className="group flex items-center justify-center gap-3 px-7 py-4 rounded-full bg-primary text-primary-foreground font-medium hq-glow-gold hover:-translate-y-1 transition-transform duration-200"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                Continue with Google
                <ArrowRight className="w-4 h-4 opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all duration-200" />
              </button>
              <p className="flex items-center text-sm text-muted-foreground">Explorers & Guides · one account, choose your role.</p>
            </div>
          </div>

          <div className="mt-24 grid gap-6 md:grid-cols-3">
            {features.map((f, i) => (
              <div
                key={f.title}
                className="hq-glass rounded-2xl p-7 border-t border-t-primary/30 hq-fade-up"
                style={{ animationDelay: `${0.15 * (i + 1)}s` }}
              >
                <f.icon className="w-8 h-8 text-primary mb-5" />
                <h3 className="font-display text-2xl mb-2">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
