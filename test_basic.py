"""
Simple test script to verify PowerShell agent basic functionality
Run this to ensure everything is working correctly
"""

import asyncio
import sys


async def test_basic_import():
    """Test 1: Can we import the module?"""
    print("\n🧪 Test 1: Import Module")
    print("-" * 50)
    try:
        from powershell_agent import PowerShellAgent
        print("✅ PASS: Module imported successfully")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


async def test_agent_creation():
    """Test 2: Can we create an agent instance?"""
    print("\n🧪 Test 2: Create Agent Instance")
    print("-" * 50)
    try:
        from powershell_agent import PowerShellAgent
        agent = PowerShellAgent()
        print("✅ PASS: Agent instance created")
        return True, agent
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False, None


async def test_simple_command(agent):
    """Test 3: Can we run a simple PowerShell command?"""
    print("\n🧪 Test 3: Execute Simple Command")
    print("-" * 50)
    try:
        result = await agent.run_powershell_command(
            "Write-Output 'Hello from PowerShell Agent!'",
            stream_output=True
        )
        
        if result['status'] == 'success':
            print(f"✅ PASS: Command executed successfully")
            print(f"   Return code: {result['return_code']}")
            return True
        else:
            print(f"❌ FAIL: Command failed - {result['error']}")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


async def test_tool_schema(agent):
    """Test 4: Can we generate tool schema?"""
    print("\n🧪 Test 4: Generate Tool Schema")
    print("-" * 50)
    try:
        schema = agent.create_tool_schema()
        if schema and len(schema) > 0:
            print(f"✅ PASS: Tool schema generated")
            print(f"   Tool name: {schema[0]['function']['name']}")
            return True
        else:
            print("❌ FAIL: Empty schema")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


async def test_parallel_execution(agent):
    """Test 5: Can we run commands in parallel?"""
    print("\n🧪 Test 5: Parallel Command Execution")
    print("-" * 50)
    try:
        commands = [
            "Write-Output 'Command 1'",
            "Write-Output 'Command 2'",
            "Write-Output 'Command 3'"
        ]
        
        results = await agent.run_parallel_commands(commands, stream_output=False)
        
        if len(results) == 3 and all(r['status'] == 'success' for r in results):
            print(f"✅ PASS: All {len(results)} commands executed in parallel")
            return True
        else:
            print(f"❌ FAIL: Some commands failed")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


async def run_all_tests():
    """Run all tests and report results"""
    print("=" * 70)
    print("🧪 PowerShell Agent - Basic Functionality Tests")
    print("=" * 70)
    
    results = []
    
    # Test 1: Import
    results.append(await test_basic_import())
    
    # Test 2: Create agent
    success, agent = await test_agent_creation()
    results.append(success)
    
    if not success or agent is None:
        print("\n❌ Cannot continue tests without agent instance")
        return
    
    # Test 3: Simple command
    results.append(await test_simple_command(agent))
    
    # Test 4: Tool schema
    results.append(await test_tool_schema(agent))
    
    # Test 5: Parallel execution
    results.append(await test_parallel_execution(agent))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED! 🎉")
        print("\nYour PowerShell agent is working correctly!")
        print("\nNext steps:")
        print("  1. Set your GROQ_API_KEY environment variable")
        print("  2. Run: poetry run python powershell_agent.py")
        print("  3. Try: 'Find all Python files in this directory'")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nTroubleshooting:")
        print("  - Make sure you ran: poetry install")
        print("  - Check that PowerShell is available on your system")
        print("  - Review error messages above")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
