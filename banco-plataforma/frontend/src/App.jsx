import { useEffect, useState } from "react";

const api = async (path, opts = {}) => {
  const r = await fetch(path, { ...opts, headers: { "Content-Type": "application/json", ...(opts.headers || {}) } });
  const data = await r.json();
  if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Error en la solicitud");
  return data;
};

export default function App() {
  const [cuentas, setCuentas] = useState([]);
  const [auditoria, setAuditoria] = useState([]);
  const [msg, setMsg] = useState("");
  const [nueva, setNueva] = useState({ titular: "", moneda: "USD", saldo_inicial: "0" });
  const [tr, setTr] = useState({ origen: "", destino: "", monto: "" });

  const cargar = async () => {
    setCuentas(await api("/api/cuentas"));
    setAuditoria(await api("/api/auditoria"));
  };
  useEffect(() => { cargar().catch((e) => setMsg(e.message)); }, []);

  const crear = async (e) => {
    e.preventDefault();
    try { await api("/api/cuentas", { method: "POST", body: JSON.stringify(nueva) }); setMsg("Cuenta creada"); cargar(); }
    catch (err) { setMsg(err.message); }
  };

  const transferir = async (e) => {
    e.preventDefault();
    try {
      await api("/api/transferencias", {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify(tr),
      });
      setMsg("Transferencia realizada"); cargar();
    } catch (err) { setMsg(err.message); }
  };

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 900, margin: "2rem auto", padding: "0 1rem" }}>
      <h1>Banco – Panel</h1>
      {msg && <p><strong>{msg}</strong></p>}

      <h2>Nueva cuenta</h2>
      <form onSubmit={crear}>
        <input placeholder="Titular" value={nueva.titular} onChange={(e) => setNueva({ ...nueva, titular: e.target.value })} />
        <input placeholder="Moneda" maxLength={3} value={nueva.moneda} onChange={(e) => setNueva({ ...nueva, moneda: e.target.value })} />
        <input placeholder="Saldo inicial" value={nueva.saldo_inicial} onChange={(e) => setNueva({ ...nueva, saldo_inicial: e.target.value })} />
        <button>Crear</button>
      </form>

      <h2>Cuentas</h2>
      <table border="1" cellPadding="6">
        <thead><tr><th>ID</th><th>Titular</th><th>Moneda</th><th>Saldo</th></tr></thead>
        <tbody>{cuentas.map((c) => (<tr key={c.id}><td>{c.id}</td><td>{c.titular}</td><td>{c.moneda}</td><td>{c.saldo}</td></tr>))}</tbody>
      </table>

      <h2>Transferir</h2>
      <form onSubmit={transferir}>
        <input placeholder="ID origen" value={tr.origen} onChange={(e) => setTr({ ...tr, origen: e.target.value })} />
        <input placeholder="ID destino" value={tr.destino} onChange={(e) => setTr({ ...tr, destino: e.target.value })} />
        <input placeholder="Monto" value={tr.monto} onChange={(e) => setTr({ ...tr, monto: e.target.value })} />
        <button>Enviar</button>
      </form>

      <h2>Auditoría</h2>
      <ul>{auditoria.map((a) => (<li key={a.id}>{a.fecha} – {a.accion}</li>))}</ul>
    </main>
  );
}
