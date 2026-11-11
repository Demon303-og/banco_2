from decimal import Decimal
from uuid import UUID
import json

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .db import tx, init_db

app = FastAPI(title="Banco API")


@app.on_event("startup")
def startup():
    init_db()


def auditar(cur, accion: str, detalle: dict):
    cur.execute("INSERT INTO auditoria(accion, detalle) VALUES (%s, %s)",
                (accion, json.dumps(detalle, default=str)))


@app.get("/health")
def health():
    return {"status": "ok"}


class CuentaIn(BaseModel):
    titular: str = Field(min_length=2)
    moneda: str = Field(min_length=3, max_length=3)
    saldo_inicial: Decimal = Field(default=Decimal("0"), ge=0)


@app.post("/api/cuentas", status_code=201)
def crear_cuenta(c: CuentaIn):
    with tx() as cur:
        cur.execute(
            "INSERT INTO cuenta(titular, moneda, saldo) VALUES (%s,%s,%s) RETURNING id",
            (c.titular, c.moneda.upper(), c.saldo_inicial))
        cid = cur.fetchone()[0]
        auditar(cur, "cuenta_creada", {"id": cid, "titular": c.titular})
    return {"id": cid}


@app.get("/api/cuentas")
def listar_cuentas():
    with tx() as cur:
        cur.execute("SELECT id, titular, moneda, saldo FROM cuenta ORDER BY creada_en DESC")
        return [{"id": r[0], "titular": r[1], "moneda": r[2], "saldo": str(r[3])}
                for r in cur.fetchall()]


class TransferenciaIn(BaseModel):
    origen: UUID
    destino: UUID
    monto: Decimal = Field(gt=0)


@app.post("/api/transferencias", status_code=201)
def transferir(t: TransferenciaIn, idempotency_key: str = Header(...)):
    if t.origen == t.destino:
        raise HTTPException(400, "Origen y destino deben ser distintos")
    with tx() as cur:
        # Idempotencia: misma clave => mismo resultado, sin duplicar el movimiento
        cur.execute("SELECT id FROM transaccion WHERE idempotency_key=%s", (idempotency_key,))
        previa = cur.fetchone()
        if previa:
            return {"id": previa[0], "idempotente": True}

        # Bloqueo en orden fijo para evitar deadlocks
        cur.execute("SELECT id, saldo, moneda FROM cuenta WHERE id = ANY(%s) ORDER BY id FOR UPDATE",
                    ([t.origen, t.destino],))
        cuentas = {r[0]: r for r in cur.fetchall()}
        if t.origen not in cuentas or t.destino not in cuentas:
            raise HTTPException(404, "Cuenta no encontrada")
        if cuentas[t.origen][2] != cuentas[t.destino][2]:
            raise HTTPException(400, "Monedas distintas: requiere conversión FX")
        if cuentas[t.origen][1] < t.monto:
            raise HTTPException(422, "Fondos insuficientes")

        moneda = cuentas[t.origen][2]
        cur.execute(
            "INSERT INTO transaccion(idempotency_key, origen, destino, monto, moneda) "
            "VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (idempotency_key, t.origen, t.destino, t.monto, moneda))
        tid = cur.fetchone()[0]
        cur.execute("INSERT INTO asiento(transaccion_id, cuenta_id, tipo, monto) VALUES (%s,%s,'D',%s)",
                    (tid, t.origen, t.monto))
        cur.execute("INSERT INTO asiento(transaccion_id, cuenta_id, tipo, monto) VALUES (%s,%s,'C',%s)",
                    (tid, t.destino, t.monto))
        cur.execute("UPDATE cuenta SET saldo = saldo - %s WHERE id=%s", (t.monto, t.origen))
        cur.execute("UPDATE cuenta SET saldo = saldo + %s WHERE id=%s", (t.monto, t.destino))
        auditar(cur, "transferencia", {"id": tid, "origen": t.origen,
                                       "destino": t.destino, "monto": t.monto})
    return {"id": tid, "idempotente": False}


@app.get("/api/auditoria")
def ver_auditoria():
    with tx() as cur:
        cur.execute("SELECT id, accion, detalle, creado_en FROM auditoria ORDER BY id DESC LIMIT 100")
        return [{"id": r[0], "accion": r[1], "detalle": r[2], "fecha": r[3].isoformat()}
                for r in cur.fetchall()]
