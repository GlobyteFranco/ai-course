# Guia de despliegue con Docker en la nube

Esta guia explica, paso a paso, como desplegar aplicaciones Dockerizadas de forma general y portable en **AWS**, **GCP** y **Azure**.  
El enfoque esta pensado para proyectos tipo API/web app/RAG y aplica tanto a staging como a produccion.

---

## 1) Objetivo

Definir un proceso estandar para:

1. Empaquetar una aplicacion con Docker.
2. Publicar la imagen en un registry.
3. Desplegar en servicios administrados de nube.
4. Operar con seguridad, monitoreo y rollback.

---

## 2) Principios de arquitectura (vendor-agnostic)

- **Contenedor inmutable**: la imagen no se modifica en runtime.
- **Config por variables de entorno**: sin hardcodear secretos.
- **Estado fuera del contenedor**: DB, archivos y vectores en servicios persistentes.
- **Deploy repetible**: CI/CD + tags de imagen inmutables.
- **Observabilidad desde el dia 1**: logs, metricas, alertas.

Arquitectura base recomendada:

- Servicio app (frontend/API/worker)
- Base de datos gestionada
- Object storage
- Secret manager
- Balanceador HTTPS
- Logs + metricas + alertas

---

## 3) Prerrequisitos

Antes de desplegar en cualquier nube:

- Docker instalado (`docker --version`)
- Docker Compose instalado (`docker compose version`)
- Git y repositorio funcional
- Cuenta cloud activa (AWS/GCP/Azure)
- CLI cloud autenticada (aws/gcloud/az)
- Dominio (opcional, recomendado en prod)
- Pipeline CI/CD (GitHub Actions, GitLab CI, Azure DevOps, etc.)

---

## 4) Contenerizacion correcta

## 4.1 Dockerfile (buenas practicas)

- Base image minima (`python:3.11-slim`, `node:20-alpine`, etc.)
- Instalar dependencias con cache controlado
- Usuario no root
- Healthcheck
- Solo puertos necesarios
- `.dockerignore` bien definido

Ejemplo (Python + Streamlit):

```Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m appuser
USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "apps/rag_app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

## 4.2 Docker Compose para local/staging

Recomendado para validar arquitectura antes de nube:

- `app`
- `db` (si aplica)
- `cache` (si aplica)
- `ollama`/servicio LLM local (si aplica)

Usa volumenes para persistencia y `.env` para configuracion local.

---

## 5) Gestion de configuracion y secretos

Separar claramente:

- **Variables no sensibles**: entorno, puertos, flags.
- **Secretos**: claves API, passwords, tokens.

Nunca:

- Guardar secretos en imagen Docker.
- Commitear `.env` con secretos reales.
- Escribir secretos en logs.

Servicios recomendados por nube:

- AWS: Secrets Manager / SSM Parameter Store
- GCP: Secret Manager
- Azure: Key Vault

---

## 6) Estrategia de versionado y promocion

No desplegar solo con `latest` en produccion.

Tags sugeridos:

- `app:1.0.0`
- `app:1.0.0-rc1`
- `app:sha-<commit>`

Flujo recomendado:

1. `dev` -> build/test
2. `staging` -> validacion funcional
3. `prod` -> canary o rolling update

---

## 7) CI/CD minimo recomendado

Pipeline estandar:

1. Lint + tests
2. Build Docker image
3. Scan de vulnerabilidades
4. Push al registry
5. Deploy a staging
6. Smoke tests
7. Aprobacion (manual o automatica)
8. Deploy a produccion

Herramientas utiles:

- Trivy / Grype (scan de imagen)
- GitHub Actions/GitLab CI/Azure DevOps
- OPA/Conftest (policy checks, opcional)

---

## 8) Despliegue en AWS

## 8.1 Opciones de servicio

- **ECS Fargate** (recomendado para empezar sin administrar nodos)
- **EKS** (si ya operan Kubernetes)
- **App Runner** (simple para apps web/API)
- **EC2 + Docker Compose** (menos recomendado para prod moderna)
- **ECS/EKS + Amazon Bedrock** (para apps de IA generativa sin alojar modelos propios)
- **ECS/EKS + Bedrock Agents / Agent Core** (para orquestacion de agentes con tools y guardrails)

## 8.2 Paso a paso (ECS Fargate)

1. Crear repositorio en **ECR**.
2. Build + push de imagen a ECR.
3. Crear **Task Definition** (CPU/RAM/puerto/env/secrets).
4. Crear **ECS Service** sobre Fargate.
5. Exponer con **ALB** + HTTPS (certificado en ACM).
6. Configurar autoscaling del servicio.
7. Enviar logs a **CloudWatch Logs**.
8. Crear alertas en CloudWatch + SNS.

## 8.3 Servicios complementarios

- DB: RDS/Aurora
- Archivos: S3
- Secretos: Secrets Manager
- DNS: Route53
- CDN/WAF: CloudFront + AWS WAF

## 8.4 Enfoque AWS con Amazon Bedrock (recomendado para GenAI)

Cuando tu aplicacion necesita capacidades LLM y quieres reducir carga operativa de inferencia, un patron comun es:

- Aplicacion en **ECS Fargate** (o EKS) como capa de negocio.
- Inferencia y embeddings en **Amazon Bedrock**.
- Base de conocimiento/vector en servicio gestionado (OpenSearch Serverless, Aurora pgvector, etc.).
- Seguridad con IAM + VPC endpoints + Secrets Manager.

Flujo recomendado:

1. Mantener tu app Docker en ECR y desplegarla en ECS/EKS.
2. Dar permisos IAM minimos al task role para `bedrock:InvokeModel` y/o `bedrock:InvokeModelWithResponseStream`.
3. Configurar region/modelo Bedrock en variables de entorno (sin hardcodear).
4. Centralizar prompts y politicas (guardrails) de forma versionada.
5. Registrar trazas y metricas de latencia/costo por modelo en CloudWatch.
6. Aplicar limites de uso (throttling, retries con backoff, presupuesto por entorno).

Buenas practicas especificas:

- Separar modelos por entorno (`dev`, `staging`, `prod`) cuando sea posible.
- Medir costo por request y por feature, no solo por servicio.
- Definir fallback de modelo (ejemplo: modelo premium -> modelo costo-eficiente).
- Activar red privada hacia servicios AWS (VPC endpoints) en entornos sensibles.

## 8.5 Enfoque AWS con Bedrock Agents y/o Agent Core

Si tu caso es un asistente que usa herramientas (APIs, SQL, RAG, workflows), el enfoque de agentes reduce logica manual en la app.

Arquitectura sugerida:

- Front/API containerizada en ECS/EKS.
- Capa de agente en **Amazon Bedrock Agents** (o funcionalidad equivalente de **Agent Core**, segun disponibilidad de tu cuenta/region).
- Tooling via Lambda/APIs internas.
- Datos y memoria en servicios gestionados (S3, DynamoDB, Aurora/OpenSearch segun caso).

Paso a paso recomendado:

1. Definir instrucciones del agente (rol, objetivos, limites y politicas de seguridad).
2. Registrar tools/acciones permitidas (Lambda, API Gateway o servicios internos).
3. Conectar knowledge base (si aplica) para grounding.
4. Configurar IAM least-privilege para que el agente solo invoque tools autorizadas.
5. Versionar agente y promover cambios de `staging` a `prod` con pruebas de regresion.
6. Integrar trazabilidad: logs de invocacion, errores de tools y tiempos de respuesta.
7. Aplicar guardrails de contenido y controles de salida para minimizar riesgo.

Patrones operativos:

- **Human-in-the-loop** para acciones sensibles (pagos, borrados, cambios de estado criticos).
- **Tool allowlist** estricta: el agente no debe tener acceso abierto a todo.
- **Timeouts y circuit breakers** en tools para evitar cascadas de fallos.
- **Canary de versiones de agente** antes de rollout total.

Nota practica:

Si tu cuenta no muestra "Agent Core" como servicio independiente, aplica el mismo enfoque usando **Bedrock Agents** + servicios de integracion (Lambda/API Gateway/EventBridge). El principio arquitectonico es el mismo: separar capa de orquestacion agente de la capa de aplicacion Docker.

---

## 9) Despliegue en GCP

## 9.1 Opciones de servicio

- **Cloud Run** (recomendado para contenedores serverless)
- **GKE** (Kubernetes)
- **Compute Engine + Docker** (mas operativo/manual)

## 9.2 Paso a paso (Cloud Run)

1. Crear **Artifact Registry**.
2. Build + push de imagen al registry.
3. Deploy en **Cloud Run** (puerto, memoria, concurrencia).
4. Configurar variables y secretos (Secret Manager).
5. Configurar dominio custom y TLS.
6. Ajustar min/max instances y autoscaling.
7. Activar Cloud Logging + Cloud Monitoring.
8. Definir alertas y uptime checks.

## 9.3 Servicios complementarios

- DB: Cloud SQL / AlloyDB / Firestore
- Archivos: Cloud Storage
- Secretos: Secret Manager
- Seguridad edge: Cloud Armor + Cloud CDN

---

## 10) Despliegue en Azure

## 10.1 Opciones de servicio

- **Azure Container Apps** (recomendado para microservicios/app web)
- **AKS** (Kubernetes)
- **App Service for Containers**
- **VM + Docker** (mas carga operativa)

## 10.2 Paso a paso (Azure Container Apps)

1. Crear **Azure Container Registry (ACR)**.
2. Build + push de imagen a ACR.
3. Crear **Container Apps Environment**.
4. Desplegar la app (ingress, puerto, replicas).
5. Configurar secretos desde **Key Vault**.
6. Habilitar autoscaling (KEDA rules).
7. Integrar logs/metricas con Azure Monitor + Log Analytics.
8. Configurar alertas.

## 10.3 Servicios complementarios

- DB: Azure Database (PostgreSQL/MySQL) o Cosmos DB
- Archivos: Blob Storage
- Secretos: Key Vault
- Seguridad edge: Front Door / Application Gateway + WAF

---

## 11) Comparativa rapida AWS vs GCP vs Azure

Esta comparativa te ayuda a decidir segun **madurez del equipo**, **carga operativa** y **prioridad de negocio** (time-to-market, costo, gobernanza o flexibilidad).

### 11.1 Criterios de decision

Antes de elegir proveedor, define:

- Que importa mas: salir rapido o control total.
- Si tu equipo operara Kubernetes o prefiere serverless.
- Si ya existe estandar corporativo (IAM, identidad, compliance).
- Volumen de trafico esperado y variabilidad (picos vs carga estable).
- Necesidades de datos/analitica/IA del negocio.

### 11.2 Diferencias clave por proveedor

#### AWS

- **Fortaleza principal**: amplitud de servicios y opciones arquitectonicas.
- **Servicios de contenedores**: ECS Fargate (simple), EKS (Kubernetes), App Runner (rapido).
- **Escalabilidad**: excelente en escenarios enterprise y multi-cuenta.
- **Gobernanza**: muy robusta con IAM, Organizations, CloudTrail, etc.
- **Trade-off**: curva de aprendizaje mas alta por cantidad de servicios y configuraciones.

#### GCP

- **Fortaleza principal**: experiencia muy fluida para serverless containers y datos.
- **Servicios de contenedores**: Cloud Run (muy simple), GKE (Kubernetes), GCE para casos especiales.
- **Escalabilidad**: muy buena para cargas elasticas y equipos pequenos/medianos.
- **Datos/IA**: integracion natural con stack de datos (BigQuery, Vertex AI, etc.).
- **Trade-off**: menos opciones "enterprise legacy" que AWS en algunos contextos corporativos tradicionales.

#### Azure

- **Fortaleza principal**: integracion empresarial con ecosistema Microsoft.
- **Servicios de contenedores**: Container Apps (rapido), AKS (Kubernetes), App Service Containers.
- **Escalabilidad**: solida para organizaciones con Microsoft 365/Entra ID/AD.
- **Gobernanza**: fuerte en entornos con politicas corporativas centralizadas.
- **Trade-off**: en algunos casos, arquitectura de red/identidad puede requerir mas coordinacion con equipos TI.

### 11.3 Comparativa operativa (en lenguaje de negocio)

- **Time-to-market mas rapido**: Cloud Run y Azure Container Apps suelen ser muy agiles para iniciar.
- **Flexibilidad maxima de arquitectura**: AWS suele ofrecer mas variantes para optimizar casos complejos.
- **Kubernetes administrado maduro**: EKS, GKE y AKS son opciones validas; GKE suele destacar en simplicidad operativa, EKS en ecosistema AWS, AKS en integracion Microsoft.
- **Entorno corporativo Microsoft**: Azure reduce friccion por identidad y gobierno.
- **Workloads data-intensive**: GCP suele ser muy competitivo por ecosistema de datos.

### 11.4 Costos (enfoque practico)

No hay "nube mas barata" universal; depende del patron de uso:

- **Cargas intermitentes**: serverless container (Cloud Run/Container Apps/App Runner) puede optimizar costo.
- **Cargas estables y altas**: ECS/EKS/GKE/AKS bien dimensionados pueden ser mas eficientes.
- **Errores comunes de costo**:
  - Sobreaprovisionar CPU/RAM.
  - No configurar autoescalado y limites.
  - No apagar entornos no productivos fuera de horario.
  - No usar alertas de presupuesto.

### 11.5 Recomendacion por tipo de equipo

- **Startup o equipo pequeno sin SRE dedicado**:
  - Priorizar Cloud Run o Azure Container Apps.
  - En AWS, evaluar App Runner o ECS Fargate con configuracion simple.

- **Equipo medio con necesidades de control**:
  - ECS Fargate (AWS), Cloud Run + servicios gestionados (GCP), Container Apps + Key Vault (Azure).
  - Introducir observabilidad y despliegues canary gradualmente.

- **Equipo grande con plataforma interna**:
  - Kubernetes (EKS/GKE/AKS) + GitOps + policy-as-code + estandares de plataforma.
  - Separacion estricta de cuentas/proyectos/subscripciones por entorno.

### 11.6 Regla de decision rapida

- Si priorizas simplicidad inicial: **Cloud Run** o **Azure Container Apps**.
- Si priorizas flexibilidad enterprise total: **AWS ECS/EKS**.
- Si tu equipo domina Kubernetes y necesita estandar multi-servicio: **EKS/GKE/AKS**.
- Si tu organizacion ya esta profundamente en Microsoft: **Azure** suele reducir friccion.
- Si la estrategia principal gira en torno a datos y analitica cloud-native: **GCP** suele ser una gran opcion.

### 11.7 Enfoque de despliegue recomendado (por etapas)

Una vez elegida la nube, el enfoque recomendado es **incremental**, empezando simple y aumentando madurez sin romper continuidad operativa.

#### Etapa 1 - Fundacion (local y baseline cloud)

- Estandarizar `Dockerfile`, `.dockerignore` y variables de entorno.
- Definir un entorno **staging** con la misma topologia basica de prod.
- Publicar imagenes versionadas en registry (ECR/Artifact Registry/ACR).
- Activar secretos en gestor nativo (Secrets Manager / Secret Manager / Key Vault).
- Configurar logs y healthchecks desde el primer deploy.

Objetivo: tener un despliegue reproducible y auditable en menos de una hora ante incidentes.

#### Etapa 2 - Despliegue controlado (CI/CD + calidad)

- Automatizar pipeline: test -> build -> scan -> push -> deploy staging.
- Ejecutar smoke tests post-despliegue antes de promover a produccion.
- Aprobar produccion con gate manual (al inicio) o reglas de calidad.
- Usar tags inmutables (`1.2.0`, `sha-...`) y prohibir `latest` en prod.

Objetivo: reducir errores manuales y tener trazabilidad completa release por release.

#### Etapa 3 - Produccion robusta (release progressive)

- Aplicar estrategia de release: rolling o canary segun criticidad.
- Definir SLOs minimos (disponibilidad, latencia, error rate).
- Activar alertas por degradacion y presupuesto.
- Documentar runbook de rollback y ownership on-call.

Objetivo: proteger experiencia de usuario y controlar riesgo durante cambios.

#### Etapa 4 - Madurez de plataforma (escala)

- Infraestructura como codigo (Terraform/Bicep/CloudFormation).
- Separacion estricta de entornos y cuentas/proyectos/subscripciones.
- Politicas de seguridad automatizadas (policy-as-code, escaneo continuo).
- Optimizacion de costos por rightsizing y autoscaling avanzado.

Objetivo: escalar equipos y servicios sin perder gobernanza.

#### Modelo operativo sugerido por tipo de organizacion

- **Equipo pequeno**: serverless containers + CI/CD simple + observabilidad basica.
- **Equipo mediano**: serverless o ECS/AKS/GKE con canary y estandares de seguridad.
- **Equipo grande**: plataforma interna sobre Kubernetes/GitOps + controles de compliance.

#### Regla de oro

No intentes iniciar en la etapa 4.  
Empieza por una arquitectura simple que puedas operar bien y evoluciona cuando los indicadores de negocio/operacion realmente lo exijan.

---

## 12) Observabilidad (operacion diaria)

Minimo que debes monitorear:

- Disponibilidad (uptime)
- Error rate
- Latencia p95/p99
- CPU/memoria
- Reinicios/fallos de healthcheck

Buenas practicas:

- Logs estructurados (JSON)
- Correlation/request id
- Alertas accionables (no ruido)
- Dashboards por entorno (staging/prod)

---

## 13) Seguridad esencial

- Ejecutar como usuario no root.
- Limitar permisos IAM (principio de minimo privilegio).
- Escaneo continuo de imagenes.
- TLS obligatorio.
- Restringir ingress/egress por red.
- Rotacion periodica de secretos.
- Backups y prueba de restauracion.

---

## 14) Persistencia y datos

No guardar datos criticos en filesystem del contenedor.

Usa servicios gestionados y/o volumenes persistentes para:

- Base de datos
- Indices vectoriales
- Archivos subidos
- Cache duradera (si aplica)

Define politicas de:

- Retencion
- Backup
- Restore probado
- Cifrado en reposo y en transito

---

## 15) Estrategias de despliegue seguro

- **Rolling update**: reemplazo gradual (default recomendado).
- **Blue/Green**: dos entornos y switch de trafico.
- **Canary**: porcentaje pequeno, valida y escala.

En sistemas criticos, canary + metricas + rollback automatico es ideal.

---

## 16) Rollback y recovery

Plan minimo:

1. Conservar imagenes estables anteriores.
2. Detectar degradacion por alertas/smoke tests.
3. Revertir a tag anterior de imagen.
4. Verificar healthchecks y KPIs.
5. Registrar incidente (RCA breve).

---

## 17) Checklist de salida a produccion

- [ ] Imagen versionada y trazable a commit.
- [ ] Secretos fuera del codigo y fuera de la imagen.
- [ ] TLS activo y dominio correcto.
- [ ] Healthchecks funcionando.
- [ ] Logs/metricas/alertas configurados.
- [ ] Backup y restore validados.
- [ ] Limites de recursos definidos (CPU/RAM).
- [ ] Estrategia de rollback probada.
- [ ] Runbook operativo documentado.
- [ ] Estimacion y alertas de costo configuradas.

---

## 18) Errores comunes

- Usar `latest` en produccion.
- Mezclar datos persistentes dentro del contenedor.
- No separar staging de produccion.
- No tener alertas antes del go-live.
- No probar rollback.
- Exponer secretos en variables visibles o logs.

---

## 19) Recomendacion para empezar rapido

Si estas iniciando, usa esta ruta:

1. Dockerfile limpio + compose local.
2. Registry cloud (ECR / Artifact Registry / ACR).
3. Servicio serverless de contenedores (Cloud Run / Container Apps / App Runner o ECS Fargate).
4. Secret manager + monitoreo basico.
5. CI/CD simple con deploy a staging y luego prod.

Con esto ya tienes una base solida, portable y escalable para evolucionar a arquitecturas mas complejas (Kubernetes, multi-region, GitOps, etc.).

