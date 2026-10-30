# GERVASIO 5.0 / EvidenceGate R4

**The industrial evidence agent that refuses to turn a plausible answer into an unsafe release decision.**

An original, runnable prototype for agricultural trailer engineering reviews. A practical question leads to source ingestion, optional **live NVIDIA Nemotron via Nebius Token Factory**, strict quotation filtering, cross-document draft conflict detection, an eight-part human evidence-request plan, source-ablation insights and an exportable audit packet.

> **HONEST STATUS (30 October 2026):** The application is implemented and tested locally. **No verified inference through an active Nebius account has occurred in this project.** Passing local tests or using a mocked provider in unit tests does **not** meet the hackathon requirement for a working NVIDIA/Nebius integration. No public repository, hosted app, YouTube video or completed Devpost entry is proven. The project must not be presented as already eligible, selected, or awarded.

## The industrial problem

Engineering release decisions rely on distributed supplier drafts, drawings, invoices, inspection evidence and design notes. A language model can summarize them, but a summary is not the same as evidence, and a supplier's draft rating is not a verified machine capacity. EvidenceGate is designed to make uncertainty visible and turn it into a reviewable action plan, while humans retain regulatory and engineering authority.

**Sector-specific case study:** A public description of a Gervasio four close-coupled-axle agricultural trailer is paired with **fictional training records**. Two imaginary supplier drafts deliberately disagree over ramp working load (`5000 kg` versus `6000 kg`). These are only deliberately invented test values. The application flags the contradiction and requests approved revisions/proof records instead of choosing a capacity. Never cite these values as properties of an actual Gervasio trailer.

Public excerpt source: https://www.gervasiorimorchi.com/it/prodotto/carrello-a-4-assi

## Why this is more than a chatbot

| Stage | Real program behavior | Trust boundary |
|---|---|---|
| 1. Ingest | Validate up to 8 source excerpts; compute SHA-256 fingerprints | Source text is untrusted |
| 2. Propose | Call NVIDIA Nemotron through Nebius Token Factory **only in configured live mode** | An LLM suggestion is not verification |
| 3. Verify | Match source IDs and verbatim quotes; reject fabricated references, unsupported numbers and positive safety/approval assertions | Substring location is not semantic truth |
| 4. Cross-check | Detect disagreement between two simulated supplier load drafts | A draft conflict is not a design limit |
| 5. Plan | Produce eight prioritized records required for an engineering review, with responsible roles | Human still sources and validates records |
| 6. Audit | Show source-ablation effect, export machine-readable review packet | SHA-256 fingerprint is not a certificate |

**Independent engineering hold:** The decision remains `ENGINEERING_HOLD`. The app never certifies a road vehicle, sets allowable loads, issues vehicle conformity, controls a machine, signs a drawing or authorizes a sale/delivery.

## Run the full local application

Requires **Python 3.10+**, a modern browser, no external Python libraries.

```bash
python3 src/server.py
```

Open `http://127.0.0.1:8765`.

1. See six starting sources (one short public manufacturer excerpt, five explicitly fictional test records).
2. Leave **Offline preview** selected and click **RUN EVIDENCE GATE**.
3. Inspect source-linked quotes, eight release-review gates, the deliberately conflicting ramp drafts, the six-step trail and the evidence-request plan.
4. Deselect source `SYN-03`, run again and observe loss of its source-linked quotations.
5. Download the audit packet JSON. Optionally add a short non-confidential source using the consent control.

**Offline preview is a deterministic non-AI test and not eligible NVIDIA inference.**

## Configure a real NVIDIA model via Nebius Token Factory

Supported configured model ID:
`nvidia/nemotron-3-super-120b-a12b`

Provider documentation: https://nebius.com/services/token-factory/nemotron

The application makes an OpenAI-compatible chat completion request at:
`https://api.tokenfactory.us-central1.nebius.com/v1/chat/completions`

On a **trusted local computer**, first check that a genuine Nebius Token Factory account is authorized to use the model and that the service has sufficient **free credits with no payable charges**. Set a private server-side API key and an explicit live attempt limit:

```bash
export NEBIUS_API_KEY='SET_PRIVATELY_ON_YOUR_OWN_COMPUTER'
export NEBIUS_MAX_LIVE_CALLS=1
python3 src/server.py
```

