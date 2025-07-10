import asyncio
import csv
import json
import logging
import os
import statistics
import subprocess
import time
from datetime import datetime
from typing import Dict, List

import aiohttp
from tabulate import tabulate

from config.settings import load_config
from core.utils.asr import create_instance as create_stt_instance
from core.utils.llm import create_instance as create_llm_instance
from core.utils.tts import create_instance as create_tts_instance

# Set global log level to WARNING to suppress INFO logs
logging.basicConfig(level=logging.WARNING)


class EnhancedPerformanceTester:
    def __init__(self):
        self.config = load_config()
        self.test_sentences = self.config.get("module_test", {}).get(
            "test_sentences",
            [
                "Hello, please introduce yourself",
                "What's the weather like today?",
                "Please explain quantum computing principles in 100 words",
                "How do I cook pasta?",
                "What are the benefits of renewable energy?",
            ],
        )

        # Load test audio files
        self.test_wav_list = []
        self.wav_root = r"config/assets"
        if os.path.exists(self.wav_root):
            for file_name in os.listdir(self.wav_root):
                file_path = os.path.join(self.wav_root, file_name)
                # Check if file is larger than 300KB
                if os.path.getsize(file_path) > 300 * 1024:
                    with open(file_path, "rb") as f:
                        self.test_wav_list.append(f.read())

        self.results = {"llm": {}, "tts": {}, "stt": {}, "combinations": []}
        self.detailed_results = []
        
        # Enhanced metrics for self-hosted models (no pricing needed)
        self.vram_usage = {}

    async def _check_service_health(self, base_url: str, service_name: str) -> bool:
        """Check if a service is healthy and accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/health", timeout=5) as response:
                    return response.status == 200
        except Exception:
            return False

    async def _check_ollama_service(self, base_url: str, model_name: str) -> bool:
        """Check Ollama service status"""
        async with aiohttp.ClientSession() as session:
            try:
                # Check if service is available
                async with session.get(f"{base_url}/api/version", timeout=5) as response:
                    if response.status != 200:
                        print(f"🚫 Ollama service not available: {base_url}")
                        return False

                # Check if model exists
                async with session.get(f"{base_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        if not any(model["name"] == model_name for model in models):
                            print(f"🚫 Ollama model {model_name} not found. Please run: ollama pull {model_name}")
                            return False
                    else:
                        print(f"🚫 Cannot get Ollama model list")
                        return False
                return True
            except Exception as e:
                print(f"🚫 Cannot connect to Ollama service: {str(e)}")
                return False

    async def _test_tts_performance(self, tts_name: str, config: Dict) -> Dict:
        """Test TTS performance with enhanced metrics"""
        try:
            print(f"🎵 Testing TTS: {tts_name}")
            
            # Skip if API key not configured
            token_fields = ["access_token", "api_key", "token"]
            if any(
                field in config
                and any(x in config[field] for x in ["你的", "placeholder", "your_"])
                for field in token_fields
            ):
                print(f"⏭️  TTS {tts_name} API key not configured, skipping")
                return {"name": tts_name, "type": "tts", "errors": 1}

            module_type = config.get("type", tts_name)
            tts = create_tts_instance(module_type, config, delete_audio_file=True)

            # Connection test
            test_start = time.time()
            tmp_file = tts.generate_filename()
            await tts.text_to_speak("Connection test", tmp_file)
            connection_time = time.time() - test_start

            if not tmp_file or not os.path.exists(tmp_file):
                print(f"❌ {tts_name} connection failed")
                return {"name": tts_name, "type": "tts", "errors": 1}

            # Performance testing
            synthesis_times = []
            file_sizes = []
            
            for i, sentence in enumerate(self.test_sentences[:3], 1):
                start_time = time.time()
                tmp_file = tts.generate_filename()
                await tts.text_to_speak(sentence, tmp_file)
                synthesis_time = time.time() - start_time
                synthesis_times.append(synthesis_time)

                if tmp_file and os.path.exists(tmp_file):
                    file_sizes.append(os.path.getsize(tmp_file))
                    print(f"✓ {tts_name} [{i}/3] - {synthesis_time:.3f}s")
                else:
                    print(f"✗ {tts_name} [{i}/3] - Failed")
                    return {"name": tts_name, "type": "tts", "errors": 1}

            return {
                "name": tts_name,
                "type": "tts",
                "avg_synthesis_time": statistics.mean(synthesis_times),
                "min_synthesis_time": min(synthesis_times),
                "max_synthesis_time": max(synthesis_times),
                "std_synthesis_time": statistics.stdev(synthesis_times) if len(synthesis_times) > 1 else 0,
                "connection_time": connection_time,
                "avg_file_size": statistics.mean(file_sizes) if file_sizes else 0,
                "errors": 0,
            }

        except Exception as e:
            print(f"⚠️ {tts_name} test failed: {str(e)}")
            return {"name": tts_name, "type": "tts", "errors": 1}

    async def _test_stt_performance(self, stt_name: str, config: Dict) -> Dict:
        """Test STT performance with enhanced metrics"""
        try:
            print(f"🎵 Testing STT: {stt_name}")
            
            # Skip if API key not configured
            token_fields = ["access_token", "api_key", "token"]
            if any(
                field in config
                and any(x in config[field] for x in ["你的", "placeholder", "your_"])
                for field in token_fields
            ):
                print(f"⏭️  STT {stt_name} API key not configured, skipping")
                return {"name": stt_name, "type": "stt", "errors": 1}

            module_type = config.get("type", stt_name)
            stt = create_stt_instance(module_type, config, delete_audio_file=True)
            stt.audio_format = "pcm"

            if not self.test_wav_list:
                print(f"⚠️ No audio files found for STT testing")
                return {"name": stt_name, "type": "stt", "errors": 1}

            # Connection test
            connection_start = time.time()
            text, _ = await stt.speech_to_text([self.test_wav_list[0]], "1", stt.audio_format)
            connection_time = time.time() - connection_start

            if text is None:
                print(f"❌ {stt_name} connection failed")
                return {"name": stt_name, "type": "stt", "errors": 1}

            # Performance testing
            processing_times = []
            recognition_results = []
            
            for i, audio_data in enumerate(self.test_wav_list, 1):
                start_time = time.time()
                text, confidence = await stt.speech_to_text([audio_data], "1", stt.audio_format)
                processing_time = time.time() - start_time
                processing_times.append(processing_time)

                if text:
                    recognition_results.append({
                        "text": text,
                        "confidence": confidence,
                        "processing_time": processing_time,
                        "audio_size": len(audio_data)
                    })
                    print(f"✓ {stt_name} [{i}/{len(self.test_wav_list)}] - {processing_time:.3f}s")
                else:
                    print(f"✗ {stt_name} [{i}/{len(self.test_wav_list)}] - Failed")
                    return {"name": stt_name, "type": "stt", "errors": 1}

            return {
                "name": stt_name,
                "type": "stt",
                "avg_processing_time": statistics.mean(processing_times),
                "min_processing_time": min(processing_times),
                "max_processing_time": max(processing_times),
                "std_processing_time": statistics.stdev(processing_times) if len(processing_times) > 1 else 0,
                "connection_time": connection_time,
                "success_rate": len(recognition_results) / len(self.test_wav_list),
                "errors": 0,
            }

        except Exception as e:
            print(f"⚠️ {stt_name} test failed: {str(e)}")
            return {"name": stt_name, "type": "stt", "errors": 1}

    async def _test_llm_performance(self, llm_name: str, config: Dict) -> Dict:
        """Test LLM performance with enhanced metrics"""
        try:
            print(f"🧠 Testing LLM: {llm_name}")
            
            # Special handling for Ollama
            if llm_name == "OllamaLLM":
                base_url = config.get("base_url", "http://localhost:11434")
                model_name = config.get("model_name")
                if not model_name:
                    print(f"🚫 Ollama model_name not configured")
                    return {"name": llm_name, "type": "llm", "errors": 1}

                if not await self._check_ollama_service(base_url, model_name):
                    return {"name": llm_name, "type": "llm", "errors": 1}
            else:
                # Skip if API key not configured
                if "api_key" in config and any(
                    x in config["api_key"] for x in ["你的", "placeholder", "your_", "sk-xxx"]
                ):
                    print(f"🚫 Skipping unconfigured LLM: {llm_name}")
                    return {"name": llm_name, "type": "llm", "errors": 1}

            # Get actual type (compatibility with old config)
            module_type = config.get("type", llm_name)
            llm = create_llm_instance(module_type, config)
            
            # Record VRAM usage before testing
            self.vram_usage[llm_name] = self._get_vram_usage()

            # Test with UTF-8 encoding
            test_sentences = [s.encode("utf-8").decode("utf-8") for s in self.test_sentences]

            # Create test tasks for all sentences
            sentence_tasks = []
            for sentence in test_sentences:
                sentence_tasks.append(
                    self._test_single_sentence(llm_name, llm, sentence)
                )

            # Execute all sentence tests concurrently
            sentence_results = await asyncio.gather(*sentence_tasks)

            # Process results
            valid_results = [r for r in sentence_results if r is not None]
            if not valid_results:
                print(f"⚠️  {llm_name} no valid data, possibly misconfigured")
                return {"name": llm_name, "type": "llm", "errors": 1}

            # Calculate metrics
            first_token_times = [r["first_token_time"] for r in valid_results]
            response_times = [r["response_time"] for r in valid_results]
            response_lengths = [r["response_length"] for r in valid_results]
            tokens_per_second = [r["tokens_per_second"] for r in valid_results]

            # Filter anomalous data
            mean_response = statistics.mean(response_times)
            stdev_response = statistics.stdev(response_times) if len(response_times) > 1 else 0
            filtered_times = [t for t in response_times if t <= mean_response + 3 * stdev_response]

            if len(filtered_times) < len(test_sentences) * 0.5:
                print(f"⚠️  {llm_name} insufficient valid data, possibly unstable network")
                return {"name": llm_name, "type": "llm", "errors": 1}

            return {
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
                "success_rate": len(valid_results) / len(test_sentences),
                "errors": 0,
            }
        except Exception as e:
            print(f"⚠️ LLM {llm_name} test failed: {str(e)}")
            return {"name": llm_name, "type": "llm", "errors": 1}

    async def _test_single_sentence(self, llm_name: str, llm, sentence: str) -> Dict:
        """Test performance for a single sentence"""
        try:
            print(f"📝 {llm_name} testing: {sentence[:30]}...")
            sentence_start = time.time()
            first_token_received = False
            first_token_time = None
            response_content = ""

            async def process_response():
                nonlocal first_token_received, first_token_time, response_content
                token_count = 0
                for chunk in llm.response("perf_test", [{"role": "user", "content": sentence}]):
                    if not first_token_received and chunk.strip() != "":
                        first_token_time = time.time() - sentence_start
                        first_token_received = True
                        print(f"✓ {llm_name} first token: {first_token_time:.3f}s")
                    response_content += chunk
                    token_count += 1
                    yield chunk

            response_chunks = []
            async for chunk in process_response():
                response_chunks.append(chunk)

            response_time = time.time() - sentence_start
            response_length = len(response_content)
            tokens_per_second = response_length / response_time if response_time > 0 else 0
            
            print(f"✓ {llm_name} completed: {response_time:.3f}s, {response_length} chars, {tokens_per_second:.1f} chars/s")

            if first_token_time is None:
                first_token_time = response_time  # If no first token detected, use total response time

            return {
                "name": llm_name,
                "type": "llm",
                "first_token_time": first_token_time,
                "response_time": response_time,
                "response_length": response_length,
                "tokens_per_second": tokens_per_second,
                "sentence": sentence,
                "response": response_content[:100] + "..." if len(response_content) > 100 else response_content,
            }
        except Exception as e:
            print(f"⚠️ {llm_name} sentence test failed: {str(e)}")
            return None

    def _get_vram_usage(self):
        """Get VRAM usage information (if available)"""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    used, total = lines[0].split(', ')
                    return {"used_mb": int(used), "total_mb": int(total), "usage_percent": int(used)/int(total)*100}
        except Exception:
            pass
        return {"used_mb": 0, "total_mb": 0, "usage_percent": 0}

    def _export_to_csv(self):
        """Export results to CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # LLM Results CSV
        llm_csv_path = f"llm_performance_{timestamp}.csv"
        with open(llm_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'model_name', 'avg_first_token_time', 'min_first_token_time', 'max_first_token_time',
                'avg_response_time', 'min_response_time', 'max_response_time',
                'std_first_token', 'std_response', 'avg_response_length',
                'avg_tokens_per_second', 'success_rate'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for name, data in self.results["llm"].items():
                if data["errors"] == 0:
                    writer.writerow({
                        'model_name': name,
                        'avg_first_token_time': data['avg_first_token_time'],
                        'min_first_token_time': data['min_first_token_time'],
                        'max_first_token_time': data['max_first_token_time'],
                        'avg_response_time': data['avg_response_time'],
                        'min_response_time': data['min_response_time'],
                        'max_response_time': data['max_response_time'],
                        'std_first_token': data['std_first_token'],
                        'std_response': data['std_response'],
                        'avg_response_length': data['avg_response_length'],
                        'avg_tokens_per_second': data['avg_tokens_per_second'],
                        'success_rate': data['success_rate']
                    })

        # VRAM Usage Summary CSV
        vram_csv_path = f"vram_usage_{timestamp}.csv"
        with open(vram_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['model_name', 'vram_used_mb', 'vram_total_mb', 'vram_usage_percent']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for name, data in self.results["llm"].items():
                if data["errors"] == 0:
                    vram_info = self.vram_usage.get(name, {"used_mb": 0, "total_mb": 0, "usage_percent": 0})
                    writer.writerow({
                        'model_name': name,
                        'vram_used_mb': vram_info['used_mb'],
                        'vram_total_mb': vram_info['total_mb'],
                        'vram_usage_percent': vram_info['usage_percent']
                    })

        print(f"📊 Results exported to:")
        print(f"   - {llm_csv_path}")
        print(f"   - {vram_csv_path}")

    def _generate_combinations(self):
        """Generate optimal combination recommendations"""
        valid_llms = [
            k for k, v in self.results["llm"].items()
            if v["errors"] == 0 and v["avg_first_token_time"] >= 0.05
        ]
        valid_tts = [k for k, v in self.results["tts"].items() if v["errors"] == 0]
        valid_stt = [k for k, v in self.results["stt"].items() if v["errors"] == 0]

        # Find baseline values
        min_first_token = (
            min([self.results["llm"][llm]["avg_first_token_time"] for llm in valid_llms])
            if valid_llms else 1
        )
        min_tts_time = (
            min([self.results["tts"][tts]["avg_synthesis_time"] for tts in valid_tts])
            if valid_tts else 1
        )
        min_stt_time = (
            min([self.results["stt"][stt]["avg_processing_time"] for stt in valid_stt])
            if valid_stt else 1
        )

        for llm in valid_llms:
            for tts in valid_tts:
                for stt in valid_stt:
                    # Calculate relative performance scores (lower is better)
                    llm_score = self.results["llm"][llm]["avg_first_token_time"] / min_first_token
                    tts_score = self.results["tts"][tts]["avg_synthesis_time"] / min_tts_time
                    stt_score = self.results["stt"][stt]["avg_processing_time"] / min_stt_time

                    # Calculate stability score (std_dev/mean, lower is more stable)
                    llm_stability = (
                        self.results["llm"][llm]["std_first_token"] /
                        self.results["llm"][llm]["avg_first_token_time"]
                    )

                    # Composite score considering performance and stability
                    llm_final_score = llm_score * 0.7 + llm_stability * 0.3
                    total_score = llm_final_score * 0.7 + tts_score * 0.3 + stt_score * 0.3

                    self.results["combinations"].append({
                        "llm": llm,
                        "tts": tts,
                        "stt": stt,
                        "score": total_score,
                        "details": {
                            "llm_first_token": self.results["llm"][llm]["avg_first_token_time"],
                            "llm_stability": llm_stability,
                            "tts_time": self.results["tts"][tts]["avg_synthesis_time"],
                            "stt_time": self.results["stt"][stt]["avg_processing_time"],
                        },
                    })

        # Sort by score (lower is better)
        self.results["combinations"].sort(key=lambda x: x["score"])

    def _print_results(self):
        """Print test results in formatted tables"""
        print("\n" + "="*80)
        print("🚀 XIAOZHI ESP32 SERVER - PERFORMANCE BENCHMARK RESULTS")
        print("="*80)
        
        # LLM Performance Table
        llm_table = []
        for name, data in self.results["llm"].items():
            if data["errors"] == 0:
                stability = data["std_first_token"] / data["avg_first_token_time"]
                llm_table.append([
                    name,
                    f"{data['avg_first_token_time']:.3f}s",
                    f"{data['avg_response_time']:.3f}s",
                    f"{data['avg_tokens_per_second']:.1f}",
                    f"{stability:.3f}",
                    f"{data['success_rate']:.1%}",
                ])

        if llm_table:
            print("\n🧠 LLM Performance Ranking:")
            print(tabulate(
                llm_table,
                headers=["Model", "First Token", "Total Time", "Tokens/sec", "Stability", "Success Rate"],
                tablefmt="github",
                colalign=("left", "right", "right", "right", "right", "right"),
            ))
        else:
            print("\n⚠️ No LLM modules available for testing.")

        # TTS Performance Table
        tts_table = []
        for name, data in self.results["tts"].items():
            if data["errors"] == 0:
                tts_table.append([
                    name,
                    f"{data['avg_synthesis_time']:.3f}s",
                    f"{data['min_synthesis_time']:.3f}s",
                    f"{data['max_synthesis_time']:.3f}s",
                    f"{data['connection_time']:.3f}s",
                ])

        if tts_table:
            print("\n🎵 TTS Performance Ranking:")
            print(tabulate(
                tts_table,
                headers=["Model", "Avg Time", "Min Time", "Max Time", "Connection"],
                tablefmt="github",
                colalign=("left", "right", "right", "right", "right"),
            ))
        else:
            print("\n⚠️ No TTS modules available for testing.")

        # STT Performance Table
        stt_table = []
        for name, data in self.results["stt"].items():
            if data["errors"] == 0:
                stt_table.append([
                    name,
                    f"{data['avg_processing_time']:.3f}s",
                    f"{data['min_processing_time']:.3f}s",
                    f"{data['max_processing_time']:.3f}s",
                    f"{data['success_rate']:.1%}",
                ])

        if stt_table:
            print("\n🎤 STT Performance Ranking:")
            print(tabulate(
                stt_table,
                headers=["Model", "Avg Time", "Min Time", "Max Time", "Success Rate"],
                tablefmt="github",
                colalign=("left", "right", "right", "right", "right"),
            ))
        else:
            print("\n⚠️ No STT modules available for testing.")

        # Recommended Combinations
        if self.results["combinations"]:
            print("\n🏆 Recommended Combinations (lower score = better):")
            combo_table = []
            for combo in self.results["combinations"][:5]:  # Show top 5
                combo_table.append([
                    f"{combo['llm']} + {combo['tts']} + {combo['stt']}",
                    f"{combo['score']:.3f}",
                    f"{combo['details']['llm_first_token']:.3f}s",
                    f"{combo['details']['llm_stability']:.3f}",
                    f"{combo['details']['tts_time']:.3f}s",
                    f"{combo['details']['stt_time']:.3f}s",
                ])

            print(tabulate(
                combo_table,
                headers=["Combination", "Score", "LLM First Token", "Stability", "TTS Time", "STT Time"],
                tablefmt="github",
                colalign=("left", "right", "right", "right", "right", "right"),
            ))
        else:
            print("\n⚠️ No module combinations available for recommendations.")

        # VRAM Usage Analysis
        if self.vram_usage:
            print("\n💾 VRAM Usage Analysis:")
            vram_table = []
            for llm_name, llm_data in self.results["llm"].items():
                if llm_data["errors"] == 0:
                    vram_info = self.vram_usage.get(llm_name, {"used_mb": 0, "total_mb": 0, "usage_percent": 0})
                    vram_table.append([
                        llm_name,
                        f"{llm_data['avg_first_token_time']:.3f}s",
                        f"{vram_info['used_mb']}MB",
                        f"{vram_info['usage_percent']:.1f}%",
                        f"{llm_data.get('avg_tokens_per_second', 0):.1f}",
                    ])
            
            if vram_table:
                print(tabulate(
                    vram_table,
                    headers=["Model", "First Token", "VRAM Used", "VRAM %", "Tokens/sec"],
                    tablefmt="github",
                    colalign=("left", "right", "right", "right", "right"),
                ))

    async def run_with_timeout(self, timeout_seconds=300):
        """Run tests with timeout handling"""
        print("🔍 Starting enhanced performance testing...")
        print(f"⏱️  Timeout set to {timeout_seconds} seconds")
        
        try:
            await asyncio.wait_for(self.run(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            print(f"\n⏰ Tests timed out after {timeout_seconds} seconds")
            print("📊 Generating report with available results...")
            self._generate_combinations()
            self._print_results()
            self._export_to_csv()

    async def run(self):
        """Execute comprehensive performance testing"""
        print("🔍 Scanning available modules...")

        # Create all test tasks
        all_tasks = []

        # LLM test tasks
        if self.config.get("LLM") is not None:
            for llm_name, config in self.config.get("LLM", {}).items():
                # Check configuration validity
                if llm_name == "CozeLLM":
                    if any(x in config.get("bot_id", "") for x in ["你的", "your_"]) or any(
                        x in config.get("user_id", "") for x in ["你的", "your_"]
                    ):
                        print(f"⏭️  LLM {llm_name} bot_id/user_id not configured, skipping")
                        continue
                elif "api_key" in config and any(
                    x in config["api_key"] for x in ["你的", "placeholder", "your_", "sk-xxx"]
                ):
                    print(f"⏭️  LLM {llm_name} api_key not configured, skipping")
                    continue

                print(f"📋 Adding LLM test task: {llm_name}")
                all_tasks.append(self._test_llm_performance(llm_name, config))

        # TTS test tasks
        if self.config.get("TTS") is not None:
            for tts_name, config in self.config.get("TTS", {}).items():
                token_fields = ["access_token", "api_key", "token"]
                if any(
                    field in config
                    and any(x in config[field] for x in ["你的", "placeholder", "your_"])
                    for field in token_fields
                ):
                    print(f"⏭️  TTS {tts_name} API key not configured, skipping")
                    continue
                print(f"🎵 Adding TTS test task: {tts_name}")
                all_tasks.append(self._test_tts_performance(tts_name, config))

        # STT test tasks
        if len(self.test_wav_list) >= 1:
            if self.config.get("ASR") is not None:
                for stt_name, config in self.config.get("ASR", {}).items():
                    token_fields = ["access_token", "api_key", "token"]
                    if any(
                        field in config
                        and any(x in config[field] for x in ["你的", "placeholder", "your_"])
                        for field in token_fields
                    ):
                        print(f"⏭️  ASR {stt_name} API key not configured, skipping")
                        continue
                    print(f"🎤 Adding ASR test task: {stt_name}")
                    all_tasks.append(self._test_stt_performance(stt_name, config))
        else:
            print(f"\n⚠️  No audio files found in {self.wav_root}, skipping STT tests")

        llm_tasks = [t for t in all_tasks if "llm" in str(t).lower()]
        tts_tasks = [t for t in all_tasks if "tts" in str(t).lower()]
        stt_tasks = [t for t in all_tasks if "stt" in str(t).lower()]

        print(f"\n✅ Found {len(llm_tasks)} LLM modules")
        print(f"✅ Found {len(tts_tasks)} TTS modules")
        print(f"✅ Found {len(stt_tasks)} STT modules")
        print(f"\n⏳ Starting concurrent testing of {len(all_tasks)} modules...\n")

        # Execute all tests concurrently
        all_results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Process results
        for result in all_results:
            if isinstance(result, dict) and result.get("errors") == 0:
                result_type = result.get("type")
                if result_type == "llm":
                    self.results["llm"][result["name"]] = result
                elif result_type == "tts":
                    self.results["tts"][result["name"]] = result
                elif result_type == "stt":
                    self.results["stt"][result["name"]] = result

        # Generate combinations and print results
        print("\n📊 Generating test report...")
        self._generate_combinations()
        self._print_results()
        self._export_to_csv()


async def main():
    tester = EnhancedPerformanceTester()
    await tester.run_with_timeout(timeout_seconds=600)  # 10 minute timeout


if __name__ == "__main__":
    asyncio.run(main())