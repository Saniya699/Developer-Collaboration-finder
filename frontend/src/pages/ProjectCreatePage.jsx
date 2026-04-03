import React, { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { AuthContext } from "../auth/AuthContext.jsx";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Card from "../components/ui/Card.jsx";
import Button from "../components/ui/Button.jsx";
import Input from "../components/ui/Input.jsx";

export default function ProjectCreatePage() {
  const navigate = useNavigate();
  const { addToast } = useContext(ToastContext);
  const { user } = useContext(AuthContext);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [requiredSkillsText, setRequiredSkillsText] = useState("");
  const [max_team_size, setMaxTeamSize] = useState(5);
  const [status, setStatus] = useState("Open");
  const [loading, setLoading] = useState(false);

  const required_skills = requiredSkillsText
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  async function onSubmit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/api/projects", {
        title,
        description,
        required_skills,
        max_team_size,
        status,
      });
      addToast({ type: "success", message: "Project created" });
      navigate("/projects");
    } catch (err) {
      addToast({ type: "error", message: err?.response?.data?.message || "Failed to create project" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card className="p-6">
        <div className="text-2xl font-bold">Create a Project</div>
        <div className="mt-1 text-sm text-slate-300">Define required skills so matching can work locally.</div>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <Input label="Title" value={title} onChange={setTitle} placeholder="Build a portfolio-ready web app" />

          <label className="block">
            <div className="mb-2 text-sm font-semibold text-slate-200">Description</div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="h-28 w-full resize-none rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
              placeholder="What are you looking to build? Any constraints?"
            />
          </label>

          <Input
            label="Required skills (comma-separated)"
            value={requiredSkillsText}
            onChange={setRequiredSkillsText}
            placeholder="Python, Flask, React"
          />

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block">
              <div className="mb-2 text-sm font-semibold text-slate-200">Max team size</div>
              <input
                type="number"
                min={1}
                value={max_team_size}
                onChange={(e) => setMaxTeamSize(parseInt(e.target.value || "1", 10))}
                className="w-full rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
              />
            </label>
            <label className="block">
              <div className="mb-2 text-sm font-semibold text-slate-200">Status</div>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
              >
                <option>Open</option>
                <option>Closed</option>
              </select>
            </label>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="secondary" type="button" onClick={() => navigate("/projects")} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !title.trim()}>
              {loading ? "Creating..." : "Create Project"}
            </Button>
          </div>

          {required_skills.length ? (
            <div className="text-sm text-slate-300">
              Will require: <span className="text-slate-100">{required_skills.slice(0, 10).join(", ")}</span>
            </div>
          ) : (
            <div className="text-sm text-amber-200">Add at least one required skill.</div>
          )}
        </form>
      </Card>
    </div>
  );
}

