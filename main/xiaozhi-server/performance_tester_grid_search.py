#!/usr/bin/env python3
"""
Enhanced Grid Search Performance Tester for Self-Hosted LLM Infrastructure
Tests LLM x TTS combinations with function calling integration
"""

import asyncio
import csv
import json
import logging
import os
import statistics
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import aiohttp
from tabulate import tabulate

from config.settings import load_config
from core.utils.asr import create_instance as create_stt_instance
from core.utils.llm import create_instance as create_llm_instance
from core.utils.tts import create_instance as create_tts_instance

# Import existing function calling system
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from plugins_func.loadplugins import auto_import_modules
from core.providers.tools.unified_tool_handler import UnifiedToolHandler

# Set global log level to WARNING to suppress INFO logs
logging.basicConfig(level=logging.WARNING)

class GridSearchPerformanceTester:
    def __init__(self):
        self.config = load_config()
        
        # ESP32 IoT test scenarios 
        self.test_sentences = [
            "Hello, please introduce yourself",
            "What's the weather like today in New York?",
            "Please explain quantum computing in 50 words",
            "Turn on the living room lights",
            "Play some relaxing music",
            "What are the latest news headlines?",
            "Set the temperature to 22 degrees",
            "What time is it?",
        ]
        
        # Function calling test scenarios
        self.function_test_scenarios = [
            {
                "prompt": "What's the weather like in San Francisco?",
                "expected_function": "get_weather",
                "function_keywords": ["weather", "temperature", "forecast"]
            },
            {
                "prompt": "Play some jazz music",
                "expected_function": "play_music", 
                "function_keywords": ["music", "play", "audio"]
            },
            {
                "prompt": "Tell me the latest news",
                "expected_function": "get_news",
                "function_keywords": ["news", "headlines", "article"]
            },
            {
                "prompt": "What time is it?",
                "expected_function": "get_time",
                "function_keywords": ["time", "clock", "hour"]
            }
        ]

        # Load test audio files
        self.test_wav_list = []
        self.wav_root = r"config/assets"
        if os.path.exists(self.wav_root):
            for file_name in os.listdir(self.wav_root):
                file_path = os.path.join(self.wav_root, file_name)
                if os.path.getsize(file_path) > 300 * 1024:
                    with open(file_path, "rb") as f:
                        self.test_wav_list.append(f.read())

        self.results = {
            "llm": {}, 
            "tts": {}, 
            "stt": {}, 
            "combinations": [],
            "function_calling": {}
        }
        
        # TTS models to test
        self.tts_models = {
            "EdgeTTS": {"type": "edge", "voice": "en-US-AriaNeural"},
            "EdgeTTS_Fast": {"type": "edge", "voice": "en-US-AriaNeural", "rate": "+20%"},
            # OSS TTS models will be added here
            # "Kokoro": {"type": "kokoro", "model_path": "models/kokoro-82m"},
            # "MeloTTS": {"type": "melo", "model_name": "EN"},
            # "Dia": {"type": "dia", "model_path": "models/dia-1.6b"}
        }

    def _get_vram_usage(self) -> Dict:
        """Get VRAM usage information"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    used, total = lines[0].split(', ')
                    return {
                        "used_mb": int(used), 
                        "total_mb": int(total), 
                        "usage_percent": int(used)/int(total)*100
                    }
        except Exception:
            pass
        return {"used_mb": 0, "total_mb": 0, "usage_percent": 0}

    async def _test_function_calling(self, llm_name: str, llm_instance, conn=None) -> Dict:
        """Test function calling capability using existing plugin system"""
        print(f"  🔧 Testing function calling: {llm_name}")
        
        function_results = {
            "total_tests": len(self.function_test_scenarios),
            "successful_calls": 0,
            "scenarios": []
        }
        
        for scenario in self.function_test_scenarios:
            try:
                start_time = time.time()
                
                # Create function calling prompt
                prompt = f"User request: {scenario['prompt']}\n\nPlease respond appropriately and use available functions if needed."
                
                # Test LLM response with function calling context
                response_chunks = []
                for chunk in llm_instance.response("function_test", [{"role": "user", "content": prompt}]):
                    response_chunks.append(chunk)
                
                response = "".join(response_chunks)
                response_time = time.time() - start_time
                
                # Analyze response for function calling patterns
                function_detected = self._analyze_function_response(response, scenario)
                
                if function_detected:
                    function_results["successful_calls"] += 1
                
                function_results["scenarios"].append({
                    "prompt": scenario["prompt"],
                    "response_time": response_time,
                    "function_detected": function_detected,
                    "response_snippet": response[:100] + "..." if len(response) > 100 else response
                })
                
            except Exception as e:
                print(f"    ⚠️ Function test failed: {str(e)}")
                function_results["scenarios"].append({
                    "prompt": scenario["prompt"], 
                    "response_time": 0,
                    "function_detected": False,
                    "error": str(e)
                })
        
        function_results["success_rate"] = function_results["successful_calls"] / function_results["total_tests"]
        print(f"    📊 Function calling success rate: {function_results['success_rate']:.1%}")
        
        return function_results

    def _analyze_function_response(self, response: str, scenario: Dict) -> bool:
        """Analyze if response shows function calling behavior"""
        response_lower = response.lower()
        
        # Check for function calling keywords
        score = 0
        for keyword in scenario["function_keywords"]:
            if keyword in response_lower:
                score += 2
        
        # Check for structured response patterns
        structured_patterns = ["function", "call", "api", "tool", "action"]
        for pattern in structured_patterns:
            if pattern in response_lower:
                score += 1
                
        return score >= 3

    async def _test_llm_performance(self, llm_name: str, config: Dict) -> Dict:
        """Test LLM performance including function calling"""
        try:
            print(f"🧠 Testing LLM: {llm_name}")
            
            # Skip if not configured for local testing
            if config.get("type") != "ollama":
                print(f"⏭️  Skipping non-Ollama model: {llm_name}")
                return {"name": llm_name, "type": "llm", "errors": 1}
            
            # Check Ollama service
            base_url = config.get("base_url", "http://localhost:11434")
            model_name = config.get("model_name")
            if not await self._check_ollama_service(base_url, model_name):
                return {"name": llm_name, "type": "llm", "errors": 1}

            # Create LLM instance
            llm = create_llm_instance(config.get("type"), config)
            
            # Record VRAM usage
            vram_before = self._get_vram_usage()
            
            # Test basic performance
            sentence_tasks = []
            for sentence in self.test_sentences:
                sentence_tasks.append(self._test_single_sentence(llm_name, llm, sentence))
            
            sentence_results = await asyncio.gather(*sentence_tasks, return_exceptions=True)
            valid_results = [r for r in sentence_results if isinstance(r, dict) and r is not None]
            
            if not valid_results:
                return {"name": llm_name, "type": "llm", "errors": 1}
            
            # Test function calling
            function_results = await self._test_function_calling(llm_name, llm)
            
            # Record VRAM usage after testing
            vram_after = self._get_vram_usage()
            
            # Calculate metrics
            first_token_times = [r["first_token_time"] for r in valid_results]
            response_times = [r["response_time"] for r in valid_results]
            response_lengths = [r["response_length"] for r in valid_results]
            tokens_per_second = [r["tokens_per_second"] for r in valid_results]

            result = {
                "name": llm_name,
                "type": "llm",
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "avg_first_token_time": statistics.mean(first_token_times),
                "min_first_token_time": min(first_token_times),
                "max_first_token_time": max(first_token_times),
                "std_first_token": statistics.stdev(first_token_times) if len(first_token_times) > 1 else 0,
                "std_response": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "avg_response_length": statistics.mean(response_lengths),
                "avg_tokens_per_second": statistics.mean(tokens_per_second),
                "success_rate": len(valid_results) / len(self.test_sentences),
                "vram_used_mb": vram_after["used_mb"],
                "vram_usage_percent": vram_after["usage_percent"],
                "function_calling_success_rate": function_results["success_rate"],
                "function_calling_details": function_results,
                "errors": 0,
            }
            
            # Store function calling results separately
            self.results["function_calling"][llm_name] = function_results
            
            return result
            
        except Exception as e:
            print(f"⚠️ LLM {llm_name} test failed: {str(e)}")
            return {"name": llm_name, "type": "llm", "errors": 1}

    async def _check_ollama_service(self, base_url: str, model_name: str) -> bool:
        """Check if Ollama service and model are available"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check service
                async with session.get(f"{base_url}/api/version", timeout=5) as response:
                    if response.status != 200:
                        print(f"🚫 Ollama service not available: {base_url}")
                        return False
                
                # Check model
                async with session.get(f"{base_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        if not any(model["name"] == model_name for model in models):
                            print(f"🚫 Model {model_name} not found. Run: ollama pull {model_name}")
                            return False
                return True
        except Exception as e:
            print(f"🚫 Ollama check failed: {str(e)}")
            return False

    async def _test_single_sentence(self, llm_name: str, llm, sentence: str) -> Optional[Dict]:
        """Test performance for a single sentence"""
        try:
            start_time = time.time()
            first_token_time = None
            response_content = ""
            
            for chunk in llm.response("perf_test", [{"role": "user", "content": sentence}]):
                if first_token_time is None and chunk.strip():
                    first_token_time = time.time() - start_time
                response_content += chunk
            
            response_time = time.time() - start_time
            if first_token_time is None:
                first_token_time = response_time
                
            return {
                "first_token_time": first_token_time,
                "response_time": response_time,
                "response_length": len(response_content),
                "tokens_per_second": len(response_content) / response_time if response_time > 0 else 0,
            }
        except Exception:
            return None

    async def _test_tts_performance(self, tts_name: str, config: Dict) -> Dict:
        """Test TTS performance"""
        try:
            print(f"🎵 Testing TTS: {tts_name}")
            
            tts = create_tts_instance(config.get("type"), config, delete_audio_file=True)
            
            # Test synthesis
            synthesis_times = []
            file_sizes = []
            
            for sentence in self.test_sentences[:3]:  # Test 3 sentences
                start_time = time.time()
                tmp_file = tts.generate_filename()
                await tts.text_to_speak(sentence, tmp_file)
                synthesis_time = time.time() - start_time
                synthesis_times.append(synthesis_time)
                
                if tmp_file and os.path.exists(tmp_file):
                    file_sizes.append(os.path.getsize(tmp_file))
                    
            return {
                "name": tts_name,
                "type": "tts", 
                "avg_synthesis_time": statistics.mean(synthesis_times),
                "min_synthesis_time": min(synthesis_times),
                "max_synthesis_time": max(synthesis_times),
                "avg_file_size": statistics.mean(file_sizes) if file_sizes else 0,
                "errors": 0,
            }
            
        except Exception as e:
            print(f"⚠️ TTS {tts_name} test failed: {str(e)}")
            return {"name": tts_name, "type": "tts", "errors": 1}

    async def _test_combination(self, llm_name: str, tts_name: str) -> Dict:
        """Test LLM + TTS combination"""
        print(f"🔄 Testing combination: {llm_name} + {tts_name}")
        
        try:
            # Test end-to-end pipeline latency
            llm_config = self.config.get("LLM", {}).get(llm_name)
            tts_config = self.tts_models.get(tts_name)
            
            if not llm_config or not tts_config:
                return {"error": "Configuration not found"}
            
            llm = create_llm_instance(llm_config.get("type"), llm_config)
            tts = create_tts_instance(tts_config.get("type"), tts_config, delete_audio_file=True)
            
            # Test pipeline: LLM -> TTS
            test_prompt = "Hello, how are you today?"
            
            # LLM response
            llm_start = time.time()
            response_chunks = []
            for chunk in llm.response("pipeline_test", [{"role": "user", "content": test_prompt}]):
                response_chunks.append(chunk)
            llm_time = time.time() - llm_start
            
            response_text = "".join(response_chunks)
            
            # TTS synthesis
            tts_start = time.time()
            tmp_file = tts.generate_filename()
            await tts.text_to_speak(response_text[:100], tmp_file)  # Limit length
            tts_time = time.time() - tts_start
            
            total_time = llm_time + tts_time
            
            return {
                "llm": llm_name,
                "tts": tts_name,
                "llm_time": llm_time,
                "tts_time": tts_time,
                "total_time": total_time,
                "response_length": len(response_text),
                "success": True
            }
            
        except Exception as e:
            print(f"  ❌ Combination test failed: {str(e)}")
            return {
                "llm": llm_name,
                "tts": tts_name,
                "error": str(e),
                "success": False
            }

    def _export_grid_search_results(self):
        """Export comprehensive grid search results to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # LLM Results with Function Calling
        llm_csv_path = f"llm_grid_search_{timestamp}.csv"
        with open(llm_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'model_name', 'avg_first_token_time', 'avg_response_time', 
                'avg_tokens_per_second', 'vram_used_mb', 'vram_usage_percent',
                'function_calling_success_rate', 'success_rate'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for name, data in self.results["llm"].items():
                if data["errors"] == 0:
                    writer.writerow({
                        'model_name': name,
                        'avg_first_token_time': data['avg_first_token_time'],
                        'avg_response_time': data['avg_response_time'],
                        'avg_tokens_per_second': data['avg_tokens_per_second'],
                        'vram_used_mb': data['vram_used_mb'],
                        'vram_usage_percent': data['vram_usage_percent'],
                        'function_calling_success_rate': data['function_calling_success_rate'],
                        'success_rate': data['success_rate']
                    })

        # TTS Results
        tts_csv_path = f"tts_grid_search_{timestamp}.csv"
        with open(tts_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['model_name', 'avg_synthesis_time', 'min_synthesis_time', 'max_synthesis_time', 'avg_file_size']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for name, data in self.results["tts"].items():
                if data["errors"] == 0:
                    writer.writerow({
                        'model_name': name,
                        'avg_synthesis_time': data['avg_synthesis_time'],
                        'min_synthesis_time': data['min_synthesis_time'],
                        'max_synthesis_time': data['max_synthesis_time'],
                        'avg_file_size': data['avg_file_size']
                    })

        # LLM x TTS Combinations
        combo_csv_path = f"llm_tts_combinations_{timestamp}.csv"
        with open(combo_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['llm_model', 'tts_model', 'llm_time', 'tts_time', 'total_time', 'success']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for combo in self.results["combinations"]:
                if combo.get("success"):
                    writer.writerow({
                        'llm_model': combo['llm'],
                        'tts_model': combo['tts'],
                        'llm_time': combo['llm_time'],
                        'tts_time': combo['tts_time'],
                        'total_time': combo['total_time'],
                        'success': combo['success']
                    })

        print(f"📊 Grid search results exported:")
        print(f"   - {llm_csv_path}")
        print(f"   - {tts_csv_path}")
        print(f"   - {combo_csv_path}")

    def _print_grid_search_results(self):
        """Print comprehensive grid search results"""
        print("\n" + "="*80)
        print("🚀 GRID SEARCH PERFORMANCE RESULTS - SELF-HOSTED LLM INFRASTRUCTURE")
        print("="*80)
        
        # LLM Performance with Function Calling
        llm_table = []
        for name, data in self.results["llm"].items():
            if data["errors"] == 0:
                llm_table.append([
                    name,
                    f"{data['avg_first_token_time']:.3f}s",
                    f"{data['avg_response_time']:.3f}s",
                    f"{data['avg_tokens_per_second']:.1f}",
                    f"{data['vram_used_mb']}MB",
                    f"{data['function_calling_success_rate']:.1%}",
                    f"{data['success_rate']:.1%}",
                ])

        if llm_table:
            print("\n🧠 LLM Performance (with Function Calling):")
            print(tabulate(
                llm_table,
                headers=["Model", "First Token", "Total Time", "Tokens/sec", "VRAM", "Function Calls", "Success Rate"],
                tablefmt="github",
            ))

        # TTS Performance
        tts_table = []
        for name, data in self.results["tts"].items():
            if data["errors"] == 0:
                tts_table.append([
                    name,
                    f"{data['avg_synthesis_time']:.3f}s",
                    f"{data['min_synthesis_time']:.3f}s",
                    f"{data['max_synthesis_time']:.3f}s",
                ])

        if tts_table:
            print("\n🎵 TTS Performance:")
            print(tabulate(
                tts_table,
                headers=["Model", "Avg Time", "Min Time", "Max Time"],
                tablefmt="github",
            ))

        # Best Combinations
        if self.results["combinations"]:
            successful_combos = [c for c in self.results["combinations"] if c.get("success")]
            if successful_combos:
                # Sort by total time
                successful_combos.sort(key=lambda x: x["total_time"])
                
                print("\n🏆 Top LLM × TTS Combinations (by total latency):")
                combo_table = []
                for combo in successful_combos[:10]:  # Show top 10
                    combo_table.append([
                        f"{combo['llm']} + {combo['tts']}",
                        f"{combo['llm_time']:.3f}s",
                        f"{combo['tts_time']:.3f}s",
                        f"{combo['total_time']:.3f}s",
                    ])
                
                print(tabulate(
                    combo_table,
                    headers=["Combination", "LLM Time", "TTS Time", "Total Time"],
                    tablefmt="github",
                ))

    async def run_grid_search(self):
        """Execute complete grid search across LLM × TTS combinations"""
        print("🚀 Starting Grid Search Performance Testing")
        print("🔍 Testing LLM × TTS combinations with function calling integration")
        print("="*80)
        
        # Test LLM models
        llm_configs = self.config.get("LLM", {})
        for llm_name, llm_config in llm_configs.items():
            if llm_config.get("type") == "ollama":  # Only test local models
                result = await self._test_llm_performance(llm_name, llm_config)
                if result["errors"] == 0:
                    self.results["llm"][llm_name] = result
                await asyncio.sleep(1)  # Brief pause between models
        
        # Test TTS models
        for tts_name, tts_config in self.tts_models.items():
            result = await self._test_tts_performance(tts_name, tts_config)
            if result["errors"] == 0:
                self.results["tts"][tts_name] = result
        
        # Test LLM × TTS combinations
        print("\n🔄 Testing LLM × TTS combinations...")
        for llm_name in self.results["llm"].keys():
            for tts_name in self.results["tts"].keys():
                combo_result = await self._test_combination(llm_name, tts_name)
                self.results["combinations"].append(combo_result)
                await asyncio.sleep(0.5)  # Brief pause between combinations
        
        # Generate results
        self._print_grid_search_results()
        self._export_grid_search_results()

async def main():
    tester = GridSearchPerformanceTester()
    await tester.run_grid_search()

if __name__ == "__main__":
    asyncio.run(main())