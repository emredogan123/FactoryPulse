# Problem Definition

## Context

PCB production lines generate process data across solder-paste printing, component placement, reflow soldering, inspection, and functional testing. A final quality result says whether a board passed, but teams still need to investigate patterns across machines, material lots, shifts, and process parameters.

The portfolio version of FactoryPulse uses only synthetic data. No confidential factory record, image, product name, machine configuration, threshold, or internal document is required.

## Core problem

Quality and process information is difficult to analyze when it is separated across production stages. Engineers need a single traceability view and early indication of abnormal conditions or increased quality risk.

## Target users

### Quality engineer

- monitors defect trends;
- investigates a failed or high-risk PCB;
- reviews factors associated with the model prediction;
- acknowledges alerts.

### Production engineer

- compares machine health and process metrics;
- identifies when a process starts deviating from normal behavior;
- filters results by machine, time range, shift, or material lot.

### Administrator

- manages users and roles;
- sees audit information;
- controls simulator and model settings.

### Viewer

- views dashboards and reports without changing records.

## Value proposition

FactoryPulse shortens investigation time by connecting four types of information:

1. the PCB's production history;
2. machine and process measurements;
3. quality-test results;
4. model-generated risk, anomaly, and explanation records.

## Product principles

- Explainability over opaque predictions.
- Traceability over isolated dashboard totals.
- Reproducible synthetic scenarios over unverifiable claims.
- A working, tested MVP over premature infrastructure complexity.
- Decision support, never automatic causal claims.

## Success criteria

The MVP is successful when a reviewer can:

1. generate a reproducible production batch;
2. observe a planted process fault;
3. find the affected machine and PCBs on the dashboard;
4. see anomaly and quality-risk scores;
5. inspect the main contributing factors;
6. follow one PCB from production order to quality result;
7. start the project with documented commands;
8. inspect automated tests and model evaluation results.

## Explicitly out of scope

- Real factory integration or confidential data
- Replacement of AOI, ICT, or functional testing
- Automated production-line control
- Computer-vision defect detection
- Proof of causality
- Kafka or Kubernetes in the three-week MVP
- Native mobile application
- LLM chatbot

