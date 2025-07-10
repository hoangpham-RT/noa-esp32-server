#!/usr/bin/env python3
"""
Function Calling Test Suite for ESP32 IoT Assistant
Tests the function calling capabilities of local LLM models with IoT scenarios
"""

import asyncio
import json
import time
from typing import Dict, List
from config.settings import load_config
from core.utils.llm import create_instance as create_llm_instance

class ESP32FunctionCallingTester:
    def __init__(self):
        self.config = load_config()
        self.test_scenarios = [
            {
                "name": "Weather Query",
                "prompt": "What's the weather like in New York today?",
                "expected_function": "get_weather",
                "description": "Should call weather API function"
            },
            {
                "name": "Smart Home Control",
                "prompt": "Turn on the living room lights",
                "expected_function": "home_control",
                "description": "Should recognize IoT device control intent"
            },
            {
                "name": "Music Playback",
                "prompt": "Play some relaxing music",
                "expected_function": "play_music",
                "description": "Should call music playback function"
            },
            {
                "name": "News Request",
                "prompt": "Tell me the latest news",
                "expected_function": "get_news",
                "description": "Should call news retrieval function"
            },
            {
                "name": "Temperature Control",
                "prompt": "Set the temperature to 22 degrees",
                "expected_function": "temperature_control",
                "description": "Should recognize temperature control intent"
            },
            {
                "name": "Time Query",
                "prompt": "What time is it?",
                "expected_function": "get_time",
                "description": "Should handle time queries"
            },
            {
                "name": "Device Status",
                "prompt": "Check if the bedroom fan is on",
                "expected_function": "device_status",
                "description": "Should query device status"
            },
            {
                "name": "Complex Control",
                "prompt": "Turn off all lights and play some jazz music",
                "expected_function": "multiple_functions",
                "description": "Should handle multiple function calls"
            }
        ]
        
        self.results = {}

    async def test_model_function_calling(self, model_name: str, config: Dict) -> Dict:
        """Test function calling capability for a specific model"""
        print(f"\n🧪 Testing Function Calling: {model_name}")
        
        try:
            module_type = config.get("type", "ollama")
            llm = create_llm_instance(module_type, config)
            
            model_results = {
                "model": model_name,
                "successful_calls": 0,
                "total_tests": len(self.test_scenarios),
                "scenarios": []
            }
            
            for scenario in self.test_scenarios:
                print(f"  📝 Testing: {scenario['name']}")
                start_time = time.time()
                
                try:
                    # Create function calling prompt
                    function_prompt = f"""
You are an IoT assistant with function calling capabilities. 
For the user request: "{scenario['prompt']}"

Available functions:
- get_weather(location): Get weather information
- play_music(genre): Play music
- get_news(source): Get latest news
- home_control(device, action): Control smart home devices
- temperature_control(temperature): Set temperature
- get_time(): Get current time
- device_status(device): Check device status

Respond with appropriate function calls in JSON format, or provide a direct answer if no function is needed.
"""
                    
                    # Test the model's response
                    response_chunks = []
                    for chunk in llm.response("function_test", [{"role": "user", "content": function_prompt}]):
                        response_chunks.append(chunk)
                    
                    response = "".join(response_chunks)
                    response_time = time.time() - start_time
                    
                    # Analyze response for function calling
                    function_detected = self._analyze_function_response(response, scenario)
                    
                    scenario_result = {
                        "name": scenario["name"],
                        "prompt": scenario["prompt"],
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "response_time": response_time,
                        "function_detected": function_detected,
                        "success": function_detected
                    }
                    
                    if function_detected:
                        model_results["successful_calls"] += 1
                        print(f"    ✅ Function calling detected ({response_time:.2f}s)")
                    else:
                        print(f"    ❌ No function calling detected ({response_time:.2f}s)")
                    
                    model_results["scenarios"].append(scenario_result)
                    
                except Exception as e:
                    print(f"    ⚠️ Test failed: {str(e)}")
                    model_results["scenarios"].append({
                        "name": scenario["name"],
                        "prompt": scenario["prompt"],
                        "response": f"Error: {str(e)}",
                        "response_time": 0,
                        "function_detected": False,
                        "success": False
                    })
            
            # Calculate success rate
            model_results["success_rate"] = model_results["successful_calls"] / model_results["total_tests"]
            
            print(f"  📊 Success Rate: {model_results['success_rate']:.1%} ({model_results['successful_calls']}/{model_results['total_tests']})")
            
            return model_results
            
        except Exception as e:
            print(f"  ❌ Model test failed: {str(e)}")
            return {
                "model": model_name,
                "successful_calls": 0,
                "total_tests": len(self.test_scenarios),
                "success_rate": 0.0,
                "error": str(e)
            }

    def _analyze_function_response(self, response: str, scenario: Dict) -> bool:
        """Analyze if the response contains function calling patterns"""
        response_lower = response.lower()
        
        # Check for JSON-like function calling patterns
        json_patterns = [
            "get_weather", "play_music", "get_news", "home_control",
            "temperature_control", "get_time", "device_status"
        ]
        
        # Check for function calling keywords
        function_keywords = [
            "function", "call", "invoke", "execute", "api",
            "weather api", "music player", "news feed", "smart home"
        ]
        
        # Check for structured response patterns
        structured_patterns = [
            "{", "}", "[", "]", "function_name", "parameters"
        ]
        
        # Score the response
        score = 0
        
        # JSON/function patterns (highest weight)
        for pattern in json_patterns:
            if pattern in response_lower:
                score += 3
                
        # Function keywords (medium weight)
        for keyword in function_keywords:
            if keyword in response_lower:
                score += 2
                
        # Structured patterns (low weight)
        for pattern in structured_patterns:
            if pattern in response_lower:
                score += 1
        
        # Special case: Direct appropriate responses
        if scenario["name"] == "Weather Query" and any(word in response_lower for word in ["weather", "temperature", "forecast"]):
            score += 2
        elif scenario["name"] == "Music Playback" and any(word in response_lower for word in ["music", "play", "song"]):
            score += 2
        elif scenario["name"] == "News Request" and any(word in response_lower for word in ["news", "article", "update"]):
            score += 2
            
        return score >= 3  # Threshold for function calling detection

    async def run_all_tests(self):
        """Run function calling tests on all available local models"""
        print("🚀 ESP32 IoT Function Calling Test Suite")
        print("=" * 60)
        
        # Get available LLM models from config
        llm_configs = self.config.get("LLM", {})
        
        for model_name, model_config in llm_configs.items():
            # Only test Ollama models (local)
            if model_config.get("type") == "ollama":
                result = await self.test_model_function_calling(model_name, model_config)
                self.results[model_name] = result
                
                # Small delay between tests
                await asyncio.sleep(2)
        
        # Generate summary report
        self._generate_summary_report()

    def _generate_summary_report(self):
        """Generate and display summary report"""
        print("\n" + "=" * 60)
        print("📋 FUNCTION CALLING TEST SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("⚠️ No test results available")
            return
            
        # Sort models by success rate
        sorted_results = sorted(
            [(name, data) for name, data in self.results.items() if "success_rate" in data],
            key=lambda x: x[1]["success_rate"],
            reverse=True
        )
        
        print("\n🏆 Model Rankings (by function calling capability):")
        for i, (model_name, data) in enumerate(sorted_results, 1):
            success_rate = data["success_rate"]
            successful_calls = data["successful_calls"]
            total_tests = data["total_tests"]
            
            status = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            
            print(f"{status} {i}. {model_name}")
            print(f"   Success Rate: {success_rate:.1%} ({successful_calls}/{total_tests})")
        
        # Best performers summary
        if sorted_results:
            best_model = sorted_results[0]
            print(f"\n🎯 Best Performer: {best_model[0]} ({best_model[1]['success_rate']:.1%} success rate)")
            
            # Show scenario breakdown for best model
            print(f"\n📊 Scenario Breakdown for {best_model[0]}:")
            for scenario in best_model[1].get("scenarios", []):
                status = "✅" if scenario["success"] else "❌"
                print(f"   {status} {scenario['name']}: {scenario['response_time']:.2f}s")
        
        print(f"\n💡 Recommendations:")
        print(f"   - Models with >70% success rate are suitable for IoT function calling")
        print(f"   - Response time <2s recommended for real-time ESP32 interaction")
        print(f"   - Test actual function integration with top performers")

async def main():
    tester = ESP32FunctionCallingTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())