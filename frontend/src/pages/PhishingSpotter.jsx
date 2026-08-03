import { useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import AppNav from "@/components/AppNav";
import { Button } from "@/components/ui/button";
import { ShieldAlert, ArrowLeft, ArrowRight, CheckCircle2, XCircle, AlertTriangle, Gem, Trophy, Map, RotateCcw, Mail } from "lucide-react";
import { toast } from "sonner";

const QUEST_ID = "t3-q5";

// Each email: parts are the inspectable elements. flag=true means it's a red flag.
const EMAILS = [
  {
    id: "e1",
    label: "Inbox · 1 of 3",
    parts: [
      { id: "from", field: "From", text: "PayPal Service <service@paypa1-alerts.com>", flag: true, reason: "The domain 'paypa1-alerts.com' spells PayPal with the number 1 — a fake look-alike sender." },
      { id: "subject", field: "Subject", text: "URGENT: Verify your account in 24 hours or it will be permanently closed!!!", flag: true, reason: "Urgent threats and pressure with lots of exclamation marks are classic phishing bait." },
      { id: "greeting", field: "Greeting", text: "Dear Valued Customer,", flag: true, reason: "A real company usually greets you by name, not with a generic 'Dear Valued Customer'." },
      { id: "ask", field: "Body", text: "Please reply with your password and PIN so we can confirm it's really you.", flag: true, reason: "Legitimate companies NEVER ask for your password or PIN by email." },
      { id: "link", field: "Link", text: "http://paypal-account-verify.ru/login", flag: true, reason: "The link uses a strange domain (.ru) that is not the real paypal.com." },
      { id: "sign", field: "Signature", text: "— PayPal Support Team", flag: false, reason: "A sign-off like this is normal and not a red flag on its own." },
    ],
  },
  {
    id: "e2",
    label: "Inbox · 2 of 3",
    parts: [
      { id: "from", field: "From", text: "Ms. Rivera <trivera@lincolnmiddle.edu>", flag: false, reason: "This is your teacher's real school (.edu) address — safe." },
      { id: "subject", field: "Subject", text: "Reminder: Science project due Friday", flag: false, reason: "A normal, expected reminder — not suspicious." },
      { id: "greeting", field: "Greeting", text: "Hi class,", flag: false, reason: "A friendly, expected greeting from your teacher — safe." },
      { id: "attachment", field: "Attachment", text: "grades_update.exe", flag: true, reason: "A '.exe' program attachment is dangerous — documents don't need to be programs." },
      { id: "link", field: "Link", text: "http://bit.ly/free-giftcard-now", flag: true, reason: "An out-of-place shortened link promising a free gift card hides its real destination." },
      { id: "sign", field: "Signature", text: "— Ms. Rivera, Science Dept.", flag: false, reason: "Matches the real sender — not a red flag." },
    ],
  },
  {
    id: "e3",
    label: "Inbox · 3 of 3",
    parts: [
      { id: "from", field: "From", text: "Netflix <no-reply@netffix-billing.com>", flag: true, reason: "'netffix-billing.com' misspells Netflix — a fake look-alike domain." },
      { id: "subject", field: "Subject", text: "Your payment could not be processed", flag: false, reason: "This subject alone is plausible — the danger is in the details below." },
      { id: "greeting", field: "Greeting", text: "Dear Customer,", flag: true, reason: "Generic greeting instead of your name is a common phishing sign." },
      { id: "ask", field: "Body", text: "Enter your card number and account password to reactivate service.", flag: true, reason: "Asking for your card number AND password by email is a major red flag." },
      { id: "link", field: "Link", text: "http://netffix-billing.com/update-now", flag: true, reason: "The link points to the fake 'netffix' domain, not netflix.com." },
      { id: "sign", field: "Signature", text: "— The Netflix Team", flag: false, reason: "A normal sign-off — not a red flag by itself." },
    ],
  },
];

const FIELD_META = {
  From: Mail, Subject: Mail, Greeting: Mail, Body: Mail, Link: AlertTriangle, Attachment: AlertTriangle, Signature: Mail,
};

export default function PhishingSpotter() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const questId = params.get("quest") || QUEST_ID;
  const { refresh } = useAuth();

  const [idx, setIdx] = useState(0);
  const [selected, setSelected] = useState({}); // partId -> true
  const [checked, setChecked] = useState(false);
  const [foundTotal, setFoundTotal] = useState(0);
  const [flagTotal, setFlagTotal] = useState(0);
  const [wrongTotal, setWrongTotal] = useState(0);
  const [finished, setFinished] = useState(false);
  const [award, setAward] = useState(null);
  const awardedRef = useRef(false);

  const email = EMAILS[idx];
  const totalFlags = useMemo(() => EMAILS.reduce((n, e) => n + e.parts.filter((p) => p.flag).length, 0), []);

  const toggle = (pid) => {
    if (checked) return;
    setSelected((s) => ({ ...s, [pid]: !s[pid] }));
  };

  const check = () => {
    const flagsHere = email.parts.filter((p) => p.flag);
    const found = flagsHere.filter((p) => selected[p.id]).length;
    const wrong = email.parts.filter((p) => !p.flag && selected[p.id]).length;
    setFoundTotal((n) => n + found);
    setFlagTotal((n) => n + flagsHere.length);
    setWrongTotal((n) => n + wrong);
    setChecked(true);
    if (found === flagsHere.length && wrong === 0) toast.success("Sharp eye! You caught every red flag.");
    else toast.info(`You found ${found} of ${flagsHere.length} red flags in this email.`);
  };

  const next = async () => {
    if (idx < EMAILS.length - 1) {
      setIdx((i) => i + 1);
      setSelected({});
      setChecked(false);
    } else {
      setFinished(true);
      if (awardedRef.current) return;
      awardedRef.current = true;
      try {
        const res = await api.post(`/labs/${questId}/complete`);
        setAward(res.data);
        await refresh();
        if (res.data.bonus > 0) toast.success(`Inbox secured! +${res.data.bonus} Horizon Points`);
        else toast.info("Lab already completed — great practice!");
      } catch (e) {
        toast.error("Could not save your lab result.");
      }
    }
  };

  const restart = () => {
    setIdx(0); setSelected({}); setChecked(false); setFoundTotal(0); setFlagTotal(0); setWrongTotal(0); setFinished(false);
  };

  const accuracy = flagTotal ? Math.round((foundTotal / flagTotal) * 100) : 0;
  const progress = Math.round(((idx + (checked ? 1 : 0)) / EMAILS.length) * 100);

  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <button data-testid="phish-back-btn" onClick={() => navigate(`/quest/${questId}`)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to the quest
        </button>

        <div className="flex items-center gap-3 mb-2">
          <div className="w-11 h-11 rounded-xl bg-[#E11D48]/15 flex items-center justify-center"><ShieldAlert className="w-6 h-6 text-[#fb7185]" /></div>
          <div>
            <h1 data-testid="phishing-title" className="font-display text-3xl sm:text-4xl tracking-tight leading-none">Phishing Spotter</h1>
            <p className="text-sm text-muted-foreground mt-1">The Cyber Frontier · Tap every red flag you can spot</p>
          </div>
        </div>

        <div className="mt-6 mb-6">
          <div className="flex justify-between text-xs font-mono-data text-muted-foreground mb-2">
            <span>{finished ? "Complete" : email.label}</span><span>{finished ? 100 : progress}%</span>
          </div>
          <div className="h-2 rounded-full bg-white/5 overflow-hidden">
            <div className="h-full rounded-full bg-[#fb7185] transition-all duration-500" style={{ width: `${finished ? 100 : progress}%` }} />
          </div>
        </div>

        {!finished ? (
          <AnimatePresence mode="wait">
            <motion.div key={email.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.3 }}>
              <p className="text-sm text-muted-foreground mb-4">Read the email below. Tap anything that looks like a <b className="text-[#fb7185]">red flag</b>, then check your answers.</p>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden">
                {email.parts.map((p) => {
                  const isSel = !!selected[p.id];
                  const Icon = FIELD_META[p.field] || Mail;
                  let stateCls = "border-white/10";
                  if (checked) {
                    if (p.flag && isSel) stateCls = "border-emerald-400/60 bg-emerald-400/10";
                    else if (p.flag && !isSel) stateCls = "border-[#fb7185]/60 bg-[#fb7185]/10";
                    else if (!p.flag && isSel) stateCls = "border-amber-400/60 bg-amber-400/10";
                    else stateCls = "border-white/5 opacity-70";
                  } else if (isSel) stateCls = "border-[#fb7185]/60 bg-[#fb7185]/10";
                  return (
                    <div key={p.id} className="px-4 py-3 border-b border-white/5 last:border-b-0">
                      <button
                        data-testid={`phish-part-${email.id}-${p.id}`}
                        onClick={() => toggle(p.id)}
                        disabled={checked}
                        className={`w-full text-left rounded-xl border p-3 transition-colors duration-200 ${stateCls} ${!checked ? "hover:bg-white/5" : ""}`}
                      >
                        <div className="flex items-start gap-3">
                          <Icon className="w-4 h-4 mt-1 text-muted-foreground shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-[11px] uppercase tracking-widest text-muted-foreground">{p.field}</p>
                            <p className="text-slate-200 break-words">{p.text}</p>
                          </div>
                          {checked ? (
                            p.flag ? (isSel ? <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" /> : <XCircle className="w-5 h-5 text-[#fb7185] shrink-0" />)
                              : (isSel ? <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" /> : <span className="w-5 h-5 shrink-0" />)
                          ) : (
                            <span className={`w-5 h-5 rounded-full border shrink-0 ${isSel ? "bg-[#fb7185] border-[#fb7185]" : "border-white/25"}`} />
                          )}
                        </div>
                        {checked && (p.flag || isSel) && (
                          <p className={`mt-2 text-sm ${p.flag ? "text-slate-300" : "text-amber-300"}`}>{p.reason}</p>
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>

              {!checked ? (
                <Button data-testid="phish-check-btn" onClick={check} className="mt-6 w-full py-6 bg-[#fb7185] text-[#04121f] hover:bg-[#fda4af]">
                  Check my answers
                </Button>
              ) : (
                <Button data-testid="phish-next-btn" onClick={next} className="mt-6 w-full py-6 bg-primary text-primary-foreground hover:bg-[#FDBA74]">
                  {idx < EMAILS.length - 1 ? <>Next email <ArrowRight className="w-4 h-4 ml-2" /></> : <>Finish & secure the inbox <ShieldAlert className="w-4 h-4 ml-2" /></>}
                </Button>
              )}
            </motion.div>
          </AnimatePresence>
        ) : (
          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="hq-glass rounded-2xl p-8 text-center border-t border-t-[#fb7185]/40">
            <div className="mx-auto w-20 h-20 rounded-full bg-[#fb7185]/15 flex items-center justify-center mb-5"><ShieldAlert className="w-9 h-9 text-[#fb7185]" /></div>
            <h2 className="font-display text-3xl mb-2">Inbox Secured!</h2>
            <p className="text-slate-300">You inspected {EMAILS.length} emails for phishing red flags.</p>
            <div className="flex justify-center gap-8 mt-6">
              <div><p className="font-mono-data text-3xl text-[#fb7185]">{foundTotal}/{totalFlags}</p><p className="text-xs text-muted-foreground mt-1">Red flags caught</p></div>
              <div><p className="font-mono-data text-3xl text-slate-200">{accuracy}%</p><p className="text-xs text-muted-foreground mt-1">Accuracy</p></div>
              {award && <div><p className="font-mono-data text-3xl text-primary flex items-center gap-1 justify-center"><Gem className="w-6 h-6" />+{award.bonus}</p><p className="text-xs text-muted-foreground mt-1">Bonus Points</p></div>}
            </div>
            <div className="mt-8 space-y-3">
              <div className="flex gap-3">
                <Button data-testid="phish-restart-btn" variant="outline" className="flex-1 border-white/15" onClick={restart}><RotateCcw className="w-4 h-4 mr-2" /> Try again</Button>
                <Button data-testid="phish-quest-btn" variant="outline" className="flex-1 border-white/15" onClick={() => navigate(`/quest/${questId}`)}><ArrowLeft className="w-4 h-4 mr-2" /> Back to quest</Button>
              </div>
              <div className="flex gap-3">
                <Button data-testid="phish-map-btn" variant="outline" className="flex-1 border-white/15" onClick={() => navigate("/map")}><Map className="w-4 h-4 mr-2" /> Map</Button>
                <Button data-testid="phish-rankings-btn" className="flex-1 bg-primary text-primary-foreground hover:bg-[#FDBA74]" onClick={() => navigate("/leaderboard")}><Trophy className="w-4 h-4 mr-2" /> Rankings</Button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
