# HANDOFF — X Marketing Operating System
## Complete Implementation Specification for the Coding Agent

> **Purpose:** This document is the authoritative handoff for an AI coding agent. Build the complete system from scratch based on this specification. Do not reinterpret the project as a generic social-media bot. Preserve the architectural decisions, constraints, scope, and separation rules below.

---

# 1. PROJECT IDENTITY

**Project name:** X Marketing Operating System  
**Short name:** XMOS  
**Primary goal:** Operate one X account as an AI-assisted marketing and content system focused on organic audience growth, original content, Saudi/Gulf trend relevance, selective competitor/watchlist intelligence, scheduled publishing, and continuous strategy improvement.

This is **not**:
- a spam bot
- a mass-engagement bot
- an auto-reply bot
- a DM bot
- an affiliate auto-poster
- a browser automation system

The system must behave as a controlled marketing operating system:

```text
Observe
→ Filter
→ Understand
→ Strategize
→ Create
→ Validate
→ Schedule
→ Publish
→ Measure
→ Learn
```

---

# 2. NON-NEGOTIABLE BUSINESS MODEL

There are two completely separate publishing paths.

## PATH A — AI ORGANIC CONTENT

The system is responsible for:
- Saudi/Gulf trend intelligence
- watchlist intelligence
- strategy
- original organic posts
- original threads
- content validation
- scheduling
- publishing through the official X API
- selective performance analysis
- weekly/monthly strategy improvement

Flow:

```text
X Data / Trends / Watchlist
            ↓
      Marketing Agent
            ↓
        DeepSeek API
            ↓
     Content + Strategy
            ↓
       Quality Gates
            ↓
          Scheduler
            ↓
          X API
            ↓
         X Account
```

## PATH B — USER COMMERCIAL CONTENT

The user personally publishes commercial content from the official X application:

- affiliate links
- coupons
- discounts
- product offers
- sponsored posts
- commercial announcements

Flow:

```text
User
 ↓
Official X App
 ↓
X Account
```

### Absolute rule

Commercial/manual posts must **not** be sent through:
- DeepSeek
- the system's publishing pipeline
- the system scheduler
- X API

Therefore those posts consume:

```text
DeepSeek usage = 0
X API publishing usage = 0
System processing for publishing = 0
```

The AI builds the audience. The user performs commercial monetization.

```text
AI → Audience / Reach / Authority / Engagement
User → Affiliate / Coupons / Offers / Revenue
```

Do not implement an affiliate auto-publishing feature in the first version.

---

# 3. PRIMARY SCOPE

Build the complete working system for **one X account**.

The system must support:

1. X authentication and secure token management.
2. DeepSeek API integration.
3. Saudi and Gulf trend collection using officially supported X capabilities.
4. Monitoring 5–10 user-selected X accounts.
5. Priority-based watchlist scanning.
6. Trend relevance scoring.
7. Content opportunity generation.
8. Content strategy memory.
9. Original post generation.
10. Original thread generation.
11. Repetition prevention.
12. Content quality gates.
13. Approval/rejection/editing workflow.
14. Scheduling.
15. Official X API publishing.
16. Duplicate-safe publishing and retry handling.
17. Selective analytics.
18. Daily summaries.
19. Weekly strategy generation.
20. Monthly strategy generation.
21. Cost/usage limits.
22. Lightweight web dashboard.
23. SQLite persistence.
24. Operation on a lightweight VPS with approximately 1 GB RAM.

---

# 4. OUT OF SCOPE FOR MVP

Do not implement:

- automated replies
- DM handling
- automated likes
- automated follows
- automated unfollows
- mass engagement
- bulk replies
- full timeline crawling
- browser automation as an API replacement
- scraping that violates X rules
- multiple AI providers
- multiple X accounts
- affiliate network integrations
- affiliate auto-posting
- CRM
- Redis
- Celery
- PostgreSQL
- Elasticsearch
- vector database
- heavy microservice architecture
- unnecessary Docker stack

Do not add these merely because they are common in social-media systems.

---

# 5. TECHNOLOGY CONSTRAINTS

## Required implementation direction

Use a lightweight Python architecture suitable for a 1 GB VPS.

Recommended stack:

```text
Python 3.12+
FastAPI
SQLite
SQLAlchemy
APScheduler
httpx
Pydantic
Jinja2 or a lightweight server-rendered UI
Nginx
systemd
```

