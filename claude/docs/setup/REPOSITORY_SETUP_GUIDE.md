# 🔄 Repository Fork & Setup Guide

## Overview
This guide walks you through forking the xiaozhi-esp32-server repository and setting up your development environment with all the enhanced self-hosted infrastructure work.

## Phase 1: Repository Forking & Cloning

### 1.1 Fork the Repository
1. **Go to GitHub**: https://github.com/xinnan-tech/xiaozhi-esp32-server
2. **Click "Fork"** in the top right corner
3. **Select your account** as the destination
4. **Wait for fork completion**

### 1.2 Clone Your Fork
```bash
# Navigate to your development directory
cd ~/Desktop/resonance/

# Clone your fork (replace YOUR_USERNAME)
git clone https://github.com/YOUR_USERNAME/xiaozhi-esp32-server.git xiaozhi-esp32-server-fork

# Navigate to the new directory
cd xiaozhi-esp32-server-fork

# Set up remotes
git remote add upstream https://github.com/xinnan-tech/xiaozhi-esp32-server.git
git remote -v  # Verify remotes

# Create feature branch
git checkout -b self-hosted-infrastructure
```

### 1.3 Verify Repository Structure
```bash
# Check that you have the basic structure
ls -la
# Should see: docs/, main/, xiaozhi-deployment/, xiaozhi-server-full/, etc.

# Verify main server directory
ls -la main/xiaozhi-server/
# Should see: config.yaml, performance_tester.py, core/, plugins_func/, etc.
```

## Phase 2: File Migration from Current Work

### 2.1 Create Documentation Structure
```bash
# Create Claude documentation structure
mkdir -p ./claude/docs/{setup,configs,testing,research}

# Verify structure
tree ./claude/ || ls -la ./claude/
```

### 2.2 Copy Files from Original Directory

**From your original directory (`/home/hehehe0803/Desktop/resonance/xiaozhi-esp32-server/`):**

```bash
# Navigate to original directory
cd /home/hehehe0803/Desktop/resonance/xiaozhi-esp32-server/

# Copy model download script
cp model_download.sh ../xiaozhi-esp32-server-fork/

# Copy enhanced performance tester
cp main/xiaozhi-server/performance_tester_en.py ../xiaozhi-esp32-server-fork/main/xiaozhi-server/

# Copy local configuration
cp main/xiaozhi-server/config_local.yaml ../xiaozhi-esp32-server-fork/main/xiaozhi-server/

# Copy function calling test
cp main/xiaozhi-server/test_function_calling.py ../xiaozhi-esp32-server-fork/main/xiaozhi-server/

# Copy data configuration
cp main/xiaozhi-server/data/.config.yaml ../xiaozhi-esp32-server-fork/main/xiaozhi-server/data/

# Copy setup guide
cp SETUP_GUIDE.md ../xiaozhi-esp32-server-fork/claude/docs/setup/

# Copy log and documentation
cp main/xiaozhi-server/log.md ../xiaozhi-esp32-server-fork/claude/docs/

# Copy API configuration guide
cp main/xiaozhi-server/api_configuration_guide.md ../xiaozhi-esp32-server-fork/claude/docs/configs/
```

### 2.3 Organize Documentation
```bash
# Navigate to your new fork
cd ~/Desktop/resonance/xiaozhi-esp32-server-fork/

# Move files to proper documentation structure
mv REPOSITORY_SETUP_GUIDE.md ./claude/docs/setup/
mv model_download.sh ./claude/docs/setup/

# Create README for claude docs
cat > ./claude/README.md << 'EOF'
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
EOF
```

## Phase 3: Docker Service Setup

### 3.1 Verify Docker Environment
```bash
# Check Docker installation
docker --version
docker-compose --version

# Check if Docker is running
docker ps
```

### 3.2 Set Up Docker Services

**Option 1: Simple Deployment (Recommended for testing)**
```bash
# Navigate to simple deployment
cd xiaozhi-deployment/

# Check current docker-compose file
cat docker-compose.yml

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f xiaozhi-esp32-server
```

