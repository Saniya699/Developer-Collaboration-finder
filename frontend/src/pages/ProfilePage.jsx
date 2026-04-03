import React, { useContext, useEffect, useMemo, useState } from "react";
import { AuthContext } from "../auth/AuthContext.jsx";
import { api } from "../api/client.js";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Card from "../components/ui/Card.jsx";
import Button from "../components/ui/Button.jsx";
import Input from "../components/ui/Input.jsx";
import SkillTag from "../components/ui/SkillTag.jsx";
import Spinner from "../components/ui/Spinner.jsx";

function uniqSkills(skills) {
  const seen = new Set();
  const out = [];
  for (const s of skills || []) {
    const v = (s || "").trim();
    const k = v.toLowerCase();
    if (!v || seen.has(k)) continue;
    seen.add(k);
    out.push(v);
  }
  return out;
}

export default function ProfilePage() {
  const { user, reloadMe } = useContext(AuthContext);
  const { addToast } = useContext(ToastContext);

  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [skillsText, setSkillsText] = useState("");
  const [experience_level, setExperience] = useState("Beginner");
  const [availability, setAvailability] = useState("Part-time");
  const [github_url, setGithub] = useState("");

  const skills = useMemo(
    () =>
      uniqSkills(
        (skillsText || "")
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      ),
    [skillsText],
  );

  const [saving, setSaving] = useState(false);

  // Resume analyzer state
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeResult, setResumeResult] = useState(null);

  useEffect(() => {
    if (!user) return;
    setName(user.name || "");
    setBio(user.bio || "");
    setSkillsText((user.skills || []).join(", "));
    setExperience(user.experience_level || "Beginner");
    setAvailability(user.availability || "Part-time");
    setGithub(user.github_url || "");
  }, [user]);

  async function onSave() {
    setSaving(true);
    try {
      await api.put("/api/profile", {
        name,
        bio,
        skills,
        experience_level,
        availability,
        github_url: github_url || null,
      });
      addToast({ type: "success", message: "Profile saved" });
      await reloadMe();
    } catch (e) {
      const msg = e?.response?.data?.message || "Could not save profile";
      addToast({ type: "error", message: msg });
    } finally {
      setSaving(false);
    }
  }

  async function onAnalyzeResume(file) {
    setResumeLoading(true);
    setResumeResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api.post("/api/resume/analyze", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResumeResult(res.data);
    } catch (e) {
      addToast({ type: "error", message: e?.response?.data?.message || "Resume analysis failed" });
    } finally {
      setResumeLoading(false);
    }
  }

  async function onApplySuggestedSkills() {
    if (!resumeResult?.suggested_skills) return;
    const merged = uniqSkills([...(skills || []), ...(resumeResult.suggested_skills || [])]);
    setSkillsText(merged.join(", "));
    addToast({ type: "info", message: "Suggested skills added to your input. Save to persist." });
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-2xl font-bold">Your Profile</div>
            <div className="mt-1 text-sm text-slate-300">
              Rating: {user?.profile_rating_avg != null ? user.profile_rating_avg : "Not yet rated"}
            </div>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={reloadMe} disabled={saving}>
              Refresh
            </Button>
            <Button onClick={onSave} disabled={saving}>
              {saving ? "Saving..." : "Save Profile"}
            </Button>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input label="Name" value={name} onChange={setName} />
          <Input label="GitHub URL (optional)" value={github_url} onChange={setGithub} placeholder="https://github.com/..." />

          <label className="block md:col-span-2">
            <div className="mb-2 text-sm font-semibold text-slate-200">Bio</div>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              className="h-24 w-full resize-none rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
              placeholder="A short bio to help others understand your goals."
            />
          </label>

          <div className="md:col-span-2">
            <Input
              label="Skills (comma-separated)"
              value={skillsText}
              onChange={setSkillsText}
              placeholder="Python, React, SQL"
            />
            <div className="mt-3 flex flex-wrap gap-2">
              {(skills || []).map((s) => (
                <SkillTag key={s} skill={s} />
              ))}
              {(skills || []).length === 0 ? <div className="text-sm text-slate-400">Add at least one skill for better matching.</div> : null}
            </div>
          </div>

          <label className="block">
            <div className="mb-2 text-sm font-semibold text-slate-200">Experience level</div>
            <select
              value={experience_level}
              onChange={(e) => setExperience(e.target.value)}
              className="w-full rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
            >
              <option>Beginner</option>
              <option>Intermediate</option>
              <option>Advanced</option>
            </select>
          </label>

          <label className="block">
            <div className="mb-2 text-sm font-semibold text-slate-200">Availability</div>
            <select
              value={availability}
              onChange={(e) => setAvailability(e.target.value)}
              className="w-full rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
            >
              <option>Part-time</option>
              <option>Full-time</option>
            </select>
          </label>
        </div>
      </Card>

      <Card className="p-6">
        <div className="text-lg font-bold">Resume Analyzer (Local PDF)</div>
        <div className="mt-1 text-sm text-slate-300">Upload a PDF resume to extract skill keywords locally, then add them to your profile.</div>

        <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-end">
          <label className="block w-full">
            <div className="mb-2 text-sm font-semibold text-slate-200">PDF Resume</div>
            <input
              type="file"
              accept="application/pdf"
              className="w-full cursor-pointer rounded-xl bg-white/5 px-4 py-2 text-sm ring-1 ring-white/10"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) onAnalyzeResume(file);
              }}
              disabled={resumeLoading}
            />
          </label>
          <Button
            variant="secondary"
            disabled={!resumeResult?.suggested_skills?.length}
            onClick={onApplySuggestedSkills}
          >
            Add Suggested Skills
          </Button>
        </div>

        {resumeLoading ? (
          <div className="mt-4 flex items-center gap-3 text-sm text-slate-300">
            <Spinner />
            Analyzing resume...
          </div>
        ) : resumeResult ? (
          <div className="mt-4">
            <div className="text-sm font-semibold text-slate-200">Suggested skills</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {(resumeResult.suggested_skills || []).map((s) => (
                <SkillTag key={s} skill={s} />
              ))}
            </div>
            {resumeResult.missing_skills_for_profile?.length ? (
              <div className="mt-3 text-sm text-amber-200">
                Missing (not on your profile): {resumeResult.missing_skills_for_profile.slice(0, 8).join(", ")}
              </div>
            ) : (
              <div className="mt-3 text-sm text-emerald-200">Your resume matches your profile well.</div>
            )}
          </div>
        ) : null}
      </Card>
    </div>
  );
}

