import React, { useContext, useEffect, useState } from "react";
import { api } from "../api/client.js";
import { AuthContext } from "../auth/AuthContext.jsx";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Card from "../components/ui/Card.jsx";
import SkillTag from "../components/ui/SkillTag.jsx";
import Button from "../components/ui/Button.jsx";
import Spinner from "../components/ui/Spinner.jsx";
import { Link } from "react-router-dom";

export default function MatchesPage() {
  const { user } = useContext(AuthContext);
  const { addToast } = useContext(ToastContext);

  const [loading, setLoading] = useState(true);
  const [teammates, setTeammates] = useState([]);
  const [projects, setProjects] = useState([]);
  const [gapLoading, setGapLoading] = useState(false);
  const [gap, setGap] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function run() {
      setLoading(true);
      try {
        const [tRes, pRes] = await Promise.all([
          api.get("/api/matches/teammates?top=10"),
          api.get("/api/matches/projects?top=10&status=Open"),
        ]);
        if (!mounted) return;
        setTeammates(tRes.data.items || []);
        setProjects(pRes.data.items || []);
      } catch (e) {
        addToast({ type: "error", message: "Could not load matches" });
      } finally {
        if (mounted) setLoading(false);
      }
    }
    run();
    return () => {
      mounted = false;
    };
  }, [addToast]);

  async function analyzeGap(projectId) {
    setGapLoading(true);
    setGap(null);
    try {
      const res = await api.get(`/api/matches/projects/${projectId}/gap`);
      setGap(res.data);
    } catch (e) {
      addToast({ type: "error", message: "Gap analysis failed" });
    } finally {
      setGapLoading(false);
    }
  }

  const onApply = async (projectId) => {
    try {
      await api.post(`/api/projects/${projectId}/apply`, { message: "" });
      addToast({ type: "success", message: "Application submitted" });
    } catch (e) {
      addToast({ type: "error", message: e?.response?.data?.message || "Apply failed" });
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="text-2xl font-bold">Match Recommendations</div>
        <div className="mt-1 text-sm text-slate-300">
          Recommendations use fully local matching: cosine similarity over binary skill vectors.
        </div>
      </Card>

      {loading ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="p-6">
            <div className="text-lg font-bold">Best Teammates</div>
            <div className="mt-3 space-y-3">
              {teammates.slice(0, 8).map((t) => (
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
                      <SkillTag key={s} skill={s} />
                    ))}
                  </div>

                  <div className="mt-3">
                    <Button
                      variant="secondary"
                      as={Link}
                      to={`/chat?type=direct&other_user_id=${t.user.id}`}
                    >
                      Message
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <div className="text-lg font-bold">Best Projects</div>
            <div className="mt-3 space-y-3">
              {projects.slice(0, 8).map((p) => (
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
                    {(p.project.required_skills || []).slice(0, 8).map((s) => (
                      <SkillTag key={s} skill={s} />
                    ))}
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button variant="secondary" onClick={() => analyzeGap(p.project.id)} disabled={gapLoading}>
                      Skill Gap Analyzer
                    </Button>
                    <Button onClick={() => onApply(p.project.id)} disabled={p.project.status !== "Open"}>
                      Apply
                    </Button>
                  </div>

                  {p.missing_skills?.length ? (
                    <div className="mt-2 text-xs text-amber-200">
                      Missing: {p.missing_skills.slice(0, 4).join(", ")}
                    </div>
                  ) : (
                    <div className="mt-2 text-xs text-emerald-200">Looks like a great match.</div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {gapLoading ? (
        <Card className="p-6">
          <div className="flex items-center gap-3 text-sm text-slate-300">
            <Spinner /> Computing skill gap...
          </div>
        </Card>
      ) : gap ? (
        <Card className="p-6">
          <div className="text-lg font-bold">Skill Gap Analyzer</div>
          <div className="mt-2 text-sm text-slate-300">
            Project: <span className="text-slate-100 font-semibold">{gap.project_id}</span>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <div className="text-sm font-semibold text-slate-200">Missing skills</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {(gap.missing_skills || []).map((s) => (
                  <SkillTag key={s} skill={s} className="bg-amber-600/20 text-amber-200 ring-1 ring-amber-400/30" />
                ))}
                {(gap.missing_skills || []).length === 0 ? <div className="text-sm text-emerald-200">No missing skills.</div> : null}
              </div>
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-200">Matched skills</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {(gap.matched_skills || []).map((s) => (
                  <SkillTag key={s} skill={s} />
                ))}
              </div>
            </div>
          </div>
        </Card>
      ) : null}
    </div>
  );
}

