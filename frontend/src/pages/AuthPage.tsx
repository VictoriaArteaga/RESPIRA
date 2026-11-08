import { useState, type FormEvent } from "react";
import { Activity, Eye, EyeOff, Lock, Mail, UserPlus } from "lucide-react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Button } from "../components/common/Button";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../services/api";

type Mode = "login" | "register";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Field = "email" | "password" | "confirmation";
interface Problem {
  field: Field;
  message: string;
}

// Misma política que el servidor (12–128 caracteres, al menos una letra y un número); el servidor valida de nuevo.
function validate(
  mode: Mode,
  email: string,
  password: string,
  confirmation: string,
): Problem | null {
  if (!email.trim())
    return { field: "email", message: "Ingresa tu correo electrónico." };
  if (!EMAIL_PATTERN.test(email.trim()))
    return { field: "email", message: "Ingresa un correo electrónico válido." };
  if (!password)
    return { field: "password", message: "Ingresa tu contraseña." };
  if (mode === "login") return null;
  if (!confirmation)
    return { field: "confirmation", message: "Confirma tu contraseña." };
  if (password.length < 12 || password.length > 128)
    return {
      field: "password",
      message: "La contraseña debe tener entre 12 y 128 caracteres.",
    };
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password))
    return {
      field: "password",
      message: "La contraseña debe incluir al menos una letra y un número.",
    };
  if (password !== confirmation)
    return { field: "confirmation", message: "Las contraseñas no coinciden." };
  return null;
}

const fieldClass =
  "flex h-12 items-center gap-2.5 rounded-xl border border-[#D5E2EA] bg-[#F4F8FA] pl-3.5 text-[#5B6E79] focus-within:border-respira-blue-dark focus-within:outline focus-within:outline-2 focus-within:outline-respira-blue-dark";
const inputClass =
  "h-full min-w-0 flex-1 bg-transparent text-sm text-respira-text outline-none placeholder:text-[#6B7C86]";
const helpClass = "text-xs text-[#5B6E79]";

