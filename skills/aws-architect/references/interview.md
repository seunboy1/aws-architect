# Interview guide

The goal is to learn enough to draw the system correctly, in the way this person's audience reads diagrams. A DevOps engineer, a solutions architect and an AI engineer need different pictures of different things, so the interview has five parts: **triage**, **core**, a **role module** (or two), optional **picture-type add-ons**, and **playback**.

## How to run it

- **Look before you ask.** Read any Terraform, CDK, CloudFormation, Helm, README, ADRs, design docs or SOWs in the working folder first. Turn what you find into proposed answers ("I see an ALB, an ECS service and Aurora in `infra/`; is that the production shape?") and ask the person to confirm. Making them retype what is in their repo wastes their time and invites mistakes.
- **At most five questions per message,** grouped by theme. Prefer multiple choice with a stated default ("default: two AZs, one NAT per AZ"). Say what each answer changes in the picture when it is not obvious; people answer better when they see why you ask.
- **Skip what is already known.** Never ask something the person or the repo already told you.
- **When someone does not know,** propose the most common pattern for their situation, draw it, and record it as an **assumption** in the footnote and in your hand-off message. Do not stall and do not invent silently.
- **Numbers only when they change the drawing.** Traffic, data volume and RTO/RPO matter because they decide whether you show multiple AZs, a second Region, a cache or a queue. Ask for them in that framing, not as a questionnaire.
- **Challenge contradictions.** If an answer conflicts with how AWS works (an "internal" load balancer reached directly from the internet, a managed service inside a subnet, a single-AZ database called highly available), say so and resolve it before drawing.
- **When the five-question cap forces a choice, ask in this order:** (1) what is being drawn and for whom, (2) boundaries and what sits outside AWS, (3) the main flow, (4) the one thing this audience will probe (for an AI system: what the model can reach and who confirms actions; for infrastructure: failure domains; for security: trust boundaries), (5) everything else. Defer observability, cost and presentation details to a later round or accept defaults.
- **Empty folder or short deadline.** If there is nothing to read, say so in one line and lean on stated defaults. If the person is short of time, ask one round only, draw with labelled assumptions, and invite corrections on the draft.
- **Stop when you could draw it.** A good interview is 2 to 4 rounds. Move to playback as soon as nothing material is unknown.

---

## Part 1: Triage (always, first)

1. **Who are you, and what is your job on this system?** Pick the closest, or describe it:
   - DevOps, platform or SRE engineer (infrastructure, networking, delivery, reliability)
   - Solutions architect or enterprise architect (the solution as a whole, trade-offs, stakeholders)
   - AI, ML or GenAI engineer (models, retrieval, agents, evaluation)
   - Data engineer or analytics engineer (pipelines, lakes, warehouses)
   - Security or compliance engineer (trust boundaries, controls, audit)
   - Backend or application developer (services, APIs, data stores)
   - Engineering lead, CTO or pre-sales (a proposal or executive overview)
2. **What kind of picture do you need?** Pick one (a system often needs more than one; start with the most important):
   - Infrastructure and network topology (accounts, VPCs, subnets, connectivity)
   - Application or solution architecture (components, integrations, flows)
   - Data platform or pipeline
   - AI or GenAI system (inference path, retrieval, agents, ML lifecycle)
   - Security and compliance boundaries (trust zones, controls, identity)
   - CI/CD and environments (how code reaches production)
   - Disaster recovery or multi-Region
   - Migration (current state and target state)
   - Executive or proposal overview
3. **Is this an existing system, a proposal, or a greenfield design?** (Existing: get the truth, including ugly parts. Proposal: show intent and alternatives. Greenfield: expect more assumptions.)
4. **Purpose and audience.** Design review, client proposal or SOW, runbook, onboarding, audit evidence, a slide? Who reads it, and what decision or action should it support?
5. **Detail level and count.** One diagram or an overview plus details? (Beyond about 14 icons, split.)

Use the answers to pick the role module(s) below. A solutions architect drawing an AI system gets module B plus module C.

---

## Part 2: Core (always)

