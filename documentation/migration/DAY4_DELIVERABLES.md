# Day 4 Deliverables - OSS Staging Environment + Storage/Secrets + Healthcheck

Ngày thực hiện: 2026-02-21
Phụ thuộc từ Day 1-3:
- [DAY1_DELIVERABLES.md](DAY1_DELIVERABLES.md)
- [DAY2_DELIVERABLES.md](DAY2_DELIVERABLES.md)
- [DAY3_DELIVERABLES.md](DAY3_DELIVERABLES.md)

## 1) Môi trường OSS tối thiểu (dev/staging) đã dựng

Package triển khai:
- [../../infrastructure/docker/migration-day4/docker-compose.staging.yml](../../infrastructure/docker/migration-day4/docker-compose.staging.yml)

Thành phần đã bao gồm:
- Zookeeper
- Kafka
- Redis
- Airflow (db + init + webserver + scheduler)
- Prometheus

Cổng mặc định:
- Kafka: `9092`
- Redis: `6379`
- Airflow: `8080`
- Prometheus: `9090`

## 2) Kết nối storage + cấu hình credentials/secret manager

File env mẫu:
- [../../infrastructure/docker/migration-day4/.env.staging.example](../../infrastructure/docker/migration-day4/.env.staging.example)

Nội dung đã chuẩn hóa:
- Airflow DB credentials
- S3-compatible storage endpoint + key/secret
- Secret provider (Vault) placeholders
- Migration feature flags từ Day 3

## 3) Verify healthcheck toàn bộ service

Script verify:
- [../../infrastructure/docker/migration-day4/scripts/verify_healthchecks.sh](../../infrastructure/docker/migration-day4/scripts/verify_healthchecks.sh)

Prometheus scrape config:
- [../../infrastructure/docker/migration-day4/prometheus.yml](../../infrastructure/docker/migration-day4/prometheus.yml)

### Cách chạy nhanh
1. Copy env:
   - `cp infrastructure/docker/migration-day4/.env.staging.example infrastructure/docker/migration-day4/.env`
2. Chỉnh secrets thật trong file `.env`.
3. Start stack:
   - `docker compose -f infrastructure/docker/migration-day4/docker-compose.staging.yml --env-file infrastructure/docker/migration-day4/.env up -d`
4. Verify:
   - `bash infrastructure/docker/migration-day4/scripts/verify_healthchecks.sh`

## 4) Acceptance Day 4
- [x] Có môi trường OSS tối thiểu cho staging.
- [x] Có mẫu cấu hình storage + credentials + secret provider.
- [x] Có cơ chế verify healthcheck toàn bộ dịch vụ core.

## 5) Handoff Day 5
- Chạy smoke test end-to-end path OSS với dữ liệu mẫu.
- Bật dual-run ở staging với read path từ legacy.
- Sinh compare report baseline đầu tiên.