export function AuthPage({ mode }: { mode: Mode }) {
  const { status, login, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invalidField, setInvalidField] = useState<Field | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") return <Navigate to="/dashboard" replace />;

  const isLogin = mode === "login";
  const passwordType = showPassword ? "text" : "password";
  const EyeIcon = showPassword ? EyeOff : Eye;

  const fieldClassFor = (field: Field, padding: string) =>
    `${fieldClass} ${padding} ${invalidField === field ? "border-rose-500 bg-rose-50/60" : ""}`;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice(null);
    const problem = validate(mode, email, password, confirmation);
    if (problem) {
      setError(problem.message);
      setInvalidField(problem.field);
      return;
    }

    setError(null);
    setInvalidField(null);
    setSubmitting(true);
    try {
      if (isLogin) {
        await login({ email: email.trim(), password });
        navigate("/dashboard", { replace: true });
      } else {
        await register({ email: email.trim(), password });
        setNotice(
          "Solicitud enviada. Un administrador debe aprobar tu cuenta antes de que puedas iniciar sesión.",
        );
        setPassword("");
        setConfirmation("");
        navigate("/login", { replace: true });
      }
    } catch (caught) {
      setInvalidField(null);
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Ocurrió un error inesperado.",
      );
    } finally {
      setSubmitting(false);
      setPassword("");
    }
  }

  const visibilityToggle = (
    <button
      type="button"
      onClick={() => setShowPassword((current) => !current)}
      aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
      className="flex h-11 w-11 flex-none items-center justify-center rounded-[10px] text-[#5B6E79] hover:text-respira-blue-dark"
    >
      <EyeIcon size={20} aria-hidden="true" />
    </button>
  );

  const feedback = (
    <>
      {error && (
        <p
          className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700"
          role="alert"
        >
          {error}
        </p>
      )}
      {notice && (
        <p
          className="rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
          role="status"
        >
          {notice}
        </p>
      )}
    </>
  );

  const submitClass =
    "mt-1.5 h-[50px] w-full rounded-xl text-base font-bold shadow-[0_4px_14px_rgba(49,95,125,0.25)]";

  if (isLogin) {
    return (
      <div className="auth-shell flex min-h-screen items-center justify-center px-5 py-8 text-respira-text">
        <main className="auth-scale w-full max-w-md overflow-hidden rounded-[20px] border border-respira-border bg-white shadow-[0_12px_36px_rgba(36,59,74,0.10)]">
          <div className="h-[5px] bg-gradient-to-r from-respira-blue to-[#6F9BB5]" />
          <div className="flex flex-col items-center px-10 pb-9 pt-9">
            <div
              role="img"
              aria-label="Logo de RESPIRA"
              className="flex h-[68px] w-[68px] items-center justify-center rounded-[20px] bg-respira-blue text-[34px] font-black text-white shadow-[0_6px_16px_rgba(49,95,125,0.25)]"
            >
              R
            </div>
            <p className="mt-[18px] text-[13px] font-bold tracking-[0.16em] text-respira-blue">
              RESPIRA
            </p>
            <h1 className="mt-1.5 text-[30px] font-extrabold tracking-tight">
              Bienvenido
            </h1>
            <p className="mt-2 text-center text-sm leading-6 text-[#4F626D]">
              Ingresa tus credenciales para acceder al sistema de monitoreo de
              infecciones respiratorias agudas en Nariño.
            </p>

            <form
              className="mt-7 flex w-full flex-col gap-[18px]"
              onSubmit={(event) => void handleSubmit(event)}
              noValidate
            >
              <div className="flex flex-col gap-1.5">
                <label htmlFor="email" className="text-sm font-semibold">
                  Correo electrónico
                </label>
                <div className={fieldClassFor("email", "pr-3.5")}>
                  <Mail size={19} aria-hidden="true" className="flex-none" />
                  <input
                    id="email"

                    aria-invalid={invalidField === "email"}
                    className={inputClass}
                    type="email"
                    autoComplete="email"
                    maxLength={254}
                    placeholder="tu@correo.com"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="password" className="text-sm font-semibold">
                  Contraseña
                </label>
                <div className={fieldClassFor("password", "pr-1.5")}>
                  <Lock size={19} aria-hidden="true" className="flex-none" />
                  <input
                    id="password"

                    aria-invalid={invalidField === "password"}
                    className={inputClass}
                    type={passwordType}
                    autoComplete="current-password"
                    maxLength={128}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                  {visibilityToggle}
                </div>
              </div>

              {feedback}

              <Button
                className={submitClass}
                type="submit"
                disabled={submitting}
              >
                {submitting ? "Procesando..." : "Iniciar sesión"}
              </Button>
            </form>

            <p className="mt-[22px] text-center text-sm text-[#4F626D]">
              ¿No tienes cuenta?{" "}
              <Link
                className="font-bold text-respira-blue hover:text-respira-blue-dark"
                to="/register"
              >
                Regístrate
              </Link>
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="auth-shell flex min-h-screen items-center justify-center px-5 py-8 text-respira-text">
      <main className="auth-scale flex w-full max-w-[960px] flex-wrap overflow-hidden rounded-[20px] border border-respira-border bg-white shadow-[0_12px_36px_rgba(36,59,74,0.10)]">
        <aside className="flex min-w-0 flex-[1_1_300px] flex-col justify-between gap-5 bg-gradient-to-br from-respira-blue to-respira-blue-dark px-11 py-12 text-white">
          <div className="flex flex-col gap-5">
            <UserPlus size={40} aria-hidden="true" />
            <h2 className="text-[28px] font-extrabold leading-tight tracking-tight">
              Únete a RESPIRA
            </h2>
            <p
              className="hyphens-auto text-justify text-[15px] leading-relaxed text-[#E6EFF5]"
              lang="es"
            >
              Solicita tu cuenta para consultar el monitoreo epidemiológico de
              infecciones respiratorias agudas en Nariño. Un administrador
              revisará y aprobará tu solicitud antes de que puedas iniciar
              sesión.
            </p>
          </div>
          <div className="flex items-center gap-2.5 text-sm font-semibold">
            <Activity size={20} aria-hidden="true" className="flex-none" />
            <span>Sistema de alerta temprana IRA</span>
          </div>
        </aside>

        <section className="flex min-w-0 flex-[999_1_420px] flex-col px-12 pb-10 pt-12">
          <h1 className="text-[30px] font-extrabold tracking-tight">
            Crear cuenta
          </h1>
          <p className="mt-2 text-sm text-[#4F626D]">
            Completa los campos para enviar tu solicitud.
          </p>

          <form
            className="mt-7 flex flex-col gap-[18px]"
            onSubmit={(event) => void handleSubmit(event)}
            noValidate
          >
            <div className="flex flex-col gap-1.5">
              <label htmlFor="email" className="text-sm font-semibold">
                Correo electrónico
              </label>
              <div className={fieldClassFor("email", "pr-3.5")}>
                <Mail size={19} aria-hidden="true" className="flex-none" />
                <input
                  id="email"

                  aria-invalid={invalidField === "email"}
                  className={inputClass}
                  type="email"
                  autoComplete="email"
                  maxLength={254}
                  placeholder="tu@correo.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </div>
              <span className={helpClass}>
                Usaremos este correo para notificarte cuando tu cuenta sea
                aprobada.
              </span>
            </div>

            <div className="flex flex-wrap gap-[18px]">
              <div className="flex min-w-0 flex-[1_1_220px] flex-col gap-1.5">
                <label htmlFor="password" className="text-sm font-semibold">
                  Contraseña
                </label>
                <div className={fieldClassFor("password", "pr-1.5")}>
                  <Lock size={19} aria-hidden="true" className="flex-none" />
                  <input
                    id="password"

                    aria-invalid={invalidField === "password"}
                    className={inputClass}
                    type={passwordType}
                    autoComplete="new-password"
                    maxLength={128}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                  {visibilityToggle}
                </div>
                <span className={helpClass}>
                  Mínimo 12 caracteres, con al menos una letra y un número.
                </span>
              </div>

              <div className="flex min-w-0 flex-[1_1_220px] flex-col gap-1.5">
                <label htmlFor="confirmation" className="text-sm font-semibold">
                  Confirmar contraseña
                </label>
                <div className={fieldClassFor("confirmation", "pr-1.5")}>
                  <Lock size={19} aria-hidden="true" className="flex-none" />
                  <input
                    id="confirmation"

                    aria-invalid={invalidField === "confirmation"}
                    className={inputClass}
                    type={passwordType}
                    autoComplete="new-password"
                    maxLength={128}
                    placeholder="••••••••••••"
                    value={confirmation}
                    onChange={(event) => setConfirmation(event.target.value)}
                    required
                  />
                  {visibilityToggle}
                </div>
                <span className={helpClass}>
                  Debe coincidir con la contraseña anterior.
                </span>
              </div>
            </div>

            {feedback}

            <Button className={submitClass} type="submit" disabled={submitting}>
              {submitting ? "Procesando..." : "Solicitar cuenta"}
            </Button>
          </form>

          <p className="mt-[22px] text-center text-sm text-[#4F626D]">
            ¿Ya tienes cuenta?{" "}
            <Link
              className="font-bold text-respira-blue hover:text-respira-blue-dark"
              to="/login"
            >
              Inicia sesión
            </Link>
          </p>
        </section>
      </main>
    </div>
  );
}
