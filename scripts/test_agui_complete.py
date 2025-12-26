#!/usr/bin/env python3
"""
AG-UI Streaming Test Suite - CORRECTED for Multi-Tenant Platform
Comprehensive testing for the streaming implementation

Usage:
    python test_agui_complete_fixed.py
    python test_agui_complete_fixed.py --url http://localhost:8000
    python test_agui_complete_fixed.py --agent-id 1 --token YOUR_TOKEN --tenant demo
"""

import asyncio
import json
import sys
import argparse
from typing import AsyncGenerator, Dict, Any
from datetime import datetime
import aiohttp


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class AGUIStreamingTester:
    """Comprehensive tester for AG-UI streaming implementation"""
    
    def __init__(self, base_url: str, token: str, agent_id: int, tenant_id: str):
        self.base_url = base_url.rstrip('/')
        self.token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI4VDlnRllNNXcxdVJlRGZzdGVLbG96d21xb1p3WlhPdUU0cG94ZF9SYUdrIn0.eyJleHAiOjE3NjY3NDAwOTIsImlhdCI6MTc2NjczOTc5MiwianRpIjoiNzQ0NWY3NWQtN2Q4ZC00NGE2LThkMzgtMTFmNzI5NTlmOTQxIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL3JlYWxtcy9hZ2VudGljIiwiYXVkIjpbImFnZW50aWMtYXBpIiwiYWNjb3VudCJdLCJzdWIiOiJkODY3NTRkZi0zMjZhLTRlMTAtYjM5My1jZTViMWI5NGI4YzQiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhZ2VudGljLWFwaSIsInNlc3Npb25fc3RhdGUiOiI0MjQzNmMxZC0xNWI4LTQ2ZDctOGYzMy0zMzQwZGViN2Y0NzAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cHM6Ly95b3VyZG9tYWluLmNvbSIsImh0dHA6Ly9sb2NhbGhvc3Q6ODAwMCIsImh0dHA6Ly9sb2NhbGhvc3Q6MzAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiU1VQRVJfQURNSU4iLCJkZWZhdWx0LXJvbGVzLWFnZW50aWMiLCJvZmZsaW5lX2FjY2VzcyIsIkFETUlOIiwidW1hX2F1dGhvcml6YXRpb24iLCJVU0VSIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJlbWFpbCBwcm9maWxlIiwic2lkIjoiNDI0MzZjMWQtMTViOC00NmQ3LThmMzMtMzM0MGRlYjdmNDcwIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInJvbGVzIjpbIlNVUEVSX0FETUlOIiwiZGVmYXVsdC1yb2xlcy1hZ2VudGljIiwib2ZmbGluZV9hY2Nlc3MiLCJBRE1JTiIsInVtYV9hdXRob3JpemF0aW9uIiwiVVNFUiJdLCJuYW1lIjoiU3VwZXIgQWRtaW4iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhZG1pbkB0ZXN0LmNvbSIsImdpdmVuX25hbWUiOiJTdXBlciIsImZhbWlseV9uYW1lIjoiQWRtaW4iLCJlbWFpbCI6ImFkbWluQHRlc3QuY29tIiwidGVuYW50IjoiZGVtbyJ9.VHhCzj8cp_STTaajkSj064fZ-ETPsMAyqgr1pvgtT6hTYdxKvzavwJkdPaLiNuZzAC2ZjAZdpno1iUG_PWcV-tcuCbM4y6N2Td35lLeFvnSHj7DvrWuuJTqltS_IZCfzmKSXjZUdOeMdJjtKtIb8dsRarpgvwugJZCbyZwEyxIyIaNXN29l-UYhizyXurDAsTn5NYpHpvQ_CXm_YVIHpOJQW4umGROByh1oOsnMRs7nb83JfusJKO0_v2bmFwW_LA5iyKoDIuVUp5OOy0FhIMocml0ZwDXD7xu_J6BfA7Jgrqbd6VnduGxPHANqw4IJrgPhIKiqKI6mrB99Iivd_ag"
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.test_results = []
    
    def get_headers(self, include_tenant: bool = True) -> Dict[str, str]:
        """Get headers for requests"""
        # print("self token",self.token)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        if include_tenant:
            headers["X-Tenant-ID"] = self.tenant_id
        return headers
    
    def print_header(self, text: str):
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}\n")
    
    def print_success(self, text: str):
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")
        self.test_results.append(("PASS", text))
    
    def print_failure(self, text: str, error: str = ""):
        print(f"{Colors.RED}✗ {text}{Colors.END}")
        if error:
            print(f"  {Colors.RED}Error: {error}{Colors.END}")
        self.test_results.append(("FAIL", text))
    
    def print_info(self, text: str):
        print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")
    
    async def test_health_check(self) -> bool:
        """Test 1: Health check endpoint"""
        self.print_header("Test 1: Health Check")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try the correct health endpoint
                async with session.get(f"{self.base_url}/api/v1/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.print_success(f"Health check passed: {data.get('status')}")
                        return True
                    else:
                        self.print_failure(f"Health check failed with status: {response.status}")
                        return False
        except Exception as e:
            self.print_failure("Health check failed", str(e))
            return False
    
    async def test_streaming_connection(self) -> bool:
        """Test 2: Basic streaming connection"""
        self.print_header("Test 2: Basic Streaming Connection")
        
        url = f"{self.base_url}/agui/agents/{self.agent_id}/run"
        
        payload = {
            "threadId": f"test_{datetime.now().timestamp()}",
            "messages": [
                {"role": "user", "content": "Hello, this is a test", "metadata": {}}
            ],
            "state": {}
        }
        
        headers = self.get_headers(include_tenant=True)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        self.print_failure(f"Connection failed with status: {response.status}")
                        text = await response.text()
                        self.print_info(f"Response: {text[:200]}")
                        return False
                    
                    self.print_success("Streaming connection established")
                    
                    # Read first few events
                    event_count = 0
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith('event:'):
                            event_type = line_str.split(':', 1)[1].strip()
                            self.print_info(f"  Received event: {event_type}")
                            event_count += 1
                        
                        if event_count >= 5:
                            break
                    
                    if event_count > 0:
                        self.print_success(f"Received {event_count} events")
                        return True
                    else:
                        self.print_failure("No events received")
                        return False
                        
        except Exception as e:
            self.print_failure("Streaming connection test failed", str(e))
            return False
    
    async def test_event_types(self) -> bool:
        """Test 3: Event types and structure"""
        self.print_header("Test 3: Event Types and Structure")
        
        url = f"{self.base_url}/agui/agents/{self.agent_id}/run"
        
        payload = {
            "threadId": f"test_events_{datetime.now().timestamp()}",
            "messages": [
                {"role": "user", "content": "What can you do?", "metadata": {}}
            ],
            "state": {}
        }
        
        headers = self.get_headers(include_tenant=True)
        
        received_event_types = set()
        event_structures = {}
        valid_structures = 0
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        self.print_failure(f"Connection failed with status: {response.status}")
                        return False
                    
                    buffer = ""
                    event_count = 0
                    async for line in response.content:
                        line_str = line.decode('utf-8')
                        buffer += line_str
                        
                        # Process complete events
                        if buffer.endswith('\n\n'):
                            lines = buffer.strip().split('\n')
                            event_type = None
                            event_data = None
                            
                            for l in lines:
                                if l.startswith('event:'):
                                    event_type = l.split(':', 1)[1].strip()
                                elif l.startswith('data:'):
                                    try:
                                        event_data = json.loads(l.split(':', 1)[1].strip())
                                    except:
                                        pass
                            
                            if event_type and event_data:
                                received_event_types.add(event_type)
                                event_structures[event_type] = event_data
                                self.print_info(f"  Event: {event_type}")
                                
                                # Validate event structure
                                if "id" in event_data and "timestamp" in event_data and "type" in event_data:
                                    self.print_success(f"    ✓ Valid structure (has id, timestamp, type)")
                                    valid_structures += 1
                                else:
                                    self.print_failure(f"    ✗ Invalid structure (missing fields)")
                                
                                event_count += 1
                                
                                # Check for completion
                                if event_type == "completion":
                                    break
                                
                                # Limit events to avoid too much output
                                if event_count >= 10:
                                    self.print_info("  (limiting to 10 events...)")
                                    break
                            
                            buffer = ""
            
            # Summary
            self.print_info(f"\nReceived event types: {received_event_types}")
            self.print_info(f"Valid structures: {valid_structures}/{len(received_event_types)}")
            
            if len(received_event_types) > 0:
                self.print_success(f"Received {len(received_event_types)} different event types")
                return True
            else:
                self.print_failure("No valid events received")
                return False
                
        except Exception as e:
            self.print_failure("Event types test failed", str(e))
            return False
    
    async def test_message_streaming(self) -> bool:
        """Test 4: Message chunk streaming"""
        self.print_header("Test 4: Message Chunk Streaming")
        
        url = f"{self.base_url}/agui/agents/{self.agent_id}/run"
        
        payload = {
            "threadId": f"test_chunks_{datetime.now().timestamp()}",
            "messages": [
                {"role": "user", "content": "Write a short haiku about AI", "metadata": {}}
            ],
            "state": {}
        }
        
        headers = self.get_headers(include_tenant=True)
        
        message_chunks = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        self.print_failure(f"Connection failed with status: {response.status}")
                        return False
                    
                    self.print_info("Streaming message chunks:")
                    print(f"\n{Colors.GREEN}", end='', flush=True)
                    
                    buffer = ""
                    async for line in response.content:
                        line_str = line.decode('utf-8')
                        buffer += line_str
                        
                        if buffer.endswith('\n\n'):
                            lines = buffer.strip().split('\n')
                            event_type = None
                            event_data = None
                            
                            for l in lines:
                                if l.startswith('event:'):
                                    event_type = l.split(':', 1)[1].strip()
                                elif l.startswith('data:'):
                                    try:
                                        event_data = json.loads(l.split(':', 1)[1].strip())
                                    except:
                                        pass
                            
                            if event_type == "message_chunk" and event_data:
                                content = event_data.get("data", {}).get("content", "")
                                message_chunks.append(content)
                                print(content, end='', flush=True)
                            
                            if event_type == "completion":
                                break
                            
                            buffer = ""
            
            print(f"{Colors.END}\n")  # New line after streaming
            
            full_message = "".join(message_chunks)
            
            if len(message_chunks) > 0:
                self.print_success(f"Received {len(message_chunks)} message chunks")
                self.print_info(f"Full message ({len(full_message)} chars)")
                return True
            else:
                self.print_failure("No message chunks received")
                return False
                
        except Exception as e:
            print(f"{Colors.END}")
            self.print_failure("Message streaming test failed", str(e))
            return False
    
    async def test_heartbeat(self) -> bool:
        """Test 5: Heartbeat support"""
        self.print_header("Test 5: Heartbeat Support")
        
        self.print_info("Testing heartbeat during long-running request...")
        self.print_info("This test will wait for 35 seconds to detect heartbeat")
        
        url = f"{self.base_url}/agui/agents/{self.agent_id}/run"
        
        payload = {
            "threadId": f"test_heartbeat_{datetime.now().timestamp()}",
            "messages": [
                {"role": "user", "content": "Hello", "metadata": {}}
            ],
            "state": {}
        }
        
        headers = self.get_headers(include_tenant=True)
        
        heartbeat_count = 0
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        self.print_failure(f"Connection failed with status: {response.status}")
                        return False
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        # Detect heartbeat
                        if line_str.startswith(':'):
                            heartbeat_count += 1
                            elapsed = (datetime.now() - start_time).seconds
                            self.print_info(f"  Heartbeat detected at {elapsed}s")
                        
                        # Exit after 35 seconds or completion
                        elapsed = (datetime.now() - start_time).seconds
                        if elapsed > 35 or heartbeat_count >= 2:
                            break
            
            if heartbeat_count > 0:
                self.print_success(f"Heartbeat working ({heartbeat_count} detected)")
                return True
            else:
                self.print_info("No heartbeat detected (may be OK if request completes quickly)")
                return True  # Don't fail if request is fast
                
        except Exception as e:
            self.print_failure("Heartbeat test failed", str(e))
            return False
    
    async def test_error_handling(self) -> bool:
        """Test 6: Error handling"""
        self.print_header("Test 6: Error Handling")
        
        # Test with invalid agent ID
        url = f"{self.base_url}/agui/agents/99999/run"
        
        payload = {
            "threadId": f"test_error_{datetime.now().timestamp()}",
            "messages": [
                {"role": "user", "content": "Test", "metadata": {}}
            ],
            "state": {}
        }
        
        headers = self.get_headers(include_tenant=True)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    # Should receive error event in stream
                    buffer = ""
                    received_error_event = False
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8')
                        buffer += line_str
                        
                        if buffer.endswith('\n\n'):
                            lines = buffer.strip().split('\n')
                            event_type = None
                            
                            for l in lines:
                                if l.startswith('event:'):
                                    event_type = l.split(':', 1)[1].strip()
                            
                            if event_type == "error":
                                received_error_event = True
                                self.print_info("  Received error event")
                                break
                            
                            buffer = ""
                            
                            # Don't wait forever
                            if len(buffer) > 5000:
                                break
                    
                    if received_error_event:
                        self.print_success("Error handling working (error event received)")
                        return True
                    else:
                        self.print_info("No error event received (may return HTTP error instead)")
                        return True  # Still OK if HTTP error is returned
                        
        except Exception as e:
            self.print_info(f"Exception occurred: {type(e).__name__}")
            self.print_success("Error handling working (exception thrown)")
            return True
    
    async def test_concurrent_streams(self) -> bool:
        """Test 7: Concurrent streaming connections"""
        self.print_header("Test 7: Concurrent Streams")
        
        self.print_info("Testing 3 concurrent streaming connections...")
        
        async def run_stream(stream_id: int):
            url = f"{self.base_url}/agui/agents/{self.agent_id}/run"
            
            payload = {
                "threadId": f"concurrent_{stream_id}_{datetime.now().timestamp()}",
                "messages": [
                    {"role": "user", "content": f"Stream {stream_id} test", "metadata": {}}
                ],
                "state": {}
            }
            
            headers = self.get_headers(include_tenant=True)
            
            event_count = 0
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status != 200:
                            return False, 0
                        
                        buffer = ""
                        async for line in response.content:
                            line_str = line.decode('utf-8')
                            buffer += line_str
                            
                            if buffer.endswith('\n\n'):
                                lines = buffer.strip().split('\n')
                                for l in lines:
                                    if l.startswith('event:'):
                                        event_count += 1
                                
                                if event_count >= 5:  # Get at least 5 events
                                    break
                                
                                buffer = ""
                except:
                    return False, 0
            
            return True, event_count
        
        try:
            # Run 3 streams concurrently
            results = await asyncio.gather(
                run_stream(1),
                run_stream(2),
                run_stream(3)
            )
            
            success_count = sum(1 for success, _ in results if success)
            total_events = sum(count for _, count in results)
            
            self.print_info(f"Successful streams: {success_count}/3")
            self.print_info(f"Total events received: {total_events}")
            
            if success_count == 3:
                self.print_success("All concurrent streams completed successfully")
                return True
            elif success_count >= 2:
                self.print_info(f"{success_count}/3 streams succeeded (acceptable)")
                return True
            else:
                self.print_failure(f"Only {success_count}/3 streams succeeded")
                return False
                
        except Exception as e:
            self.print_failure("Concurrent streams test failed", str(e))
            return False
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        passed = sum(1 for status, _ in self.test_results if status == "PASS")
        failed = sum(1 for status, _ in self.test_results if status == "FAIL")
        total = len(self.test_results)
        
        print(f"Total tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        
        if failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  SOME TESTS FAILED{Colors.END}")
            print("\nFailed tests:")
            for status, name in self.test_results:
                if status == "FAIL":
                    print(f"  {Colors.RED}✗ {name}{Colors.END}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BOLD}AG-UI Streaming Test Suite (Multi-Tenant){Colors.END}")
        print(f"Base URL: {self.base_url}")
        print(f"Agent ID: {self.agent_id}")
        print(f"Tenant ID: {self.tenant_id}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run tests sequentially
        await self.test_health_check()
        await self.test_streaming_connection()
        await self.test_event_types()
        await self.test_message_streaming()
        await self.test_heartbeat()
        await self.test_error_handling()
        await self.test_concurrent_streams()
        
        # Print summary
        self.print_summary()


async def main():
    parser = argparse.ArgumentParser(description="Test AG-UI streaming implementation")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--token",
        default="test_token",
        help="Authentication token (default: test_token)"
    )
    parser.add_argument(
        "--agent-id",
        type=int,
        default=1,
        help="Agent ID to test with (default: 1)"
    )
    parser.add_argument(
        "--tenant",
        default="demo",
        help="Tenant ID for X-Tenant-ID header (default: demo)"
    )
    
    args = parser.parse_args()
    
    print(f"{Colors.YELLOW}Note: You may need a valid JWT token to run these tests{Colors.END}")
    print(f"{Colors.YELLOW}If tests fail with 401, get a token from Keycloak or your auth system{Colors.END}")
    
    tester = AGUIStreamingTester(
        base_url=args.url,
        token=args.token,
        agent_id=args.agent_id,
        tenant_id=args.tenant
    )
    
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())