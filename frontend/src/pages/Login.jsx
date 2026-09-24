import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/api";
import { useAuth } from "../context/AuthContext";

const TABS = ["Member Login", "Staff Login", "Sign Up"];

export default function Login() {
  const [tab, setTab] = useState(TABS[0]);
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
  });
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      if (tab === "Sign Up") {
        await api.signup({
          email: form.email,
          password: form.password,
          first_name: form.first_name,
          last_name: form.last_name,
        });
        setMessage("Account created. You can log in now.");
        setTab("Member Login");
      } else if (tab === "Member Login") {
        const { access_token } = await api.login({
          email: form.email,
          password: form.password,
        });
        login(access_token, "member");
        navigate("/account");
      } else {
        const { access_token } = await api.staffLogin({
          email: form.email,
          password: form.password,
        });
        login(access_token, "staff");
        navigate("/staff");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page narrow">
      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? "active" : ""}`}
            onClick={() => {
              setTab(t);
              setError(null);
              setMessage(null);
            }}
          >
            {t}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="card">
        {tab === "Sign Up" && (
          <>
            <label>
              First name
              <input value={form.first_name} onChange={update("first_name")} required />
            </label>
            <label>
              Last name
              <input value={form.last_name} onChange={update("last_name")} required />
            </label>
          </>
        )}
        <label>
          Email
          <input
            type="email"
            value={form.email}
            onChange={update("email")}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={update("password")}
            minLength={8}
            required
          />
        </label>

        {error && <p className="error">{String(error)}</p>}
        {message && <p className="success">{message}</p>}

        <button type="submit" disabled={busy}>
          {busy ? "Working..." : tab}
        </button>
      </form>
    </div>
  );
}
