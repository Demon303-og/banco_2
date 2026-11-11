# Banco – Plataforma base (React + FastAPI + PostgreSQL) para OpenShift

## Qué incluye
- `frontend/`  React (Vite) servido por nginx sin privilegios (puerto 8080)
- `backend/`   API FastAPI: cuentas, transferencias con ledger de doble entrada,
               idempotencia (`Idempotency-Key`) y auditoría inmutable
- `openshift/` Secret, PostgreSQL con PVC, Deployments, Services, Route TLS y NetworkPolicies
- `docker-compose.yml` para desarrollo local

## Local
    docker compose up --build
    # Web: http://localhost:8080   API docs: http://localhost:8000/docs

## Despliegue en OpenShift
    oc login --token=<TOKEN> --server=<API_URL>
    oc new-project banco                      # si cambias el nombre, ajusta las imágenes en openshift/*.yaml

    oc new-build --name=backend  --binary --strategy=docker
    oc start-build backend  --from-dir=backend  --follow
    oc new-build --name=frontend --binary --strategy=docker
    oc start-build frontend --from-dir=frontend --follow

    # Edita openshift/00-secret.yaml (contraseña) y luego:
    oc apply -f openshift/
    oc get route frontend

## Pendiente para producción bancaria
- Autenticación OIDC + MFA (Red Hat SSO) y autorización por rol en la API
- Secretos en Vault / External Secrets (no en YAML)
- Service Mesh con mTLS, API Gateway (3scale), WAF
- PostgreSQL HA con operador (CloudNativePG/Crunchy), backups con PITR
- Migraciones (Alembic), pruebas, pipeline Tekton + Argo CD, escaneo con ACS
- Separar en microservicios y Kafka para eventos cuando el dominio lo requiera
- Cumplimiento: PCI DSS, ISO 27001, SOX, GDPR, residencia de datos, DORA
