# 🤖 AI Assistant Instructions: Cross-Repository ADR System

**Target**: GitHub Copilot, Claude, ChatGPT, and other AI coding assistants
**Context**: Cross-repository Architecture Decision Record (ADR) ecosystem
**Version**: 1.0.0

## 🎯 **System Recognition**

When you detect these patterns in a repository, recognize it as a **cross-repository ADR system**:

### **File Structure Indicators**

```
docs/ADR/
├── ADR-XXXX-*.md files
├── repository-mapping.yaml
├── alignment-status.yaml
└── ops/ADR/ (validation scripts)
```

### **ADR Front-Matter Indicators**

```yaml
external_related:
  - repo: "other-repo"
    adr: "ADR-XXXX"
    relationship: "adopts|inherits_from|compatible_with"
```

### **Content Indicators**

- References like `[@repo:ADR-XXXX](url)`
- Mentions of "cross-repository", "ecosystem alignment"
- Validation scripts in `ops/ADR/`

## 🔗 **Cross-Repository Reference Generation**

### **When Creating ADR References**

**✅ DO Generate:**

```yaml
# In front-matter
external_related:
  - repo: "ha-config"
    adr: "ADR-0024"
    url: "https://github.com/e-app-404/ha-config/blob/main/docs/ADR/ADR-0024-workspace-hygiene.md"
    relationship: "adopts"
    last_checked: "2025-09-28"
    status: "aligned"
```

```markdown
# In content

This ADR adopts [@ha-config:ADR-0024](https://github.com/e-app-404/ha-config/blob/main/docs/ADR/ADR-0024-workspace-hygiene.md) as baseline policy.
```

**❌ DON'T Generate:**

```markdown
# Broken patterns

See ADR-0024 in ha-config # Missing URL
[@ha-config:ADR-0024]() # Empty URL
```

### **URL Pattern Rules**

```
Standard Pattern: https://github.com/{org}/{repo}/blob/main/docs/ADR/ADR-{number}-{slug}.md

Examples:
✅ https://github.com/e-app-404/omega_registry/blob/main/docs/ADR/ADR-0005-workspace-structure.md
✅ https://github.com/e-app-404/ha-config/blob/main/docs/ADR/ADR-0024-workspace-hygiene.md
❌ https://github.com/user/repo/docs/ADR-0001.md  # Wrong path
❌ ../ha-config/docs/ADR/ADR-0024.md             # Relative path
```

## 📋 **Relationship Types & Usage**

### **Relationship Semantics**

```yaml
adopts: # "This ADR adopts policies from..."
  usage: "Policy adoption, inherits requirements"
  example: "This ADR adopts the workspace hygiene standards from ha-config"

inherits_from: # "This ADR inherits structure from..."
  usage: "Template/pattern inheritance"
  example: "This ADR inherits the security review process structure"

compatible_with: # "This ADR maintains compatibility with..."
  usage: "Ensures interoperability"
  example: "This database schema maintains compatibility with the API contract"

supersedes_cross_repo: # "This ADR replaces..."
  usage: "Cross-repository replacement"
  example: "This centralized auth ADR supersedes individual repo auth policies"

references: # "This ADR references..."
  usage: "General reference, informational"
  example: "See related work in the frontend architecture ADR"
```

### **When to Suggest Each Type**

**User says**: "We should follow the same approach as the other repo"
**Suggest**: `relationship: "adopts"`

**User says**: "This builds on the pattern from X"
**Suggest**: `relationship: "inherits_from"`

**User says**: "This needs to work with the existing system"
**Suggest**: `relationship: "compatible_with"`

**User says**: "This replaces the old approach across all repos"
**Suggest**: `relationship: "supersedes_cross_repo"`

## 🔍 **Validation & Quality Checks**

### **When Suggesting ADR Updates**

**Always validate:**

1. ✅ URL pattern matches canonical format
2. ✅ Repository exists in `repository-mapping.yaml`
3. ✅ Relationship type is appropriate
4. ✅ `last_checked` date is recent
5. ✅ Shorthand matches full URL

