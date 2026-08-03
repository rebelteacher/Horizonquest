import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Download, CheckCircle2, ArrowLeft, Gem, Loader2 } from "lucide-react";
import { toast } from "sonner";

export function LabActions({ questId, onExport, exportLabel = "Export PDF" }) {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [exporting, setExporting] = useState(false);

  const complete = async () => {
    setBusy(true);
    try {
      const res = await api.post(`/labs/${questId}/complete`);
      await refresh();
      setDone(true);
      if (res.data.bonus > 0) toast.success(`Lab complete! +${res.data.bonus} Horizon Points`);
      else toast.info("Lab already completed — nice practice!");
    } catch (e) {
      toast.error("Could not save lab result.");
    } finally {
      setBusy(false);
    }
  };

  const doExport = async () => {
    setExporting(true);
    try {
      await onExport();
      toast.success("PDF exported ⛵");
    } catch (e) {
      toast.error("Export failed. Try again.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="flex flex-wrap gap-3 mt-6">
      <Button data-testid="lab-export-btn" variant="outline" className="border-white/15" onClick={doExport} disabled={exporting}>
        {exporting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}{exportLabel}
      </Button>
      <Button data-testid="lab-complete-btn" onClick={complete} disabled={busy || done} className="bg-primary text-primary-foreground hover:bg-[#FDBA74]">
        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : done ? <><CheckCircle2 className="w-4 h-4 mr-2" />Completed</> : <><Gem className="w-4 h-4 mr-2" />Complete Lab (+75)</>}
      </Button>
      <Button data-testid="lab-back-btn" variant="ghost" onClick={() => navigate(`/quest/${questId}`)}><ArrowLeft className="w-4 h-4 mr-2" />Back to quest</Button>
    </div>
  );
}
