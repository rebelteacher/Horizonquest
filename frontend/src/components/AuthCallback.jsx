import { useEffect, useRef, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Compass, AlertTriangle } from "lucide-react";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export default function AuthCallback() {
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const process = async () => {
      const hash = window.location.hash || "";
      const match = hash.match(/session_id=([^&]+)/);
      const sessionId = match ? decodeURIComponent(match[1]) : null;

      // Clear the fragment immediately so we can never get stuck looping on it.
      window.history.replaceState(null, "", window.location.pathname + window.location.search);

      if (!sessionId) {
        window.location.replace("/");
        return;
      }

      try {
        const res = await api.post(
          "/auth/session",
          {},
          { headers: { "X-Session-ID": sessionId }, timeout: 20000 }
        );
        const u = res.data.user;
        setUser(u);
        // Hard redirect: the cookie is now set, so /auth/me becomes the source of truth.
        const dest = !u.role ? "/welcome" : u.role === "guide" ? "/guide" : "/map";
        window.location.replace(dest);
      } catch (e) {
        setFailed(true);
      }
    };
    process();
  }, [setUser]);

  if (failed) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground px-6 text-center">
        <AlertTriangle className="w-12 h-12 text-primary" />
        <p className="mt-6 font-display text-3xl">That sign-in link expired</p>
        <p className="mt-2 text-muted-foreground max-w-md">Your session link couldn't be verified — this usually happens if it was already used or timed out. Let's try again.</p>
        <button
          data-testid="auth-retry-btn"
          onClick={() => window.location.replace("/")}
          className="mt-8 px-7 py-3.5 rounded-full bg-primary text-primary-foreground font-medium hover:bg-[#FDBA74] transition-colors"
        >
          Back to sign in
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground">
      <Compass className="w-12 h-12 text-primary animate-spin" style={{ animationDuration: "3s" }} />
      <p className="mt-6 font-display text-2xl">Charting your course…</p>
    </div>
  );
}
