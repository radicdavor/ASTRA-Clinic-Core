import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/client";

export function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo.admin@astra.local");
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prijava nije uspjela");
    }
  }

  return (
    <div className="login-page">
      <form className="login-panel" onSubmit={submit}>
        <div className="brand large">
          <div className="brand-mark">A</div>
          <div>
            <strong>ASTRA Clinic Core</strong>
            <span>Operativna jezgra klinike</span>
          </div>
        </div>
        <label>
          E-pošta
          <input value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label>
          Lozinka
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="primary">Prijava</button>
      </form>
    </div>
  );
}
