# FactoryPulse Synthetic Data Scenarios

FactoryPulse uses synthetic manufacturing data because
real factory data may be confidential or unavailable.

The simulator does not generate completely random records.
It introduces controlled statistical relationships that can
later be discovered by machine-learning models.

## Dataset Size

The current ML dataset contains:

- 20 production orders
- 20,000 PCB units
- Five manufacturing stages
- Four solder paste material lots
- DAY and NIGHT shifts
- Process events and quality measurements

The dataset can be reproduced with:

```powershell
python -m scripts.seed_demo_data `
    --prefix ML-20K `
    --orders 20 `
    --pcbs-per-order 1000 `
    --seed 42
Reproducibility

The simulator uses a fixed random seed. Running the simulator
with the same configuration produces the same statistical
distributions and manufacturing outcomes.

Base Anomaly Probability

Every PCB begins with a base anomaly probability of 12%.

Base anomaly probability: 0.12
Shift Scenario

Two shifts are simulated:

DAY: approximately 75% of production
NIGHT: approximately 25% of production

The NIGHT shift adds four percentage points to the anomaly
probability.

DAY probability: base probability
NIGHT probability: base probability + 0.04

Observed results in the ML-20K dataset:

Shift	PCB Count	Issue Rate
DAY 	14,988	14.88%
NIGHT	5,012	20.13%

An issue means that the PCB has either the FAILED or
REWORK status.

Material Lot Scenario

Four synthetic solder paste lots are generated:

LP-101
LP-205
LP-302
LP-410

LP-302 is assigned to approximately 15% of PCB units. It adds
18 percentage points to the anomaly probability.

The database does not store an is_problematic label. This
prevents the model from receiving the answer directly. The
relationship must be discovered from production and quality
outcomes.

Observed results in the ML-20K dataset:

Material Lot	PCB Count	Issue Rate
LP-101	        5,529	13.56%
LP-205      	5,661	13.28%
LP-302	        3,043	30.53%
LP-410	        5,767	14.01%
Process Drift Scenario

An anomalous PCB is assigned an anomaly stage. The simulator
then introduces a shared drift score into:

Machine process parameters
Quality measurements

As drift increases, process parameters move away from their
normal values and at least one quality measurement exceeds its
specification limit.

This relationship allows a future model to associate abnormal
machine behavior with quality outcomes.

Interpretation Limitation

These relationships are synthetic associations, not proof of
causality. FactoryPulse should describe model explanations as:

Factors associated with or contributing to increased quality
risk.

The system should not claim that a factor is the definitive
root cause without controlled experiments or causal evidence.