Use official SDKs only where appropriate and actively maintained. Avoid unnecessary dependencies.

### Database

Use:

```text
SQLite
```

Configure:
- WAL mode where appropriate
- foreign keys enabled
- migrations
- indexes for frequent queries

### No Redis

Use SQLite-backed persistence and in-process scheduling suitable for the current scope.

### No Celery

APScheduler + systemd-managed application processes are sufficient for MVP.

---

# 6. EXTERNAL SERVICES

The architecture should depend primarily on only:

```text
1. DeepSeek API
2. Official X API
```

Do not require:
- Make
- Zapier
- n8n Cloud
- Supabase
- Firebase
- a second AI provider

Use environment variables for secrets.

---

# 7. AI MODEL

The current design assumes:

```text
DeepSeek V4-Pro
```

Important implementation rule:

Do not hardcode model-specific logic throughout the codebase.

Create an AI provider abstraction:

```text
AIProvider
    generate()
    analyze()
    structured_output()
```

Then configure the active model from settings/environment.

For the initial implementation, only one concrete provider is required:

```text
DeepSeekProvider
```

This keeps future model replacement possible without adding multiple providers now.

---

# 8. AGENT DESIGN

Use one primary orchestration agent:

```text
MarketingAgent
```

Do not create many autonomous agents unless there is a clear technical need.

The agent orchestrates deterministic services/tools:

```text
MarketingAgent
├── TrendService
├── WatchlistService
├── AccountService
├── ContentService
├── ThreadService
├── AnalyticsService
├── StrategyService
├── SchedulerService
├── PublishingService
└── CostGuardService
```

AI reasoning must not directly execute unrestricted actions.

Actions should be mediated by application services.

Example:

```text
AI proposes content
→ deterministic validator
→ database queue
→ approval policy
→ scheduler
→ publishing service
```

---

# 9. MARKET AND TREND PRIORITIES

Primary geographic relevance:

```text
Priority 1: Saudi Arabia
Priority 2: Gulf region
    - UAE
    - Kuwait
    - Qatar
    - Bahrain
    - Oman
Priority 3: Global topics only when strongly relevant to Saudi/Gulf audience
```

Never publish about a global trend merely because it is popular.

A trend must be evaluated for audience relevance.

---

# 10. TREND ENGINE

The Trend Engine must process available trend/search data into content opportunities.

Pipeline:

```text
Collect
↓
Normalize
↓
Deduplicate
↓
Classify
↓
Score relevance
↓
Assess freshness
↓
Generate possible angle
↓
Approve / Monitor / Ignore
```

## Trend score

Implement configurable scoring:

```text
Saudi Relevance       0–30
Gulf Relevance        0–20
Audience Relevance    0–20
Timing/Freshness      0–15
Content Potential     0–15
--------------------------------
Total                 0–100
```

Suggested interpretation:

```text
85–100 = Immediate Opportunity
70–84  = Potential Opportunity
50–69  = Monitor
0–49   = Ignore
```

These values must be configurable, not scattered magic numbers.

### Trend record

Store at minimum:

```text
id
source
external_id
title/topic
region
first_seen_at
last_seen_at
freshness_score
saudi_score
gulf_score
audience_score
timing_score
content_potential_score
total_score
status
suggested_angle
metadata_json
created_at
updated_at
```

### Important behavior

A trend is not automatically content.

The system must reason:

```text
Why is this relevant?
Does it matter to our audience?
Is there a useful original angle?
Is information sufficiently reliable?
Should we post, create a thread, monitor, or ignore?
```

---

# 11. WATCHLIST

Support:

```text
Minimum initial use: 5 accounts
Maximum MVP target: 10 accounts
```

The user configures the accounts.

Each account has a priority:

```text
TIER_1 = high
TIER_2 = medium
TIER_3 = low
```

Suggested scan frequency:

```text
Tier 1: 3 times/day
Tier 2: 2 times/day
Tier 3: 1 time/day
```

Make scan frequencies configurable.

## Watchlist purpose

The watchlist is for intelligence only:
- new topics
- relevant news
- recurring content themes
- useful ideas
- market shifts
- content opportunities

It must not:
- copy content
- automatically reply
- like
- follow
- DM

Use incremental retrieval where supported, such as tracking the latest known post identifier, to avoid repeatedly retrieving the same data.

Store:

```text
watchlist_accounts
watchlist_scans
watchlist_posts
watchlist_insights
```

