# 🏢 Data Platform - Product-Oriented Architecture V2

[![Data Platform CI](https://github.com/hathientuyethy2004-del/Data-Platform/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/hathientuyethy2004-del/Data-Platform/actions/workflows/ci.yml)

**Status**: 🟢 50% IMPLEMENTATION COMPLETE - 3/5 Products Production-Ready  
**Date**: February 18, 2026  
**Completed**: web-analytics (8.5K LOC), ops-metrics (2.9K LOC), compliance-auditing (2.8K LOC)

---

## 🎯 What This Is

A **comprehensive refactoring plan and implementation framework** to migrate the Data Platform from a **Layer-Based Architecture** (current state in `examples/`) to a **Product-Oriented Architecture** (new structure with 5 focused products).

### Current State
```
examples/
├── ingestion_layer/      ← 9 independent layers
├── processing_layer/
├── lakehouse_layer/
├── analytics_layer/
├── bi_layer/
├── monitoring_layer/
├── governance_layer/
├── serving_layer/
└── ...
```

### Target State
```
products/                  ← 5 focused products
├── mobile-user-analytics/
├── web-user-analytics/
├── user-segmentation/
├── operational-metrics/
└── compliance-auditing/

shared/                    ← Shared infrastructure
├── core/
├── platform/
└── tests/
```

---

## 📊 Implementation Status

| Component | Status | Metrics | Notes |
|-----------|--------|---------|-------|
| **Framework** | ✅ Complete | 102 dirs, 50+ files | All structures ready |
| **Products Implemented** | 🟢 3/5 | 27 modules, 14.2K LOC | web, ops, compliance |
| **Products In Progress** | 🟡 1/5 | 2 modules, 900 LOC | user-segmentation |
| **Products Template** | ⏳ 1/5 | Full template | mobile-user-analytics |
| **API Endpoints** | ✅ 26+ | Fully functional | ops-metrics, compliance, web |
| **Test Cases** | ✅ 60+ | Unit + integration | Comprehensive coverage |
| **Delta Tables** | ✅ 30+ | Bronze/Silver/Gold | Per-product schemas |
| **SHARED layer** | ✅ Structure | 13 dirs ready | Awaiting shared code extraction |
| **Infrastructure** | ✅ Templates | docker, k8s, terraform | Ready to use |
| **Documentation** | ✅ Complete | 2,300+ lines | All products documented |

---

## 🌐 Platform API Gateway Configuration

The platform gateway at `shared/platform/api_gateway.py` now supports service URL configuration by environment.

### Environment Selection

Set active environment:

```bash
export PLATFORM_ENV=dev      # dev | staging | prod
```

### Override Options (priority order)

1. **Global override (all environments)**

```bash
export PLATFORM_PRODUCT_SERVICES_JSON='[
    {"name": "web-user-analytics", "base_url": "http://localhost:8002"},
    {"name": "operational-metrics", "base_url": "http://localhost:8003"}
]'
```

2. **Environment map override**

```bash
export PLATFORM_PRODUCT_SERVICES_BY_ENV_JSON='{
    "dev": [
        {"name": "web-user-analytics", "base_url": "http://localhost:8002"}
    ],
    "staging": [
        {"name": "web-user-analytics", "base_url": "http://staging-web:9100"}
    ],
    "prod": [
        {"name": "web-user-analytics", "base_url": "http://prod-web:9200"}
    ]
}'
```

3. **Environment-specific override**

```bash
export PLATFORM_ENV=staging
export PLATFORM_PRODUCT_SERVICES_STAGING_JSON='[
    {"name": "web-user-analytics", "base_url": "http://staging-web:9100"},
    {"name": "operational-metrics", "base_url": "http://staging-ops:9101"}
]'
```

### Run Gateway

```bash
PYTHONPATH=. uvicorn shared.platform.api_gateway:app --host 0.0.0.0 --port 8000
```

### Runtime Inspection

- `GET /health` → gateway + per-service health (includes active environment)
- `GET /services` → resolved service registry for current environment
- `GET /environment` → active env and supported override variables

### DevOps Quick Preset (`.env.gateway`)

```bash
cd /workspaces/Data-Platform
source .env.gateway

# Choose one environment preset
gateway_env_dev
# gateway_env_staging
# gateway_env_prod

# Optional: verify active vars
gateway_show_env

# Run gateway
gateway_run
```

---

## 📚 Key Documentation

Read in this order:

### 1. **[PRODUCT_ORIENTED_ARCHITECTURE.md](PRODUCT_ORIENTED_ARCHITECTURE.md)** ← START HERE
**The "Why"** - Understand the architecture decision

- Current layer-based architecture analysis
- Product-oriented architecture design
- Comparison table
- Best practices (Conway's Law, DDD, Vertical Slicing)
- Decision matrix (when to use)
- **Time to read**: 30-45 minutes

### 2. **[BUILD_PLAN.md](BUILD_PLAN.md)**
**The "How"** - Detailed 8-week implementation timeline

- Phase 1-6 breakdown (2 weeks each)
- Parallel workstreams
- Team allocation
- Detailed tasks with code examples
- Risk management & mitigation
- Success criteria
- **Time to read**: 45-60 minutes

### 3. **[ARCHITECTURE_V2_OVERVIEW.md](ARCHITECTURE_V2_OVERVIEW.md)**
**The "What"** - Quick reference for directory structure

- Current directory map (with ✅ done / 👉 TODO)
- Migration statistics
- Expected outcomes
- Quick links
- **Time to read**: 15-20 minutes

### 4. **[COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md)**
**The "Status"** - What's been built and what's next

- Files created
- Templates included
- Metrics & statistics
- Next actions by role
- **Time to read**: 15 minutes

### 5. **[documentation/UI_SPEC_REACT_FASTAPI.md](documentation/UI_SPEC_REACT_FASTAPI.md)**
**The "UI + API Contract"** - Detailed frontend/backend spec for operations console

- Screen-by-screen UI specification
- Component contract and UX states
- FastAPI endpoint matrix + envelope/error model
- React frontend structure and TypeScript contracts
- **Time to read**: 25-35 minutes

---

## 🚀 Quick Start (5 Minutes)

### Pre-merge Test Gate (Team Standard)

Use one unified command before opening/approving PRs:

```bash
./pre_merge_tests.sh
```

This script runs shared tests first, then product tests in the stable repo order used by CI.

### For Developers
```bash
# 1. Check product structure
ls -la products/mobile-user-analytics/

# 2. Review product documentation
cat products/mobile-user-analytics/PRODUCT_README.md

# 3. Check available configuration
cat products/mobile-user-analytics/config/product_config.yaml

# 4. Start coding in src/
cd products/mobile-user-analytics/src/ingestion
# Add your code here following the template
```

### For DevOps/SRE
```bash
# 1. Review infrastructure templates
ls -la infrastructure/

# 2. Check Dockerfile template
cat products/mobile-user-analytics/Dockerfile

# 3. Review Makefile
cat products/mobile-user-analytics/Makefile

# 4. Update Kubernetes manifests
cd infrastructure/k8s/deployments
# Create product-specific manifests
```

### For Product Managers
```bash
# 1. Understand product structure
cat products/mobile-user-analytics/PRODUCT_README.md

# 2. Check KPI definitions
cat products/mobile-user-analytics/docs/METRICS.md

# 3. Review configuration
cat products/mobile-user-analytics/config/product_config.yaml
```

---

## 🏗️ The Complete Structure

### Products (5 × fully independent)
```
products/
├── mobile-user-analytics/       ✅ Fully documented template
│   ├── PRODUCT_README.md        ✅ Owner, SLA, team
│   ├── src/ingestion/           ✅ Kafka consumers
│   ├── src/processing/          ✅ Spark jobs
│   ├── src/storage/             ✅ Delta schemas
│   ├── src/serving/             ✅ REST APIs
│   ├── src/monitoring/          ✅ Health checks
│   ├── config/
│   │   └── product_config.yaml  ✅ Full config template
│   ├── docs/
│   │   ├── DESIGN.md            ✅ Design document
│   │   ├── METRICS.md           ✅ KPI definitions
│   │   └── API.md               ✅ API reference
│   ├── data/bronze,silver,gold/ ✅ Data layers
│   ├── Dockerfile              ✅ Multi-stage build
│   ├── Makefile                ✅ Development commands
│   └── requirements.txt        ✅ Dependencies
│
├── web-user-analytics/          ✅ Structure + basic docs
├── user-segmentation/           ✅ Structure + basic docs
├── operational-metrics/         ✅ Structure + basic docs
└── compliance-auditing/         ✅ Structure + basic docs
```

### Shared Infrastructure
```
shared/
├── core/
│   ├── utils/           ✅ Logging, config, dataframe utils
│   ├── connectors/      ✅ Kafka, Delta, DB connectors
│   ├── metrics/         ✅ Prometheus metrics
│   ├── monitoring/      ✅ Health checks, alerting
│   └── governance/      ✅ Quality, lineage, access control
│
├── platform/
│   ├── orchestrator.py  👉 TODO: Master coordinator
│   ├── api_gateway.py   👉 TODO: Central gateway
│   ├── catalog/         ✅ Metadata registry
│   ├── admin/           ✅ User management
│   └── reporting/       ✅ Platform reporting
│
└── tests/
    ├── fixtures/        ✅ Pytest fixtures
    ├── integration_tests.py  👉 TODO
    └── e2e_tests.py          👉 TODO
```

### Infrastructure & DevOps
```
infrastructure/
├── docker/              ✅ Docker templates
├── k8s/                 ✅ Kubernetes manifests
├── terraform/           ✅ Infrastructure as Code
├── monitoring/          ✅ Prometheus/Grafana
└── ci-cd/               ✅ GitHub Actions templates
```

### Data Lake & Tests
```
data_lake/              ✅ Bronze/Silver/Gold
tests/                  ✅ Unit/Integration/E2E/Performance
documentation/          ✅ Central docs hub
```

---

## 🎯 Implementation Timeline

### Quick View
```
Week 1-2:  SHARED Layer (infrastructure team)
Week 3:    Product Templates Finalization (all teams)
Week 4-5:  Mobile Analytics Migration (mobile team)
Week 6-7:  Web, Segmentation, Ops, Compliance (multi-team)
Week 8:    DevOps & Integration (DevOps team + QA)
```

**See [BUILD_PLAN.md](BUILD_PLAN.md) for detailed breakdown with specific tasks.**

---

## 💡 How It Works

### Example: Access Mobile User Analytics Code

**Before** (Layer-based):
```
Find "mobile" code scattered across:
- examples/ingestion_layer/consumers/app_events_consumer.py
- examples/processing_layer/spark_jobs_mobile.py
- examples/lakehouse_layer/schemas/mobile_schema.py
- examples/analytics_layer/mobile_analytics.py
- examples/monitoring_layer/mobile_monitors.py
```

**After** (Product-oriented):
```
Everything for mobile analytics is in ONE place:
products/mobile-user-analytics/
├── src/ingestion/consumer.py
├── src/processing/spark_jobs.py
├── src/storage/schemas.py
├── src/serving/api.py
└── src/monitoring/health_checks.py
```

### Example: Add New Product

**Time**: ~1 day (vs 1 month)

```bash
# 1. Create folder (1 minute)
mkdir -p products/new-analytics/src/{ingestion,processing,storage,serving,monitoring,tests}

# 2. Copy templates (5 minutes)
cp products/mobile-user-analytics/{PRODUCT_README.md,config,docs,Dockerfile,Makefile} \
   products/new-analytics/

# 3. Update config (30 minutes)
vim products/new-analytics/config/product_config.yaml

# 4. Start coding (remaining day)
# Done! New product is now part of platform
```

---

## 🔑 Key Benefits

| Benefit | Before | After |
|---------|--------|-------|
| **Code Discovery** | Search 9 layers | Look in 1 product folder |
| **Team Ownership** | Unclear | Crystal clear |
| **Deployment** | All monolith (2 hours) | Per-product (<15 min) |
| **New Product** | 1 month | 1-2 days |
| **Microservices** | Hard to split | Easy to containerize |
| **Test Speed** | All tests | Product-specific only |
| **Onboarding** | Complex | Easy to understand |

---

## 📋 Next Steps by Role

### Technical Lead
1. [ ] Read PRODUCT_ORIENTED_ARCHITECTURE.md
2. [ ] Review BUILD_PLAN.md
3. [ ] Approve ARCHITECTURE_V2_OVERVIEW.md
4. [ ] Schedule kickoff meeting

### Project Manager
1. [ ] Review BUILD_PLAN.md timeline
2. [ ] Allocate resources per phase
3. [ ] Set up tracking (Jira/GitHub Projects)
4. [ ] Plan team communication

### Team Leads
1. [ ] Identify your team's product(s)
2. [ ] Review product-specific PRODUCT_README.md
3. [ ] Plan Week 1-2 (SHARED layer) work
4. [ ] Prepare for your product migration phase

### Developers
1. [ ] Check `products/{your-product}/`
2. [ ] Read PRODUCT_README.md
3. [ ] Review documentation templates
4. [ ] Wait for Week X when your product migrates

### DevOps/SRE
1. [ ] Review infrastructure/ templates
2. [ ] Plan Docker image strategy
3. [ ] Prepare Kubernetes manifests
4. [ ] Set up CI/CD pipelines

---

## 🎓 Learning Path

### 1. Understand Why (15 min)
- Read "The Problem" section in PRODUCT_ORIENTED_ARCHITECTURE.md
- Review Conway's Law & DDD concepts
- Check current vs proposed comparison table

### 2. Understand How (45 min)
- Read BUILD_PLAN.md phases 1-3
- Understand dependency graph
- Check risk mitigation strategies

### 3. Understand Where (15 min)
- Review ARCHITECTURE_V2_OVERVIEW.md
- Check products/mobile-user-analytics/
- Understand directory structure

### 4. Start Building (following BUILD_PLAN.md)
- Phase 1: Extract SHARED utilities
- Phase 2: Create product stubs
- Phase 3: Migrate first product
- Etc.

---

## 🚨 Important Notes

### ℹ️ Current Code is Safe
- All existing code in `examples/` is untouched
- No breaking changes to current platform
- Migration is phased (not one-shot)
- Can rollback at any time

### 🔄 Parallel Development Possible
- Products can be migrated simultaneously
- Different teams work on different products
- SHARED layer is extracted first (no dependencies)

### ✅ Framework is Ready Now
- All directories created
- All templates prepared
- All documentation written
- Ready to start implementation immediately

---

## 📞 For Questions

| Question | Answer Location |
|----------|-----------------|
| **Why change architecture?** | PRODUCT_ORIENTED_ARCHITECTURE.md |
| **How long will it take?** | BUILD_PLAN.md (8 weeks) |
| **What's the directory structure?** | ARCHITECTURE_V2_OVERVIEW.md |
| **What's been completed?** | COMPLETION_SUMMARY.md |
| **How do I start?** | BUILD_PLAN.md, Phase 1 |
| **What does my product look like?** | products/mobile-user-analytics/ |

---

## 🎉 Let's Build!

The framework is ready. The plan is detailed. The templates are complete.

**Next step**: Follow [BUILD_PLAN.md](BUILD_PLAN.md) Week 1-2 to start building the SHARED layer.

**Questions?** Review the documentation above or check the product examples.

**Ready?** Let's implement Product-Oriented Data Platform V2! 🚀

---

## 📚 File Structure

```
Data-Platform/ (root)
├── README.md                                    ← You are here
├── PRODUCT_ORIENTED_ARCHITECTURE.md             ← Design & rationale
├── BUILD_PLAN.md                                ← 8-week timeline
├── ARCHITECTURE_V2_OVERVIEW.md                  ← Directory reference
├── COMPLETION_SUMMARY.md                        ← What's been built
│
├── products/                                    ← 5 focused products
│   ├── mobile-user-analytics/                   ← See this for full example
│   ├── web-user-analytics/
│   ├── user-segmentation/
│   ├── operational-metrics/
│   └── compliance-auditing/
│
├── shared/                                      ← Shared infrastructure
│   ├── core/                                    ← Common utilities
│   ├── platform/                                ← Platform orchestration
│   └── tests/                                   ← Shared fixtures
│
├── infrastructure/                              ← DevOps templates
│   ├── docker/
│   ├── k8s/
│   ├── terraform/
│   ├── monitoring/
│   └── ci-cd/
│
├── data_lake/                                   ← Data storage
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── tests/                                       ← Global test suite
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── performance/
│
├── documentation/                               ← Central docs hub
│
└── examples/                                    ← Current code (untouched)
    ├── ingestion_layer/
    ├── processing_layer/
    └── ... (all current layers)
```

---

**Created**: 2024-02-18  
**Status**: ✅ Ready for Implementation  
**Framework**: Complete & Tested

