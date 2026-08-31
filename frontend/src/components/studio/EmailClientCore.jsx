import { useRef, useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { toast } from "sonner";
import { Inbox, Send, FileText, Trash2, Search, Reply, ReplyAll, Forward, Paperclip, Bold, List, PenSquare, X, Star, GripVertical, ArrowLeft, Save, SpellCheck, Loader2 } from "lucide-react";
import { SquigglyText } from "./Squiggly";

// ---- Rich compose editor: real bold + bullets, serialized back to the plain-text
// markdown the grader expects (**bold**, "• " bullets, "—" signature). ----
const escapeHtml = (s) => (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function serializeNode(node) {
  let out = "";
  node.childNodes.forEach((n) => {
    if (n.nodeType === 3) { out += n.textContent; return; }
    if (n.nodeType !== 1) return;
    const tag = n.tagName.toLowerCase();
    if (tag === "br") { out += "\n"; return; }
    if (tag === "b" || tag === "strong") { const inner = serializeNode(n); out += inner.trim() ? `**${inner}**` : inner; return; }
    if (tag === "span") {
      const fw = n.style.fontWeight; const bold = fw === "bold" || parseInt(fw, 10) >= 600;
      const inner = serializeNode(n); out += bold && inner.trim() ? `**${inner}**` : inner; return;
    }
    if (tag === "li") { if (out && !out.endsWith("\n")) out += "\n"; out += `• ${serializeNode(n).trim()}\n`; return; }
    if (tag === "ul" || tag === "ol") { out += serializeNode(n); return; }
    if (tag === "div" || tag === "p") {
      if (out && !out.endsWith("\n")) out += "\n";
      const inner = serializeNode(n); out += inner; if (!inner.endsWith("\n")) out += "\n"; return;
    }
    out += serializeNode(n);
  });
  return out;
}

function htmlToText(html) {
  const d = document.createElement("div");
  d.innerHTML = html || "";
  return serializeNode(d).replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/\n+$/g, "");
}

function textToHtml(text) {
  if (!text) return "";
  const lines = text.split("\n");
  const html = [];
  let i = 0;
  const inline = (l) => escapeHtml(l).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  while (i < lines.length) {
    if (/^\s*(•|-)\s+/.test(lines[i])) {
      html.push("<ul>");
      while (i < lines.length && /^\s*(•|-)\s+/.test(lines[i])) {
        html.push(`<li>${inline(lines[i].replace(/^\s*(•|-)\s+/, ""))}</li>`);
        i += 1;
      }
      html.push("</ul>");
    } else {
      html.push(`<div>${inline(lines[i]) || "<br>"}</div>`);
      i += 1;
    }
  }
  return html.join("");
}

function RichBody({ initialHtml, onChange, config, proofread, onCheck, checking }) {
  const ref = useRef(null);
  const [active, setActive] = useState({ bold: false, bullet: false });
  const syncActive = () => {
    if (!ref.current || document.activeElement !== ref.current) return;
    try { setActive({ bold: document.queryCommandState("bold"), bullet: document.queryCommandState("insertUnorderedList") }); } catch (e) { /* noop */ }
  };
  useEffect(() => {
    try { document.execCommand("styleWithCSS", false, false); } catch (e) { /* noop */ }
    if (ref.current) ref.current.innerHTML = initialHtml || "";
    document.addEventListener("selectionchange", syncActive);
    return () => document.removeEventListener("selectionchange", syncActive);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const emit = () => { if (ref.current) onChange(ref.current.innerHTML); };
  const exec = (cmd) => (e) => { e.preventDefault(); ref.current?.focus(); try { document.execCommand(cmd); } catch (x) { /* noop */ } emit(); syncActive(); };
  const insertSig = (e) => {
    e.preventDefault(); ref.current?.focus();
    try { document.execCommand("insertHTML", false, "<br>" + escapeHtml(config.signature || "").replace(/\n/g, "<br>")); } catch (x) { /* noop */ }
    emit();
  };
  const btn = (on) => `w-8 h-8 flex items-center justify-center rounded ${on ? "bg-[#818CF8] text-[#04121f]" : "text-slate-200 hover:bg-white/10"}`;
  return (
    <>
      <div className="flex items-center gap-1 border border-slate-600 rounded-md px-1 bg-slate-800/60 w-max">
        <button type="button" data-testid="email-fmt-bold" aria-pressed={active.bold} title="Bold (select text, then click)" onMouseDown={exec("bold")} className={btn(active.bold)}><Bold className="w-4 h-4" /></button>
        <button type="button" data-testid="email-fmt-bullets" aria-pressed={active.bullet} title="Bullet list (press Enter for the next bullet)" onMouseDown={exec("insertUnorderedList")} className={btn(active.bullet)}><List className="w-4 h-4" /></button>
        <button type="button" data-testid="email-fmt-signature" title="Insert signature" onMouseDown={insertSig} className="px-2 h-8 text-xs text-slate-200 hover:bg-white/10 rounded">Signature</button>
        {proofread && (
          <button type="button" data-testid="email-check-writing-btn" title="Check my writing" onMouseDown={(e) => { e.preventDefault(); onCheck(htmlToText(ref.current?.innerHTML || "")); }} disabled={checking} className="ml-1 inline-flex items-center gap-1.5 px-2 h-8 text-xs text-[#a5b4fc] hover:bg-[#818CF8]/15 rounded disabled:opacity-50">
            {checking ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <SpellCheck className="w-3.5 h-3.5" />} Check my writing
          </button>
        )}
      </div>
      <div
        ref={ref}
        data-testid="email-body"
        contentEditable
        suppressContentEditableWarning
        onInput={emit}
        onKeyUp={syncActive}
        onMouseUp={syncActive}
        className="hq-richbody min-h-[168px] rounded-md bg-slate-800 border border-slate-600 px-3 py-2 text-sm text-white outline-none focus:border-[#818CF8] overflow-y-auto"
        style={{ maxHeight: "260px" }}
      />
    </>
  );
}

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
const snippetOf = (m) => (m.body || "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/(^|\n)\s*(•|-)\s+/g, "$1").replace(/\s*\n+\s*/g, " ").trim().slice(0, 80);

export default function EmailClientCore({ doc, setDoc, config, proofread, readingIssues = [] }) {
  const messages = doc.messages || [];
  const [folder, setFolder] = useState("inbox");
  const [openId, setOpenId] = useState(null);
  const [query, setQuery] = useState("");
  const [compose, setCompose] = useState(null);
  const [attachOpen, setAttachOpen] = useState(false);
  const [pos, setPos] = useState({ x: null, y: null });
  const [drag, setDrag] = useState(null);
  const [bodyIssues, setBodyIssues] = useState([]);
  const [checking, setChecking] = useState(false);
  const panelRef = useRef(null);

  const checkWriting = async (rawText) => {
    if (!proofread) return;
    const text = studentPortion(rawText != null ? rawText : (compose.body || ""));
    if (text.split(/\s+/).filter(Boolean).length < 3) {
      toast.info("Write a few sentences first, then I can check your writing.");
      return;
    }
    setChecking(true);
    try {
      const issues = await proofread(text);
      setBodyIssues(issues);
      if (!issues.length) toast.success("Nice writing — no spelling or grammar issues found! ⚓");
      else toast.warning(`Found ${issues.length} thing${issues.length > 1 ? "s" : ""} to fix — see the tips below.`);
    } catch (e) {
      toast.error("The Writing Coach was unavailable. Try again in a moment.");
    } finally {
      setChecking(false);
    }
  };

  const open = messages.find((m) => m.id === openId);
  const picked = doc.picked || [];
  const pick = (field) => { if (!(doc.picked || []).includes(field)) setDoc({ ...doc, picked: [...(doc.picked || []), field] }); };

  let list = messages.filter((m) => m.folder === folder);
  if (folder === "inbox" && query) {
    const q = query.toLowerCase();
    list = list.filter((m) => (m.subject + m.fromName + m.body).toLowerCase().includes(q));
  }

  const openMsg = (m) => {
    if (m.folder === "drafts") { editDraft(m); return; }
    setOpenId(m.id);
    if (!m.read) setDoc({ ...doc, messages: messages.map((x) => (x.id === m.id ? { ...x, read: true } : x)) });
  };
  const editDraft = (m) => {
    setAttachOpen(false); setPos({ x: null, y: null }); setOpenId(null); setBodyIssues([]);
    setCompose({
      mode: m.kind === "new" ? "new" : m.kind, kind: m.kind || "new", draftId: m.id, _id: Date.now(),
      to: (m.to || []).join(", "), cc: (m.cc || []).join(", "), bcc: (m.bcc || []).join(", "),
      subject: m.subject || "", body: m.body || "", attachments: m.attachments || [],
      showCc: !!((m.cc || []).length || (m.bcc || []).length),
    });
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
    setBodyIssues([]);
    if (mode === "new") setCompose({ mode: "new", kind: "new", _id: Date.now(), to: "", cc: "", bcc: "", subject: "", body: "", attachments: [], showCc: false });
    else if (mode === "reply") setCompose({ mode, kind: "reply", _id: Date.now(), to: s.fromEmail, cc: "", bcc: "", subject: s.subject.startsWith("Re:") ? s.subject : `Re: ${s.subject}`, body: `\n\n---\n${s.fromName} wrote:\n${s.body}`, attachments: [], showCc: false });
    else if (mode === "replyall") setCompose({ mode, kind: "replyall", _id: Date.now(), to: s.fromEmail, cc: (s.cc || []).join(", "), bcc: "", subject: s.subject.startsWith("Re:") ? s.subject : `Re: ${s.subject}`, body: `\n\n---\n${s.fromName} wrote:\n${s.body}`, attachments: [], showCc: true });
    else if (mode === "forward") setCompose({ mode, kind: "forward", _id: Date.now(), to: "", cc: "", bcc: "", subject: s.subject.startsWith("Fwd:") ? s.subject : `Fwd: ${s.subject}`, body: `\n\n---\nForwarded message from ${s.fromName}:\n${s.body}`, attachments: [], showCc: false });
  };

  const setC = (patch) => setCompose((c) => ({ ...c, ...patch }));

  const onBodyChange = (html) => setCompose((c) => ({ ...c, bodyHtml: html, body: htmlToText(html) }));

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
    // Sending a draft removes it from the Drafts folder.
    setDoc({ ...doc, messages: [...messages.filter((m) => m.id !== c.draftId), msg] });
    setCompose(null); setAttachOpen(false); setFolder("sent"); setOpenId(msg.id);
  };

  const saveDraft = () => {
    const c = compose;
    const id = c.draftId || `draft_${Date.now()}`;
    const draft = {
      id, folder: "drafts", kind: c.kind, fromName: "You", fromEmail: config.studentEmail,
      to: splitAddrs(c.to), cc: splitAddrs(c.cc), bcc: splitAddrs(c.bcc), subject: c.subject, body: c.body,
      bodyStudent: studentPortion(c.body || ""), attachments: c.attachments, read: true, date: "Draft", external: false,
    };
    setDoc({ ...doc, messages: [...messages.filter((m) => m.id !== id), draft] });
    setCompose(null); setAttachOpen(false); setFolder("drafts");
    toast.success("Saved to Drafts ⛵ — finish it anytime.");
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
            const unreadN = f.id === "inbox" ? messages.filter((m) => m.folder === "inbox" && !m.read).length : 0;
            return (
              <button key={f.id} data-testid={`email-folder-${f.id}`} onClick={() => { setFolder(f.id); setOpenId(null); }}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm ${folder === f.id ? "bg-[#818CF8]/15 text-[#a5b4fc] border-r-2 border-[#818CF8]" : "text-slate-300 hover:bg-white/5"}`}>
                <f.icon className="w-4 h-4" /> {f.name}{unreadN ? <span data-testid="email-inbox-unread" className="ml-auto text-xs font-semibold text-[#22D3EE]">{unreadN}</span> : null}
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
                  className={`w-full text-left pl-2 pr-3 py-2.5 flex items-center gap-2 transition-colors duration-200 ${openId === m.id ? "bg-white/[0.06]" : unread ? "bg-white/[0.02] hover:bg-white/[0.05]" : "opacity-60 hover:bg-white/[0.03] hover:opacity-90"}`}>
                  <span className={`w-2 h-2 rounded-full shrink-0 ${unread ? "bg-[#22D3EE]" : "bg-transparent"}`} data-testid={unread ? `email-unread-dot-${m.id}` : undefined} />
                  <Star className={`w-4 h-4 shrink-0 hidden sm:block ${unread ? "text-slate-500" : "text-slate-700"}`} />
                  <span className={`w-24 sm:w-36 shrink-0 truncate text-sm ${unread ? "text-white font-semibold" : "text-slate-400"}`}>
                    {m.folder === "sent" ? `To: ${(m.to || []).join(", ")}` : m.fromName}
                  </span>
                  <span className="flex-1 min-w-0 truncate text-sm">
                    {m.external && <span className="text-[10px] font-bold text-amber-400/90 mr-1 align-middle">[EXTERNAL]</span>}
                    <span className={unread ? "text-white font-semibold" : "text-slate-400"}>{m.subject}</span>
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
              <div className="mt-3 text-slate-200 text-sm leading-relaxed hq-richbody">
                {open.folder === "sent" && readingIssues.length > 0
                  ? <span className="whitespace-pre-wrap"><SquigglyText value={open.body} issues={readingIssues} /></span>
                  : <span dangerouslySetInnerHTML={{ __html: textToHtml(open.body) }} />}
              </div>
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
            <button data-testid="email-compose-close" onClick={() => { setCompose(null); setBodyIssues([]); }} className="text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
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
            <RichBody
              key={compose._id}
              initialHtml={compose.bodyHtml != null ? compose.bodyHtml : textToHtml(compose.body || "")}
              onChange={onBodyChange}
              config={config}
              proofread={proofread}
              onCheck={checkWriting}
              checking={checking}
            />
            {bodyIssues.length > 0 && (
              <div data-testid="email-writing-tips" className="rounded-md border border-[#818CF8]/30 bg-[#818CF8]/10 p-2.5 space-y-1.5">
                <p className="text-[11px] uppercase tracking-widest text-[#a5b4fc] flex items-center gap-1.5"><SpellCheck className="w-3.5 h-3.5" /> Writing tips ({bodyIssues.length})</p>
                {bodyIssues.slice(0, 6).map((iss, i) => (
                  <p key={i} className="text-xs text-slate-200">
                    <span className="line-through text-[#fb7185]">{iss.text}</span>
                    {iss.suggestion && <> → <span className="text-emerald-300 font-medium">{iss.suggestion}</span></>}
                    <span className="text-slate-400"> — {iss.message}</span>
                  </p>
                ))}
              </div>
            )}
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
              <button data-testid="email-savedraft-btn" onClick={saveDraft} className="inline-flex items-center gap-1.5 px-3 h-9 rounded-md border border-white/15 text-sm text-slate-200 hover:bg-white/5"><Save className="w-4 h-4" /> Save draft</button>
              <button data-testid="email-send-btn" onClick={send} className="inline-flex items-center gap-1.5 px-4 h-9 rounded-md bg-[#818CF8] text-white text-sm font-medium hover:bg-[#6366F1] ml-auto"><Send className="w-4 h-4" /> Send</button>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
