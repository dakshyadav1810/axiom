#!/usr/bin/env python3
"""
Axiom - Deterministic End-to-End Testing Engine

CLI entry point for running test flows.

Usage:
    python run_flow.py flow.json [--headless] [--verbose]

Arguments:
    flow.json       Path to the flow definition JSON file

Options:
    --headless      Run browser in headless mode
    --verbose       Enable verbose logging
    --timeout MS    Set action timeout in milliseconds (default: 10000)

Example:
    python run_flow.py sample_flow.json --verbose
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from ..models.resolver_models import FlowDefinition
from .executor import Executor, ExecutorConfig


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Axiom - Deterministic End-to-End Testing Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_flow.py sample_flow.json
    python run_flow.py sample_flow.json --verbose
    python run_flow.py sample_flow.json --headless --verbose
        """,
    )
    
    parser.add_argument(
        "flow_file",
        type=Path,
        help="Path to the flow definition JSON file",
    )
    
    parser.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (default: visible)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=10000,
        help="Action timeout in milliseconds (default: 10000)",
    )
    
    return parser.parse_args()


def load_flow(flow_path: Path) -> FlowDefinition:
    """Load and parse flow definition from JSON file."""
    if not flow_path.exists():
        print(f"Error: Flow file not found: {flow_path}")
        sys.exit(1)
    
    try:
        with open(flow_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in flow file: {e}")
        sys.exit(1)
    
    try:
        return FlowDefinition.from_dict(data)
    except KeyError as e:
        print(f"Error: Missing required field in flow file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to parse flow file: {e}")
        sys.exit(1)


async def main():
    """Main entry point."""
    args = parse_args()
    
    # Print header
    print("=" * 50)
    print("Axiom - Deterministic Testing Engine")
    print("=" * 50)
    print()
    
    # Load flow
    print(f"Loading flow: {args.flow_file}")
    flow = load_flow(args.flow_file)
    
    # Display flow info
    if flow.name:
        print(f"Flow: {flow.name}")
    if flow.description:
        print(f"Description: {flow.description}")
    print(f"Start URL: {flow.start_url}")
    print(f"Actions: {len(flow.actions)}")
    print()
    
    # Configure executor
    config = ExecutorConfig(
        headless=args.headless,
        timeout=args.timeout,
        verbose=args.verbose,
        screenshot_on_failure=True,
    )
    
    # Create and run executor
    executor = Executor(config)
    result = await executor.run_flow(flow)
    
    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    asyncio.run(main())
