# 🐳 Docker Service Restoration Guide

## Overview
This guide helps you restore and configure Docker services in your forked repository for the self-hosted LLM infrastructure project.

## Prerequisites

### System Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- NVIDIA Docker runtime (for GPU support)
- 8GB+ RAM available
- 50GB+ disk space

### Verification Commands
```bash
# Check Docker installation
docker --version
docker-compose --version

# Check if Docker daemon is running
docker ps

# Check NVIDIA Docker support (if using GPU)
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

## Phase 1: Choose Deployment Type

### Option 1: Simple Deployment (Recommended for Development)
**Best for**: Local development, testing, minimal setup
**Ports**: 8000 (WebSocket), 8003 (HTTP API)

### Option 2: Full Stack Deployment  
**Best for**: Production-like environment, web interface access
**Ports**: 8010 (WebSocket), 8013 (HTTP API), 8012 (Management API), 8011 (Web UI)

## Phase 2: Simple Deployment Setup

### 2.1 Navigate to Deployment Directory
```bash
cd ~/Desktop/resonance/xiaozhi-esp32-server-fork/xiaozhi-deployment/
```

### 2.2 Verify Configuration
```bash
# Check docker-compose file
cat docker-compose.yml

# Verify model mount point
ls -la models/  # Should contain SenseVoiceSmall/
ls -la data/    # Should contain configuration files
```

### 2.3 Update Data Configuration
```bash
# Copy your local configuration
cp ../main/xiaozhi-server/data/.config.yaml ./data/

# Verify configuration
cat ./data/.config.yaml | head -20
```

### 2.4 Start Simple Deployment
```bash
# Pull latest image
docker-compose pull

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f xiaozhi-esp32-server

# Verify service status
docker-compose ps
```

### 2.5 Test Simple Deployment
```bash
# Test WebSocket endpoint
curl -i http://localhost:8000/

# Test HTTP API endpoint  
curl http://localhost:8003/

# Check if service responds
curl http://localhost:8003/health || echo "Health endpoint might not exist"
```

## Phase 3: Full Stack Deployment (Optional)

### 3.1 Navigate to Full Deployment Directory
```bash
cd ~/Desktop/resonance/xiaozhi-esp32-server-fork/xiaozhi-server-full/
```

### 3.2 Configure Full Stack
```bash
# Copy configuration files
cp ../main/xiaozhi-server/data/.config.yaml ./data/

# Generate manager-api secret if not present
if ! grep -q "ccd2d0e7-3944-4279-b481-bc7d1c459975" ./data/.config.yaml; then
    echo "Adding manager-api secret to configuration..."
    # Update configuration with the secret
fi

# Verify docker-compose configuration
cat docker-compose_all.yml
```

### 3.3 Start Full Stack
```bash
# Start all services
docker-compose -f docker-compose_all.yml up -d

# Check all services
docker-compose -f docker-compose_all.yml ps

# Monitor logs
docker-compose -f docker-compose_all.yml logs -f
```

### 3.4 Test Full Stack
```bash
# Test xiaozhi-esp32-server (port 8010)
curl http://localhost:8010/

# Test HTTP API (port 8013)
curl http://localhost:8013/

# Test manager-api (port 8012)
curl http://localhost:8012/health || echo "Manager API might be starting..."

# Test web interface (port 8011)
curl http://localhost:8011/ || echo "Web interface might need time to start"
```

### 3.5 Access Web Interface
```bash
# Open browser to web interface
echo "Web Interface: http://localhost:8011"
echo "If web interface doesn't load, check Docker logs:"
echo "docker-compose -f docker-compose_all.yml logs web"
```

## Phase 4: Ollama Integration

### 4.1 Host-Based Ollama (Recommended)
```bash
# Install Ollama on host system
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Test Ollama API
curl http://localhost:11434/api/version

# Pull a test model
ollama pull qwen2.5:0.6b
```

### 4.2 Configure Docker to Access Host Ollama

**For Simple Deployment:**
```bash
# Edit data/.config.yaml to use host network
# Update Ollama base_url from localhost:11434 to host.docker.internal:11434
sed -i 's/localhost:11434/host.docker.internal:11434/g' ./data/.config.yaml

# Restart container
docker-compose restart xiaozhi-esp32-server
```

**For Full Stack Deployment:**
```bash
# Same configuration update
sed -i 's/localhost:11434/host.docker.internal:11434/g' ./data/.config.yaml

# Restart all services
docker-compose -f docker-compose_all.yml restart
```

### 4.3 Test Ollama Integration
```bash
# Test from container
docker exec -it xiaozhi-esp32-server sh -c "curl http://host.docker.internal:11434/api/version"

