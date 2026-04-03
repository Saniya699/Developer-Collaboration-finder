import React, { useContext, useEffect, useMemo, useRef, useState } from "react";
import { io } from "socket.io-client";
import { AuthContext } from "../auth/AuthContext.jsx";
import { api } from "../api/client.js";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Card from "../components/ui/Card.jsx";
import Button from "../components/ui/Button.jsx";
import Spinner from "../components/ui/Spinner.jsx";
import { useSearchParams } from "react-router-dom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

export default function ChatPage() {
  const { user, accessToken } = useContext(AuthContext);
  const { addToast } = useContext(ToastContext);
  const [searchParams] = useSearchParams();

  const socket = useMemo(
    () => io(API_BASE_URL, { autoConnect: false, transports: ["websocket"] }),
    [],
  );

  const [conversations, setConversations] = useState({ direct: [], projects: [] });
  const [loadingConvos, setLoadingConvos] = useState(true);

  const [selected, setSelected] = useState({ type: "direct", other_user_id: null, project_id: null });
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [draft, setDraft] = useState("");
  const [typing, setTyping] = useState(null);
  const typingTimeoutRef = useRef(null);

  const scrollRef = useRef(null);

  async function loadConversations() {
    setLoadingConvos(true);
    try {
      const res = await api.get("/api/chat/conversations");
      setConversations(res.data || { direct: [], projects: [] });
    } catch (e) {
      addToast({ type: "error", message: "Failed to load chat conversations" });
    } finally {
      setLoadingConvos(false);
    }
  }

  async function loadHistory(sel) {
    if (!sel || !user?.id) return;
    setLoadingMessages(true);
    try {
      if (sel.type === "direct") {
        const res = await api.get("/api/chat/history", {
          params: { type: "direct", other_user_id: sel.other_user_id, page: 1, per_page: 50 },
        });
        setMessages(res.data.items || []);
      } else {
        const res = await api.get("/api/chat/history", {
          params: { type: "project", project_id: sel.project_id, page: 1, per_page: 50 },
        });
        setMessages(res.data.items || []);
      }
    } catch (e) {
      addToast({ type: "error", message: "Could not load chat history" });
    } finally {
      setLoadingMessages(false);
    }
  }

  useEffect(() => {
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!accessToken) return;

    socket.connect();
    socket.emit("authenticate", { token: accessToken });

    socket.on("presence_update", (data) => {
      // For now we don't show global presence; typing can be used as a lightweight signal.
    });

    socket.on("typing", (data) => {
      // data: {sender_id, to_user_id, project_id, is_typing}
      if (!data || data.is_typing === false) {
        setTyping(null);
        return;
      }
      if (selected.type === "direct" && data.to_user_id) {
        if (
          (data.sender_id === selected.other_user_id && data.to_user_id === user.id) ||
          (data.sender_id === selected.other_user_id)
        ) {
          setTyping(data.sender_id);
        }
      }
      if (selected.type === "project" && data.project_id) {
        if (data.project_id === selected.project_id) {
          setTyping(data.sender_id);
        }
      }
    });

    socket.on("new_message", (msg) => {
      if (!msg) return;
      if (selected.type === "direct") {
        // For direct: message includes direct: true and sender_id
        const isSame =
          msg.direct === true &&
          ((msg.sender_id === user.id && msg.recipient_user_id === selected.other_user_id) ||
            (msg.sender_id === selected.other_user_id && msg.recipient_user_id === user.id));
        if (isSame) {
          setMessages((prev) => [...prev, msg]);
        }
      } else {
        if (msg.project_id && msg.project_id === selected.project_id) {
          setMessages((prev) => [
            ...prev,
            {
              id: msg.id,
              sender_id: msg.sender_id,
              project_id: msg.project_id,
              content: msg.content,
              created_at: msg.created_at,
            },
          ]);
        }
      }
    });

    return () => {
      socket.disconnect();
      socket.removeAllListeners();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  // Allow opening chat directly from deep links.
  useEffect(() => {
    const type = (searchParams.get("type") || "").toLowerCase();
    const other = searchParams.get("other_user_id");
    const project = searchParams.get("project_id");
    if (!type) return;
    if (type === "direct" && other) {
      const otherId = parseInt(other, 10);
      if (!Number.isNaN(otherId)) selectDirect(otherId);
      return;
    }
    if (type === "project" && project) {
      const projectId = parseInt(project, 10);
      if (!Number.isNaN(projectId)) selectProject(projectId);
      return;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, accessToken]);

  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loadingMessages]);

  function selectDirect(other_user_id) {
    const next = { type: "direct", other_user_id: other_user_id, project_id: null };
    setSelected(next);
    socket.emit("join_direct", { other_user_id });
    loadHistory(next);
  }

  function selectProject(project_id) {
    const next = { type: "project", other_user_id: null, project_id };
    setSelected(next);
    socket.emit("join_project", { project_id });
    loadHistory(next);
  }

  function sendTypingIndicator() {
    if (!selected || !user?.id) return;

    // Clear and re-schedule to avoid spamming.
    if (typingTimeoutRef.current) window.clearTimeout(typingTimeoutRef.current);

    const typingPayload = selected.type === "direct"
      ? { to_user_id: selected.other_user_id, is_typing: true }
      : { project_id: selected.project_id, is_typing: true };

    socket.emit("typing", typingPayload);

    typingTimeoutRef.current = window.setTimeout(() => {
      socket.emit("typing", { ...(typingPayload || {}), is_typing: false });
      setTyping(null);
    }, 900);
  }

  async function sendMessage() {
    const content = (draft || "").trim();
    if (!content) return;
    setDraft("");

    try {
      if (selected.type === "direct") {
        socket.emit("send_message", { to_user_id: selected.other_user_id, content });
      } else {
        socket.emit("send_message", { project_id: selected.project_id, content });
      }
    } catch (e) {
      addToast({ type: "error", message: "Message failed to send" });
    }
  }

  const selectedTitle =
    selected.type === "direct"
      ? conversations.direct.find((d) => d.other_user.id === selected.other_user_id)?.other_user?.name || "Direct chat"
      : conversations.projects.find((p) => p.project.id === selected.project_id)?.project?.title || "Project chat";

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="text-2xl font-bold">Chat</div>
        <div className="mt-1 text-sm text-slate-300">Real-time chat powered by local Socket.IO + DB persistence.</div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="p-4 lg:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <div className="font-semibold">Conversations</div>
            <Button variant="secondary" onClick={loadConversations} disabled={loadingConvos}>
              Refresh
            </Button>
          </div>

          {loadingConvos ? (
            <div className="mt-4 flex justify-center">
              <Spinner />
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              <div>
                <div className="text-xs font-bold text-slate-400">Direct</div>
                <div className="mt-2 space-y-2">
                  {conversations.direct.length === 0 ? (
                    <div className="text-sm text-slate-400">No direct messages yet.</div>
                  ) : (
                    conversations.direct.map((c) => (
                      <button
                        key={c.other_user.id}
                        className="w-full rounded-xl bg-white/5 p-3 text-left ring-1 ring-white/10 hover:bg-white/10"
                        onClick={() => selectDirect(c.other_user.id)}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold">{c.other_user.name}</div>
                          <div className="text-xs text-slate-400">Direct</div>
                        </div>
                        <div className="mt-1 text-xs text-slate-300 truncate">
                          {c.latest_message?.content || ""}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>

              <div>
                <div className="text-xs font-bold text-slate-400">Projects</div>
                <div className="mt-2 space-y-2">
                  {conversations.projects.length === 0 ? (
                    <div className="text-sm text-slate-400">Join a project to start group chat.</div>
                  ) : (
                    conversations.projects.map((c) => (
                      <button
                        key={c.project.id}
                        className="w-full rounded-xl bg-white/5 p-3 text-left ring-1 ring-white/10 hover:bg-white/10"
                        onClick={() => selectProject(c.project.id)}
                      >
                        <div className="text-sm font-semibold">{c.project.title}</div>
                        <div className="mt-1 text-xs text-slate-400">{c.project.status}</div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </Card>

        <Card className="p-4 lg:col-span-2">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-lg font-bold">{selectedTitle}</div>
              <div className="text-xs text-slate-400">
                {typing ? `Typing...` : `Live conversation`}
              </div>
            </div>
            <div className="text-xs text-slate-400">
              {selected.type === "direct" ? "One-to-one" : "Project group"}
            </div>
          </div>

          <div
            ref={scrollRef}
            className="mt-4 h-[420px] overflow-y-auto rounded-2xl bg-black/20 ring-1 ring-white/10 p-4"
          >
            {loadingMessages ? (
              <div className="flex justify-center py-10">
                <Spinner />
              </div>
            ) : messages.length === 0 ? (
              <div className="text-sm text-slate-400">No messages yet. Say hi.</div>
            ) : (
              <div className="space-y-3">
                {messages.map((m) => {
                  const isMe = m.sender_id === user.id;
                  return (
                    <div key={m.id} className={isMe ? "flex justify-end" : "flex justify-start"}>
                      <div
                        className={[
                          "max-w-[78%] rounded-2xl px-4 py-2 text-sm",
                          isMe
                            ? "bg-indigo-600/30 ring-1 ring-indigo-300/20"
                            : "bg-white/5 ring-1 ring-white/10",
                        ].join(" ")}
                      >
                        <div className="font-semibold">{isMe ? "You" : `User #${m.sender_id}`}</div>
                        <div className="mt-1 text-slate-100/95 whitespace-pre-wrap">{m.content}</div>
                        {m.created_at ? (
                          <div className="mt-1 text-[11px] text-slate-400">
                            {new Date(m.created_at).toLocaleTimeString()}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="mt-4 space-y-3">
            <label className="block">
              <div className="mb-2 text-sm font-semibold text-slate-200">Message</div>
              <div className="flex gap-3">
                <input
                  value={draft}
                  onChange={(e) => {
                    setDraft(e.target.value);
                    sendTypingIndicator();
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder="Type a message..."
                  className="flex-1 rounded-xl bg-white/5 px-4 py-3 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
                />
                <Button onClick={sendMessage} disabled={!draft.trim()}>
                  Send
                </Button>
              </div>
            </label>
            <div className="text-xs text-slate-400">Tip: select a conversation on the left. Messages are stored in your local DB.</div>
          </div>
        </Card>
      </div>
    </div>
  );
}