---

# 12. CONTENT STRATEGY

The system must support configurable content pillars.

Do not hardcode a niche.

Example placeholders:

```text
Pillar A
Pillar B
Pillar C
Pillar D
Pillar E
```

The actual pillars, audience, brand voice, vocabulary, and strategy must be editable through settings/database.

## Content formats

Support at least:

```text
POST
THREAD
```

Content categories should be configurable, for example:

```text
Educational
Trend
Opinion
Conversation
Authority
News Analysis
```

Commercial is not an AI publishing category.

---

# 13. DAILY CONTENT LIMITS

Default policy:

```text
Maximum AI posts/day = 5
Minimum target is not mandatory
Maximum AI threads/day = 2
```

Suggested operating range:

```text
3–5 posts/day
0–2 threads/day
```

### Critical rule

Do not publish simply to satisfy a quota.

```text
No valuable content = no publication
```

The system should be able to produce fewer than the maximum when opportunities are weak.

---

# 14. CONTENT GENERATION PIPELINE

For each candidate:

```text
Opportunity
↓
Topic
↓
Angle
↓
Audience relevance
↓
Hook
↓
Draft
↓
Originality/repetition check
↓
Quality validation
↓
Queue
↓
Review policy
↓
Schedule
↓
Publish
```

Store content as structured records.

Suggested fields:

```text
id
type
topic
angle
pillar
category
source_type
source_reference
hook
body
thread_items_json
score
status
scheduled_at
published_at
x_post_id
validation_json
created_at
updated_at
```

---

# 15. THREAD GENERATION

Threads must not be generated merely to increase output.

Before generating a thread, evaluate:

```text
Topic Depth
Audience Value
Timeliness
Original Insight
Narrative Potential
```

Store the evaluation.

Suggested thread structure:

```text
1. Hook
2. Context
3. Main point(s)
4. Analysis
5. Practical value or conclusion
```

Thread length must depend on the subject.

---

# 16. ORIGINALITY AND REPETITION PREVENTION

Store content history with:

```text
topic
angle
hook
format
pillar
published_at
performance metrics
```

Before approval:

```text
Candidate
↓
Compare with recent history
↓
Same topic?
Same angle?
Same hook pattern?
Too soon?
↓
Similarity result
↓
Approve / Rewrite / Reject
```

Implement deterministic checks first:
- normalized exact duplicates
- repeated topic windows
- repeated hooks
- repeated source references

AI-assisted similarity assessment may be used selectively, but do not send the entire history unnecessarily.

---

# 17. QUALITY GATE

Every AI-generated item must pass validation before automatic publishing.

Validate:

```text
Originality
Relevance
Clarity
Accuracy / uncertainty handling
Audience value
Hook strength
Brand voice
Repetition
Spam risk
X policy compliance
```

Possible outcomes:

```text
APPROVED
REWRITE_REQUIRED
REJECTED
```

Do not silently publish failed content.

---

# 18. APPROVAL POLICY

Implement configurable publishing modes:

```text
MANUAL_APPROVAL
AUTO_APPROVE_HIGH_CONFIDENCE
```

For MVP, default to:

```text
MANUAL_APPROVAL
```

The user should be able to:
- approve
- reject
- edit
- reschedule
- publish now

The system must retain audit information about manual changes.

---

# 19. CONTENT QUEUE STATE MACHINE

Implement explicit states:

```text
IDEA
DRAFT
REVIEW
REWRITE_REQUIRED
APPROVED
SCHEDULED
PUBLISHING
PUBLISHED
FAILED
REJECTED
CANCELLED
```

Do not use ambiguous boolean flags.

Every state transition should be validated.

---

# 20. SCHEDULING

Use APScheduler or equivalent lightweight internal scheduling.

Do not assume fixed posting times are optimal.

Start with configurable default windows.

The analytics system should later recommend improved time windows based on actual account performance.

Example concept:

```text
Morning
Midday
Afternoon
Evening
Late Evening
```

The final times must be configurable.

---

# 21. PUBLISHING

Only AI organic content may enter:

```text
Content Queue
↓
PublishingService
↓
Official X API
↓
X Account
```

### Commercial/manual content must never enter this path.

Publishing service requirements:
- idempotency strategy
- persistent publish attempt records
- retry policy
- exponential backoff
- retry limit
- duplicate prevention
- API error logging
- rate/usage awareness