### Boundaries
- How many AWS accounts appear (single, or dev/stage/prod, or a multi-account landing zone) and in which Regions?
- Is there a VPC? How many? Public, private and isolated subnets? Show Availability Zones or keep it logical?
- What sits outside AWS: end users, browsers and mobile apps, third-party services (payments, messaging, identity, monitoring), on-premises systems, another cloud?

### The flow
- What starts the main path: a user, a webhook, a schedule, a file landing in storage, an event, another system?
- Walk the main path one hop at a time ("request hits X, X calls Y, Y writes to Z"). Number it. This becomes the layout direction.
- Which hops are asynchronous (queues, topics, streams, event bus)? Is there a retry, dead-letter or redrive path worth drawing?
- How does the result get back to the caller?

### Services by tier
- **Edge:** DNS, CDN, API gateway, load balancer, WAF or DDoS protection?
- **Compute:** Lambda, ECS/Fargate, EKS, EC2, Batch, Step Functions? Which of these run inside the VPC?
- **Data:** relational, NoSQL, cache, object storage, search, analytics? Which are managed services outside the VPC and how are they reached privately (endpoints)?
- **Integration:** queues, topics, streams, event bus, workflow engine?

### Security and operations (baseline)
- Identity: how do users and services authenticate (Cognito, OIDC, IAM roles, API keys)?
- Show IAM, KMS, Secrets Manager, CloudTrail, Config, GuardDuty as one "applies to everything" band (the default), or attached to specific resources?
- Observability and cost: CloudWatch, X-Ray, alarms, dashboards, budgets?

### Presentation
- Title, subtitle, version or date, owner? Any naming convention or branding rules?
- Anything that must be called out (a decision, a deviation from a standard, a known limitation)? That goes in the footnote.
- Output: an editable `.drawio` only, or also a PNG for slides?

---

## Part 3: Role modules

Use the module that matches the person and the picture. Combine two when needed. Each module lists what to ask, what usually belongs in the drawing, and the layout that works.

### A. DevOps, platform and SRE (infrastructure and delivery)

**Ask**
1. Account structure: AWS Organization and OUs, separate accounts per environment, a landing zone or Control Tower? Which accounts hold shared services (networking, logging, security tooling)?
2. Network design: VPC CIDR ranges, how many AZs, which subnet tiers (public, private app, private data, isolated), NAT per AZ or shared, internet gateway, egress control?
3. Connectivity: Transit Gateway, VPC peering, Direct Connect, Site-to-Site VPN, PrivateLink, VPC endpoints (gateway and interface)? Private hosted zones?
4. Ingress path: DNS, CDN, WAF, load balancer (ALB or NLB, internal or internet-facing), targets? Where is TLS terminated?
5. Compute platform: EKS, ECS, EC2 with Auto Scaling, or serverless? Node groups or Fargate? Service mesh, ingress controller, autoscaling policy (HPA, KEDA, target tracking)?
6. Delivery: source control, CI system, build, artifact registry (ECR, CodeArtifact), IaC tool and state location, deployment strategy (rolling, blue/green, canary), approvals, drift detection?
7. Secrets and configuration: Secrets Manager, Parameter Store, how they reach workloads (task role, IRSA, CSI driver)?
8. Reliability: availability target, RTO and RPO, multi-AZ for every stateful tier, backups and restore tests, failover mechanism?
9. Observability and on-call: metrics, logs, traces, alert routing, dashboards, SLOs?
10. Access and operations: SSO, bastion or SSM Session Manager, break-glass access, change management?
11. Cost and guardrails: budgets, tagging, service control policies, quotas?

**Usually drawn:** account frame, VPC with AZ and subnet nesting, load balancers, compute, data tier, endpoints, NAT, connectivity to on-premises, a security and observability band. The CI/CD pipeline is usually a **second diagram** (left to right: source, build, test, registry, deploy to each environment).

**Layout:** account > VPC > AZ > subnet nesting, one flow direction from the internet inward. Draw each tier once per AZ only if AZ placement is the point of the diagram; otherwise label the tier "(2 AZs)".

### B. Solutions architect (the solution as a whole)

