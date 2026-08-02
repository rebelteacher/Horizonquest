import { useState, useRef, useEffect } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles, Send, Bot } from "lucide-react";
import { API } from "@/lib/api";

export default function AICopilot({ questId, questTitle }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Ahoy, Explorer! I'm your Copilot. Ask me for a hint and I'll nudge you in the right direction — but the discovery is yours to make. ⛵" },
  ]);
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setStreaming(true);

    try {
      const res = await fetch(`${API}/ai/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: text, quest_id: questId }),
      });
      if (!res.ok || !res.body) throw new Error("no stream");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        acc += decoder.decode(value, { stream: true });
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { role: "assistant", content: acc };
          return copy;
        });
      }
    } catch (e) {
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { role: "assistant", content: "The signal dropped, Explorer. Try again in a moment." };
        return copy;
      });
    } finally {
      setStreaming(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          data-testid="copilot-open-btn"
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-5 py-3.5 rounded-full bg-[#22D3EE] text-[#04121f] font-medium hq-glow-teal hover:-translate-y-1 transition-transform duration-200"
        >
          <Sparkles className="w-5 h-5" /> Copilot
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:max-w-md hq-glass border-l border-[#22D3EE]/30 flex flex-col p-0">
        <SheetHeader className="p-6 pb-4 border-b border-white/10">
          <SheetTitle className="flex items-center gap-2 font-display text-2xl">
            <Bot className="w-6 h-6 text-[#22D3EE]" /> Copilot
          </SheetTitle>
          {questTitle && <p className="text-sm text-muted-foreground text-left">Guiding you through “{questTitle}”</p>}
        </SheetHeader>

        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-4 hq-scrollbar">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-primary/20 text-foreground rounded-br-sm"
                    : "bg-white/5 text-foreground/90 rounded-bl-sm border border-[#22D3EE]/20"
                }`}
              >
                {m.content || <span className="text-muted-foreground">…</span>}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-white/10 flex items-center gap-2">
          <Input
            data-testid="copilot-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask for a hint…"
            className="bg-white/5 border-white/10"
          />
          <Button data-testid="copilot-send-btn" onClick={send} disabled={streaming} size="icon" className="bg-[#22D3EE] text-[#04121f] hover:bg-[#67E8F9]">
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
