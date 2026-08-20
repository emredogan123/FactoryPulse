# Requirements

Requirements use stable identifiers so commits, tests, API endpoints, and demo steps can reference them.

## Functional requirements

| ID | Requirement | MVP priority |
| --- | --- | --- |
| FR-001 | The system shall authenticate users with email and password. | Must |
| FR-002 | The system shall authorize Admin, Quality Engineer, and Viewer roles. | Must |
| FR-003 | The simulator shall generate production orders, PCBs, process events, and quality results. | Must |
| FR-004 | The simulator shall support reproducible random seeds and planted fault scenarios. | Must |
| FR-005 | Users shall list, search, filter, and paginate PCBs. | Must |
| FR-006 | Users shall view the complete production history of a PCB. | Must |
| FR-007 | Users shall view machine status, metrics, and quality performance. | Must |
| FR-008 | The dashboard shall show production, pass rate, defect rate, alerts, and risky machines. | Must |
| FR-009 | The system shall calculate an anomaly score for eligible process events. | Must |
| FR-010 | The system shall calculate PCB quality-failure probability. | Must |
| FR-011 | The system shall store the model version with every prediction. | Must |
| FR-012 | The system shall show ranked factors contributing to a prediction. | Should |
| FR-013 | The system shall create alerts from configurable risk and anomaly thresholds. | Must |
| FR-014 | Users shall acknowledge alerts. | Should |
| FR-015 | Administrators shall start or generate batches through the simulator. | Should |
| FR-016 | The system shall expose OpenAPI documentation. | Must |
| FR-017 | Model experiments and metrics shall be tracked. | Should |
| FR-018 | Critical user actions shall produce audit records. | Could |

## Non-functional requirements

| ID | Requirement | Acceptance target |
| --- | --- | --- |
| NFR-001 | Reproducibility | A seed produces the same synthetic batch and labels. |
| NFR-002 | Security | Passwords are hashed; secrets are outside source control. |
| NFR-003 | Reliability | Critical API and ML paths have automated tests. |
| NFR-004 | Performance | A paginated list request returns within 500 ms locally for 20,000 PCBs. |
| NFR-005 | Usability | Main demo flow requires no database or CLI knowledge. |
| NFR-006 | Maintainability | API, service, repository, domain, and ML responsibilities are separated. |
| NFR-007 | Explainability | Risk output includes probability, level, model version, and top factors. |
| NFR-008 | Portability | Local dependencies start through Docker Compose. |
| NFR-009 | Data integrity | Foreign keys and constrained status fields prevent invalid states. |
| NFR-010 | Documentation | README covers setup, architecture, evaluation, limitations, and demo. |

## Primary demo use case

1. Admin starts a seeded simulation containing a reflow temperature drift.
2. Process events and quality outcomes are stored.
3. The anomaly model flags abnormal reflow events.
4. The quality model assigns elevated failure probabilities to affected PCBs.
5. An alert is created for the machine.
6. The engineer opens the alert, machine, and PCB trace.
7. The UI shows ranked contributing factors without presenting them as proven causes.

## Definition of done for a feature

- Acceptance behavior is implemented.
- Invalid input and unauthorized access are handled.
- Relevant automated tests pass.
- API or user-facing behavior is documented.
- No secret or generated dataset is committed.

