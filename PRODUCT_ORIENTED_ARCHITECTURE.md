# 🏢 Product-Oriented Architecture Design

**Ngày tạo**: 18/02/2026  
**Trạng thái**: Design Proposal

---

## 📊 Phân Tích Cấu Trúc Hiện Tại

### 1. Cấu Trúc Hiện Tại: Layer-Based Architecture

```
Data-Platform/
├── simulations/                 ← Data generation layer
├── ingestion_layer/             ← Kafka consumption
├── processing_layer/            ← Spark processing
├── lakehouse_layer/             ← Delta Lake storage
├── analytics_layer/             ← Analytics engines
├── bi_layer/                    ← BI & dashboards
├── monitoring_layer/            ← Monitoring & alerts
├── governance_layer/            ← Data governance
├── serving_layer/               ← API serving
└── serving_data/                ← Output data
```

### 2. Đặc Điểm: Tổ Chức Theo Tầng (Horizontal Slicing)

**Ưu điểm:**
- ✅ Kiến trúc hệ thống rõ ràng
- ✅ Dễ hiểu tính độc lập của các layer
- ✅ Dễ quản lý technical dependencies
- ✅ Tốt cho các dự án nhỏ đến vừa
- ✅ Phù hợp để học kiến trúc hệ thống

**Khuyết điểm:**
- ❌ **Khó mở rộng** với nhiều products/domains khác nhau
- ❌ **Khó tìm code** liên quan đến một use case cụ thể
- ❌ **Khó tổ chức team** theo product hoặc domain
- ❌ **Code scatter** - logic của một feature phân tán khắp các layer
- ❌ **Khó độc lập hóa** từng use case thành microservice
- ❌ **Khó quản lý ownership** - không rõ team nào chịu trách nhiệm sản phẩm nào
- ❌ **Khó versioning** - khi cần có nhiều phiên bản của cùng một product
- ❌ **Tight coupling** - các layer phụ thuộc vào nhau

---

## 💡 Cấu Trúc Mới: Product-Oriented Architecture

### 1. Nguyên Tắc Thiết Kế

```
Product-Oriented Architecture = Master-Detail Pattern in Folder Structure
```

**Mỗi product** là một **vertical slice** (cắt dọc) chứ không phải **horizontal slice** (cắt ngang):
- Mỗi product có đủ layers cần thiết (ingestion, processing, serving)
- Team này sở hữu toàn bộ product từ đầu đến cuối
- Dễ dàng deploy/scale từng product độc lập

### 2. Cấu Trúc Đề Xuất

