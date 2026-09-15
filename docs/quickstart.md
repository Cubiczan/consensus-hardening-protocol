```markdown
# Consensus Hardening Protocol (CHP) – Quickstart

Consensus Hardening Protocol (CHP) is an open-source multi-agent decision orchestration tool (Python 3.10+, MIT licensed) that generates structured, verifiable consensus reports with executable workflows.

## Prerequisites
- Python 3.10 or later
- Git (to clone the repository)

## Installation
```bash
git clone https://github.com/Cubiczan/consensus-hardening-protocol.git
cd consensus-hardening-protocol
pip install -e .
```

Once installed, the command-line tool `cme` becomes available. Verify it by running a plain demo:

```bash
cme demo
```

## Run without installing
If you prefer not to install the package, you can run the same demo directly:

```bash
PYTHONPATH=src python3 -m cme.cli demo
```

## Run a basic consensus round
A basic consensus round is simply a demo run that includes a decision question. After installation, execute:

```bash
cme demo "Should we invest $4M in a new enterprise tier next quarter?"
```

This single command triggers a full multi-agent deliberation pipeline and writes an orchestration report.

## What to expect
The command above generates a complete Markdown orchestration report. The report includes the following sections:

- **Problem classification**
- **Per-agent reasoning traces**
- **Grounding verdicts**
- **Playbook deltas**
- **Final executable workflow**

The demo runs three agents in sequence:
1. **Finance agent** runs first and produces its conclusions.
2. **Strategy agent** reads the finance agent’s output and builds on it.
3. **Compliance agent** reads both previous outputs and issues a conditional approval.

Finally, a **synthesizer** takes all agent contributions and produces a **Statement** and an **executable Workflow**.

The output is written as a Markdown file – look for the generated report in your working directory.

## Further reading
- Core state models: `src/cme/chp/`
- Complete demonstration script: `DEMO_SCRIPT.md`
- Finance-focused roadmap: `docs/CHP_FINANCE_PROJECT_ROADMAP.md`
- Minimal example file: `examples/basic_demo.py`
- Run the test suite (42 tests passing):  
  ```bash
  pip install pytest
  PYTHONPATH=src pytest tests/ -v
  ```
- Explore initial agent playbooks and context:  
  ```bash
  cme playbook finance
  cme context
  ```
- Launch a CHP funding allocation session:  
  ```bash
  cme chp-start
  ```
```
