import React, { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../auth/AuthContext.jsx";
import { ToastContext } from "../components/toast/ToastContext.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Input from "../components/ui/Input.jsx";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);
  const { addToast } = useContext(ToastContext);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const msg = err?.response?.data?.message || "Login failed";
      addToast({ type: "error", message: msg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-10">
      <Card className="p-6">
        <div className="text-2xl font-bold">Welcome back</div>
        <div className="mt-2 text-sm text-slate-300">Login to find collaborators and projects.</div>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <Input label="Email" value={email} onChange={setEmail} type="email" placeholder="you@example.com" />
          <Input label="Password" value={password} onChange={setPassword} type="password" placeholder="••••••••" />

          <Button className="w-full" disabled={loading} type="submit">
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <div className="mt-4 text-sm text-slate-300">
          No account?{" "}
          <a className="text-indigo-300 hover:underline" href="/signup">
            Create one
          </a>
        </div>
      </Card>
    </div>
  );
}

