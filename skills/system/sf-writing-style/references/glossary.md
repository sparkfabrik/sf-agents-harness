# Glossary

The vocabulary of SparkFabrik's engineering practice and European open-source
positioning, for every text that `voice.md` covers. Use the terms a subject needs, never
the whole list in one text. A snapshot of the tone-of-voice guide of SparkFabrik's
editorial pipeline (built from the site, version of 2026-11-02): when the site's offer changes,
refresh it from there.

## Preferred terms

**Cloud-native architecture and infrastructure.** Cloud native as an architectural and
operational principle; Kubernetes, container orchestration, containers; control plane,
worker nodes, desired state, reconciliation; microservices, decoupled services, API;
managed Kubernetes; serverless, event-driven execution; service mesh; hybrid, private,
public and multi-cloud; infrastructure as code (IaC), Terraform, Pulumi, Crossplane;
state file, drift, versioned configuration; GitOps, for versioned desired state and
reconciliation; FinOps, for cloud spending, accountability and operating discipline.

**Delivery, platforms and reliability.** DevOps, DevSecOps, CI/CD; continuous
integration and delivery, automated testing; platform engineering; Internal Developer
Platform (IDP); developer experience, self-service workflows, cognitive load; Site
Reliability Engineering (SRE); observability, telemetry, logs, metrics, traces;
OpenTelemetry, runtime security, eBPF; provisioning, deployment, rollback, release
pipeline; shared responsibility, incremental delivery, operational ownership.

**Drupal and content architecture.** Drupal, Drupal CMS, Drupal AI; the Drupal
ecosystem and community; core, contributed modules, maintainers, issue queues;
structured content, content types, fields; configuration management; composable
architecture, API-based integration; migration, modernisation, dependency management;
Composer, PHP runtime, module compatibility.

**AI engineering and governance.** Large language models (LLM); AI agents, agent
orchestration; agentic AI, for agents that act through tools and governed workflows;
guardrails, input and output validation; non-deterministic behaviour, prompt injection,
sensitive-data exposure; permissions, authentication, policy enforcement; human
supervision, traceability, governed execution; Model Context Protocol (MCP);
retrieval-augmented generation (RAG), semantic reranking; Spec Driven Development,
executable specifications.

**Security and regulation.** Software supply chain; Software Bill of Materials (SBOM);
vulnerabilities, dependencies, security advisories; signed artifacts, admission
controls, provenance; VEX, vulnerability assessment, remediation; threat modelling,
shift-left security; SAST, SCA, DAST; Cyber Resilience Act (CRA), NIS2, DORA, European
Accessibility Act; evidence, traceability, reporting windows, support obligations;
security by design, operational resilience. Name a regulation or a control only where
its relationship to the subject can be explained accurately.

## Positioning concepts

- **Digital sovereignty**: control over data, infrastructure, source code, and the
  ability to evolve or transfer a platform. Explain it through the actual control it
  gives, never as a slogan.
- **Vendor lock-in**: dependence from proprietary interfaces, services, contracts or
  operating models.
- **Independence and portability**: what can be moved, maintained, replaced or operated
  independently.
- **Technical debt**: the maintenance burden, delayed changes, obsolete dependencies or
  architectural constraints involved.
- **Open source**: licensing, collaborative development, governance, maintenance,
  funding and contribution.
- **Platform engineering and IDP**: infrastructure as a documented internal product
  that serves development teams.
- **Cloud-native principles**: automation, reproducibility, decoupling, resilience and
  operational responsibility, through concrete architecture.

Digital sovereignty and open source are related, but one does not guarantee the other:
explain the control mechanism. Never call SparkFabrik "Agentic-first" or give it a
"sovereign AI" positioning unless the brief or a source supports it.

## Business terms and their concrete basis

Keep a business term when it names an observable consequence, and give it that basis:

| Term                  | Ground it in                                                                           |
| --------------------- | -------------------------------------------------------------------------------------- |
| Scalability           | Request volume, replica counts, resource allocation, capacity constraints              |
| Resilience            | Failure isolation, recovery procedures, redundancy, tested restoration                 |
| Time-to-market        | Release frequency, environment setup, approval delays, deployment lead time            |
| Cost optimisation     | Resource consumption, operational effort, licensing, maintenance, total cost           |
| Competitive advantage | Faster service delivery, procurement eligibility, accessibility, platform independence |
| Productivity          | Less manual work, fewer handoffs, shorter feedback loops, better developer workflows   |
| Sustainability        | Maintainability, support funding, contributor capacity, long-term ownership            |
| Business value        | A specific user need, organisational outcome or measurable improvement                 |

## Phrasing that fits, when supported

"In produzione" / "in production", "contributori diretti" / "direct contributors",
"responsabilità condivisa" / "shared responsibility", "versionato e riproducibile" /
"versioned and reproducible", "sotto supervisione umana" / "under human supervision",
"controllo su dati, infrastruttura e codice sorgente" / "control over data,
infrastructure and source code". Each one names a condition, a responsibility or
evidence; repeated as a slogan it becomes a tell.

## Terms to avoid

Aggressive sales commands and artificial scarcity ("la migliore offerta", "buy now");
unsupported superlatives ("il migliore", "unmatched"); empty claims ("soluzioni
innovative", "approccio olistico", "sinergie strategiche"); a standalone "ecosistema
digitale" (name the Drupal or cloud-native ecosystem, or the participants); "cambio di
paradigma" as decoration.