**Ask**
1. Business context: who are the actors (customers, staff, partners, other systems) and through which channels (web, mobile, API, WhatsApp, email)? What is the business outcome?
2. Capabilities to components: what major capabilities exist, and which service or team owns each?
3. Integration landscape: third-party SaaS, legacy or on-premises systems, partner APIs. Which direction does data flow, and how (REST, events, files, batch)?
4. Interaction style: synchronous request/response, asynchronous events, or both? Where is eventual consistency acceptable?
5. API strategy: public, partner or internal APIs; versioning; authentication and authorisation; throttling?
6. Data: system of record for each entity, data ownership per service, caching, analytics copies, retention and residency?
7. Identity and tenancy: single or multi-tenant, how tenants are isolated, identity provider?
8. Non-functional targets: availability, latency, throughput, scale peaks, security and compliance regimes?
9. Constraints and decisions: build versus buy, existing platform standards, vendor or skill constraints. What alternatives were considered and rejected?
10. Delivery stages: what is in the first release and what comes later? Should the diagram show target state only, or current and target?

**Usually drawn:** actors and channels on the left, the solution's components in the middle grouped by capability, external systems on the right, a data tier at the bottom. Start with a **logical view** (no subnets, no AZs); add a physical view only if asked.

**Layout:** one flow direction, actors outside any boundary, third-party boxes (`box` nodes) outside the account frame, decisions called out in the footnote.

### C. AI, ML and GenAI engineer

**Ask**
1. Use case: chat assistant, retrieval-augmented generation (RAG), agent with tools, document processing, classification, recommendation, forecasting, speech or vision? Interactive or batch?
2. Model strategy: hosted foundation models (which provider and family, via Amazon Bedrock), custom or fine-tuned models on SageMaker, classic ML endpoints? Any fallback model?
3. Inference path: client, gateway, orchestrator, model. Synchronous, streaming, or asynchronous with a queue? Where does latency matter?
4. Orchestration: a Lambda or container orchestrator, an agent framework, Step Functions? Where does conversation state live (DynamoDB, ElastiCache)?
5. Tools and actions: what can the model call (internal APIs, databases, search)? Who executes a tool call, the model or your code? Which actions need human confirmation or are blocked from the model entirely? (Draw that boundary clearly; reviewers look for it.)
6. Retrieval, if any: knowledge sources, ingestion pipeline (parse, chunk, embed), embedding model, vector store (OpenSearch, Aurora pgvector, a managed knowledge base), refresh schedule, access control on documents?
7. Safety and governance: guardrails, PII detection and redaction, prompt-injection defences, content filters, audit logging of prompts and responses, data retention, what data may leave the account or Region?
8. Evaluation and monitoring: offline evaluation sets, online quality signals, token and cost tracking, latency, drift, human review loop?
9. ML lifecycle (if custom models): data sources, labelling, training and tuning jobs, feature store, model registry, deployment (real-time, serverless, batch transform), CI/CD for models and prompts?
10. Scale and cost: requests per second, token budgets, caching of responses or embeddings, rate limits per user?
11. Where is the human? Review queues, escalation, feedback capture?

**Usually drawn:** two planes. The **online path** (user, channel, gateway, orchestrator, model, tools, data) across the main row. The **offline path** (ingestion, embedding, training, evaluation, registry) on a lower row, joined to the online path at the vector store or model endpoint. A clearly labelled boundary around "what the model can reach".

**Layout:** put the model service (`bedrock`, `bedrock_agentcore`, `sagemaker`) in the managed-services zone outside the VPC, with endpoints inside. Use `elasticsearch_service` for OpenSearch (the OpenSearch name does not render). Use `box` nodes for third-party models or tools. Show guardrails and the human-confirmation step on the path, not in a footnote.

### D. Data engineer and analytics