```
Data-Platform/
│
├── 📦 PRODUCTS/                          ← Các sản phẩm dữ liệu
│   │
│   ├── 🎯 mobile-user-analytics/        ← Product: Mobile User Analytics
│   │   ├── PRODUCT_README.md            ← Product documentation
│   │   ├── docs/                        ← Product-specific docs
│   │   ├── src/
│   │   │   ├── ingestion/               ← Ingest mobile events from Kafka
│   │   │   │   ├── __init__.py
│   │   │   │   ├── consumer.py
│   │   │   │   ├── schema.py
│   │   │   │   └── validators.py
│   │   │   ├── processing/              ← Transform & aggregate
│   │   │   │   ├── __init__.py
│   │   │   │   ├── spark_jobs.py
│   │   │   │   ├── transformations.py
│   │   │   │   └── aggregations.py
│   │   │   ├── storage/                 ← Layer: Bronze/Silver/Gold
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bronze_schema.py
│   │   │   │   ├── silver_transforms.py
│   │   │   │   └── gold_metrics.py
│   │   │   ├── serving/                 ← Expose via API/analytics
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api_handlers.py
│   │   │   │   ├── query_service.py
│   │   │   │   └── cache_layer.py
│   │   │   ├── monitoring/              ← Product-specific monitoring
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health_checks.py
│   │   │   │   ├── metrics.py
│   │   │   │   └── alerts.py
│   │   │   └── tests/
│   │   │       ├── test_consumer.py
│   │   │       ├── test_processing.py
│   │   │       └── test_api.py
│   │   ├── config/
│   │   │   ├── product_config.yaml
│   │   │   └── environment/
│   │   ├── data/                        ← Product data outputs
│   │   │   ├── bronze/
│   │   │   ├── silver/
│   │   │   └── gold/
│   │   └── requirements.txt
│   │
│   ├── 🎯 web-user-analytics/           ← Product: Web User Analytics
│   │   ├── PRODUCT_README.md
│   │   ├── src/
│   │   │   ├── ingestion/
│   │   │   ├── processing/
│   │   │   ├── storage/
│   │   │   ├── serving/
│   │   │   ├── monitoring/
│   │   │   └── tests/
│   │   ├── config/
│   │   ├── data/
│   │   └── requirements.txt
│   │
│   ├── 🎯 user-segmentation/            ← Product: User Segmentation
│   │   ├── PRODUCT_README.md
│   │   ├── src/
│   │   │   ├── ingestion/   (consolidates data from mobile, web)
│   │   │   ├── processing/  (ML-based segmentation)
│   │   │   ├── storage/
│   │   │   ├── serving/
│   │   │   ├── monitoring/
│   │   │   └── tests/
│   │   ├── config/
│   │   ├── data/
│   │   └── requirements.txt
│   │
│   ├── 🎯 operational-metrics/          ← Product: Real-time KPIs
│   │   ├── PRODUCT_README.md
│   │   ├── src/
│   │   │   ├── ingestion/
│   │   │   ├── processing/
│   │   │   ├── storage/
│   │   │   ├── serving/
│   │   │   ├── monitoring/
│   │   │   └── tests/
│   │   ├── config/
│   │   ├── data/
│   │   └── requirements.txt
│   │
│   └── 🎯 compliance-auditing/          ← Product: Governance & Audit
│       ├── PRODUCT_README.md
│       ├── src/
│       │   ├── ingestion/    (lineage, access logs)
│       │   ├── processing/   (audit trails)
│       │   ├── storage/
│       │   ├── serving/
│       │   ├── monitoring/
│       │   └── tests/
│       ├── config/
│       ├── data/
│       └── requirements.txt
│
├── 🔧 SHARED/                           ← Shared infrastructure & libraries
│   │
│   ├── core/                            ← Core libraries
│   │   ├── __init__.py
│   │   ├── data_models.py               ← Shared data models
│   │   ├── utils/
│   │   │   ├── logger.py
│   │   │   ├── config_loader.py
│   │   │   ├── dataframe_utils.py
│   │   │   └── spark_utils.py
│   │   ├── connectors/
│   │   │   ├── kafka_connector.py
│   │   │   ├── delta_connector.py
│   │   │   ├── db_connector.py
│   │   │   └── api_client.py
│   │   ├── metrics/
│   │   │   ├── collector.py
│   │   │   └── prometheus_exporter.py
│   │   ├── monitoring/
│   │   │   ├── health_checker.py
│   │   │   ├── alerting.py
│   │   │   └── sla_tracker.py
│   │   └── governance/
│   │       ├── lineage_tracker.py
│   │       ├── quality_checker.py
│   │       ├── access_control.py
│   │       └── compliance_checker.py
│   │
│   ├── platform/                        ← Platform-level components
│   │   ├── __init__.py
│   │   ├── orchestrator.py              ← Master orchestrator (launches all products)
│   │   ├── api_gateway.py               ← Central API gateway
│   │   ├── catalog/                     ← Data catalog
│   │   │   ├── metadata_registry.py
│   │   │   ├── lineage_registry.py
│   │   │   └── discovery_engine.py
│   │   ├── admin/                       ← Admin & operations
│   │   │   ├── user_management.py
│   │   │   ├── role_management.py
│   │   │   └── system_config.py
│   │   └── reporting/                   ← Platform-wide reports
│   │       ├── platform_health.py
│   │       ├── usage_analytics.py
│   │       └── cost_analytics.py
│   │
│   └── tests/                           ← Integration & E2E tests
│       ├── integration_tests.py
│       ├── e2e_tests.py
│       └── fixtures/
│
├── 🔄 INFRASTRUCTURE/                   ← Infrastructure & DevOps
│   ├── docker/
│   │   ├── Dockerfile.base              ← Base image for all products
│   │   ├── Dockerfile.product           ← Product deployment template
│   │   └── docker-compose.yml           ← Local development environment
│   ├── k8s/                             ← Kubernetes manifests
│   │   ├── namespace.yaml
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── configmaps/
│   │   └── secrets/
│   ├── terraform/                       ← Infrastructure as Code
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── modules/
│   ├── monitoring/
│   │   ├── prometheus-config.yaml
│   │   ├── grafana-dashboards/
│   │   └── alerting-rules.yaml
│   └── ci-cd/
│       ├── .github/workflows/
│       ├── GitLab-CI.yaml
│       └── scripts/
│
├── 📚 DOCUMENTATION/                    ← Central documentation
│   ├── ARCHITECTURE.md
│   ├── DESIGN_DECISIONS.md
│   ├── DATA_MODELS.md
│   ├── API_CONTRACTS.md
│   ├── SETUP_GUIDE.md
│   ├── OPERATIONS_GUIDE.md
│   └── DEVELOPERS_GUIDE.md

├── 📊 DATA_LAKE/                        ← Physical data storage
│   ├── bronze/                          ← All bronze data
│   ├── silver/                          ← All silver data
│   └── gold/                            ← All gold data
│
├── 🧪 TESTS/                            ← Global test suite
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── performance/
│
├── configuration.yaml                   ← Global platform config
├── requirements.txt                     ← Core dependencies
├── Makefile                             ← Build automation
├── pytest.ini                           ← Test configuration
├── docker-compose.yml                   ← Local dev environment
└── README.md                            ← Getting started
```

