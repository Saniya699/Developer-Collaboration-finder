import React, { useContext, useEffect, useState } from "react";
import { api } from "../api/client.js";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Card from "../components/ui/Card.jsx";
import Button from "../components/ui/Button.jsx";
import Spinner from "../components/ui/Spinner.jsx";

function labelForType(t) {
  switch (t) {
    case "application_created":
      return "New Application";
    case "application_accepted":
      return "Application Accepted";
    case "application_rejected":
      return "Application Rejected";
    case "message_received":
      return "New Message";
    case "rating_created":
      return "New Rating";
    default:
      return "Notification";
  }
}

export default function NotificationsPage() {
  const { addToast } = useContext(ToastContext);
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);

  async function load() {
    setLoading(true);
    try {
      const res = await api.get("/api/notifications");
      setItems(res.data.items || []);
    } catch (e) {
      addToast({ type: "error", message: "Failed to load notifications" });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function markRead(id) {
    try {
      await api.post(`/api/notifications/${id}/read`);
      addToast({ type: "success", message: "Marked as read" });
      await load();
    } catch (e) {
      addToast({ type: "error", message: "Could not update notification" });
    }
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="text-2xl font-bold">Notifications</div>
        <div className="mt-1 text-sm text-slate-300">Applications, messages, and ratings — stored locally on your DB.</div>
      </Card>

      {loading ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : items.length === 0 ? (
        <Card className="p-6">
          <div className="text-sm text-slate-300">No notifications yet.</div>
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((n) => (
            <Card key={n.id} className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm font-semibold">{labelForType(n.type)}</div>
                  <div className="mt-1 text-xs text-slate-400">
                    {n.created_at ? new Date(n.created_at).toLocaleString() : "—"}
                  </div>
                  <div className="mt-2 text-sm text-slate-200">
                    <span className="text-slate-400">Payload:</span> <span className="text-slate-100">{JSON.stringify(n.payload || {})}</span>
                  </div>
                </div>
                <div className="flex flex-col gap-2 items-end">
                  {n.read_at ? (
                    <div className="text-xs text-emerald-200 font-semibold">Read</div>
                  ) : (
                    <Button variant="secondary" onClick={() => markRead(n.id)}>
                      Mark read
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