# Or test from host
curl http://localhost:11434/api/version
```

## Phase 5: Configuration Verification

### 5.1 Verify Model Files
```bash
# Check model directory structure
ls -la models/
ls -la models/SenseVoiceSmall/

# If models missing, download them
# Follow model_download.sh instructions
```

### 5.2 Test Configuration Loading
```bash
# Access container shell
docker exec -it xiaozhi-esp32-server /bin/bash

# Test configuration loading inside container
python -c "from config.settings import load_config; print('Config loaded successfully')"

# Exit container
exit
```

### 5.3 Test Model Inference
```bash
# Test through Ollama (from host)
ollama run qwen2.5:0.6b "Hello, this is a test"

# Test through xiaozhi server (when ready)
# This will be available after models are downloaded and configured
```

## Phase 6: Performance Testing Setup

### 6.1 Install Python Dependencies (Host)
```bash
# Navigate to server directory
cd ~/Desktop/resonance/xiaozhi-esp32-server-fork/main/xiaozhi-server/

# Install dependencies in virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install aiohttp tabulate pyyaml

# Test dependencies
python -c "import aiohttp, tabulate; print('Dependencies OK')"
```

### 6.2 Test Performance Suite
```bash
# Test basic performance tester
python performance_tester_en.py

# Test grid search (when models available)
python performance_tester_grid_search.py

# Test function calling
python test_function_calling.py
```

## Troubleshooting

### Common Issues & Solutions

#### 1. Port Conflicts
```bash
# Check what's using ports
sudo netstat -tlnp | grep -E ':8000|:8003|:8010|:8011|:8012|:8013'

# Stop conflicting services
sudo systemctl stop apache2  # If Apache is running
sudo systemctl stop nginx    # If Nginx is running

# Or change ports in docker-compose files
```

#### 2. Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or use:
newgrp docker

# Test Docker without sudo
docker ps
```

#### 3. Container Startup Failures
```bash
# Check detailed logs
docker-compose logs xiaozhi-esp32-server

# Check if configuration is valid
docker exec -it xiaozhi-esp32-server cat /app/data/.config.yaml

# Restart with fresh pull
docker-compose down
docker-compose pull
docker-compose up -d
```

#### 4. Ollama Connection Issues
```bash
# Test Ollama from host
curl http://localhost:11434/api/version

# Test from container
docker exec -it xiaozhi-esp32-server curl http://host.docker.internal:11434/api/version

# Check firewall (Linux)
sudo ufw status
sudo ufw allow 11434

# Restart Ollama
killall ollama
ollama serve &
```

#### 5. Manager-API Secret Issues (Full Stack)
```bash
# Check if secret is configured
grep -A 5 -B 5 "manager-api" ./data/.config.yaml

# Add secret if missing
echo "manager_api_secret: ccd2d0e7-3944-4279-b481-bc7d1c459975" >> ./data/.config.yaml

# Restart services
docker-compose -f docker-compose_all.yml restart
```

#### 6. Model Loading Issues
```bash
# Check model directory
ls -la models/SenseVoiceSmall/

# If missing, download models
cd ../../../  # Go to repo root
chmod +x claude/docs/setup/model_download.sh
./claude/docs/setup/model_download.sh
```

## Verification Checklist

### Simple Deployment
- [ ] Docker and Docker Compose installed
- [ ] Simple deployment directory accessible
- [ ] Configuration files copied
- [ ] Container starts successfully
- [ ] Port 8000 (WebSocket) accessible
- [ ] Port 8003 (HTTP API) accessible
- [ ] Ollama service running and accessible
- [ ] Basic model inference working

### Full Stack Deployment  
- [ ] All simple deployment requirements ✓
- [ ] Full stack directory accessible
- [ ] Manager-API secret configured
- [ ] All containers start successfully
- [ ] Port 8010 (WebSocket) accessible
- [ ] Port 8013 (HTTP API) accessible
- [ ] Port 8012 (Manager API) accessible
- [ ] Port 8011 (Web UI) accessible
- [ ] Web interface loads properly

### Integration Testing
- [ ] Python dependencies installed
- [ ] Configuration loading works
- [ ] Performance tester runs
- [ ] Function calling tests work
- [ ] Model inference through Docker works
- [ ] Ollama integration functional

## Next Steps

1. **Download Models**: Follow `model_download.sh` to get LLM models
2. **Run Benchmarks**: Execute grid search performance testing
3. **Configure TTS**: Add OSS TTS models to the testing suite
4. **Test Function Calling**: Verify IoT integration scenarios
5. **Scale Testing**: Plan for multi-GPU deployment

---

**Note**: Keep this terminal session open for monitoring Docker logs during initial setup. Use `docker-compose logs -f` to watch real-time container output.