import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import AuthCallback from "@/components/AuthCallback";
import Landing from "@/pages/Landing";
import RoleSelect from "@/pages/RoleSelect";
import JourneyMap from "@/pages/JourneyMap";
import QuestView from "@/pages/QuestView";
import Leaderboard from "@/pages/Leaderboard";
import GuideConsole from "@/pages/GuideConsole";
import MockMeeting from "@/pages/MockMeeting";
import DocEditor from "@/pages/DocEditor";
import SpreadsheetEditor from "@/pages/SpreadsheetEditor";
import SlideBuilder from "@/pages/SlideBuilder";
import CipherPlayground from "@/pages/CipherPlayground";
import PhishingSpotter from "@/pages/PhishingSpotter";
import { Compass } from "lucide-react";

function Loader() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background">
      <Compass className="w-10 h-10 text-primary animate-spin" style={{ animationDuration: "3s" }} />
    </div>
  );
}

function Protected({ children, role }) {
  const { user, loading } = useAuth();
  if (loading) return <Loader />;
  if (!user) return <Navigate to="/" replace />;
  if (!user.role) return <Navigate to="/welcome" replace />;
  if (role && user.role !== role) {
    return <Navigate to={user.role === "guide" ? "/guide" : "/map"} replace />;
  }
  return children;
}

function AppRouter() {
  const location = useLocation();
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/welcome" element={<RoleSelect />} />
      <Route path="/map" element={<Protected role="explorer"><JourneyMap /></Protected>} />
      <Route path="/quest/:questId" element={<Protected role="explorer"><QuestView /></Protected>} />
      <Route path="/lab/mock-meeting" element={<Protected role="explorer"><MockMeeting /></Protected>} />
      <Route path="/lab/doc-editor" element={<Protected role="explorer"><DocEditor /></Protected>} />
      <Route path="/lab/spreadsheet" element={<Protected role="explorer"><SpreadsheetEditor /></Protected>} />
      <Route path="/lab/slide-builder" element={<Protected role="explorer"><SlideBuilder /></Protected>} />
      <Route path="/lab/cipher" element={<Protected role="explorer"><CipherPlayground /></Protected>} />
      <Route path="/lab/phishing" element={<Protected role="explorer"><PhishingSpotter /></Protected>} />
      <Route path="/leaderboard" element={<Protected><Leaderboard /></Protected>} />
      <Route path="/guide" element={<Protected role="guide"><GuideConsole /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <div className="App hq-noise">
      <BrowserRouter>
        <AuthProvider>
          <AppRouter />
          <Toaster position="top-center" richColors />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}
