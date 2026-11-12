import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  FileText,
  Image as ImageIcon,
  LogOut,
  Mic,
  Plus,
  Square,
  X,
} from "lucide-react";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080/api";
const SESSION_KEY = "ai-interface-session";
const SESSION_LENGTH = 7 * 24 * 60 * 60 * 1000;

type Role = "engineer" | "customer";
type Citation = { title?: string; url?: string; snippet?: string };
type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  files?: string[];
  citations?: Citation[];
};
type Conversation = { id: string; title: string; updatedAt?: string };
type Session = { token: string; expiresAt: number };

async function api<T>(
  path: string,
  token?: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return response.json() as Promise<T>;
}

function readSession(): Session | null {
  try {
    const session = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    if (session?.token && session.expiresAt > Date.now()) return session;
  } catch {
    // Invalid saved session; start signed out.
  }
  localStorage.removeItem(SESSION_KEY);
  return null;
}

export default function App() {
  const [session, setSession] = useState<Session | null>(readSession);
  const [role, setRole] = useState<Role | null>(null);
  const [username, setUsername] = useState("testuser");
  const [password, setPassword] = useState("password");
  const [loginError, setLoginError] = useState("");
  const [busy, setBusy] = useState(false);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState("");
  const [recording, setRecording] = useState(false);

  const fileInput = useRef<HTMLInputElement>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const logout = useCallback(() => {
    localStorage.removeItem(SESSION_KEY);
    setSession(null);
    setRole(null);
    setConversations([]);
    setMessages([]);
    setConversationId("");
  }, []);

  useEffect(() => {
    if (!session) return;
    const remaining = session.expiresAt - Date.now();
    if (remaining <= 0) logout();
    else {
      const timer = window.setTimeout(logout, remaining);
      return () => window.clearTimeout(timer);
    }
  }, [session, logout]);

  useEffect(() => {
    if (!session || !role) return;
    api<Conversation[]>("/conversations", session.token)
      .then(setConversations)
      .catch((e) => setError(e.message));
  }, [session, role]);

  async function signIn(event: React.FormEvent) {
    event.preventDefault();
    setLoginError("");
    setBusy(true);
    try {
      // The demo credentials are prefilled; the backend remains responsible for issuing the JWT.
      const result = await api<{ token: string }>("/login", undefined, {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      const nextSession = {
        token: result.token,
        expiresAt: Date.now() + SESSION_LENGTH,
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
      setSession(nextSession);
    } catch (e) {
      setLoginError(e instanceof Error ? e.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  async function openConversation(id: string) {
    if (!session) return;
    setError("");
    setConversationId(id);
    try {
      const result = await api<{ messages: Message[] }>(
        `/conversations/${encodeURIComponent(id)}`,
        session.token,
      );
      setMessages(result.messages ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load conversation.");
    }
  }

  function newConversation() {
    setConversationId("");
    setMessages([]);
    setError("");
  }

  function addFiles(selected: FileList | null) {
    if (!selected) return;
    setFiles((current) => [...current, ...Array.from(selected)]);
  }

  async function toggleRecording() {
    if (recording) {
      recorder.current?.stop();
      setRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      recorder.current = mediaRecorder;
      audioChunks.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size) audioChunks.current.push(event.data);
      };
      mediaRecorder.onstop = () => {
        const audio = new File(
          [new Blob(audioChunks.current, { type: mediaRecorder.mimeType })],
          `recording-${Date.now()}.webm`,
          { type: mediaRecorder.mimeType },
        );
        setFiles((current) => [...current, audio]);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setRecording(true);
    } catch {
      setError("Microphone access was unavailable. Check browser permissions.");
    }
  }

  async function sendMessage(event?: React.FormEvent) {
    event?.preventDefault();
    if (!session || !role || busy || (!prompt.trim() && files.length === 0)) return;

    const text = prompt.trim();
    const attachedNames = files.map((file) => file.name);
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text || "Please review the attached file(s).",
      files: attachedNames,
    };

    setMessages((current) => [...current, userMessage]);
    setPrompt("");
    setFiles([]);
    setError("");
    setBusy(true);

    try {
      const body = new FormData();
      body.append("message", text);
      body.append("role", role);
      if (conversationId) body.append("conversationId", conversationId);
      files.forEach((file) => body.append("files[]", file));

      const result = await api<{
        answer: string;
        conversationId?: string;
        citations?: Citation[];
      }>("/ask", session.token, { method: "POST", body });

      if (result.conversationId) setConversationId(result.conversationId);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          citations: result.citations ?? [],
        },
      ]);

      const updated = await api<Conversation[]>("/conversations", session.token);
      setConversations(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Message could not be sent.");
    } finally {
      setBusy(false);
    }
  }

  if (!session) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#f7f7f5] px-4 text-stone-900">
        <form
          onSubmit={signIn}
          className="w-full max-w-sm rounded-2xl border border-stone-200 bg-white p-8 shadow-sm"
        >
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 grid h-11 w-11 place-items-center rounded-full bg-stone-900 text-lg text-white">
              A
            </div>
            <h1 className="text-2xl font-semibold">Welcome back</h1>
            <p className="mt-2 text-sm text-stone-500">Sign in to continue</p>
          </div>
          <label className="mb-4 block text-sm">
            Username
            <input
              className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-600"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="mb-5 block text-sm">
            Password
            <input
              type="password"
              className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-600"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {loginError && <p className="mb-4 text-sm text-red-700">{loginError}</p>}
          <button
            disabled={busy}
            className="w-full rounded-lg bg-stone-900 py-2.5 font-medium text-white disabled:opacity-60"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <p className="mt-4 text-center text-xs text-stone-500">
            Demo credentials: testuser / password
          </p>
        </form>
      </main>
    );
  }

  if (!role) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#f7f7f5] px-4 text-stone-900">
        <section className="w-full max-w-lg rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-semibold">Choose your workspace</h1>
          <p className="mb-6 mt-2 text-stone-500">Select a role to continue.</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {(["engineer", "customer"] as Role[]).map((item) => (
              <button
                key={item}
                onClick={() => setRole(item)}
                className="rounded-xl border border-stone-200 p-5 text-left transition hover:border-stone-500 hover:bg-stone-50"
              >
                <span className="block font-medium capitalize">{item}</span>
                <span className="mt-1 block text-sm text-stone-500">
                  {item === "engineer"
                    ? "Engineering workspace"
                    : "Customer workspace"}
                </span>
              </button>
            ))}
          </div>
          <button onClick={logout} className="mt-6 text-sm text-stone-500 hover:text-stone-900">
            Sign out
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="flex h-screen overflow-hidden bg-[#faf9f6] text-stone-900">
      <aside className="hidden w-72 shrink-0 flex-col border-r border-stone-200 bg-[#f2f1ed] p-4 md:flex">
        <div className="mb-8 flex items-center gap-2 px-2 font-semibold">
          <span className="grid h-7 w-7 place-items-center rounded-full bg-stone-900 text-sm text-white">A</span>
          Assistant
        </div>
        <button
          onClick={newConversation}
          className="mb-5 flex items-center gap-2 rounded-lg border border-stone-300 px-3 py-2 text-sm hover:bg-white"
        >
          <Plus size={16} /> New conversation
        </button>
        <p className="mb-2 px-2 text-xs font-medium uppercase tracking-wide text-stone-500">
          Recent
        </p>
        <nav className="flex-1 space-y-1 overflow-y-auto">
          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => openConversation(conversation.id)}
              className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm hover:bg-white ${
                conversation.id === conversationId ? "bg-white" : ""
              }`}
            >
              {conversation.title}
            </button>
          ))}
        </nav>
        <div className="flex items-center justify-between border-t border-stone-300 pt-4 text-sm">
          <span className="capitalize text-stone-600">{role} workspace</span>
          <button onClick={logout} aria-label="Sign out" title="Sign out">
            <LogOut size={17} />
          </button>
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-stone-200 px-5">
          <span className="font-medium capitalize md:hidden">{role} workspace</span>
          <span className="hidden text-sm text-stone-500 md:block">AI assistant</span>
          <button onClick={logout} className="text-sm text-stone-500 hover:text-stone-900">
            Sign out
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-8">
          {messages.length === 0 ? (
            <div className="mx-auto mt-[12vh] max-w-2xl text-center">
              <h1 className="text-3xl font-medium tracking-tight sm:text-4xl">
                What can I help you with?
              </h1>
              <p className="mt-3 text-stone-500">
                Ask a question or attach a document, image, or audio recording.
              </p>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-8">
              {messages.map((message) => (
                <article key={message.id} className="whitespace-pre-wrap">
                  <p className="mb-2 text-sm font-semibold">
                    {message.role === "user" ? "You" : "Assistant"}
                  </p>
                  <p className="leading-7 text-stone-800">{message.content}</p>
                  {message.files?.length ? (
                    <p className="mt-2 text-xs text-stone-500">
                      Attached: {message.files.join(", ")}
                    </p>
                  ) : null}
                  {!!message.citations?.length && (
                    <details className="mt-4 rounded-xl border border-stone-200 bg-white p-4">
                      <summary className="flex cursor-pointer items-center gap-2 text-sm font-medium">
                        <FileText size={16} /> Sources ({message.citations.length})
                      </summary>
                      <div className="mt-3 space-y-3">
                        {message.citations.map((citation, index) => (
                          <div key={`${citation.url}-${index}`} className="text-sm">
                            {citation.url ? (
                              <a
                                className="font-medium underline underline-offset-2"
                                href={citation.url}
                                target="_blank"
                                rel="noreferrer"
                              >
                                {citation.title || citation.url}
                              </a>
                            ) : (
                              <p className="font-medium">{citation.title || `Source ${index + 1}`}</p>
                            )}
                            {citation.snippet && (
                              <p className="mt-1 text-stone-600">{citation.snippet}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </article>
              ))}
              {busy && <p className="text-sm text-stone-500">Thinking…</p>}
            </div>
          )}
        </div>

        <div className="px-4 pb-5">
          <form
            onSubmit={sendMessage}
            className="mx-auto max-w-3xl rounded-2xl border border-stone-300 bg-white p-3 shadow-sm"
          >
            {files.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-2">
                {files.map((file, index) => (
                  <span
                    key={`${file.name}-${index}`}
                    className="flex max-w-full items-center gap-2 rounded-lg bg-stone-100 px-2.5 py-1.5 text-xs"
                  >
                    {file.type.startsWith("image/") ? <ImageIcon size={14} /> : <FileText size={14} />}
                    <span className="max-w-48 truncate">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => setFiles((current) => current.filter((_, i) => i !== index))}
                      aria-label={`Remove ${file.name}`}
                    >
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>
            )}
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void sendMessage();
                }
              }}
              placeholder="Message the assistant…"
              rows={2}
              className="w-full resize-none bg-transparent px-2 py-2 outline-none"
            />
            {error && <p className="px-2 pb-2 text-sm text-red-700">{error}</p>}
            <div className="flex items-center justify-between border-t border-stone-100 pt-2">
              <div className="flex items-center gap-1">
                <input
                  ref={fileInput}
                  type="file"
                  accept="image/*,audio/*,.pdf,.txt,.doc,.docx"
                  multiple
                  className="hidden"
                  onChange={(e) => {
                    addFiles(e.target.files);
                    e.currentTarget.value = "";
                  }}
                />
                <button
                  type="button"
                  onClick={() => fileInput.current?.click()}
                  className="rounded-lg p-2 text-stone-600 hover:bg-stone-100"
                  aria-label="Attach files"
                  title="Attach files"
                >
                  <Plus size={18} />
                </button>
                <button
                  type="button"
                  onClick={() => void toggleRecording()}
                  className={`rounded-lg p-2 hover:bg-stone-100 ${recording ? "text-red-700" : "text-stone-600"}`}
                  aria-label={recording ? "Stop recording" : "Record audio"}
                  title={recording ? "Stop recording" : "Record audio"}
                >
                  {recording ? <Square size={17} /> : <Mic size={18} />}
                </button>
              </div>
              <button
                disabled={busy || (!prompt.trim() && files.length === 0)}
                className="grid h-9 w-9 place-items-center rounded-xl bg-stone-900 text-white disabled:opacity-40"
                aria-label="Send message"
              >
                <ArrowUp size={18} />
              </button>
            </div>
          </form>
          <p className="mt-2 text-center text-xs text-stone-400">
            Review important information before relying on it.
          </p>
        </div>
      </section>
    </main>
  );
}