---

## 🎯 So Sánh Chi Tiết

### Layer-Based vs Product-Oriented

| Tiêu Chí | Layer-Based | Product-Oriented |
|---------|------------|------------------|
| **Tổ chức** | Theo technical tiers | Theo business domains |
| **Ownership** | Chia sẻ giữa các layers | Rõ ràng per product |
| **Team Structure** | Platform teams | Product teams |
| **Code Discovery** | Phân tán khắp 9 folders | Tập trung 1 folder |
| **Scaling Products** | ❌ Khó | ✅ Dễ |
| **Independence** | ❌ Tight coupling | ✅ Loose coupling |
| **Microservices** | ❌ Khó | ✅ Dễ |
| **Versioning** | ❌ Phức tạp | ✅ Đơn giản |
| **Testing** | ❌ Phức tạp | ✅ Tự chứa |
| **Learning Curve** | ✅ Dễ hiểu | Trung bình |
| **Onboarding** | ❌ Phức tạp | ✅ Đơn giản |
| **CI/CD** | ❌ Monolithic | ✅ Per-product |
| **Deployment** | Tất cả cùng lúc | Độc lập per product |

---

## 🔄 Migration Strategy (Product-Based Refactoring)

### Giai Đoạn 1: Chuẩn Bị (Week 1)

1. **Tạo SHARED layer** - Extract common utilities
   ```python
   shared/
   ├── core/utils/
   ├── core/connectors/
   ├── core/monitoring/
   └── core/governance/
   ```

2. **Tạo stub cho mỗi Product**
   ```
   products/mobile-user-analytics/
   products/web-user-analytics/
   products/user-segmentation/
   ```

3. **Setup documentation** cho mỗi product

### Giai Đoạn 2: Refactoring (Week 2-4)