If a network failure occurs after a publish request:

```text
Do not blindly retry.
```

First determine whether the post was created using available identifiers/response data before creating another attempt.

---

# 22. X API ADAPTER

Create an abstraction:

```text
XClient
```

Methods should be organized around actual application needs, for example:

```text
authenticate()
refresh_token()
get_own_account()
get_own_posts()
get_watchlist_posts()
get_trend_or_search_data()
publish_post()
publish_thread()
get_post_metrics()
```

Do not expose raw HTTP calls throughout business logic.

All X API access should pass through the adapter/client layer.

Because X API capabilities and pricing may change, keep endpoint/version details isolated.

---

# 23. ANALYTICS PHILOSOPHY

Do not analyze every possible event.

Use selective and aggregated analysis.

## Daily

Collect enough data to identify:

```text
Best post
Weakest post
Top topic
Format performance
Immediate observation
```

## Weekly

Analyze:

```text
Top topics
Weak topics
Top hooks
Top formats
Best time windows
Trend conversion
Thread performance
Content fatigue
Recommended changes
```

## Monthly

Analyze:

```text
Audience growth
Content growth
Topic evolution
Best formats
Best themes
Strategic direction
```

---

# 24. LOCAL AGGREGATION BEFORE AI

Calculate simple statistics locally before sending summaries to DeepSeek.

Examples:

```text
engagement rate
averages
medians
top/bottom performers
performance by topic
performance by format
performance by time window
trend opportunity performance
```

Do not send large raw datasets when a compact summary is sufficient.

Example AI context:

```text
Top 10 content items
Bottom 10 content items
Topic aggregates
Format aggregates
Time aggregates
Trend aggregates
Previous strategy
Current strategic questions
```

---

# 25. STRATEGY LEARNING LOOP

Implement:

```text
Publish
↓
Measure
↓
Aggregate
↓
Analyze
↓
Store strategy insight
↓
Update next planning cycle
```

This is not model training.

The system learns operationally through:
- database history
- analytics
- stored strategy decisions
- retrieved context

---

# 26. MEMORY DESIGN

Use SQLite as the primary memory.

Suggested tables:

```text
brand_profiles
brand_rules
audience_profiles
content_pillars
content_items
content_versions
content_history
content_validations
trends
trend_assessments
watchlist_accounts
watchlist_scans
watchlist_posts
watchlist_insights
strategies
strategy_insights
analytics_snapshots
publish_attempts
api_usage
system_jobs
audit_logs
settings
oauth_tokens
```

Do not use a vector database in MVP.

Use focused SQL queries and curated context.

---

# 27. BRAND MEMORY

Store configurable:

```text
Brand Voice
Tone
Audience
Content Pillars
Preferred Vocabulary
Forbidden Vocabulary
Writing Rules
CTA Rules
Approved Examples
Rejected Examples
```

When generating content, retrieve only relevant context.

Do not place the entire database history into every prompt.

---

# 28. AI REASONING / COST POLICY

Use model effort intelligently.

Simple tasks:
- classification
- filtering
- extraction
- normalization
- deterministic decisions

should use minimal AI or no AI.

Reserve stronger AI reasoning for:
- strategy
- trend interpretation
- difficult content planning
- original content generation
- weekly/monthly analysis

Create an internal task profile:

```text
LOW
STANDARD
HIGH
```

Map provider parameters in one adapter layer.

---

# 29. CONTEXT EFFICIENCY

Separate:

```text
STATIC CONTEXT
```

from:

```text
DYNAMIC CONTEXT
```

Static examples:

```text
brand
audience
voice
rules
content pillars
```

Dynamic examples:

```text
current trends
new watchlist insights
recent performance
current strategy
```

Only send the required context for each task.

---

# 30. COST GUARDS

Implement application-level limits.

Suggested settings:

```text
MAX_AI_POSTS_PER_DAY = 5
MAX_AI_THREADS_PER_DAY = 2
MAX_TREND_SCANS_PER_DAY = 3
MAX_WATCHLIST_ACCOUNTS = 10
MAX_MONTHLY_AI_BUDGET = configurable
MAX_MONTHLY_X_API_BUDGET = configurable
```

Track actual requests/estimated cost where provider data allows.

When budget threshold is reached:

```text
PAUSE_NONCRITICAL_AI_TASKS
PAUSE_NONCRITICAL_X_REQUESTS
```

