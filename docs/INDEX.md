# Risk Manager V34 - Documentation Index

**Last Updated**: 2025-10-23
**Current Phase**: Phase 2 - SDK Integration

---

## 📖 Quick Navigation

### **Start Here**
- [README.md](../README.md) - Project overview and quick start
- [STATUS.md](../STATUS.md) - Current status and known issues

### **Latest Updates**
- [Project Summary](summary_2025-10-23.md) - Complete project snapshot (Oct 23, 2025)
- [Phase 2.1 Complete](progress/phase_2-1_complete_2025-10-23.md) - SDK integration milestone

### **Implementation**
- [Implementation Plan](implementation/plan_2025-10-23.md) - 5-week roadmap for full build

### **Architecture & Specifications**
- [PROJECT_DOCS/](PROJECT_DOCS/) - Complete v2 architecture and rule specifications
  - [Architecture v2](PROJECT_DOCS/architecture/system_architecture_v2.md)
  - [Rules](PROJECT_DOCS/rules/) - 12 risk rule specifications
  - [Modules](PROJECT_DOCS/modules/) - 4 core module specs

### **Quick Start**
- [Quick Start Guide](quickstart.md) - 5-minute setup

---

## 📁 Documentation Structure

```
docs/
├── INDEX.md                    # ← YOU ARE HERE (main navigation)
│
├── quickstart.md              # Quick start guide
├── summary_2025-10-23.md      # Project snapshot
│
├── implementation/            # Implementation plans
│   └── plan_2025-10-23.md    # Current implementation roadmap
│
├── progress/                  # Progress milestones
│   └── phase_2-1_complete_2025-10-23.md  # SDK integration complete
│
└── PROJECT_DOCS/              # Architecture & specifications (from v1)
    ├── INTEGRATION_NOTE.md    # How PROJECT_DOCS relate to v34
    ├── architecture/          # System architecture
    ├── rules/                 # 12 risk rule specs
    ├── modules/               # 4 core module specs
    └── api/                   # API integration docs
```

---

## 🗂️ Document Naming Convention

All dated documents follow this format:
- **Format**: `{type}_{YYYY-MM-DD}.md`
- **Examples**:
  - `summary_2025-10-23.md` - Project summary from Oct 23, 2025
  - `plan_2025-10-23.md` - Implementation plan from Oct 23, 2025
  - `phase_2-1_complete_2025-10-23.md` - Phase 2.1 milestone

**Why?**
- Easy to see what's current vs old
- Clear version history
- No confusion about which doc to read

---

## 🎯 What to Read for Different Goals

### **I want to understand the project**
1. Start: [README.md](../README.md)
2. Then: [Project Summary](summary_2025-10-23.md)
3. Dive: [Architecture v2](PROJECT_DOCS/architecture/system_architecture_v2.md)

### **I want to implement a new rule**
1. Read: [Implementation Plan](implementation/plan_2025-10-23.md)
2. Check: [Rule specifications](PROJECT_DOCS/rules/)
3. Reference: [Phase 2.1 Complete](progress/phase_2-1_complete_2025-10-23.md) for SDK integration examples

### **I want to fix an issue**
1. Check: [STATUS.md](../STATUS.md) for known issues
2. Reference: [SDK Integration](progress/phase_2-1_complete_2025-10-23.md) for architecture

### **I want to add a feature**
1. Review: [Implementation Plan](implementation/plan_2025-10-23.md) for roadmap
2. Study: [Architecture v2](PROJECT_DOCS/architecture/system_architecture_v2.md)
3. Follow: Existing patterns in [Phase 2.1](progress/phase_2-1_complete_2025-10-23.md)

---

## 📊 Project Status (Oct 23, 2025)

| Component | Status | Documentation |
|-----------|--------|---------------|
| **Foundation** | ✅ Complete | [Summary](summary_2025-10-23.md) |
| **SDK Integration** | ✅ Complete | [Phase 2.1](progress/phase_2-1_complete_2025-10-23.md) |
| **Rules (3/12)** | 🟡 In Progress | [Implementation Plan](implementation/plan_2025-10-23.md) |
| **State Management** | ⏳ Planned | [Implementation Plan](implementation/plan_2025-10-23.md) |
| **CLI** | ⏳ Planned | [Implementation Plan](implementation/plan_2025-10-23.md) |

---

## 🔄 Document Lifecycle

### **Active Documents** (Read These)
- [README.md](../README.md) - Always current
- [STATUS.md](../STATUS.md) - Always current
- [Project Summary](summary_2025-10-23.md) - Latest snapshot
- [Implementation Plan](implementation/plan_2025-10-23.md) - Current roadmap

### **Milestone Documents** (Reference)
- [Phase 2.1 Complete](progress/phase_2-1_complete_2025-10-23.md) - Completed milestone

### **Reference Documents** (Specifications)
- [PROJECT_DOCS/](PROJECT_DOCS/) - Architecture and rule specs

---

## 🗃️ Archive Policy

When a new version of a document is created:
1. **Keep** the old document with its date
2. **Update** this INDEX.md to point to the new version
3. **Mark** old documents with `[ARCHIVED]` prefix if superseded

Example:
```
docs/implementation/
├── plan_2025-10-23.md          # ← Current
└── [ARCHIVED]_plan_2025-10-15.md  # Old version (kept for history)
```

---

## 💡 Tips

- **For AI assistants**: Read the latest dated documents + PROJECT_DOCS/
- **For developers**: Start with README.md, then follow links
- **For reference**: PROJECT_DOCS/ has detailed specifications
- **For progress**: Check progress/ directory for milestones

---

## 📝 Contributing New Docs

When adding documentation:
1. **Use dates**: Name files with `{name}_{YYYY-MM-DD}.md`
2. **Update INDEX.md**: Add your doc to the appropriate section
3. **Link properly**: Use relative paths (e.g., `[Link](../README.md)`)
4. **Be specific**: Include "Last Updated" date at the top

---

**Need help?** Check [README.md](../README.md) or [STATUS.md](../STATUS.md)
