import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Compass, Map, Trophy, LogOut, Anchor, Gem } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function AppNav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  if (!user) return null;

  const isExplorer = user.role === "explorer";

  const navItem = (to, label, Icon) => {
    const active = location.pathname === to;
    return (
      <Link
        to={to}
        data-testid={`nav-${label.toLowerCase()}`}
        className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-colors duration-200 ${
          active ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-foreground hover:bg-white/5"
        }`}
      >
        <Icon className="w-4 h-4" />
        <span className="hidden sm:inline">{label}</span>
      </Link>
    );
  };

  const handleLogout = async () => {
    await logout();
    navigate("/", { replace: true });
  };

  return (
    <header className="sticky top-0 z-40 hq-glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link to={isExplorer ? "/map" : "/guide"} className="flex items-center gap-2.5" data-testid="nav-logo">
          <Compass className="w-7 h-7 text-primary hq-float" />
          <span className="font-display text-2xl tracking-tight">HorizonQuest</span>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          {isExplorer && navItem("/map", "Map", Map)}
          {isExplorer && (
            <div className="hidden sm:flex items-center gap-4 px-4 mr-1 border-l border-white/10">
              <span className="flex items-center gap-1.5 text-sm" data-testid="nav-points">
                <Gem className="w-4 h-4 text-primary" />
                <span className="font-mono-data text-primary">{user.horizon_points ?? 0}</span>
              </span>
              <span className="flex items-center gap-1.5 text-sm" data-testid="nav-marks">
                <Anchor className="w-4 h-4 text-[#06B6D4]" />
                <span className="font-mono-data text-[#06B6D4]">{user.compass_marks ?? 0}</span>
              </span>
            </div>
          )}
          {navItem("/leaderboard", "Rankings", Trophy)}
          {user.role === "guide" && navItem("/guide", "Console", Anchor)}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button data-testid="nav-user-menu" className="ml-1 rounded-full ring-1 ring-white/10 hover:ring-primary/50 transition-colors">
                <Avatar className="w-9 h-9">
                  <AvatarImage src={user.picture} alt={user.name} />
                  <AvatarFallback className="bg-secondary text-foreground">{(user.name || "E")[0]}</AvatarFallback>
                </Avatar>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 hq-glass">
              <DropdownMenuLabel>
                <div className="font-medium">{user.name}</div>
                <div className="text-xs text-muted-foreground capitalize">{user.role} {user.fleet ? `· ${user.fleet}` : ""}</div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem data-testid="logout-btn" onClick={handleLogout} className="cursor-pointer">
                <LogOut className="w-4 h-4 mr-2" /> Set sail elsewhere
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </nav>
      </div>
    </header>
  );
}
