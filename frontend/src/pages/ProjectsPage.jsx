import React, { useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api/client.js";
import { AuthContext } from "../auth/AuthContext.jsx";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Card from "../components/ui/Card.jsx";
import Button from "../components/ui/Button.jsx";
import SkillTag from "../components/ui/SkillTag.jsx";
import Spinner from "../components/ui/Spinner.jsx";
import { Link } from "react-router-dom";

export default function ProjectsPage() {
  const { user } = useContext(AuthContext);
  const { addToast } = useContext(ToastContext);

  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [total, setTotal] = useState(0);

  const [status, setStatus] = useState("Open");
  const [page, setPage] = useState(1);
  const perPage = 10;

  const [appsByProject, setAppsByProject] = useState({});
  const [appsLoading, setAppsLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await api.get("/api/projects", {
        params: { page, per_page: perPage, status: status === "All" ? undefined : status },
      });
      setProjects(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) {
      addToast({ type: "error", message: "Failed to load projects" });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, status]);

  const userId = user?.id;

  const projectMemberIdSet = (p) => new Set((p.members || []).map((m) => m.id));

  async function applyToProject(projectId) {
    try {
      await api.post(`/api/projects/${projectId}/apply`, { message: "" });
      addToast({ type: "success", message: "Application submitted" });
      await load();
    } catch (e) {
      addToast({ type: "error", message: e?.response?.data?.message || "Could not apply" });
    }
  }

  async function loadApplications(projectId) {
    setAppsLoading(true);
    try {
      const res = await api.get(`/api/projects/${projectId}/applications`);
      setAppsByProject((prev) => ({ ...prev, [projectId]: res.data.items || [] }));
    } catch (e) {
      addToast({ type: "error", message: "Failed to load applications" });
    } finally {
      setAppsLoading(false);
    }
  }

  async function decide(projectId, applicantId, decision) {
    try {
      await api.post(`/api/projects/${projectId}/applications/${applicantId}/decision`, { decision });
      addToast({ type: "success", message: `Applicant ${decision}d` });
      setAppsByProject((prev) => ({ ...prev, [projectId]: [] }));
      await loadApplications(projectId);
      await load();
    } catch (e) {
      addToast({ type: "error", message: e?.response?.data?.message || "Decision failed" });
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / perPage));

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-2xl font-bold">Projects</div>
            <div className="mt-1 text-sm text-slate-300">Apply to open projects or manage applicants if you created one.</div>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" as={Link} to="/projects/new">
              Create Project
            </Button>
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <label className="block">
            <div className="mb-2 text-sm font-semibold text-slate-200">Project status</div>
            <select
              value={status}
              onChange={(e) => {
                setPage(1);
                setStatus(e.target.value);
              }}
              className="w-full md:w-56 rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
            >
              <option>Open</option>
              <option>Closed</option>
              <option>All</option>
            </select>
          </label>
          <div className="text-sm text-slate-400">
            Page {page} / {totalPages}
          </div>
        </div>
      </Card>

      {loading ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {projects.map((p) => {
            const membersSet = projectMemberIdSet(p);
            const isMember = membersSet.has(userId);
            const isCreator = p.creator_id === userId;
            const apps = appsByProject[p.id] || [];
            return (
              <Card key={p.id} className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-lg font-bold">{p.title}</div>
                    <div className="mt-1 text-sm text-slate-300">
                      {p.status} • {p.members_count}/{p.max_team_size} members
                    </div>
                  </div>
                  <div className="text-sm font-semibold text-indigo-200">{p.id}</div>
                </div>

                <div className="mt-3 text-sm text-slate-300">{p.description || ""}</div>

                <div className="mt-4">
                  <div className="text-sm font-semibold text-slate-200">Required skills</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(p.required_skills || []).map((s) => (
                      <SkillTag key={s} skill={s} />
                    ))}
                  </div>
                </div>

                <div className="mt-5 flex flex-col gap-3">
                  {!isMember && !isCreator ? (
                    p.status === "Open" ? (
                      <Button onClick={() => applyToProject(p.id)} disabled={!userId}>
                        Apply
                      </Button>
                    ) : (
                      <div className="text-sm text-slate-400">Project is closed.</div>
                    )
                  ) : isMember ? (
                    <div className="space-y-2">
                      <div className="text-sm text-emerald-200 font-semibold">You are a member</div>
                      <Button
                        variant="secondary"
                        as={Link}
                        to={`/chat?type=project&project_id=${p.id}`}
                      >
                        Open Project Chat
                      </Button>
                    </div>
                  ) : (
                    <div className="text-sm text-indigo-200 font-semibold">You created this project</div>
                  )}

                  {isCreator ? (
                    <div className="space-y-3">
                      <Button
                        variant="secondary"
                        disabled={appsLoading}
                        onClick={() => loadApplications(p.id)}
                      >
                        {apps.length ? "Refresh Applications" : "Manage Applications"}
                      </Button>

                      {appsLoading ? <Spinner /> : null}

                      {apps.length ? (
                        <div className="rounded-xl bg-white/5 ring-1 ring-white/10 p-3">
                          <div className="text-sm font-semibold text-slate-200">Applicants</div>
                          <div className="mt-2 space-y-2">
                            {apps.map((a) => (
                              <div key={a.id} className="flex items-center justify-between gap-3 rounded-lg bg-black/10 p-2">
                                <div className="min-w-0">
                                  <div className="text-sm font-semibold">Applicant #{a.applicant_id}</div>
                                  <div className="text-xs text-slate-400">{a.status}</div>
                                </div>
                                <div className="flex gap-2">
                                  {a.status === "pending" ? (
                                    <>
                                      <Button variant="primary" onClick={() => decide(p.id, a.applicant_id, "accept")}>
                                        Accept
                                      </Button>
                                      <Button variant="danger" onClick={() => decide(p.id, a.applicant_id, "reject")}>
                                        Reject
                                      </Button>
                                    </>
                                  ) : (
                                    <div className="text-xs text-slate-400">Decided</div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <div className="flex items-center justify-between">
        <Button
          variant="secondary"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

