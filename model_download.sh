#!/bin/bash
# Model Download Script for Self-Hosted LLM Testing
# Estimated total storage needed: ~100-150GB for sub-20B models
# Current available space: 139GB (sufficient)

echo "======================================================"
echo "🚀 XIAOZHI ESP32 SERVER - MODEL DOWNLOAD SCRIPT"
echo "======================================================"
echo "Available disk space: $(df -h / | awk 'NR==2{print $4}')"
echo "Estimated download time: 2-4 hours depending on internet speed"
echo ""

# Function to check if ollama is installed and running
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        echo "❌ Ollama not found. Please install first:"
        echo "   curl -fsSL https://ollama.ai/install.sh | sh"
        exit 1
    fi
    
    echo "✅ Ollama found. Testing connection..."
    if ! ollama list &> /dev/null; then
        echo "⚠️  Starting Ollama service..."
        ollama serve &
        sleep 5
    fi
    echo "✅ Ollama service ready"
}

# Function to download and verify model
download_model() {
    local model=$1
    local description=$2
    local size=$3
    
    echo ""
    echo "📥 Downloading: $model ($description) - Est. size: $size"
    echo "   Started at: $(date)"
    
    if ollama pull "$model"; then
        echo "✅ Successfully downloaded: $model"
        # Test the model briefly
        echo "🧪 Quick test..."
        if echo "Hello" | ollama run "$model" --verbose 2>/dev/null | head -1; then
            echo "✅ Model test passed: $model"
        else
            echo "⚠️  Model downloaded but test failed: $model"
        fi
    else
        echo "❌ Failed to download: $model"
        return 1
    fi
}

# Main execution
echo "🔍 Checking prerequisites..."
check_ollama

echo ""
echo "======================================================"
echo "📋 DOWNLOAD PLAN - Sub-20B Models for RTX 3070"
echo "======================================================"
echo "Phase 1: Ultra-lightweight (0.6B-1.7B) - ~5GB total"
echo "Phase 2: Small models (1B-4B) - ~15GB total" 
echo "Phase 3: Medium models (8B-14B) - ~50GB total"
echo "Phase 4: Larger models (11B-12B) - ~30GB total"
echo ""

read -p "🚀 Start downloads? This will take several hours. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Download cancelled by user"
    exit 0
fi

echo ""
echo "======================================================"
echo "🏁 PHASE 1: ULTRA-LIGHTWEIGHT MODELS"
echo "======================================================"

download_model "qwen2.5:0.6b" "Qwen 2.5 0.6B - Ultra compact" "~1GB"
download_model "qwen2.5:1.7b" "Qwen 2.5 1.7B - Balanced tiny" "~2GB"

echo ""
echo "======================================================"
echo "🏃 PHASE 2: SMALL MODELS" 
echo "======================================================"

download_model "llama3.2:1b" "Llama 3.2 1B - Edge optimized" "~1GB"
download_model "gemma3:1b" "Gemma 3 1B - Google compact" "~1GB"
download_model "qwen2.5:4b" "Qwen 2.5 4B - Good balance" "~3GB"
download_model "llama3.2:3b" "Llama 3.2 3B - Quantized efficient" "~2GB"
download_model "gemma3:4b" "Gemma 3 4B - Enhanced quality" "~3GB"

echo ""
echo "======================================================"
echo "🚀 PHASE 3: MEDIUM MODELS"
echo "======================================================"

download_model "qwen2.5:8b" "Qwen 2.5 8B - High quality" "~5GB"
download_model "qwen2.5:14b" "Qwen 2.5 14B - Near state-of-art" "~8GB"
download_model "glm4:9b" "GLM-4 9B - Strong function calling" "~6GB"

echo ""
echo "======================================================"
echo "🎯 PHASE 4: SPECIALTY MODELS"
echo "======================================================"

download_model "llama3.2:11b" "Llama 3.2 11B - Multimodal vision" "~8GB"
download_model "gemma3:12b" "Gemma 3 12B - High performance" "~8GB"

echo ""
echo "======================================================"
echo "✅ DOWNLOAD COMPLETE - SUB-20B MODELS"
echo "======================================================"

echo "📊 Downloaded models:"
ollama list

echo ""
echo "💾 Storage usage:"
du -sh ~/.ollama/models/ 2>/dev/null || echo "Ollama models directory not found"

echo ""
echo "🧪 Ready for testing! Run:"
echo "   cd /home/hehehe0803/Desktop/resonance/xiaozhi-esp32-server/main/xiaozhi-server"
echo "   python performance_tester_en.py"

echo ""
echo "⚠️  OPTIONAL: Larger models (20B+) available but need ~40GB more:"
echo "   ollama pull qwen2.5:32b     # ~20GB - Qwen 2.5 32B"
echo "   ollama pull gemma3:27b      # ~20GB - Gemma 3 27B"
echo ""
echo "🎉 Setup complete! Check log.md for detailed testing progress."