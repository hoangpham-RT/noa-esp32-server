# 📋 File Migration Checklist

## Files to Copy from Current Directory to New Fork

### Source Directory: `/home/hehehe0803/Desktop/resonance/xiaozhi-esp32-server/`
### Target Directory: `~/Desktop/resonance/xiaozhi-esp32-server-fork/`

## ✅ Enhanced Code Files

| File | Source Path | Target Path | Status | Notes |
|------|-------------|-------------|---------|-------|
| Model Download Script | `./model_download.sh` | `./claude/docs/setup/model_download.sh` | □ | Automated model downloading |
| Enhanced Performance Tester | `main/xiaozhi-server/performance_tester_en.py` | `main/xiaozhi-server/performance_tester_en.py` | □ | VRAM monitoring, no pricing |
| Local Configuration | `main/xiaozhi-server/config_local.yaml` | `main/xiaozhi-server/config_local.yaml` | □ | Local model configurations |
| Function Calling Tests | `main/xiaozhi-server/test_function_calling.py` | `main/xiaozhi-server/test_function_calling.py` | □ | ESP32 IoT scenarios |
| Data Configuration | `main/xiaozhi-server/data/.config.yaml` | `main/xiaozhi-server/data/.config.yaml` | □ | Working local config |

## ✅ Documentation Files

| File | Source Path | Target Path | Status | Notes |
|------|-------------|-------------|---------|-------|
| Setup Guide | `SETUP_GUIDE.md` | `./claude/docs/setup/SETUP_GUIDE.md` | □ | Complete setup instructions |
| Repository Setup Guide | `REPOSITORY_SETUP_GUIDE.md` | `./claude/docs/setup/REPOSITORY_SETUP_GUIDE.md` | □ | This checklist |
| Progress Log | `main/xiaozhi-server/log.md` | `./claude/docs/log.md` | □ | Development progress |
| API Configuration Guide | `main/xiaozhi-server/api_configuration_guide.md` | `./claude/docs/configs/api_configuration_guide.md` | □ | API key setup |
| Migration Checklist | `FILE_MIGRATION_CHECKLIST.md` | `./claude/docs/setup/FILE_MIGRATION_CHECKLIST.md` | □ | This checklist |

## ✅ Configuration Templates

| File | Source Path | Target Path | Status | Notes |
|------|-------------|-------------|---------|-------|
| English Config | `main/xiaozhi-server/config_en.yaml` | `./claude/docs/configs/config_en.yaml` | □ | English configuration template |
| Local Config Template | `main/xiaozhi-server/config_local.yaml` | `./claude/docs/configs/config_local_template.yaml` | □ | Template for local setup |

## 🔄 Copy Commands Script