Never silently continue spending beyond configured hard limits.

Dashboard should show:
- current estimated AI usage
- current estimated X API usage
- configured budget
- remaining budget

---

# 31. SECURITY

Never store:
- X password
- API keys in source code
- secrets in frontend JavaScript

Use:
- OAuth for X
- environment variables for service secrets
- secure token storage
- token refresh handling
- restricted file permissions where applicable

Log redaction is mandatory for:
- API keys
- access tokens
- refresh tokens
- authorization headers

Add a `.env.example`, never commit `.env`.

---

# 32. DASHBOARD

Create a lightweight responsive web dashboard.

Main sections:

```text
Dashboard
Today
Content Queue
Trends
Watchlist
Analytics
Strategy
Content History
API Usage
Settings
```

## Dashboard home

Show:

```text
Today's strategy
AI posts planned / published
Threads planned / published
Top trend opportunity
Top watchlist insight
Next scheduled item
Recent performance summary
AI budget status
X API budget status
```

## Content Queue

Show:
- type
- topic
- score
- status
- scheduled time

Actions:
- approve
- reject
- edit
- reschedule
- publish now
- cancel

## Trends

Show:
- trend/topic
- score
- region
- freshness
- suggested angle
- status

## Watchlist

Show:
- account
- priority
- last scan
- new relevant items
- latest insight

## Analytics

Show:
- impressions where available
- engagement
- top topics
- top formats
- best time windows
- top posts
- weak posts

---

# 33. DATABASE DESIGN

Use SQLAlchemy models and Alembic migrations.

At minimum, ensure indexes for:

```text
content_items.status
content_items.scheduled_at
content_items.published_at
content_items.x_post_id
trends.status
trends.total_score
watchlist_posts.account_id + external_post_id
publish_attempts.content_item_id
analytics_snapshots.created_at
system_jobs.next_run_at
```

Use UTC internally. Convert to configured display timezone in UI.

Default operational timezone should be configurable; initial deployment target is Saudi Arabia.

---

# 34. JOBS

Use persistent job execution records.

Suggested recurring jobs:

```text
trend_scan
watchlist_scan_tier_1
watchlist_scan_tier_2
watchlist_scan_tier_3
daily_planning
content_generation
content_validation
publishing_dispatch
metrics_collection
daily_summary
weekly_strategy
monthly_strategy
usage_reconciliation
cleanup
```

Do not schedule all jobs simultaneously on a 1 GB VPS.

Stagger them.

---

# 35. ERROR HANDLING

Every external operation must use:
- timeouts
- structured exceptions
- retries only when safe
- backoff
- persistent failure records

Differentiate:
- validation errors
- authentication errors
- rate-limit errors
- provider outages
- network errors
- duplicate risks
- database errors

Do not swallow exceptions.

---

# 36. LOGGING AND AUDIT

Use structured application logs.

Store relevant audit events:

```text
content created
content edited
content approved
content rejected
publish requested
publish succeeded
publish failed
strategy changed
watchlist changed
settings changed
token refresh failed
budget threshold reached
```

Do not store secrets in logs.

---

# 37. PROJECT STRUCTURE

Use a clean modular structure similar to:

```text
xmos/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── database.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   │   ├── ai/
│   │   │   ├── base.py
│   │   │   └── deepseek.py
│   │   ├── x/
│   │   │   ├── client.py
│   │   │   └── auth.py
│   │   ├── trends/
│   │   ├── watchlist/
│   │   ├── content/
│   │   ├── analytics/
│   │   ├── strategy/
│   │   ├── publishing/
│   │   ├── scheduler/
│   │   └── costs/
│   ├── agents/
│   │   └── marketing_agent.py
│   ├── prompts/
│   │   ├── strategy.py
│   │   ├── content.py
│   │   ├── trend.py
│   │   └── analytics.py
│   ├── api/
│   │   ├── routes/
│   │   └── dependencies.py
│   ├── web/
│   │   ├── templates/
│   │   └── static/
│   └── jobs/
│       └── definitions.py
├── migrations/
├── tests/
├── scripts/
├── requirements.txt or pyproject.toml
├── .env.example
├── README.md
└── systemd/
```

The exact structure may improve, but preserve clear separation between:
- API
- domain/business logic
- persistence
- AI provider
- X integration
- jobs
- UI

---

# 38. IMPLEMENTATION ORDER