**Option 2: Full Stack Deployment (If needed)**
```bash
# Navigate to full deployment
cd xiaozhi-server-full/

# Update configuration if needed
cp ../main/xiaozhi-server/data/.config.yaml ./data/

# Start services  
docker-compose -f docker-compose_all.yml up -d

# Check all services
docker-compose -f docker-compose_all.yml ps
```

### 3.3 Verify Services
```bash
# Test WebSocket connectivity
curl -i http://localhost:8000/

# Test HTTP API
curl http://localhost:8003/

# Check if web interface is accessible (full deployment)
# Open browser to http://localhost:8001 (if using full deployment)
```

### 3.4 Configure Ollama Integration

**If using Docker deployment:**
```bash
# Install Ollama on host system (not in container)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Update configuration to use host Ollama
# Edit main/xiaozhi-server/data/.config.yaml
# Change base_url from localhost:11434 to host.docker.internal:11434
```

**If using local deployment:**
```bash
# Install Ollama locally
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &

# Configuration should work with localhost:11434
```

## Phase 4: Configuration and Testing

### 4.1 Update Configuration Files
```bash
# Verify local configuration is in place
cat main/xiaozhi-server/data/.config.yaml | head -20

# Test configuration loading
cd main/xiaozhi-server/
python -c "from config.settings import load_config; print('Config loaded successfully')"
```

### 4.2 Test Basic Functionality
```bash
# Test if Python dependencies are available
cd main/xiaozhi-server/
python -c "import aiohttp, tabulate; print('Dependencies OK')"

# If missing dependencies:
pip install aiohttp tabulate pyyaml
```

### 4.3 Initial Model Testing
```bash
# Start with smallest model for testing
ollama pull qwen2.5:0.6b

# Test basic inference
ollama run qwen2.5:0.6b "Hello, this is a test"

# Test through performance tester (once models are available)
python performance_tester_en.py
```

## Phase 5: Commit Initial Setup

### 5.1 Add Files to Git
```bash
# Stage all new files
git add .

# Check what's being added
git status

# Commit initial setup
git commit -m "Initial self-hosted infrastructure setup

- Add enhanced performance tester with VRAM monitoring
- Add local model configuration (config_local.yaml)
- Add function calling test suite
- Add Claude documentation structure
- Add model download scripts and setup guides
- Configure for local Ollama integration

🤖 Generated with Claude Code"
```

### 5.2 Push to Your Fork
```bash
# Push feature branch
git push -u origin self-hosted-infrastructure

# Verify on GitHub that your branch is there
```

## Troubleshooting

### Common Issues

**Docker Permission Issues:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in, or:
newgrp docker
```

**Port Conflicts:**
```bash
# Check what's using ports
sudo netstat -tlnp | grep -E ':8000|:8003|:11434'

# Stop conflicting services or change ports
```

**Ollama Connection Issues:**
```bash
# Check Ollama status
curl http://localhost:11434/api/version

# Restart Ollama if needed
killall ollama
ollama serve &
```

**Python Dependencies:**
```bash
# Create virtual environment if needed
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt  # If available
# Or install manually:
pip install aiohttp tabulate pyyaml
```

## Verification Checklist

- [ ] Repository forked and cloned successfully
- [ ] Feature branch created and checked out
- [ ] All files migrated from original directory
- [ ] Documentation organized in ./claude/docs/ structure
- [ ] Docker services running (8000, 8003 accessible)
- [ ] Ollama service running (11434 accessible)
- [ ] Configuration files in correct locations
- [ ] Python dependencies installed
- [ ] Basic model inference working
- [ ] Initial commit pushed to fork

## Next Steps

1. **Follow SETUP_GUIDE.md** to download models with `./claude/docs/setup/model_download.sh`
2. **Run enhanced benchmarks** with `python performance_tester_en.py`
3. **Test function calling** with `python test_function_calling.py`
4. **Begin grid search testing** across LLM×TTS combinations

---

**Note**: This setup provides a clean, organized development environment for the self-hosted infrastructure project while maintaining all the enhanced functionality we've developed.