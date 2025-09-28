# ADR-{NUMBER}: {TITLE_HERE}

**Status**: {Proposed|Accepted|Rejected|Superseded|Deprecated}
**Date**: {YYYY-MM-DD}
**Author(s)**: {Author Name(s)}
**Reviewer(s)**: {Reviewer Name(s)}

## 🌐 Cross-Repository Context

**Related Repositories**:
- `{ORG}/{REPO}` - Primary implementation repository
- `{ORG}/{RELATED_REPO}` - Related/dependent repository
<!-- TODO: Add actual repository references -->

**Cross-References**:
```yaml
# Machine-parseable cross-references for validation
cross_repo_links:
  - repo: "{ORG}/{REPO}"
    adr: "ADR-{NUMBER}"
    status: "linked"
    relationship: "depends_on|implements|supersedes|related"
```

## 📋 Summary

<!-- Brief summary of the architectural decision -->
{BRIEF_ONE_PARAGRAPH_SUMMARY}

## 🎯 Problem Statement

### Context
<!-- What is the issue that we're seeing that is motivating this decision or change? -->

### Business Impact
<!-- How does this problem affect users, operations, or business objectives? -->

### Technical Impact
<!-- How does this problem affect the technical architecture, performance, or maintainability? -->

## 🏗️ Decision

<!-- What is the change that we're proposing or have agreed to implement? -->

### Architecture Overview
<!-- High-level architectural approach and key components -->

### Implementation Strategy
<!-- How will this decision be implemented across repositories? -->

## 🤔 Rationale

### Why This Approach?
<!-- Why is this the best option among alternatives considered? -->

### Key Benefits
<!-- What are the primary advantages of this decision? -->

### Trade-offs Accepted
<!-- What are we giving up or compromising on with this decision? -->

## 📊 Alternatives Considered

### Option 1: {ALTERNATIVE_NAME}
**Description**: {Brief description}
**Pros**: {Key advantages}
**Cons**: {Key disadvantages}
**Decision**: ❌ Rejected because {reason}

### Option 2: {ALTERNATIVE_NAME}
**Description**: {Brief description}
**Pros**: {Key advantages}
**Cons**: {Key disadvantages}
**Decision**: ❌ Rejected because {reason}

### Option 3: {ALTERNATIVE_NAME}
**Description**: {Brief description}
**Pros**: {Key advantages}
**Cons**: {Key disadvantages}
**Decision**: ❌ Rejected because {reason}

## 🛠️ Implementation Details

### Repository Impact Matrix
| Repository | Files Affected | Changes Required | Migration Needed |
|------------|----------------|------------------|------------------|
| `{ORG}/{REPO}` | {file paths} | {change type} | {yes/no} |
| `{ORG}/{RELATED_REPO}` | {file paths} | {change type} | {yes/no} |

### Technical Specifications
<!-- Detailed technical requirements, APIs, data structures, etc. -->

### Dependencies
**External Dependencies**:
- {Dependency name and version requirements}

**Internal Dependencies**:
- {Reference to other ADRs or architectural components}

### Migration Strategy
<!-- If applicable, how will existing systems be migrated? -->

## ✅ Acceptance Criteria

### Functional Requirements
- [ ] {Specific functional requirement}
- [ ] {Specific functional requirement}
- [ ] {Specific functional requirement}

### Non-Functional Requirements
- [ ] Performance: {Specific performance criteria}
- [ ] Security: {Specific security requirements}
- [ ] Reliability: {Specific reliability requirements}
- [ ] Maintainability: {Specific maintainability requirements}

### Cross-Repository Alignment
- [ ] All related repositories have been updated
- [ ] Cross-repository tests pass
- [ ] Documentation updated across all affected repositories
- [ ] Migration scripts tested and validated

## 🔍 Testing Strategy

### Test Coverage
<!-- What types of testing will validate this decision? -->

### Cross-Repository Testing
<!-- How will integration across repositories be tested? -->

### Rollback Plan
<!-- How can this decision be safely reversed if needed? -->

## 📈 Success Metrics

### Measurable Outcomes
- {Specific metric}: Target value and measurement method
- {Specific metric}: Target value and measurement method

### Timeline Expectations
- Implementation completion: {Date}
- Full rollout: {Date}
- First success metrics available: {Date}

## 🚨 Risks and Mitigation

### Technical Risks
| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|---------|---------------------|
| {Risk description} | High/Medium/Low | High/Medium/Low | {Mitigation approach} |

### Operational Risks
| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|---------|---------------------|
| {Risk description} | High/Medium/Low | High/Medium/Low | {Mitigation approach} |

## 🔗 Related Documents

### ADRs
- [`ADR-{NUMBER}`](ADR-{NUMBER}-{title}.md) - {Relationship description}
- Cross-repository: [`{ORG}/{REPO}/docs/ADR/ADR-{NUMBER}`]({REPO_URL}/docs/ADR/ADR-{NUMBER}-{title}.md)

### Documentation
- [Technical Specification]({URL})
- [API Documentation]({URL})
- [Migration Guide]({URL})

### References
- [External Reference]({URL})
- [Standards Document]({URL})

## 📝 Changelog

| Date | Change | Author |
|------|--------|--------|
| {YYYY-MM-DD} | Initial draft | {Author} |
| {YYYY-MM-DD} | {Change description} | {Author} |

---

**Validation Block** (Machine-parseable):
```yaml
adr_metadata:
  number: {NUMBER}
  title: "{TITLE_HERE}"
  status: "{STATUS}"
  created: "{YYYY-MM-DD}"
  last_modified: "{YYYY-MM-DD}"
  author: "{AUTHOR}"
  repository: "{ORG}/{REPO}"
  cross_repo_aligned: {true|false}
  validation_status: "pending|validated|invalid"
```

**Template Version**: 2.0.0 (Enhanced for Cross-Repository Usage)
**Last Updated**: 2025-09-28