**Ask**
1. Sources: operational databases, SaaS apps, event streams, files, partner feeds? Volume and change rate?
2. Ingestion: batch or streaming; CDC with DMS, Kinesis, MSK, AppFlow, Transfer Family, DataSync?
3. Lake layout: landing, raw, curated, serving layers (bronze, silver, gold)? Storage formats and partitioning?
4. Processing: Glue, EMR, Lambda, Step Functions, dbt? Orchestration (MWAA, Step Functions, EventBridge schedules)?
5. Catalogue and governance: Glue Data Catalog, Lake Formation, column or row security, data classification, lineage?
6. Serving: Athena, Redshift, OpenSearch, an API, a feature store? Which BI tools or ML jobs consume?
7. Quality and operations: data quality checks, alerting, backfill and reprocessing, freshness SLAs?
8. Privacy and retention: PII handling, masking, retention, cross-account sharing?

**Usually drawn:** sources on the left, ingestion, then the lake layers in the middle (S3 zones), processing and orchestration above or below, serving and consumers on the right. Governance as a band.

### E. Security and compliance engineer

**Ask**
1. Trust boundaries: internet, partner networks, corporate network, each account, each VPC, data tiers. Which boundaries must the diagram prove?
2. Identity flow: workforce identity (SSO), customer identity, service identity (roles, OIDC federation), how credentials are issued and rotated?
3. Network controls: segmentation, security group and NACL intent, inspection points (WAF, Network Firewall, GuardDuty), egress filtering, private connectivity?
4. Data protection: encryption at rest and in transit, KMS key ownership per account, key policies, secrets handling, data classification and residency?
5. Detection and response: CloudTrail (organisation trail), Config, Security Hub, GuardDuty, log archive account, alerting and incident-response path?
6. Compliance: which framework or regulation (ISO 27001, SOC 2, PCI DSS, NDPA, GDPR), and which control does each element evidence?
7. Privileged access: who can reach production, how (SSO roles, SSM, break-glass), and how is it logged?

**Usually drawn:** trust zones as nested boundaries, with each control shown where it enforces. Use sub-labels that name the control (for example "encrypts with CMK app-data").

### F. Backend or application developer

**Ask**
1. Services: which services exist, what does each own, who calls whom, and over what (HTTP, gRPC, events)?
2. Data stores per service: database type, schema ownership, caches?
3. Authentication and authorisation between services and from clients?
4. Async work: queues, topics, scheduled jobs, workers, idempotency and retries?
5. Deployment target for each service (Lambda, Fargate, EKS, EC2) and how they scale?
6. External dependencies and failure behaviour (timeouts, circuit breakers, fallbacks)?

**Usually drawn:** services as the main row, data stores beneath each owner, queues between producers and consumers. Keep infrastructure detail light unless asked.

### G. Executive overview or proposal

**Ask**
1. What is the one message the diagram must carry (for example "no customer traffic is moved", "everything is auditable")?
2. Which 6 to 8 elements must appear? Everything else is detail to hide or fold into a group.
3. Should it show phases, current versus target, or the value delivered rather than every component?

**Usually drawn:** at most 8 icons, large labels, numbered steps for the story, no subnets or endpoints, a short footnote with the key assumptions. Offer a detailed technical diagram as a second file.

---

## Part 4: Picture-type add-ons

Add these questions when the triage says so.

- **Migration (current to target):** What moves, in what order, and what stays? How do old and new coexist (parallel run, replication, traffic shifting)? Which data syncs and how often? What are the cutover and rollback paths? Draw current and target as two diagrams or two zones, with the migration tooling (DMS, DataSync, replication) between them. State clearly what is not moving.
- **Disaster recovery or multi-Region:** Which pattern (backup and restore, pilot light, warm standby, active-active)? What is replicated (data, images, configuration) and how? What triggers failover and who or what performs it? RTO and RPO targets? Draw the primary and secondary Regions side by side with the replication and failover paths between them.
- **CI/CD and environments:** What triggers a build? Which stages (build, test, scan, package, deploy)? Which environments and accounts, with what approvals? How are secrets and cross-account roles handled? Show pipeline stages left to right and each environment as its own zone.

---

## Part 5: Playback (always, last)

Summarise what you understood as the three tables from SKILL.md step 2 (nodes, groups, arrows), plus:
- the persona and picture type you assumed,
- the **assumptions** you made for anything the person did not know,
- what you are deliberately **leaving out**.

Then wait for a yes or corrections before you write the spec.
