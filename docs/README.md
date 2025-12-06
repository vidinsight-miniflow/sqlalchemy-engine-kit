# Documentation

Welcome to the sqlalchemy-engine-kit documentation!

## 📚 Documentation Index

### 🚀 Getting Started

| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Get up and running in 5 minutes |
| **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** | Migrate from vanilla SQLAlchemy to engine-kit |

### 📖 Usage Guides

| Document | Description |
|----------|-------------|
| **[API_REFERENCE.md](API_REFERENCE.md)** | Complete API documentation - all classes, methods, and parameters |
| **[EXAMPLES.md](EXAMPLES.md)** | Real-world examples and framework integrations (Flask, FastAPI, Django) |
| **[BEST_PRACTICES.md](BEST_PRACTICES.md)** | Best practices, anti-patterns, and performance tips |
| **[OPTIONAL_DEPENDENCIES.md](OPTIONAL_DEPENDENCIES.md)** | How optional dependencies work and are handled |

### 🏗️ Architecture & Design

| Document | Description |
|----------|-------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical architecture, design patterns, and implementation details |

### 🚢 Operations & Deployment

| Document | Description |
|----------|-------------|
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Production deployment guide and environment setup |
| **[LOGGING_AND_MONITORING.md](LOGGING_AND_MONITORING.md)** | Configure logging and monitoring (modular approach) |
| **[RUNBOOK.md](RUNBOOK.md)** | Troubleshooting guide for common issues |
| **[PRODUCTION_READINESS_CHECKLIST.md](PRODUCTION_READINESS_CHECKLIST.md)** | Checklist for production readiness |

---

## 🎯 Quick Navigation by Use Case

### I'm New Here
1. Start with **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
2. Check **[EXAMPLES.md](EXAMPLES.md)** - See real-world usage
3. Read **[BEST_PRACTICES.md](BEST_PRACTICES.md)** - Learn the right way

### I Want to Migrate from SQLAlchemy
1. Read **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Step-by-step migration
2. Check **[EXAMPLES.md](EXAMPLES.md)** - Before/after comparisons
3. Review **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API reference

### I Need to Deploy to Production
1. Read **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production setup
2. Configure **[LOGGING_AND_MONITORING.md](LOGGING_AND_MONITORING.md)** - Observability
3. Bookmark **[RUNBOOK.md](RUNBOOK.md)** - Troubleshooting
4. Check **[PRODUCTION_READINESS_CHECKLIST.md](PRODUCTION_READINESS_CHECKLIST.md)** - Final checklist

### I Want to Understand the Architecture
1. Read **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep dive
2. Check **[API_REFERENCE.md](API_REFERENCE.md)** - Implementation details
3. Review **[BEST_PRACTICES.md](BEST_PRACTICES.md)** - Design patterns

### I'm Having Issues
1. Check **[RUNBOOK.md](RUNBOOK.md)** - Common problems and solutions
2. Review **[OPTIONAL_DEPENDENCIES.md](OPTIONAL_DEPENDENCIES.md)** - Dependency issues
3. See **[EXAMPLES.md](EXAMPLES.md)** - Working examples

---

## 📋 Documentation Structure

```
docs/
├── README.md (this file)
│
├── Getting Started
│   ├── QUICKSTART.md
│   └── MIGRATION_GUIDE.md
│
├── Usage
│   ├── API_REFERENCE.md
│   ├── EXAMPLES.md
│   ├── BEST_PRACTICES.md
│   └── OPTIONAL_DEPENDENCIES.md
│
├── Architecture
│   └── ARCHITECTURE.md
│
└── Operations
    ├── DEPLOYMENT.md
    ├── LOGGING_AND_MONITORING.md
    ├── RUNBOOK.md
    └── PRODUCTION_READINESS_CHECKLIST.md
```

---

## 🔍 Finding What You Need

### By Topic

**Session Management**
- [API_REFERENCE.md](API_REFERENCE.md) → Decorators section
- [EXAMPLES.md](EXAMPLES.md) → Flask/FastAPI examples
- [BEST_PRACTICES.md](BEST_PRACTICES.md) → Session management best practices

**Connection Pooling**
- [API_REFERENCE.md](API_REFERENCE.md) → DatabaseEngine section
- [ARCHITECTURE.md](ARCHITECTURE.md) → Connection Pooling section
- [DEPLOYMENT.md](DEPLOYMENT.md) → Connection pool configuration

**Migrations**
- [API_REFERENCE.md](API_REFERENCE.md) → Migrations section
- [EXAMPLES.md](EXAMPLES.md) → Migration examples
- [OPTIONAL_DEPENDENCIES.md](OPTIONAL_DEPENDENCIES.md) → Alembic setup

**Monitoring**
- [API_REFERENCE.md](API_REFERENCE.md) → Monitoring section
- [LOGGING_AND_MONITORING.md](LOGGING_AND_MONITORING.md) → Complete guide
- [EXAMPLES.md](EXAMPLES.md) → Custom monitor examples

**Error Handling**
- [API_REFERENCE.md](API_REFERENCE.md) → Exceptions section
- [BEST_PRACTICES.md](BEST_PRACTICES.md) → Error handling patterns
- [RUNBOOK.md](RUNBOOK.md) → Common errors

---

## 💡 Tips

1. **New users**: Start with QUICKSTART.md, then EXAMPLES.md
2. **Experienced developers**: Jump to API_REFERENCE.md for specific details
3. **Production deployment**: Follow DEPLOYMENT.md → LOGGING_AND_MONITORING.md → RUNBOOK.md
4. **Troubleshooting**: Check RUNBOOK.md first, then relevant sections in other docs

---

## 📝 Contributing to Documentation

Found an error or want to improve the docs? 

1. Check the main [README.md](../README.md) for contribution guidelines
2. Keep documentation clear and example-focused
3. Update this index if adding new documents

---

## 🔗 External Resources

- **GitHub Repository**: [sqlalchemy-engine-kit](https://github.com/vidinsight/sqlalchemy-engine-kit)
- **Issues**: [Report bugs or request features](https://github.com/vidinsight/sqlalchemy-engine-kit/issues)
- **SQLAlchemy Docs**: [Official SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- **Alembic Docs**: [Database Migration Tool](https://alembic.sqlalchemy.org/)

---

**Last Updated**: 2024-12-06  
**Version**: 0.1.0

