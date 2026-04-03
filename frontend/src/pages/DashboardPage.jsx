import React, { useContext, useEffect, useState } from "react";
import { api } from "../api/client.js";
import { AuthContext } from "../auth/AuthContext.jsx";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Card from "../components/ui/Card.jsx";
import SkillTag from "../components/ui/SkillTag.jsx";
import Button from "../components/ui/Button.jsx";
import Spinner from "../components/ui/Spinner.jsx";
import { Link } from "react-router-dom";

export default function DashboardPage() {
  const { user } = useContext(AuthContext);
  const { addToast } = useContext(ToastContext);

  const [loading, setLoading] = useState(true);
  const [teammates, setTeammates] = useState([]);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    let mounted = true;
    async function run() {
      setLoading(true);
      try {
        const [tRes, pRes] = await Promise.all([
          api.get("/api/matches/teammates?top=5"),
          api.get("/api/matches/projects?top=5&status=Open"),
        ]);
        if (!mounted) return;
        setTeammates(tRes.data.items || []);
        setProjects(pRes.data.items || []);
      } catch (e) {
        addToast({ type: "error", message: "Could not load recommendations" });
      } finally {
        if (mounted) setLoading(false);
      }
    }
    run();
    return () => {
      mounted = false;
    };
  }, [addToast]);

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-2xl font-bold">Dashboard</div>
            <div className="mt-1 text-sm text-slate-300">
              {user ? `${user.experience_level} • ${user.availability}` : "—"}
            </div>
          </div>
          <div className="flex gap-3">
            <Button as={Link} to="/projects/new" variant="primary">
              Create Project
            </Button>
            <Button as={Link} to="/matches" variant="secondary">
              View Matches
            </Button>
          </div>
        </div>

        <div className="mt-5">
          <div className="text-sm font-semibold text-slate-200">Your skills</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {(user?.skills || []).map((s) => (
              <SkillTag key={s} skill={s} />
            ))}
          </div>
        </div>
      </Card>

      {loading ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="p-6">
            <div className="text-lg font-bold">Top Teammates</div>
            <div className="mt-3 space-y-3">
              {teammates.length === 0 ? (
                <div className="text-sm text-slate-300">No teammate recommendations yet.</div>
              ) : (
                teammates.map((t) => (
                  <div key={t.user.id} className="rounded-xl bg-white/5 ring-1 ring-white/10 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold">{t.user.name}</div>
                        <div className="text-xs text-slate-400">
                          {t.user.experience_level} • {t.user.availability}
                        </div>
                      </div>
                      <div className="text-sm font-bold text-indigo-200">{t.overall_score.toFixed(2)}</div>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(t.user.skills || []).slice(0, 8).map((s) => (
                        <SkillTag key={s} skill={s} className="bg-indigo-600/10" />
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>

          <Card className="p-6">
            <div className="text-lg font-bold">Best Projects</div>
            <div className="mt-3 space-y-3">
              {projects.length === 0 ? (
                <div className="text-sm text-slate-300">No projects found.</div>
              ) : (
                projects.map((p) => (
                  <div key={p.project.id} className="rounded-xl bg-white/5 ring-1 ring-white/10 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold">{p.project.title}</div>
                        <div className="text-xs text-slate-400">
                          {p.project.members_count}/{p.project.max_team_size} members
                        </div>
                      </div>
                      <div className="text-sm font-bold text-indigo-200">{p.overall_score.toFixed(2)}</div>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(p.project.required_skills || []).slice(0, 6).map((s) => (
                        <SkillTag key={s} skill={s} className="bg-indigo-600/10" />
                      ))}
                    </div>
                    {p.missing_skills && p.missing_skills.length > 0 ? (
                      <div className="mt-2 text-xs text-amber-200">
                        Missing: {p.missing_skills.slice(0, 3).join(", ")}
                      </div>
                    ) : (
                      <div className="mt-2 text-xs text-emerald-200">Skills match looks strong.</div>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