Build in this order.

## Phase 1 — Foundation

1. Initialize project.
2. Configuration management.
3. Logging.
4. SQLite + SQLAlchemy.
5. Alembic migrations.
6. Core models.
7. Health endpoint.
8. Basic dashboard shell.
9. Authentication/administration for local dashboard if exposed publicly.

## Phase 2 — X Integration

1. OAuth.
2. Token persistence.
3. Token refresh.
4. Own account retrieval.
5. Test API connectivity.
6. Publish test abstraction.
7. Error/rate-limit handling.

Do not implement bulk automation.

## Phase 3 — AI Integration

1. DeepSeek provider abstraction.
2. Structured response schema.
3. Prompt templates.
4. Cost/usage tracking.
5. Failure handling.

## Phase 4 — Intelligence

1. Trend collection.
2. Trend normalization.
3. Trend scoring.
4. Watchlist CRUD.
5. Priority scanning.
6. Insight extraction.

## Phase 5 — Content

1. Content opportunity model.
2. Strategy context retrieval.
3. Post generation.
4. Thread generation.
5. Duplicate checks.
6. Quality gate.
7. Queue state machine.
8. Manual approval UI.

## Phase 6 — Publishing

1. Scheduler.
2. Scheduled dispatch.
3. Publish attempt persistence.
4. Idempotency.
5. Safe retry logic.
6. Published state reconciliation.

## Phase 7 — Analytics

1. Metrics retrieval.
2. Local aggregation.
3. Daily summary.
4. Weekly analysis.
5. Monthly analysis.
6. Strategy persistence.

## Phase 8 — Operations

1. Cost guard.
2. Job monitoring.
3. Audit logs.
4. Backup script.
5. systemd service files.
6. Nginx deployment configuration.
7. Documentation.

---

# 39. TESTING REQUIREMENTS

Add tests for critical logic.

At minimum:

```text
trend scoring
content state transitions
daily limits
thread limits
duplicate prevention
commercial-path exclusion
budget guards
publish retry logic
idempotency handling
token refresh failure
quality gate outcomes
watchlist priority scheduling
```

Mock all external APIs in unit tests.

No real API calls during ordinary tests.

---

# 40. DEPLOYMENT

Target:

```text
Ubuntu VPS
~1 GB RAM
```

Provide:
- environment template
- migration command
- application startup command
- systemd service
- scheduler startup strategy
- Nginx reverse proxy example
- backup procedure for SQLite
- restore procedure

Do not expose development server directly to the internet.

---

# 41. SQLITE BACKUP

Provide a simple automated backup process.

Requirements:
- consistent SQLite backup
- timestamped files
- retention policy
- documented restore command

Do not overengineer cloud backup in MVP unless explicitly configured.

---

# 42. RESOURCE DISCIPLINE

The VPS is lightweight.

Avoid:
- loading large ML models locally
- background workers that remain idle with large memory footprints
- excessive concurrent API requests
- large in-memory datasets
- full social graph storage
- high-frequency polling

Use:
- incremental retrieval
- database indexes
- compact AI context
- staggered jobs
- HTTP connection reuse where appropriate

---

# 43. MANUAL COMMERCIAL CONTENT EXCLUSION TEST

This is a mandatory design rule.

There must be no route or scheduled process that automatically converts commercial content into AI or API publishing activity.

The application should not require the user to enter affiliate posts at all.

If the user publishes manually through the official X app, the system remains independent.

Therefore:

```text
Manual X App Post
≠ AI Content Item
≠ Scheduled Item
≠ X API Publish Request
```

Do not violate this separation in future code without an explicit requirements change.

---

# 44. SAFETY AND PLATFORM COMPLIANCE

Use official X APIs and supported authentication mechanisms.

Do not implement features intended to create artificial engagement.

Explicitly exclude:
- engagement farming
- automated mass replies
- mass likes
- mass follows
- artificial traffic
- spam posting

The system's automation must focus on content operations and analytics.

---

# 45. ACCEPTANCE CRITERIA

The MVP is complete only when all of the following work:

## Core
- [ ] Application starts reliably.
- [ ] SQLite database migrates correctly.
- [ ] Dashboard is usable.
- [ ] Configuration is environment-based.

## X
- [ ] X authentication works with official supported flow.
- [ ] Tokens are not exposed.
- [ ] Own account can be retrieved.
- [ ] AI organic post can be published through the official API.
- [ ] Thread publishing works if API/account capabilities permit.
- [ ] Failed publishing does not create uncontrolled duplicates.

