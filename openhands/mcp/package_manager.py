"""
Robust MCP Package Manager
Handles validation, installation, and management of MCP servers across different package types.
Inspired by VS Code Copilot Chat implementation.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
import aiohttp

from openhands.core.config.mcp_config import MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger


class PackageType(Enum):
    """Supported package types for MCP servers"""

    NPM = "npm"
    PIP = "pip"
    DOCKER = "docker"
    BINARY = "binary"
    UNKNOWN = "unknown"


class PackageValidationResult:
    """Result of package validation"""

    def __init__(
        self, success: bool, error: str = "", publisher: str = "", version: str = ""
    ):
        self.success = success
        self.error = error
        self.publisher = publisher
        self.version = version


class MCPPackageManager:
    """Robust MCP package manager with validation and installation capabilities"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._installed_packages: Dict[str, bool] = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def detect_package_type(self, server: MCPStdioServerConfig) -> PackageType:
        """Detect the package type based on server configuration"""
        command = server.command.lower()

        if command == 'npx':
            return PackageType.NPM
        elif command == 'python' or command == 'python3':
            # Check if it's a pip package (using -m flag)
            if '-m' in server.args:
                return PackageType.PIP
            return PackageType.BINARY
        elif command == 'docker':
            return PackageType.DOCKER
        elif command in ['node', 'npm']:
            return PackageType.NPM
        else:
            # Check if it's a binary command
            if shutil.which(command):
                return PackageType.BINARY
            return PackageType.UNKNOWN

    def extract_package_name(
        self, server: MCPStdioServerConfig, package_type: PackageType
    ) -> Optional[str]:
        """Extract package name from server configuration"""
        if package_type == PackageType.NPM:
            # Look for npm package in args
            for arg in server.args:
                if arg.startswith('@') and '/' in arg:  # Scoped package
                    return arg
                elif arg.startswith('@') and not arg.startswith('@latest'):
                    return arg
                elif (
                    not arg.startswith('-') and '/' in arg
                ):  # Regular package with scope
                    return arg
        elif package_type == PackageType.PIP:
            # Look for -m flag followed by package name
            for i, arg in enumerate(server.args):
                if arg == '-m' and i + 1 < len(server.args):
                    return server.args[i + 1]
        elif package_type == PackageType.DOCKER:
            # Docker image name is usually the first argument
            if server.args:
                return server.args[0]

        return None

    async def validate_package(
        self, package_name: str, package_type: PackageType
    ) -> PackageValidationResult:
        """Validate package exists in registry"""
        try:
            if package_type == PackageType.NPM:
                return await self._validate_npm_package(package_name)
            elif package_type == PackageType.PIP:
                return await self._validate_pip_package(package_name)
            elif package_type == PackageType.DOCKER:
                return await self._validate_docker_package(package_name)
            else:
                return PackageValidationResult(
                    True, "Binary package - no validation needed"
                )
        except Exception as e:
            return PackageValidationResult(False, f"Validation error: {str(e)}")

    async def _validate_npm_package(self, package_name: str) -> PackageValidationResult:
        """Validate npm package exists"""
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    version = data.get('dist-tags', {}).get('latest', '')
                    publisher = ''
                    maintainers = data.get('maintainers', [])
                    if maintainers:
                        publisher = maintainers[0].get('name', 'unknown')
                    return PackageValidationResult(True, "", publisher, version)
                else:
                    return PackageValidationResult(
                        False, f"Package {package_name} not found in npm registry"
                    )
        except Exception as e:
            return PackageValidationResult(
                False, f"Error validating npm package: {str(e)}"
            )

    async def _validate_pip_package(self, package_name: str) -> PackageValidationResult:
        """Validate pip package exists"""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    info = data.get('info', {})
                    version = info.get('version', '')
                    publisher = info.get('author', info.get('author_email', 'unknown'))
                    return PackageValidationResult(True, "", publisher, version)
                else:
                    return PackageValidationResult(
                        False, f"Package {package_name} not found in PyPI registry"
                    )
        except Exception as e:
            return PackageValidationResult(
                False, f"Error validating pip package: {str(e)}"
            )

    async def _validate_docker_package(
        self, package_name: str
    ) -> PackageValidationResult:
        """Validate docker image exists"""
        try:
            # Handle both formats: 'namespace/repository' or just 'repository'
            if '/' in package_name:
                namespace, repository = package_name.split('/', 1)
            else:
                namespace, repository = 'library', package_name

            url = f"https://hub.docker.com/v2/repositories/{namespace}/{repository}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    publisher = data.get('namespace', data.get('user', 'unknown'))
                    return PackageValidationResult(True, "", publisher, "")
                else:
                    return PackageValidationResult(
                        False, f"Docker image {package_name} not found in Docker Hub"
                    )
        except Exception as e:
            return PackageValidationResult(
                False, f"Error validating docker image: {str(e)}"
            )

    async def install_package(
        self, package_name: str, package_type: PackageType, force: bool = False
    ) -> bool:
        """Install package if not already installed"""
        cache_key = f"{package_type.value}:{package_name}"

        if not force and cache_key in self._installed_packages:
            return self._installed_packages[cache_key]

        try:
            if package_type == PackageType.NPM:
                success = await self._install_npm_package(package_name)
            elif package_type == PackageType.PIP:
                success = await self._install_pip_package(package_name)
            elif package_type == PackageType.DOCKER:
                success = await self._install_docker_image(package_name)
            else:
                success = True  # Binary packages don't need installation

            self._installed_packages[cache_key] = success
            return success
        except Exception as e:
            logger.error(
                f"Failed to install {package_type.value} package {package_name}: {e}"
            )
            self._installed_packages[cache_key] = False
            return False

    async def _install_npm_package(self, package_name: str) -> bool:
        """Install npm package or verify it's available via npx"""
        try:
            # First check if npx can run the package (with shorter timeout)
            logger.info(
                f"Checking if npm package {package_name} is available via npx..."
            )
            result = await self._run_command(
                ['npx', '-y', package_name, '--help'], timeout=15
            )

            if result.returncode == 0:
                logger.info(f"✅ npm package {package_name} is available via npx")
                return True

            # Check if it's a known package that doesn't support --help
            if 'unknown option' in result.stderr or 'invalid option' in result.stderr:
                logger.info(
                    f"✅ npm package {package_name} is available (doesn't support --help)"
                )
                return True

            # If package doesn't exist, the npx command will fail with E404
            if 'E404' in result.stderr or 'not found' in result.stderr:
                logger.error(f"❌ npm package {package_name} not found in registry")
                return False

            # For other errors, try to run without --help to see if package works
            logger.info(f"Testing npm package {package_name} without --help...")
            result = await self._run_command(['npx', '-y', package_name], timeout=5)

            # If it starts up (even with errors), it's probably available
            if result.returncode != 127:  # 127 = command not found
                logger.info(f"✅ npm package {package_name} appears to be available")
                return True

            # Last resort: try to install globally with user permissions
            logger.info(f"Attempting to install npm package {package_name} globally...")
            result = await self._run_command(
                ['npm', 'install', '-g', package_name], timeout=60
            )

            if result.returncode == 0:
                logger.info(f"✅ Successfully installed npm package {package_name}")
                return True
            else:
                # If global install fails, check if we can use npx anyway
                logger.warning(
                    f"Global install failed, but npx might still work: {result.stderr}"
                )
                return True  # npx can download packages on-demand

        except Exception as e:
            logger.error(f"❌ Error with npm package {package_name}: {e}")
            return False

    async def _install_pip_package(self, package_name: str) -> bool:
        """Install pip package"""
        try:
            logger.info(f"Installing pip package {package_name}...")
            result = await self._run_command(
                [sys.executable, '-m', 'pip', 'install', package_name], timeout=60
            )

            if result.returncode == 0:
                logger.info(f"✅ Successfully installed pip package {package_name}")
                return True
            else:
                logger.error(
                    f"❌ Failed to install pip package {package_name}: {result.stderr}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Error installing pip package {package_name}: {e}")
            return False

    async def _install_docker_image(self, image_name: str) -> bool:
        """Pull docker image"""
        try:
            logger.info(f"Pulling docker image {image_name}...")
            result = await self._run_command(
                ['docker', 'pull', image_name], timeout=120
            )

            if result.returncode == 0:
                logger.info(f"✅ Successfully pulled docker image {image_name}")
                return True
            else:
                logger.error(
                    f"❌ Failed to pull docker image {image_name}: {result.stderr}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Error pulling docker image {image_name}: {e}")
            return False

    async def _run_command(
        self, cmd: List[str], timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """Run command asynchronously with timeout"""
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            return subprocess.CompletedProcess(
                cmd, process.returncode, stdout.decode(), stderr.decode()
            )
        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=2)
                except asyncio.TimeoutError:
                    try:
                        process.kill()
                        await asyncio.wait_for(process.wait(), timeout=1)
                    except:
                        pass
                except:
                    pass
            # Return a failed result instead of raising
            return subprocess.CompletedProcess(
                cmd, -1, "", f"Command timed out after {timeout}s"
            )
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)}: {e}")
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=1)
                except:
                    pass
            # Return a failed result instead of raising
            return subprocess.CompletedProcess(cmd, -1, "", f"Command failed: {str(e)}")

    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if required tools are available"""
        tools = {
            'npx': self._check_tool_available('npx'),
            'npm': self._check_tool_available('npm'),
            'python': self._check_tool_available('python')
            or self._check_tool_available('python3'),
            'pip': self._check_tool_available('pip')
            or self._check_tool_available('pip3'),
            'docker': self._check_tool_available('docker'),
        }
        return tools

    def _check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available in PATH"""
        return shutil.which(tool) is not None

    async def prepare_server(self, server: MCPStdioServerConfig) -> Tuple[bool, str]:
        """Prepare MCP server by validating and installing if needed"""
        try:
            # Detect package type
            package_type = self.detect_package_type(server)

            if package_type == PackageType.UNKNOWN:
                return False, f"Unknown package type for server {server.name}"

            # Extract package name
            package_name = self.extract_package_name(server, package_type)

            if not package_name and package_type != PackageType.BINARY:
                return False, f"Could not extract package name for server {server.name}"

            # For binary packages, just check if command exists
            if package_type == PackageType.BINARY:
                if shutil.which(server.command):
                    return True, f"Binary command {server.command} is available"
                else:
                    return False, f"Binary command {server.command} not found"

            # Validate package exists in registry
            validation_result = await self.validate_package(package_name, package_type)

            if not validation_result.success:
                return False, f"Package validation failed: {validation_result.error}"

            # For npm packages, trust npx to handle downloads
            if package_type == PackageType.NPM:
                return (
                    True,
                    f"npm package {package_name} will be downloaded by npx as needed",
                )

            # Install package if needed for other types
            install_success = await self.install_package(package_name, package_type)

            if not install_success:
                return (
                    False,
                    f"Failed to install {package_type.value} package {package_name}",
                )

            return (
                True,
                f"Successfully prepared {package_type.value} package {package_name}",
            )

        except Exception as e:
            return False, f"Error preparing server {server.name}: {str(e)}"
