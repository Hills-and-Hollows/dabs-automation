# Technical Architecture Specification

## 🏗️ **SSCS Integration Architecture (Updated)**

### **EDI Integration Layer**
```mermaid
graph LR
    A[DABS Excel] --> B[NAXML Generator]
    B --> C[EDI Email Service]
    C --> D[@edidelivery.com]
    D --> E[SSCS CDB Auto-Import]
    E --> F[Price Change Alerts]
    E --> G[POS Distribution]
```

### **Official SSCS EDI Standards**
- **Format**: NAXML (NACS XML) - officially supported
- **Delivery**: Email-based EDI channel
- **Processing**: Automatic CDB vendor import
- **Validation**: Built-in SSCS price/item alerts
