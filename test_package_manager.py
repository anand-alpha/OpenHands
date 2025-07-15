#!/usr/bin/env python3
"""
Test script to verify MCP package manager functionality
"""

import asyncio
import sys
import os

# Add OpenHands to the path
sys.path.insert(0, '/home/hac/code/OpenHands')

from openhands.mcp.package_manager import MCPPackageManager, PackageType
from openhands.core.config.mcp_config import MCPStdioServerConfig


async def test_package_manager():
    """Test the MCP package manager functionality"""
    print("🧪 Testing MCP Package Manager")
    print("=" * 50)

    async with MCPPackageManager() as pm:
        # Test 1: Check prerequisites
        print("\n1. Checking prerequisites...")
        prereqs = pm.check_prerequisites()
        for tool, available in prereqs.items():
            status = "✅" if available else "❌"
            print(
                f"   {status} {tool}: {'Available' if available else 'Not available'}"
            )

        # Test 2: Package type detection
        print("\n2. Testing package type detection...")
        test_servers = [
            MCPStdioServerConfig(
                name="npm-test",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            ),
            MCPStdioServerConfig(
                name="pip-test", command="python", args=["-m", "some_package"]
            ),
            MCPStdioServerConfig(
                name="docker-test", command="docker", args=["run", "hello-world"]
            ),
        ]

        for server in test_servers:
            package_type = pm.detect_package_type(server)
            package_name = pm.extract_package_name(server, package_type)
            print(f"   {server.name}: {package_type.value} -> {package_name}")

        # Test 3: Weather server validation
        print("\n3. Testing weather server validation...")
        try:
            result = await pm.validate_package(
                "@timlukahorstmann/mcp-weather", PackageType.NPM
            )
            if result.success:
                print(f"   ✅ Package valid: {result.publisher} v{result.version}")
            else:
                print(f"   ❌ Package invalid: {result.error}")
        except Exception as e:
            print(f"   ❌ Validation error: {e}")

        # Test 4: Server preparation
        print("\n4. Testing server preparation...")
        weather_server = MCPStdioServerConfig(
            name="weather",
            command="npx",
            args=["-y", "@timlukahorstmann/mcp-weather"],
            env={"ACCUWEATHER_API_KEY": "dummy_key"},
        )

        success, message = await pm.prepare_server(weather_server)
        status = "✅" if success else "❌"
        print(f"   {status} Weather server: {message}")

    print("\n✅ Package manager test completed!")


if __name__ == "__main__":
    asyncio.run(test_package_manager())
