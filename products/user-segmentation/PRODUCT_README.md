# 🔀 User Segmentation Product

**Owner**: @team-ml  
**SLA**: 99.5% uptime  

---

## 🎯 Overview

User Segmentation consolidates data from Mobile and Web User Analytics to create ML-based user segments.

### Key Segments
- **VIP Users**: High-value, frequent users
- **Active Users**: Regular engagement
- **At-Risk Users**: Churning risk
- **Dormant Users**: Inactive >30 days
- **New Users**: Created in last 7 days

### Use Cases
- Targeted marketing campaigns
- Product personalization
- Retention focus areas
- Premium feature targeting

---

## 🏗️ Data Sources

- `products/mobile-user-analytics/` - Mobile behavior
- `products/web-user-analytics/` - Web behavior
- External data: CRM, payment systems (optional)

## 🔄 Processing

ML-based segmentation:
1. Feature engineering from mobile + web data
2. K-means clustering
3. Behavioral rule application
4. Segment embedding for recommendation systems

See full design in `products/user-segmentation/` 
