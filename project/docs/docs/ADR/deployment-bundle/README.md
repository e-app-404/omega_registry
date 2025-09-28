# 📦 Cross-Repository ADR Deployment Bundle

**Version**: 1.0.0
**Date**: 2025-09-28
**Compatibility**: All repositories in the omega_registry ecosystem

## 🎯 **Overview**

This deployment bundle enables **cross-repository ADR alignment and linking** across your entire repository ecosystem. It provides standardized templates, automated deployment, and validation tools for maintaining architectural coherence while preserving local autonomy.

## 🚀 **Quick Start**

### For Any Repository in Your Ecosystem:

```bash
# 1. Copy the bundle to target repository
cp -r docs/ADR/deployment-bundle /path/to/other-repo/

# 2. Deploy automatically
cd /path/to/other-repo/
./deployment-bundle/scripts/deploy.sh

# 3. Validate deployment
./deployment-bundle/scripts/post_deploy_validation.sh
```

**That's it!** The system will automatically:
- ✅ Create all necessary directories
- ✅ Deploy and customize templates
- ✅ Set up validation scripts
- ✅ Update ADR index
- ✅ Configure .gitignore
- ✅ Backup existing files
- ✅ Validate deployment success

## 📋 **Bundle Contents**

### **Core Documentation**
- `README.md` - This deployment guide
- `COPILOT-INSTRUCTIONS.md` - AI assistant guidance for cross-repo ADRs
- `MANIFEST.md` - Complete bundle manifest with checksums

### **Templates**
- `ADR-XXXX-cross-repo-standard.md` - Cross-repository ADR standard template
- `ADR-template-enhanced.md` - Enhanced ADR template with cross-repo support
- `repository-mapping.yaml.template` - Repository ecosystem configuration
- `alignment-status.yaml.template` - Alignment tracking configuration
- `gitignore-additions.txt` - Git ignore patterns for ADR tooling

### **Scripts**
- `deploy.sh` - Automated deployment script
- `validate_cross_repo_links.sh` - Cross-repository link validation
- `post_deploy_validation.sh` - Deployment verification
- `copy_validation_script.sh` - Helper for script distribution

### **Examples**
- `example-adr-with-cross-refs.md` - Working example of cross-repo references
- `ci-workflow-addition.yml` - GitHub Actions CI/CD integration

## 🔗 **Cross-Repository Linking**

### **URL Patterns**
```yaml
# Canonical ADR URL pattern
https://github.com/{org}/{repo}/blob/main/docs/ADR/ADR-{number}-{title}.md

# Shorthand notation in content
[@repo:ADR-XXXX](full-canonical-url)
```

### **Relationship Types**
- `adopts` - This ADR adopts policies from another ADR
- `inherits_from` - Inherits structure/principles from another ADR
- `compatible_with` - Maintains compatibility with another ADR
- `supersedes_cross_repo` - Replaces an ADR in another repository
- `references` - General reference to another ADR

### **Front-Matter Format**
```yaml
external_related:
  - repo: "ha-config"
    adr: "ADR-0024"
    url: "https://github.com/e-app-404/ha-config/blob/main/docs/ADR/ADR-0024-workspace-hygiene.md"
    relationship: "adopts"
    last_checked: "2025-09-28"
    status: "aligned"
```

## 🔧 **Configuration**

### **Repository Mapping**
Edit `repository-mapping.yaml` to define your ecosystem:

```yaml
repositories:
  omega_registry:
    url: "https://github.com/e-app-404/omega_registry"
    adr_path: "docs/ADR"
    contact: "maintainer@example.com"

  ha-config:
    url: "https://github.com/e-app-404/ha-config"
    adr_path: "docs/ADR"
    contact: "maintainer@example.com"
```

### **Alignment Tracking**
Configure drift detection in `alignment-status.yaml`:

```yaml
alignment_checks:
  frequency: "weekly"
  notify_on_drift: true
  auto_update_status: true
```

## 🔍 **Validation**

### **Manual Validation**
```bash
# Validate all cross-repository links
./ops/ADR/validate_cross_repo_links.sh

# Check alignment status
./ops/ADR/check_alignment_status.sh
```

### **CI Integration**
Add to your GitHub Actions workflow:

```yaml
- name: Validate Cross-Repo ADR Links
  run: |
    if [ -f "./ops/ADR/validate_cross_repo_links.sh" ]; then
      ./ops/ADR/validate_cross_repo_links.sh
    fi
```

## 🤖 **AI Assistant Integration**

The bundle includes specialized instructions for GitHub Copilot and other AI assistants:

- **Auto-recognition** of cross-repository ADR systems
- **Proper reference generation** with correct URL patterns
- **Relationship validation** and suggestions
- **Drift detection** recommendations
- **Repository-specific guidance** based on mapping configuration

## 📊 **Features**

### **Cross-Repository Governance**
- Canonical URL patterns for stable references
- Structured relationship types with validation
- Shorthand notation for easy authoring
- Automated link validation and drift detection

### **Alignment Management**
- Track compatibility across repositories
- Detect when upstream ADRs change
- Coordinate policy updates across ecosystem
- Automated status reporting

### **Production Ready**
- Comprehensive backup and rollback
- Error handling and validation
- CI/CD integration examples
- Extensive documentation and examples

## 🔄 **Deployment Process**

### **Phase 1: Bundle Copy**
1. Copy deployment bundle to target repository
2. Review repository-specific customizations needed
3. Update repository mapping configuration

### **Phase 2: Automated Deployment**
1. Run `deploy.sh` script
2. Review generated templates and configurations
3. Validate deployment with verification script

### **Phase 3: Integration**
1. Create first cross-repository ADR references
2. Set up CI validation
3. Train team on new linking capabilities

## 🚨 **Important Notes**

### **Before Deployment**
- ✅ Backup existing ADR structure
- ✅ Review repository-mapping.yaml configuration
- ✅ Ensure repository has docs/ADR/ directory
- ✅ Verify write permissions for deployment

### **After Deployment**
- ✅ Run post-deployment validation
- ✅ Update existing ADRs with cross-repo references
- ✅ Set up CI validation workflow
- ✅ Document repository-specific customizations

## 📞 **Support**

### **Troubleshooting**
- Check `deployment.log` for detailed deployment information
- Run validation scripts to identify configuration issues
- Review MANIFEST.md for expected file structure

### **Customization**
- All templates include customization points marked with `TODO:`
- Repository-specific configurations in `repository-mapping.yaml`
- Validation rules can be extended in validation scripts

## 🔗 **Related Documentation**

- **ADR-0001**: ADR governance and formatting standards
- **ADR-0005**: Workspace structure canonicalization
- **Cross-Repository Architecture Guide**: [Coming Soon]

---

**Bundle Version**: 1.0.0
**Last Updated**: 2025-09-28
**Maintainer**: Omega Registry Team
