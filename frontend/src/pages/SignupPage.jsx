import React, { useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../auth/AuthContext.jsx";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Input from "../components/ui/Input.jsx";

export default function SignupPage() {
  const navigate = useNavigate();
  const { signup } = useContext(AuthContext);
  const { addToast } = useContext(ToastContext);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [bio, setBio] = useState("");
  const [skillsText, setSkillsText] = useState("");
  const [experience_level, setExperience] = useState("Beginner");
  const [availability, setAvailability] = useState("Part-time");
  const [github_url, setGithub] = useState("");
  const [loading, setLoading] = useState(false);

  const skills = useMemo(() => {
    return (skillsText || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }, [skillsText]);

  async function onSubmit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await signup({
        name,
        email,
        password,
        bio,
        skills,
        experience_level,
        availability,
        github_url: github_url || null,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const msg = err?.response?.data?.message || "Signup failed";
      addToast({ type: "error", message: msg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <Card className="p-6">
        <div className="text-2xl font-bold">Create your profile</div>
        <div className="mt-1 text-sm text-slate-300">Build skills and availability to get smart matches.</div>

        <form className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2" onSubmit={onSubmit}>
          <div className="md:col-span-1">
            <Input label="Name" value={name} onChange={setName} placeholder="Your name" />
          </div>
          <div className="md:col-span-1">
            <Input label="Email" value={email} onChange={setEmail} placeholder="you@example.com" type="email" />
          </div>
          <div className="md:col-span-1">
            <Input label="Password" value={password} onChange={setPassword} placeholder="••••••••" type="password" />
          </div>
          <div className="md:col-span-1">
            <Input label="GitHub (optional)" value={github_url} onChange={setGithub} placeholder="https://github.com/..." />
          </div>

          <div className="md:col-span-2">
            <label className="block">
              <div className="mb-2 text-sm font-semibold text-slate-200">Bio</div>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="What do you want to build? What are you excited about?"
                className="h-24 w-full resize-none rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-indigo-500/40"
              />
            </label>
          </div>

          <div className="md:col-span-2">
            <Input
              label="Skills (comma-separated)"
              value={skillsText}
              onChange={setSkillsText}
              placeholder="Python, React, SQL"
            />
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

          <div className="md:col-span-2">
            <Button className="w-full" disabled={loading} type="submit">
              {loading ? "Creating..." : "Create account"}
            </Button>
          </div>
        </form>
      </Card>

      <div className="mt-4 text-center text-sm text-slate-400">
        Already have an account?{" "}
        <a className="text-indigo-300 hover:underline" href="/login">
          Sign in
        </a>
      </div>
    </div>
  );
}

