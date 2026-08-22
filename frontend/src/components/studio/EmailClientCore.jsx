import { useRef, useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Inbox, Send, FileText, Trash2, Search, Reply, ReplyAll, Forward, Paperclip, Bold, List, PenSquare, X, Star, Square, GripVertical, ArrowLeft } from "lucide-react";

const FOLDERS = [
  { id: "inbox", name: "Inbox", icon: Inbox },
  { id: "sent", name: "Sent", icon: Send },
  { id: "drafts", name: "Drafts", icon: FileText },
  { id: "trash", name: "Trash", icon: Trash2 },
];
const splitAddrs = (s) => (s || "").split(/[,;\s]+/).map((x) => x.trim()).filter(Boolean);
// The part of a reply/forward body the STUDENT actually typed (before the quoted original).
const studentPortion = (body) => {
  const i = (body || "").indexOf("\n---");
  return (i >= 0 ? (body || "").slice(0, i) : body || "").trim();
};
const snippetOf = (m) => (m.body || "").replace(/\s*\n+\s*/g, " ").trim().slice(0, 80);

export default function EmailClientCore({ doc, setDoc, config }) {
  const messages = doc.messages || [];
  const [folder, setFolder] = useState("inbox");
  const [openId, setOpenId] = useState(null);
  const [query, setQuery] = useState("");
  const [compose, setCompose] = useState(null);
  const [attachOpen, setAttachOpen] = useState(false);
  const [pos, setPos] = useState({ x: null, y: null });
  const [drag, setDrag] = useState(null);
  const bodyRef = useRef(null);
  const panelRef = useRef(null);

  const open = messages.find((m) => m.id === openId);
  const picked = doc.picked || [];
  const pick = (field) => { if (!(doc.picked || []).includes(field)) setDoc({ ...doc, picked: [...(doc.picked || []), field] }); };

  let list = messages.filter((m) => m.folder === folder);
  if (folder === "inbox" && query) {
    const q = query.toLowerCase();
    list = list.filter((m) => (m.subject + m.fromName + m.body).toLowerCase().includes(q));
  }

  const openMsg = (m) => {
    setOpenId(m.id);
    if (!m.read) setDoc({ ...doc, messages: messages.map((x) => (x.id === m.id ? { ...x, read: true } : x)) });
  };
  const doSearch = (v) => { setQuery(v); if (v) setDoc({ ...doc, searched: true }); };

  // Drag the floating compose panel by its title bar.
  useEffect(() => {
    if (!drag) return;
    const move = (e) => {
      const p = e.touches ? e.touches[0] : e;
      const w = panelRef.current?.offsetWidth || 480;
      const x = Math.max(4, Math.min(window.innerWidth - w - 4, p.clientX - drag.dx));
      const y = Math.max(4, Math.min(window.innerHeight - 56, p.clientY - drag.dy));
      setPos({ x, y });
    };
    const up = () => setDrag(null);
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    window.addEventListener("touchmove", move, { passive: true });
    window.addEventListener("touchend", up);
    return () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      window.removeEventListener("touchmove", move);
      window.removeEventListener("touchend", up);
    };
  }, [drag]);

  const startDrag = (e) => {
    if (!panelRef.current) return;
    const p = e.touches ? e.touches[0] : e;
    const rect = panelRef.current.getBoundingClientRect();
    if (pos.x == null) setPos({ x: rect.left, y: rect.top });
    setDrag({ dx: p.clientX - rect.left, dy: p.clientY - rect.top });
  };

  const startCompose = (mode) => {
    const s = open;
    setAttachOpen(false);
    setPos({ x: null, y: null });
    if (mode === "new") setCompose({ mode: "new", kind: "new", to: "", cc: "", bcc: "", subject: "", body: "", attachments: [], showCc: false });
    else if (mode === "reply") setCompose({ mode, kind: "reply", to: s.fromEmail, cc: "", bcc: "", subject: s.subject.startsWith("Re:") ? s.subject : `Re: ${s.subject}`, body: `\n\n---\n${s.fromName} wrote:\n${s.body}`, attachments: [], showCc: false });
    else if (mode === "replyall") setCompose({ mode, kind: "replyall", to: s.fromEmail, cc: (s.cc || []).join(", "), bcc: "", subject: s.subject.startsWith("Re:") ? s.subject : `Re: ${s.subject}`, body: `\n\n---\n${s.fromName} wrote:\n${s.body}`, attachments: [], showCc: true });
    else if (mode === "forward") setCompose({ mode, kind: "forward", to: "", cc: "", bcc: "", subject: s.subject.startsWith("Fwd:") ? s.subject : `Fwd: ${s.subject}`, body: `\n\n---\nForwarded message from ${s.fromName}:\n${s.body}`, attachments: [], showCc: false });
  };

  const setC = (patch) => setCompose((c) => ({ ...c, ...patch }));
  const insertAtCursor = (text, wrap) => {
    const el = bodyRef.current; const b = compose.body;
    if (!el) { setC({ body: b + text }); return; }
    const s = el.selectionStart, e = el.selectionEnd;
    const nb = wrap ? b.slice(0, s) + wrap[0] + (b.slice(s, e) || "text") + wrap[1] + b.slice(e) : b.slice(0, s) + text + b.slice(e);
    setC({ body: nb });
  };

  const send = () => {
    const c = compose;
    const body = c.body || "";
    const msg = {
      id: `sent_${Date.now()}`, folder: "sent", kind: c.kind, fromName: "You", fromEmail: config.studentEmail,
      to: splitAddrs(c.to), cc: splitAddrs(c.cc), bcc: splitAddrs(c.bcc), subject: c.subject, body,
      bodyStudent: studentPortion(body),
      attachments: c.attachments, read: true, inReplyTo: open?.id || null, date: "Just now", external: false,
      hasBold: body.includes("**"), hasBullets: /(^|\n)\s*(•|-)\s+/.test(body), hasSignature: body.includes("—"),
    };
    setDoc({ ...doc, messages: [...messages, msg] });
    setCompose(null); setAttachOpen(false); setFolder("sent"); setOpenId(msg.id);
  };

  const Btn = ({ onClick, icon: Icon, label, testid }) => (
    <button data-testid={testid} onClick={onClick} className="inline-flex items-center gap-1.5 px-3 h-9 rounded-md text-sm border border-white/15 text-slate-200 hover:bg-white/5 transition-colors">
      <Icon className="w-4 h-4" /> {label}
    </button>
  );

  const AddrLine = ({ label, arr, field }) => (
    <>
      <span className="text-slate-500 ml-2 first:ml-0">{label}</span>
      {arr.map((a, i) => (
        <button key={`${field}${i}`} data-testid={`email-addr-${field}-${i}`} onClick={() => pick(field)} title="Click to identify this address"
          className={`underline decoration-dotted underline-offset-2 transition-colors ${picked.includes(field) ? "text-[#34D399]" : "text-slate-400 hover:text-[#a5b4fc]"}`}>{a}</button>
      ))}
    </>
  );

  return (
    <div className="rounded-2xl overflow-hidden border border-white/10 bg-[#0a1628] relative">
      {/* top bar */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/10 bg-white/[0.03]">
        <PenSquare className="w-4 h-4 text-[#818CF8]" />
        <button data-testid="email-compose-btn" onClick={() => startCompose("new")} className="text-sm bg-[#818CF8] text-white px-3 h-8 rounded-md hover:bg-[#6366F1]">Compose</button>
        <div className="flex-1 flex items-center gap-2 ml-2 bg-white/5 rounded-md px-2 h-8 max-w-xs">
          <Search className="w-4 h-4 text-slate-400" />
          <input data-testid="email-search" value={query} onChange={(e) => doSearch(e.target.value)} placeholder="Search inbox…" className="bg-transparent text-sm text-white placeholder:text-slate-500 outline-none w-full" />
        </div>
      </div>

      <div className="flex" style={{ minHeight: 440 }}>
        {/* folders */}
        <div className="w-28 sm:w-32 shrink-0 border-r border-white/10 py-2">
          {FOLDERS.map((f) => {
            const n = messages.filter((m) => m.folder === f.id).length;
            return (
              <button key={f.id} data-testid={`email-folder-${f.id}`} onClick={() => { setFolder(f.id); setOpenId(null); }}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm ${folder === f.id ? "bg-[#818CF8]/15 text-[#a5b4fc] border-r-2 border-[#818CF8]" : "text-slate-300 hover:bg-white/5"}`}>
                <f.icon className="w-4 h-4" /> {f.name}{n ? <span className="ml-auto text-xs opacity-60">{n}</span> : null}
              </button>
            );
          })}
        </div>

        {/* message area (Gmail-style rows + reading overlay) */}
        <div className="relative flex-1 min-w-0">
          <div className="overflow-y-auto hq-scrollbar divide-y divide-white/[0.06]" style={{ maxHeight: 470 }}>
            {list.length === 0 && <p className="text-xs text-slate-500 p-4">No emails here.</p>}
            {list.map((m) => {
              const unread = !m.read && m.folder === "inbox";
              return (
                <button key={m.id} data-testid={`email-item-${m.id}`} onClick={() => openMsg(m)}
                  className={`w-full text-left pl-2 pr-3 py-2.5 flex items-center gap-2 ${openId === m.id ? "bg-white/[0.06]" : unread ? "bg-white/[0.02] hover:bg-white/[0.05]" : "hover:bg-white/[0.03]"}`}>
                  <Square className="w-4 h-4 text-slate-600 shrink-0 hidden sm:block" />
                  <Star className={`w-4 h-4 shrink-0 hidden sm:block ${unread ? "text-slate-500" : "text-slate-700"}`} />
                  <span className={`w-24 sm:w-36 shrink-0 truncate text-sm ${unread ? "text-white font-semibold" : "text-slate-300"}`}>
                    {m.folder === "sent" ? `To: ${(m.to || []).join(", ")}` : m.fromName}
                  </span>
                  <span className="flex-1 min-w-0 truncate text-sm">
                    {m.external && <span className="text-[10px] font-bold text-amber-400/90 mr-1 align-middle">[EXTERNAL]</span>}
                    <span className={unread ? "text-white font-semibold" : "text-slate-300"}>{m.subject}</span>
                    <span className="text-slate-500"> — {snippetOf(m)}</span>
                  </span>
                  <span className={`shrink-0 text-xs ml-1 ${unread ? "text-white font-semibold" : "text-slate-500"}`}>{m.date || ""}</span>
                </button>
              );
            })}
          </div>

          {/* reading overlay */}
          {open && (
            <div data-testid="email-reading-pane" className="absolute inset-0 bg-[#0a1628] overflow-y-auto hq-scrollbar p-4" style={{ maxHeight: 470 }}>
              <button data-testid="email-reading-back" onClick={() => setOpenId(null)} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white mb-3">
                <ArrowLeft className="w-4 h-4" /> Back to {FOLDERS.find((f) => f.id === folder)?.name}
              </button>
              <h3 className="font-display text-xl text-white">{open.subject}</h3>
              <p className="text-sm text-slate-300 mt-1"><b>{open.fromName}</b> <span className="text-slate-500">&lt;{open.fromEmail}&gt;</span></p>
              <div className="text-xs mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-1">
                <AddrLine label="To:" arr={open.to || []} field="to" />
                {open.cc?.length ? <AddrLine label="Cc:" arr={open.cc} field="cc" /> : null}
                {open.bcc?.length ? <AddrLine label="Bcc:" arr={open.bcc} field="bcc" /> : null}
              </div>
              {open.bcc?.length ? <p className="text-[11px] text-slate-500 mt-1 italic">Bcc is a hidden copy — normally only the sender can see it.</p> : null}
              {open.attachments?.length ? <div className="mt-2 flex flex-wrap gap-2">{open.attachments.map((a, i) => <span key={i} className="inline-flex items-center gap-1 text-xs bg-white/5 rounded px-2 py-1 text-slate-300"><Paperclip className="w-3 h-3" />{a.name}</span>)}</div> : null}
              <div className="mt-3 text-slate-200 text-sm whitespace-pre-wrap leading-relaxed">{open.body}</div>
              {open.folder === "inbox" && (
                <div className="flex flex-wrap gap-2 mt-5">
                  <Btn testid="email-reply-btn" onClick={() => startCompose("reply")} icon={Reply} label="Reply" />
                  <Btn testid="email-replyall-btn" onClick={() => startCompose("replyall")} icon={ReplyAll} label="Reply All" />
                  <Btn testid="email-forward-btn" onClick={() => startCompose("forward")} icon={Forward} label="Forward" />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* draggable floating compose panel (portaled so it floats over the page, instructions stay visible) */}
      {compose && createPortal(
        <div ref={panelRef} data-testid="email-compose-panel"
          className="fixed z-[60] w-[calc(100vw-16px)] max-w-lg bg-[#0d1b30] border border-[#818CF8]/40 rounded-xl shadow-2xl"
          style={pos.x == null ? { right: 16, bottom: 16 } : { left: pos.x, top: pos.y }}>
          <div data-testid="email-compose-header" onMouseDown={startDrag} onTouchStart={startDrag}
            className="flex items-center justify-between px-4 py-2.5 border-b border-white/10 cursor-move select-none bg-white/[0.04] rounded-t-xl">
            <span className="flex items-center gap-1.5 text-sm font-medium text-white capitalize"><GripVertical className="w-4 h-4 text-slate-500" />{compose.mode === "new" ? "New message" : compose.mode} <span className="text-[10px] font-normal text-slate-500 ml-1 normal-case">· drag to move</span></span>
            <button data-testid="email-compose-close" onClick={() => setCompose(null)} className="text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
          </div>
          <div className="p-4 space-y-2">
            <input data-testid="email-to" value={compose.to} onChange={(e) => setC({ to: e.target.value })} placeholder="To" className="w-full h-9 rounded-md bg-slate-800 border border-slate-600 px-2 text-sm text-white placeholder:text-slate-400 outline-none focus:border-[#818CF8]" />
            {!compose.showCc && <button data-testid="email-showcc" onClick={() => setC({ showCc: true })} className="text-xs text-[#a5b4fc]">+ Cc / Bcc</button>}
            {compose.showCc && (
              <>
                <input data-testid="email-cc" value={compose.cc} onChange={(e) => setC({ cc: e.target.value })} placeholder="Cc" className="w-full h-9 rounded-md bg-slate-800 border border-slate-600 px-2 text-sm text-white placeholder:text-slate-400 outline-none focus:border-[#818CF8]" />
                <input data-testid="email-bcc" value={compose.bcc} onChange={(e) => setC({ bcc: e.target.value })} placeholder="Bcc" className="w-full h-9 rounded-md bg-slate-800 border border-slate-600 px-2 text-sm text-white placeholder:text-slate-400 outline-none focus:border-[#818CF8]" />
              </>
            )}
            <input data-testid="email-subject" value={compose.subject} onChange={(e) => setC({ subject: e.target.value })} placeholder="Subject" className="w-full h-9 rounded-md bg-slate-800 border border-slate-600 px-2 text-sm text-white placeholder:text-slate-400 outline-none focus:border-[#818CF8]" />
            <div className="flex items-center gap-1 border border-slate-600 rounded-md px-1 bg-slate-800/60 w-max">
              <button data-testid="email-fmt-bold" title="Bold" onClick={() => insertAtCursor(null, ["**", "**"])} className="w-8 h-8 flex items-center justify-center text-slate-200 hover:bg-white/10 rounded"><Bold className="w-4 h-4" /></button>
              <button data-testid="email-fmt-bullets" title="Bullet list" onClick={() => insertAtCursor("\n• ")} className="w-8 h-8 flex items-center justify-center text-slate-200 hover:bg-white/10 rounded"><List className="w-4 h-4" /></button>
              <button data-testid="email-fmt-signature" title="Insert signature" onClick={() => setC({ body: compose.body + config.signature })} className="px-2 h-8 text-xs text-slate-200 hover:bg-white/10 rounded">Signature</button>
            </div>
            <textarea ref={bodyRef} data-testid="email-body" value={compose.body} onChange={(e) => setC({ body: e.target.value })} rows={7} placeholder="Write your message…" className="w-full rounded-md bg-slate-800 border border-slate-600 px-2 py-2 text-sm text-white placeholder:text-slate-400 outline-none resize-none focus:border-[#818CF8]" />
            {compose.attachments.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {compose.attachments.map((a, i) => <span key={i} className="inline-flex items-center gap-1 text-xs bg-[#818CF8]/15 text-[#a5b4fc] rounded px-2 py-1">{a.name}<button data-testid={`email-att-remove-${i}`} onClick={() => setC({ attachments: compose.attachments.filter((_, x) => x !== i) })}><X className="w-3 h-3" /></button></span>)}
              </div>
            )}
            <div className="flex items-center gap-2 flex-wrap">
              <div className="relative">
                <button data-testid="email-attach-btn" onClick={() => setAttachOpen((o) => !o)} className="inline-flex items-center gap-1.5 px-3 h-9 rounded-md border border-white/15 text-sm text-slate-200 hover:bg-white/5"><Paperclip className="w-4 h-4" /> Attach</button>
                {attachOpen && (
                  <div className="absolute z-[70] bottom-11 left-0 block bg-[#0d1b30] border border-white/15 rounded-lg p-1 w-52 shadow-xl">
                    {config.fileLibrary.map((f) => (
                      <button key={f} data-testid={`email-file-${f}`} onClick={() => { if (!compose.attachments.some((a) => a.name === f)) setC({ attachments: [...compose.attachments, { name: f }] }); setAttachOpen(false); }} className="w-full text-left px-2 py-1.5 text-sm text-slate-200 hover:bg-white/10 rounded truncate">{f}</button>
                    ))}
                  </div>
                )}
              </div>
              <button data-testid="email-send-btn" onClick={send} className="inline-flex items-center gap-1.5 px-4 h-9 rounded-md bg-[#818CF8] text-white text-sm font-medium hover:bg-[#6366F1] ml-auto"><Send className="w-4 h-4" /> Send</button>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
