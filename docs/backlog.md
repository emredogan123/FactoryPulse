# Three-Week Backlog

## Working agreement

- One vertical slice is finished before a new optional feature starts.
- Must-have items block release; Should/Could items do not.
- Every completed feature meets the definition of done in `requirements.md`.
- Generated data and secrets never enter source control.

## Week 1: Foundation and data

| ID | Task | Priority | Estimate | Status |
| --- | --- | --- | --- | --- |
| FP-001 | Define scope, architecture, requirements, and data model | Must | 1 day | Done |
| FP-002 | Create FastAPI package and configuration | Must | 0.5 day | Todo |
| FP-003 | Add PostgreSQL connection and session management | Must | 0.5 day | Todo |
| FP-004 | Implement SQLAlchemy domain models | Must | 1 day | Todo |
| FP-005 | Add Alembic and initial migration | Must | 0.5 day | Todo |
| FP-006 | Implement seed users, machines, and material lots | Must | 0.5 day | Todo |
| FP-007 | Implement JWT login and role authorization | Must | 1 day | Todo |
| FP-008 | Implement PCB, machine, and process-event APIs | Must | 1 day | Todo |
| FP-009 | Implement reproducible simulator core | Must | 1 day | Todo |
| FP-010 | Add five planted fault scenarios | Must | 1 day | Todo |

## Week 2: Product UI and ML

| ID | Task | Priority | Estimate | Status |
| --- | --- | --- | --- | --- |
| FP-011 | Create React/TypeScript application shell | Must | 0.5 day | Todo |
| FP-012 | Add login, protected routes, and navigation | Must | 0.5 day | Todo |
| FP-013 | Implement dashboard queries and UI | Must | 1 day | Todo |
| FP-014 | Implement PCB list, filters, and trace view | Must | 1 day | Todo |
| FP-015 | Implement machine list and detail view | Must | 1 day | Todo |
| FP-016 | Build leakage-safe ML feature pipeline | Must | 0.5 day | Todo |
| FP-017 | Train and evaluate anomaly model | Must | 0.5 day | Todo |
| FP-018 | Train baseline and boosted risk models | Must | 1 day | Todo |
| FP-019 | Persist predictions and expose inference API | Must | 0.5 day | Todo |
| FP-020 | Add ranked prediction factors | Should | 0.5 day | Todo |

## Week 3: Integration and delivery

| ID | Task | Priority | Estimate | Status |
| --- | --- | --- | --- | --- |
| FP-021 | Create and acknowledge automatic alerts | Must | 1 day | Todo |
| FP-022 | Add dashboard refresh or WebSocket updates | Should | 0.5 day | Todo |
| FP-023 | Track experiments and versions in MLflow | Should | 0.5 day | Todo |
| FP-024 | Complete backend integration tests | Must | 1 day | Todo |
| FP-025 | Add critical Playwright flow | Should | 0.5 day | Todo |
| FP-026 | Add lint, test, and build CI | Must | 0.5 day | Todo |
| FP-027 | Finalize production containers | Must | 0.5 day | Todo |
| FP-028 | Deploy public demo | Must | 1 day | Todo |
| FP-029 | Complete English README and diagrams | Must | 0.5 day | Todo |
| FP-030 | Record demo and prepare interview notes | Must | 0.5 day | Todo |

## Risk register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Frontend consumes too much time | ML/demo stays incomplete | Use one dashboard layout and reusable table/chart components. |
| Synthetic data is unrealistically easy | Model metrics look misleading | Add noise, interactions, drift, imbalance, and time-based evaluation. |
| Leakage inflates performance | Portfolio claim becomes invalid | Maintain a feature cutoff and exclude post-test fields. |
| Infrastructure scope expands | MVP misses deadline | Keep Kafka/Kubernetes/microservices out of MVP. |
| SHAP integration delays release | Explanation screen incomplete | Fall back to stored global feature importance for MVP. |
| Deployment blocks late | No live demo | Keep Docker Compose runnable and record a local demo as fallback. |