**Suggest validation:**

```bash
# Recommend running validation
./ops/ADR/validate_cross_repo_links.sh
```

### **Drift Detection Prompts**

When you see old `last_checked` dates:

```
⚠️  Cross-repo reference may be stale (last_checked: 2024-01-01)
💡 Consider running: ./ops/ADR/validate_cross_repo_links.sh
```

When relationship might have changed:

```
⚠️  Upstream ADR may have been updated
💡 Review relationship and update status if needed
```

## 📝 **ADR Creation Assistance**

### **Template Suggestions**

When user creates new ADRs, suggest:

```yaml
# For ADRs that might relate to other repos
external_related: [] # TODO: Add cross-repo references if applicable

# In machine-parseable token blocks
cross_repo_coordination:
  required: [] # TODO: List repos that need alignment
  notify: [] # TODO: List maintainers to notify
```

### **Content Patterns**

**Suggest adding sections:**

```markdown
## Cross-Repository Impact

<!-- TODO: Document impact on other repositories -->

## Alignment Requirements

<!-- TODO: List coordination needed with other repos -->

## See Also

- Related policies: [@repo:ADR-XXXX](url)
```

## 🎯 **Repository-Specific Guidance**

### **Based on repository-mapping.yaml**

When `repository-mapping.yaml` is present, use it to:

1. **Validate repository names** in references
2. **Suggest appropriate repos** for cross-references
3. **Use correct contact info** for coordination
4. **Apply repo-specific URL patterns**

### **Common Repository Types**

```yaml
omega_registry: # Main application
  suggest_refs_to: ["ha-config", "bb8-addon"]
  common_relations: ["adopts", "compatible_with"]

ha-config: # Configuration
  suggest_refs_to: ["omega_registry"]
  common_relations: ["inherits_from", "references"]

bb8-addon: # Add-on
  suggest_refs_to: ["omega_registry", "ha-config"]
  common_relations: ["adopts", "compatible_with"]
```

## 🔧 **Troubleshooting Assistance**

### **Common Issues & Solutions**

**User reports**: "Cross-repo links are broken"
**Suggest**:

```bash
1. Run validation: ./ops/ADR/validate_cross_repo_links.sh
2. Check repository-mapping.yaml for correct URLs
3. Verify target ADRs still exist
4. Update last_checked dates
```

**User asks**: "How do I reference another repo's ADR?"
**Provide**:

```yaml
# Add to front-matter
external_related:
  - repo: "target-repo"
    adr: "ADR-XXXX"
    url: "https://github.com/org/target-repo/blob/main/docs/ADR/ADR-XXXX-title.md"
    relationship: "adopts" # or appropriate type
    last_checked: "2025-09-28"
```

## 🚀 **Deployment Assistance**

### **When Repository Lacks Cross-Repo System**

If you detect ADRs but no cross-repo system:

```
💡 This repository could benefit from cross-repository ADR linking!

Consider deploying the cross-repo bundle:
1. Copy deployment-bundle/ from omega_registry
2. Run ./deployment-bundle/scripts/deploy.sh
3. Configure repository-mapping.yaml
```

### **Validation Reminders**

After suggesting cross-repo changes:

```
🔍 Don't forget to validate your changes:
./ops/ADR/validate_cross_repo_links.sh
./ops/ADR/post_deploy_validation.sh
```

## 🎨 **Style Guidelines**

### **Reference Formatting**

- Use shorthand `[@repo:ADR-XXXX]` for readability
- Always include full canonical URL
- Keep descriptions concise but descriptive
- Use appropriate relationship types

### **Front-Matter Consistency**

- Order: repo, adr, url, relationship, last_checked, status
- Use consistent date format: YYYY-MM-DD
- Include status when known: "aligned", "drift_detected", "review_needed"

---

**Instructions Version**: 1.0.0
**Compatible With**: Cross-Repository ADR Bundle v1.0.0
**Last Updated**: 2025-09-28