```bash
#!/bin/bash
# File Migration Script
# Run this from the original directory

ORIGINAL_DIR="/home/hehehe0803/Desktop/resonance/xiaozhi-esp32-server"
TARGET_DIR="$HOME/Desktop/resonance/xiaozhi-esp32-server-fork"

# Ensure we're in the right directory
cd "$ORIGINAL_DIR" || exit 1

echo "🔄 Starting file migration..."
echo "Source: $ORIGINAL_DIR"
echo "Target: $TARGET_DIR"

# Create target directory structure
mkdir -p "$TARGET_DIR/claude/docs/"{setup,configs,testing,research}

# Copy enhanced code files
echo "📁 Copying enhanced code files..."
cp model_download.sh "$TARGET_DIR/claude/docs/setup/"
cp main/xiaozhi-server/performance_tester_en.py "$TARGET_DIR/main/xiaozhi-server/"
cp main/xiaozhi-server/config_local.yaml "$TARGET_DIR/main/xiaozhi-server/"
cp main/xiaozhi-server/test_function_calling.py "$TARGET_DIR/main/xiaozhi-server/"
cp main/xiaozhi-server/data/.config.yaml "$TARGET_DIR/main/xiaozhi-server/data/"

# Copy documentation files
echo "📄 Copying documentation files..."
cp SETUP_GUIDE.md "$TARGET_DIR/claude/docs/setup/"
cp REPOSITORY_SETUP_GUIDE.md "$TARGET_DIR/claude/docs/setup/"
cp main/xiaozhi-server/log.md "$TARGET_DIR/claude/docs/"
cp main/xiaozhi-server/api_configuration_guide.md "$TARGET_DIR/claude/docs/configs/"
cp FILE_MIGRATION_CHECKLIST.md "$TARGET_DIR/claude/docs/setup/"

# Copy configuration templates
echo "⚙️  Copying configuration templates..."
cp main/xiaozhi-server/config_en.yaml "$TARGET_DIR/claude/docs/configs/"
cp main/xiaozhi-server/config_local.yaml "$TARGET_DIR/claude/docs/configs/config_local_template.yaml"

# Create README for claude docs
cat > "$TARGET_DIR/claude/README.md" << 'EOF'
# Claude-Generated Documentation

This directory contains all documentation and tools created by Claude for the self-hosted LLM infrastructure project.

## Structure
- `docs/setup/` - Installation and setup guides
- `docs/configs/` - Configuration files and templates  
- `docs/testing/` - Test suites and benchmarks
- `docs/research/` - Model analysis and licensing research

## Quick Start
1. Follow `docs/setup/REPOSITORY_SETUP_GUIDE.md` for initial setup
2. Use `docs/setup/SETUP_GUIDE.md` for model installation
3. Configure using templates in `docs/configs/`
4. Run tests from `docs/testing/`

## Files Overview

### Setup & Installation
- `REPOSITORY_SETUP_GUIDE.md` - Fork and clone setup
- `SETUP_GUIDE.md` - Complete installation guide
- `model_download.sh` - Automated model downloading
- `FILE_MIGRATION_CHECKLIST.md` - Migration checklist

### Configuration
- `config_local_template.yaml` - Local model configuration template
- `config_en.yaml` - English configuration reference
- `api_configuration_guide.md` - API key setup guide

### Testing & Benchmarking
- `performance_tester_en.py` - Enhanced performance testing (main/xiaozhi-server/)
- `test_function_calling.py` - Function calling tests (main/xiaozhi-server/)

### Progress Tracking
- `log.md` - Development progress and results
EOF

echo "✅ File migration completed!"
echo ""
echo "📋 Verification checklist:"
echo "- Navigate to: $TARGET_DIR"
echo "- Check claude/docs/ structure exists"
echo "- Verify all files copied successfully"
echo "- Review README.md in claude/ directory"
echo ""
echo "🚀 Next steps:"
echo "1. cd $TARGET_DIR"
echo "2. git add ."
echo "3. git commit -m 'Add Claude-generated infrastructure'"
echo "4. Follow REPOSITORY_SETUP_GUIDE.md for Docker setup"
```

## 🔍 Verification Steps

### After Migration, Verify These Files Exist:

```bash
# Navigate to new fork directory
cd ~/Desktop/resonance/xiaozhi-esp32-server-fork/

# Check documentation structure
tree claude/ || ls -la claude/

# Verify key files
ls -la claude/docs/setup/model_download.sh
ls -la main/xiaozhi-server/performance_tester_en.py
ls -la main/xiaozhi-server/config_local.yaml
ls -la main/xiaozhi-server/test_function_calling.py
ls -la main/xiaozhi-server/data/.config.yaml

# Check documentation
ls -la claude/docs/setup/SETUP_GUIDE.md
ls -la claude/docs/configs/api_configuration_guide.md
ls -la claude/docs/log.md
```

### Test File Integrity:

```bash
# Test Python syntax
python -m py_compile main/xiaozhi-server/performance_tester_en.py
python -m py_compile main/xiaozhi-server/test_function_calling.py

# Test YAML syntax
python -c "import yaml; yaml.safe_load(open('main/xiaozhi-server/config_local.yaml'))"
python -c "import yaml; yaml.safe_load(open('main/xiaozhi-server/data/.config.yaml'))"

# Test script executability
chmod +x claude/docs/setup/model_download.sh
head -5 claude/docs/setup/model_download.sh
```

## 📝 Post-Migration Tasks

### 1. Update File Paths
- [ ] Check all documentation for relative path references
- [ ] Update any hardcoded paths in scripts
- [ ] Verify Docker mount paths in configurations

### 2. Git Integration
- [ ] Add all files to git staging
- [ ] Create initial commit with descriptive message
- [ ] Push to feature branch on your fork

### 3. Documentation Organization
- [ ] Verify all files are in correct ./claude/docs/ subdirectories
- [ ] Update any cross-references between documents
- [ ] Ensure README.md accurately describes structure

### 4. Testing
- [ ] Verify Docker services can start with new configuration
- [ ] Test that Python files import correctly
- [ ] Validate YAML configuration files load properly

## 🚨 Important Notes

1. **CLAUDE.md stays in project root** (as requested)
2. **Relative paths may need updating** after migration
3. **Docker configurations may need path adjustments**
4. **Test everything after migration** before proceeding
5. **Keep original directory as backup** until verification complete

---

This checklist ensures complete and organized migration of all Claude-generated enhancements to your forked repository.