## AI
- [ ] DeepSeek integration works.
- [ ] Structured generation is validated.
- [ ] AI provider failures are handled.
- [ ] Usage/cost data is recorded as available.

## Intelligence
- [ ] Trends can be collected from supported X capabilities.
- [ ] Trend scoring works.
- [ ] 5–10 watchlist accounts are supported.
- [ ] Priority scanning works.

## Content
- [ ] Posts can be generated.
- [ ] Threads can be generated.
- [ ] Repetition checks work.
- [ ] Quality gate works.
- [ ] Approval workflow works.
- [ ] Daily limits work.

## Scheduling
- [ ] Approved content can be scheduled.
- [ ] Scheduled content publishes at the correct time.
- [ ] Retry logic is safe.

## Analytics
- [ ] Metrics are stored.
- [ ] Daily summaries work.
- [ ] Weekly strategy analysis works.
- [ ] Historical insights influence future planning.

## Cost
- [ ] AI budget limits work.
- [ ] X API budget limits work.
- [ ] Noncritical jobs pause when hard limits are reached.

## Separation Rule
- [ ] No affiliate/coupon/product/sponsored content is auto-published.
- [ ] Manual publishing through the official X app remains outside the system.
- [ ] Such manual publishing does not consume system AI or X API publishing operations.

---

# 46. FINAL ARCHITECTURE

```text
                    ┌─────────────────────┐
                    │      X ACCOUNT      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
     AI ORGANIC SYSTEM                    USER MANUAL
              │                         COMMERCIAL POSTS
              │                                 │
              ▼                                 ▼
       Marketing Agent                     Official X App
              │
      ┌───────┼────────┬─────────┐
      ▼       ▼        ▼         ▼
   Trends  Watchlist Strategy  Analytics
      │       │        │         │
      └───────┴────┬───┴─────────┘
                   ▼
             DeepSeek V4-Pro
                   │
                   ▼
          Content / Threads / Plan
                   │
                   ▼
              Quality Gate
                   │
                   ▼
              Content Queue
                   │
                   ▼
                Scheduler
                   │
                   ▼
                X API
                   │
                   └──────────────→ X ACCOUNT
```

---

# 47. FINAL IMPLEMENTATION PRINCIPLES

1. Build a marketing operating system, not a posting bot.
2. Keep AI organic publishing separate from manual commercial publishing.
3. Use one AI provider in MVP.
4. Keep the architecture compatible with a 1 GB VPS.
5. Prefer deterministic logic where AI is unnecessary.
6. Use AI for judgment, strategy, and original content.
7. Do not publish simply to meet quotas.
8. Store enough history to avoid repetition and improve strategy.
9. Aggregate data locally before expensive AI analysis.
10. Put hard limits around AI and X API spending.
11. Use official X integration; do not substitute browser automation.
12. Keep the MVP narrow and working before adding advanced features.
13. Do not invent unsupported X API capabilities. Verify current official documentation during implementation.
14. Isolate external-provider details behind adapters because APIs, models, endpoints, and pricing can change.

---

# 48. CODING AGENT EXECUTION RULES

When implementing:

- Start with the repository structure and architecture.
- Create the database schema and migrations before feature code.
- Implement features in the stated phases.
- Keep code, comments, identifiers, and technical documentation in English.
- Make UI text easy to internationalize; initial UI can use Arabic where appropriate for the target user.
- Do not use placeholder implementations for critical paths.
- Do not claim an external API capability exists without verifying current official documentation.
- Do not silently broaden the scope.
- If an X API capability required by this specification is unavailable under the selected access/pricing model, implement a clear capability check and document the limitation rather than replacing it with scraping or browser automation.
- Test each phase before proceeding.
- Preserve the separation between AI organic publishing and manual commercial publishing.
- Prefer simple, maintainable code over speculative abstractions.

## Required first deliverables

Before writing the entire system, produce:

1. Final repository tree.
2. `pyproject.toml` or dependency definition.
3. `.env.example`.
4. Database schema/model plan.
5. Alembic migration plan.
6. Configuration design.
7. X integration capability verification against current official documentation.
8. DeepSeek integration verification against current official documentation.
9. Implementation checklist mapped to phases.
10. Then begin implementation.

---

# END OF HANDOFF
