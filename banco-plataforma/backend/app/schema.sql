CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS cuenta (
  id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titular  TEXT NOT NULL,
  moneda   CHAR(3) NOT NULL,                       -- ISO 4217
  saldo    NUMERIC(20,4) NOT NULL DEFAULT 0 CHECK (saldo >= 0),
  creada_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transaccion (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  idempotency_key TEXT NOT NULL UNIQUE,
  origen          UUID NOT NULL REFERENCES cuenta(id),
  destino         UUID NOT NULL REFERENCES cuenta(id),
  monto           NUMERIC(20,4) NOT NULL CHECK (monto > 0),
  moneda          CHAR(3) NOT NULL,
  creada_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ledger de doble entrada: nunca se edita ni se borra
CREATE TABLE IF NOT EXISTS asiento (
  id             BIGSERIAL PRIMARY KEY,
  transaccion_id UUID NOT NULL REFERENCES transaccion(id),
  cuenta_id      UUID NOT NULL REFERENCES cuenta(id),
  tipo           CHAR(1) NOT NULL CHECK (tipo IN ('D','C')),
  monto          NUMERIC(20,4) NOT NULL CHECK (monto > 0),
  creado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auditoria (
  id        BIGSERIAL PRIMARY KEY,
  accion    TEXT NOT NULL,
  detalle   JSONB NOT NULL,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION inmutable() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'Tabla inmutable: % no permitido', TG_OP; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS asiento_inmutable ON asiento;
CREATE TRIGGER asiento_inmutable BEFORE UPDATE OR DELETE ON asiento
  FOR EACH ROW EXECUTE FUNCTION inmutable();
DROP TRIGGER IF EXISTS auditoria_inmutable ON auditoria;
CREATE TRIGGER auditoria_inmutable BEFORE UPDATE OR DELETE ON auditoria
  FOR EACH ROW EXECUTE FUNCTION inmutable();