Alternatively run `RUN_NEBIUS_LIVE_WINDOWS.bat` on Windows or `./RUN_NEBIUS_LIVE_MAC_LINUX.sh` on macOS/Linux. These launchers prompt locally for the key, do not write it to a file and enable one provider request. Do **not** put credentials into a public chat, Git repo, video, email or browser code.

**Important:** A per-process API attempt counter is *not* a financial spending cap. Restarting a process resets the counter. Do not configure public paid access without provider-side quotas, authentication and approval. No charges or subscriptions are authorized by this repository. A live inference is genuine only after an actual successful provider response; the status `LIVE ADAPTER CONFIGURED` is not proof of a live call.

## Files and architecture

```text
src/core.py              input validation, deterministic preview, strict citation guard,
                         Nebius/NVIDIA inference adapter
src/workflow.py          six-step orchestration, versioned source hashes,
                         conflict detection, eight engineering follow-ups
src/server.py            local-first JSON API and static UI
src/run_live_once.py     private single-request live-launch helper
src/benchmark.py         reproducible synthetic adversarial test cases
web/index.html           responsive industrial quality-review interface
web/style.css, app.js    UI and downloadable audit packet
src/tests/               unit, API and workflow tests (see tests/)
docs/                    Devpost draft, reviewer guide, quality evidence, screenshots
```

The internal backend keeps model keys server-side. The frontend safely uses text nodes for document contents. The server binds to `127.0.0.1` by default and live inference is disabled unless explicitly configured.

## Reproduce the tests and evaluation

```bash
python3 -m unittest discover -s tests -v
python3 src/benchmark.py
```

- **Local tests (see verified build report) passed** as of R3 build, covering source filtering, HTTP endpoints, fake approval attempts, numerical hallucinations, configuration handling, workflow determinism and browser-observed features.
- **144 synthetic challenge cases**, including 120 deliberately invalid inputs all rejected and 24 valid citation fixtures all accepted, plus a self-evident fictional contradiction. These are controlled software tests, **not** measured LLM accuracy, field-relevant safety evidence or regulatory validation.
- Browser UI check included interactive audit, visible conflict, source-ablation behavior, adding a nonconfidential source and downloading the JSON report; no JavaScript exceptions observed.

Proof/limitations: `docs/R3_SYNTHETIC_EVALUATION.json`, `docs/R3_dashboard_audit.png`, `docs/ENGINEERING_CASE_STUDY.md`.

## Security and operational limitations

- The six demo documents do not contain confidential Gervasio drawings, real customers, production certificates, testing results, bids, finances or client records.
- User-pasted information must be owned/authorized and **non-confidential**. Live mode transmits the selected excerpts to Nebius.
- A quote match validates textual presence only, not factual accuracy or legal compliance; semantic validity, source authenticity and regulatory status still require an engineer.
- The contradiction matcher is deliberately limited to the illustrated ramp-load pattern. It is **not** a general machine-safety or mathematical validation engine.
- There is no integration with manufacturing equipment, cloud storage, account systems or actual acceptance tests.
- `Dockerfile` is for a controlled deployment environment only. Public production hosting requires HTTPS, authorization, rate limiting, anti-abuse/billing safeguards, documentation retention policy and testing.

## Hackathon submission: indispensable external steps

The official contest rules require a runtime call to Nebius Token Factory or use of Nebius AI Cloud, an NVIDIA open model, public original source code and license, a working demo/test build, a public YouTube video showing real operation (under three minutes) and a completed Devpost entry with tool feedback.

**Not yet completed**: real inference, public code host, public demo/test-build URL, live demonstration video uploaded to YouTube, official Devpost entry receipt.

Deadline: **30 October 2026, 10:00 PDT / 18:00 CET**.
Rules: https://nebiusglobalaihackathon.devpost.com/rules

## License

MIT (see `LICENSE`). Original demonstration software built for Gervasio Rimorchi. The demo public text excerpt belongs to its respective author and is attributed. Model and provider names identify supported integrations; no endorsement is implied.

## R4: conservative release firewall

R4 adds a second affirmative-risk detection gate, blocks synthetic-to-production claims, and adds injection regression tests. See `docs/R4_SECURITY_REVIEW.md`. No NVIDIA provider invocation is claimed.
