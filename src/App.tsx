import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  Bot,
  ChevronRight,
  FileArchive,
  FileText,
  HardHat,
  History,
  LayoutDashboard,
  Image as ImageIcon,
  LogOut,
  Mic,
  Package,
  Plus,
  Scale,
  Settings,
  ShieldCheck,
  Square,
  Upload,
  Users,
  X,
} from "lucide-react";
import "./App.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080/api/v1";
const SESSION_KEY = "ai-interface-session";
const ROLE_KEY = "ai-interface-role";
const SESSION_LENGTH = 7 * 24 * 60 * 60 * 1000;

type Role = "engineer" | "customer";
type Citation = {
  source_id?: string;
  title?: string;
  url?: string;
  snippet?: string;
};
type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  files?: string[];
  citations?: Citation[];
};
type Conversation = { id: string; title: string; updatedAt?: string };
type Session = { token: string; expiresAt: number };
type Product = {
  id: number;
  category: string;
  name: string;
  model_number: string;
  specifications: string;
  price_ksh: number;
};

function formatPrice(priceKsh: number): string {
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: "KES",
    maximumFractionDigits: 0,
  }).format(priceKsh);
}

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
  const [role, setRole] = useState<Role | null>(() => {
    const savedRole = localStorage.getItem(ROLE_KEY);
    return savedRole === "engineer" || savedRole === "customer" ? savedRole : null;
  });
  const [selectedRole, setSelectedRole] = useState<Role>("engineer");
  const [activeNav, setActiveNav] = useState("Dashboard");
  const [productPage, setProductPage] = useState(0);
  const [products, setProducts] = useState<Product[]>([]);
  const [catalogLoaded, setCatalogLoaded] = useState(false);
  const [catalogError, setCatalogError] = useState("");
  const [username, setUsername] = useState("engineer@jenga.com");
  const [password, setPassword] = useState("engineer123");
  const [loginError, setLoginError] = useState("");
  const [busy, setBusy] = useState(false);

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
    localStorage.removeItem(ROLE_KEY);
    setSession(null);
    setRole(null);
    setMessages([]);
    setConversationId("");
    setProducts([]);
    setCatalogLoaded(false);
    setCatalogError("");
  }, []);

  useEffect(() => {
    if (!session) return;
    const remaining = session.expiresAt - Date.now();
    const timer = window.setTimeout(logout, Math.max(remaining, 0));
    return () => window.clearTimeout(timer);
  }, [session, logout]);

  useEffect(() => {
    if (!session || !role) return;
    api<Conversation[]>("/conversations", session.token).catch((e) => setError(e.message));
  }, [session, role]);

  useEffect(() => {
    if (!session) return;
    let active = true;
    api<Product[]>("/catalogue/products", session.token)
      .then((catalogue) => {
        if (active) {
          setProducts(catalogue);
          setCatalogError("");
          setCatalogLoaded(true);
        }
      })
      .catch((e: unknown) => {
        if (active) {
          setCatalogError(
            e instanceof Error ? e.message : "Product catalogue is unavailable.",
          );
          setCatalogLoaded(true);
        }
      })
    return () => {
      active = false;
    };
  }, [session]);

  async function signIn(event: React.FormEvent) {
    event.preventDefault();
    setLoginError("");
    setBusy(true);
    try {
      // The demo credentials are prefilled; the backend remains responsible for issuing the JWT.
      const result = await api<{ access_token: string }>("/auth/login", undefined, {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      const nextSession = {
        token: result.access_token,
        expiresAt: Date.now() + SESSION_LENGTH,
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
      localStorage.setItem(ROLE_KEY, selectedRole);
      setProducts([]);
      setCatalogLoaded(false);
      setCatalogError("");
      setSession(nextSession);
      setRole(selectedRole);
    } catch (e) {
      setLoginError(e instanceof Error ? e.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  function newConversation() {
    setConversationId("");
    setMessages([]);
    setError("");
  }

  function chooseRole(nextRole: Role) {
    setSelectedRole(nextRole);
    if (nextRole === "customer") {
      setUsername("customer@jenga.com");
      setPassword("customer123");
    } else {
      setUsername("engineer@jenga.com");
      setPassword("engineer123");
    }
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
    if (files.length > 0) {
      setError("Image, audio, and document analysis is not connected yet. Remove attachments and send a text question.");
      return;
    }

    const text = prompt.trim();
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };

    setMessages((current) => [...current, userMessage]);
    setPrompt("");
    setError("");
    setBusy(true);

    try {
      const result = await api<{
        answer: string;
        conversation_id?: string;
        citations?: Citation[];
      }>("/chat/query", session.token, {
        method: "POST",
        body: JSON.stringify({
          query: text,
          conversation_id: conversationId || undefined,
        }),
      });

      if (result.conversation_id) setConversationId(result.conversation_id);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          citations: result.citations ?? [],
        },
      ]);

    } catch (e) {
      setError(e instanceof Error ? e.message : "Message could not be sent.");
    } finally {
      setBusy(false);
    }

  }

  const pageDetails: Record<string, { title: string; description: string }> = {
    "Chat Assistant": { title: "Chat Assistant", description: "Ask Jenga Copilot about equipment, specifications, and technical documentation." },
    "Browse Products": { title: "Browse Products", description: "Explore equipment and find the right solution for your project." },
    Documents: { title: "Documents", description: "Access manuals, datasheets, safety guides, and approved documentation." },
    "Compare Solutions": { title: "Compare Solutions", description: "Compare equipment options side by side before making a decision." },
    "Upload Media": { title: "Upload Media", description: "Add drawings, images, audio notes, and project files for analysis." },
    History: { title: "History", description: "Review your recent questions, comparisons, and saved recommendations." },
    Settings: { title: "Settings", description: "Manage your workspace preferences and assistant experience." },
  };
  const engineerOnlyPages = new Set(["Compare Solutions", "Upload Media"]);
  const canAccessPage = (page: string) => role === "engineer" || !engineerOnlyPages.has(page);

  if (!session) {
    return (
      <main className="auth-page">
        <section className="auth-hero">
          <div className="brand-lockup">
            <span className="brand-mark">⚙</span>
            <span>Jenga Consultants<br /><b>Product Copilot</b></span>
          </div>
          <div className="auth-copy">
            <p className="eyebrow">INDUSTRIAL INTELLIGENCE, SIMPLIFIED</p>
            <h1>Your AI-Powered<br /><strong>Equipment Assistant</strong></h1>
            <p>Find the right industrial equipment, get expert answers, and access trusted documentation.</p>
            <div className="auth-benefits">
              <span><b>⚡</b>Instant<br />Answers</span>
              <span><b>✓</b>Trusted<br />Sources</span>
              <span><b>▥</b>Smarter<br />Decisions</span>
            </div>
          </div>
          <div className="hero-machine" aria-hidden="true">⚙</div>
        </section>
        <form
          onSubmit={signIn}
          className="auth-card"
        >
          <div className="auth-card-heading">
            <span className="lock-icon"><ShieldCheck size={24} /></span>
            <h2>Welcome Back</h2>
            <p>Sign in to access your AI assistant</p>
          </div>
          <label className="auth-field">
            <span><Users size={15} /> {selectedRole === "customer" ? "Customer account" : "Engineer account"}</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="auth-field">
            <span><ShieldCheck size={15} /> Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          <p className="role-label">Account type:</p>
          <div className="role-switcher">
            <button type="button" className={selectedRole === "engineer" ? "selected" : ""} onClick={() => chooseRole("engineer")}><HardHat size={16} /> Engineer</button>
            <button type="button" className={selectedRole === "customer" ? "selected" : ""} onClick={() => chooseRole("customer")}><Users size={16} /> Customer</button>
          </div>
          {loginError && <p className="login-error">{loginError}</p>}
          <button disabled={busy} className="auth-submit">{busy ? "Signing in…" : <>Sign In <ArrowUp size={16} /></>}</button>
          <div className="auth-divider"><span>or</span></div>
          <p className="auth-version">Jenga Consultants Product Copilot v1.0</p>
        </form>
      </main>
    );
  }

  if (!role) {
    return (
      <main className="auth-page fallback-role">
        <section className="auth-card">
          <h2>Choose your workspace</h2>
          <p>Select a role to continue.</p>
          <div className="role-switcher">
            <button onClick={() => { localStorage.setItem(ROLE_KEY, "engineer"); setRole("engineer"); }}><HardHat size={16} /> Engineer</button>
            <button onClick={() => { localStorage.setItem(ROLE_KEY, "customer"); setRole("customer"); }}><Users size={16} /> Customer</button>
          </div>
          <button onClick={logout}>Sign out</button>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand"><span className="brand-mark">⚙</span><span>Jenga Consultants<br /><b>Product Copilot</b></span></div>
        <nav className="dashboard-nav">
          <button className={activeNav === "Dashboard" ? "active" : ""} onClick={() => setActiveNav("Dashboard")}><LayoutDashboard size={16} /> Dashboard</button>
          <button className={activeNav === "Chat Assistant" ? "active" : ""} onClick={() => { setActiveNav("Chat Assistant"); newConversation(); }}><Bot size={16} /> Chat Assistant</button>
          <button className={activeNav === "Browse Products" ? "active" : ""} onClick={() => setActiveNav("Browse Products")}><Package size={16} /> Browse Products</button>
          <button className={activeNav === "Documents" ? "active" : ""} onClick={() => setActiveNav("Documents")}><FileArchive size={16} /> Documents</button>
          {role === "engineer" && <button className={activeNav === "Compare Solutions" ? "active" : ""} onClick={() => setActiveNav("Compare Solutions")}><Scale size={16} /> Compare Solutions</button>}
          {role === "engineer" && <button className={activeNav === "Upload Media" ? "active" : ""} onClick={() => setActiveNav("Upload Media")}><Upload size={16} /> Upload Media</button>}
          <button className={activeNav === "History" ? "active" : ""} onClick={() => setActiveNav("History")}><History size={16} /> History</button>
          <button className={activeNav === "Settings" ? "active" : ""} onClick={() => setActiveNav("Settings")}><Settings size={16} /> Settings</button>
        </nav>
        <button className="sidebar-signout" onClick={logout}><LogOut size={16} /> Sign Out</button>
        <div className="online-status"><span>●</span><b>Online</b><small>Secure Session</small></div>
      </aside>
      <section className="dashboard-main">
        <header className="dashboard-header">
          <div className="dashboard-title"><LayoutDashboard size={18} /><div><b>{activeNav}</b><small>Your AI equipment assistant at work</small></div></div>
          <div className="account-chip">
            <span className="account-avatar">👷</span>
            <div className="account-details">
              <b>{username.split("@")[0]}</b>
              <small>{role === "engineer" ? "Engineer" : "Customer"}</small>
            </div>
            </div>
        </header>
        <div className={`dashboard-content ${activeNav !== "Dashboard" ? "subpage-active" : ""}`}>
          {!canAccessPage(activeNav) && <section className="page-panel"><div className="page-panel-heading"><div><p className="page-kicker">ACCESS RESTRICTED</p><h1>Engineer workspace required</h1><p>This resource is available to authenticated engineers only.</p></div><span className="page-panel-icon"><ShieldCheck size={24} /></span></div></section>}
          {canAccessPage(activeNav) && activeNav !== "Dashboard" && (
            <section className="page-panel">
              <div className="page-panel-heading">
                <div>
                  <p className="page-kicker">JENGA WORKSPACE</p>
                  <h1>{pageDetails[activeNav].title}</h1>
                  <p>{pageDetails[activeNav].description}</p>
                </div>
                <span className="page-panel-icon"><Bot size={24} /></span>
              </div>
              {activeNav === "Chat Assistant" && (
                <div className="page-chat-layout">
                  <div className="dashboard-card chat-card">
                    <h2><Bot size={16} /> Start a conversation</h2>
                    <p className="panel-muted">Ask a question below and receive a sourced answer from the copilot.</p>
                    <form onSubmit={sendMessage} className="dashboard-composer standalone-composer">
                      <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="What would you like to know?" rows={4} />
                      <div className="composer-actions"><span>Answers include relevant sources where available.</span><button className="send-button" aria-label="Send message"><ArrowUp size={16} /></button></div>
                    </form>
                  </div>
                  <div className="dashboard-card"><h2><ShieldCheck size={16} /> Copilot guidance</h2><ul className="feature-list"><li>Equipment recommendations</li><li>Technical specifications</li><li>Document and image analysis</li></ul></div>
                </div>
              )}
              {activeNav === "Browse Products" && (
                <>
                  {!catalogLoaded && <p className="panel-muted">Loading product catalogue…</p>}
                  {catalogError && <p className="login-error" role="alert">{catalogError}</p>}
                  {catalogLoaded && !catalogError && products.length === 0 && (
                    <p className="panel-muted">No products are currently available.</p>
                  )}
                  {catalogLoaded && !catalogError && products.length > 0 && (
                    <>
                      <div className="catalog-grid">
                        {products.slice(productPage * 4, productPage * 4 + 4).map((product) => (
                          <article className="catalog-card" key={product.id}>
                            <Package className="product-image" aria-hidden="true" />
                            <div>
                              <small className="product-category">{product.category}</small>
                              <h2>{product.name}</h2>
                              <p className="panel-muted">Model: {product.model_number}</p>
                              <strong className="catalog-price">{formatPrice(product.price_ksh)}</strong>
                              <p>{product.specifications}</p>
                            </div>
                          </article>
                        ))}
                      </div>
                      {products.length > 4 && (
                        <div className="catalog-pagination">
                          <button disabled={productPage === 0} onClick={() => setProductPage((page) => page - 1)}>Previous</button>
                          <span>Page {productPage + 1} of {Math.ceil(products.length / 4)}</span>
                          <button disabled={(productPage + 1) * 4 >= products.length} onClick={() => setProductPage((page) => page + 1)}>Next</button>
                        </div>
                      )}
                    </>
                  )}
                </>
              )}
              {activeNav === "Documents" && <div className="document-list">{["Equipment Safety Handbook.pdf", "JCB 3CX Technical Datasheet.pdf", "Site Operations Guide.pdf"].map((item) => <article key={item}><FileText size={22} /><div><b>{item}</b><small>Verified project documentation · PDF</small></div><button><ChevronRight size={15} /></button></article>)}</div>}
              {activeNav === "Compare Solutions" && <div className="comparison-card dashboard-card"><div className="comparison-toolbar"><span>Selected solutions</span><button className="primary-small">Add product</button></div><div className="comparison-table"><b>Category</b><b>JCB 3CX</b><b>CAT 320</b><span>Equipment type</span><span>Backhoe loader</span><span>Excavator</span><span>Best for</span><span>General construction</span><span>Earthmoving</span></div></div>}
              {activeNav === "Upload Media" && <div className="upload-panel dashboard-card"><Upload size={30} /><h2>Upload project media</h2><p>Drag files here or choose files from your device. Supported formats include PDF, images, audio, and documents.</p><button className="primary-small" onClick={() => fileInput.current?.click()}>Choose files</button></div>}
              {activeNav === "History" && <div className="history-list dashboard-card"><h2><History size={16} /> Recent activity</h2><p className="panel-muted">Your recent assistant activity will appear here after your first question.</p></div>}
              {activeNav === "Settings" && <div className="settings-list dashboard-card"><h2><Settings size={16} /> Workspace settings</h2><label><span>Workspace notifications</span><input type="checkbox" defaultChecked /></label><label><span>Show source citations</span><input type="checkbox" defaultChecked /></label><label><span>Active role <small>Locked for this session</small></span><strong className="locked-role">{role === "engineer" ? "Engineer" : "Customer"}</strong></label></div>}
            </section>
          )}
          <section className="welcome-banner">
            <div><h1>Hi {username.split("@")[0]}! 👋</h1><p>Ask me about our industrial equipment,<br />get recommendations, or find technical specs.</p><button onClick={newConversation}>Start a new chat <ArrowUp size={14} /></button></div>
            <div className="welcome-checks"><span>● Trusted Information</span><span>● Source Citations</span><span>● Role-Based Access</span></div>
          </section>
          <div className="dashboard-grid">
            <section className="dashboard-card chat-card">
              <h2><Bot size={16} /> Chat with Jenga Copilot</h2>
              <div className="chat-preview"><span className="bot-avatar">🤖</span><p>Hello! I can help you find equipment information, compare products, or answer technical questions.<br /><b>What would you like to know?</b></p></div>
              {messages.length > 0 && <div className="mini-messages">{messages.slice(-2).map((message) => <p key={message.id}><b>{message.role === "user" ? "You" : "Copilot"}:</b> {message.content}</p>)}</div>}
              <div className="chat-composer">
          <form
            onSubmit={sendMessage}
            className="dashboard-composer"
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
              placeholder="Type your question here..."
              rows={2}
              className="w-full resize-none bg-transparent px-2 py-2 outline-none"
            />
            {error && <p className="composer-error">{error}</p>}
            <div className="composer-actions">
              <div>
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
                className="send-button"
                aria-label="Send message"
              >
                <ArrowUp size={18} />
              </button>
            </div>
          </form>
              </div>
            </section>
            <section className="dashboard-card recommendations-card">
              <div className="recommendation-heading">
                <div><p className="recommendation-kicker">CURRENT BACKEND CATALOGUE</p><h2>Available Products</h2></div>
                <button type="button" onClick={() => setActiveNav("Browse Products")}>View All <ChevronRight size={13} /></button>
              </div>
              <p className="recommendation-intro">Products and prices are loaded from the application catalogue.</p>
              <div className="recommendation-list">
                {products.slice(0, 3).map((product) => (
                  <div className="recommendation" key={product.id}>
                    <Package className="product-icon" aria-hidden="true" />
                    <span><b>{product.name}</b><small>{product.model_number} · {formatPrice(product.price_ksh)}</small></span>
                  </div>
                ))}
                {catalogLoaded && products.length === 0 && (
                  <p className="panel-muted">{catalogError || "No catalogue products are available."}</p>
                )}
              </div>
            </section>
          </div>
          <div className="metrics-row">{[["▣", "15+", "Equipment Products"], ["✓", "100%", "Trusted Sources"], ["▥", "60+", "Benchmark Items"], ["▥", "Real-Time", "AI Insights"]].map(([icon, value, label]) => <div className="metric-card" key={label}><span>{icon}</span><b>{value}</b><small>{label}</small></div>)}</div>
          {messages.length > 0 && <div className="message-history">{messages.map((message) => <article key={message.id}><b>{message.role === "user" ? "You" : "Copilot"}</b><p>{message.content}</p></article>)}</div>}
        </div>
      </section>
    </main>
  );
}