**Product 1: Mobile User Analytics**
- Move từ `simulations/mobile-sim` → `products/mobile-user-analytics/src/ingestion/`
- Move từ `processing_layer/` (mobile part) → `products/mobile-user-analytics/src/processing/`
- Move từ `lakehouse_layer/` (mobile tables) → `products/mobile-user-analytics/src/storage/`
- Move từ `analytics_layer/` (mobile metrics) → `products/mobile-user-analytics/src/serving/`
- Move từ `monitoring_layer/` (mobile alerts) → `products/mobile-user-analytics/src/monitoring/`

**Product 2: Web User Analytics**
- Tương tự Mobile Analytics

**Product 3: User Segmentation**
- Consolidates data từ Mobile & Web
- Thêm ML models
- Tạo separate serving APIs

**Product 4: Operational Metrics**
- Real-time KPIs & dashboards
- Aggregated từ tất cả products

**Product 5: Compliance & Auditing**
- Lineage & audit trails
- Access control

### Giai Đoạn 3: Integration (Week 5-6)

1. **Tạo Master Orchestrator** - Điều phối tất cả products
2. **API Gateway** - Unified access point
3. **Data Catalog** - Metadata nghiệp vụ
4. **Platform Monitoring** - Health dashboard

### Giai Đoạn 4: DevOps & CI/CD (Week 7-8)

1. **Docker** - Per-product containers
2. **Kubernetes** - Deployment manifests
3. **CI/CD Pipelines** - Per-product workflows
4. **Testing** - Unit, Integration, E2E

---

## 📈 Lợi Ích Của Kiến Trúc Mới

### 1. **Clarity & Maintainability**
```python
# Finding mobile user analytics code is now easy:
cd products/mobile-user-analytics/
ls  # Everything for this product is here!
```

### 2. **Team Autonomy**
- Team A owns `products/mobile-user-analytics/`
- Team B owns `products/web-user-analytics/`
- Team C owns `products/user-segmentation/`
- Minimal cross-team dependencies

### 3. **Scalability**
```
Before: Add new product = modify 9 layers + central orchestrator
After:  Add new product = create products/new-product/ folder
```

### 4. **Independent Deployment**
```bash
# Deploy only Mobile Analytics (no need to test everything)
make deploy-product PRODUCT=mobile-user-analytics VERSION=v2.1.0
```

### 5. **Microservices Ready**
```
Product → Container → K8s Pod → Independent scaling
```

### 6. **Versioning & Rollback**
```
products/mobile-user-analytics/
├── v1/
├── v2/  ← Current
└── v2-beta/
```

---

## 🏗️ Tiêu Chuẩn Cấu Trúc Product

Mỗi product phải có cấu trúc chuẩn:

```
products/{product-name}/
├── PRODUCT_README.md           (mô tả, owner, SLA)
├── VERSION                     (phiên bản hiện tại)
├── docs/
│   ├── DESIGN.md              (thiết kế sản phẩm)
│   ├── METRICS.md             (KPIs)
│   ├── API.md                 (API specs)
│   └── TROUBLESHOOTING.md
├── src/
│   ├── ingestion/             (input pipelines)
│   ├── processing/            (transformations)
│   ├── storage/               (data layers)
│   ├── serving/               (outputs & APIs)
│   ├── monitoring/            (health & alerts)
│   └── tests/
├── config/
│   ├── product_config.yaml
│   ├── dev.env
│   ├── staging.env
│   └── prod.env
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── requirements.txt
├── Dockerfile
├── pytest.ini
└── Makefile
```

---

## 🔧 Configuration Management

### Global Configuration
```yaml
# configuration.yaml (root level)
platform:
  name: Data Platform
  version: 1.0.0
  environment: production
  
kafka:
  brokers: ["kafka:9092"]
  
spark:
  master: "spark://spark-master:7077"
  
delta_lake:
  path: "/data/lake"
  
products:
  - mobile-user-analytics
  - web-user-analytics
  - user-segmentation
  - operational-metrics
  - compliance-auditing
```

