import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Compass } from "lucide-react";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const process = async () => {
      const hash = window.location.hash || "";
      const match = hash.match(/session_id=([^&]+)/);
      const sessionId = match ? decodeURIComponent(match[1]) : null;

      if (!sessionId) {
        navigate("/", { replace: true });
        return;
      }

      try {
        const res = await api.post(
          "/auth/session",
          {},
          { headers: { "X-Session-ID": sessionId } }
        );
        const u = res.data.user;
        setUser(u);
        window.history.replaceState(null, "", window.location.pathname);
        if (!u.role) {
          navigate("/welcome", { replace: true });
        } else if (u.role === "guide") {
          navigate("/guide", { replace: true });
        } else {
          navigate("/map", { replace: true });
        }
      } catch (e) {
        navigate("/", { replace: true });
      }
    };
    process();
  }, [navigate, setUser]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground">
      <Compass className="w-12 h-12 text-primary animate-spin" style={{ animationDuration: "3s" }} />
      <p className="mt-6 font-display text-2xl">Charting your course…</p>
    </div>
  );
}