### Product-Specific Configuration
```yaml
# products/mobile-user-analytics/config/product_config.yaml
product:
  name: Mobile User Analytics
  owner: platform-team-mobile
  sla_uptime: 99.9%
  
ingestion:
  topics: ["topic_app_events", "topic_mobile_sessions"]
  consumer_group: "mobile-analytics-consumer"
  
processing:
  spark_app_name: "mobile-user-analytics-processor"
  batch_interval: 10  # seconds
  
serving:
  api_port: 8001
  cache_ttl: 3600
```

---

## 📋 Implementation Checklist

- [ ] **Phase 1: Setup SHARED layer**
  - [ ] Create `shared/core/` structure
  - [ ] Extract common utilities
  - [ ] Create shared test fixtures
  
- [ ] **Phase 2: Create product stubs**
  - [ ] `products/mobile-user-analytics/`
  - [ ] `products/web-user-analytics/`
  - [ ] `products/user-segmentation/`
  - [ ] `products/operational-metrics/`
  - [ ] `products/compliance-auditing/`
  
- [ ] **Phase 3: Migrate Mobile Analytics**
  - [ ] Move ingestion code
  - [ ] Move processing code
  - [ ] Move storage schemas
  - [ ] Move serving APIs
  - [ ] Move tests
  - [ ] Update documentation
  
- [ ] **Phase 4: Migrate Web Analytics**
  - [ ] Move code (similar to Mobile)
  - [ ] Test integration
  
- [ ] **Phase 5: Create consolidated products**
  - [ ] User Segmentation (consolidates Mobile + Web)
  - [ ] Operational Metrics
  - [ ] Compliance & Auditing
  
- [ ] **Phase 6: Platform integration**
  - [ ] Master orchestrator
  - [ ] API gateway
  - [ ] Data catalog
  - [ ] Admin console
  
- [ ] **Phase 7: DevOps**
  - [ ] Per-product Dockerfiles
  - [ ] K8s manifests
  - [ ] CI/CD pipelines
  - [ ] Monitoring dashboards

---

## 🎓 Best Practices

### 1. **Conway's Law**
> "Organizations which design systems are constrained to produce designs which are copies of  the communication structures of these organizations." - Melvin Conway

🎯 **Ứng dụng**: Cấu trúc folder nên phản ánh cấu trúc team

### 2. **Domain-Driven Design (DDD)**
🎯 **Ứng dụng**: Mỗi product là một **Bounded Context**

### 3. **Vertical Slicing**
🎯 **Ứng dụng**: Mỗi feature xuyên qua toàn bộ stack

### 4. **Clear Ownership**
```
CODEOWNERS file:
products/mobile-user-analytics/ @team-mobile
products/web-user-analytics/ @team-web
shared/core/ @platform-team
```

---

## 📞 Decision Matrix

**Khi nào nên dùng Product-Oriented Architecture?**

✅ **DÙNG khi:**
- 3+ independent business domains/products
- Multiple teams working in parallel
- Need independent deployment cycles
- Plan to open-source individual components
- Different SLAs for different products
- Need to scale products independently

❌ **KHÔNG nên dùng khi:**
- Single monolithic platform
- All features tightly coupled
- Small team (<5 people)
- Simple analytics pipeline
- All code changes always deployed together

---

## 🚀 Conclusion

**Product-Oriented Architecture** là tiếp cận tốt hơn cho:
- ✅ Scaling teams
- ✅ Multiple independent products
- ✅ Clear ownership & accountability
- ✅ Independent deployments
- ✅ Future microservices transition

**Current Layer-Based Architecture** tốt cho:
- ✅ Learning infrastructure
- ✅ Understanding data flow
- ✅ Small monolithic platform
- ✅ Centralized governance

**Đề xuất**: Thực hiện **phân giai đoạn** từ Layer-Based → Product-Oriented, không migration one-shot.

---

## 📚 References

- Domain-Driven Design: Eric Evans
- Building Microservices: Sam Newman
- Team Topologies: Matthew Skelton & Manuel Pais
- The Phoenix Project: Gene Kim
- Product-Based Org Structure: Spotify Model

