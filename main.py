#!/usr/bin/env python3
"""
AUTOFORGE - Test-First GenAI Pipeline for Automotive SDV Code Generation

Usage:
    python main.py --requirement input/requirements/bms_diagnostic.yaml
    python main.py --demo vehicle-health
    python main.py --mock  # Run with mock LLM (no API key needed)
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from pipeline.orchestrator import Pipeline, PipelineResult
from llm.client import get_client


def print_banner():
    """Print AUTOFORGE banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     █████╗ ██╗   ██╗████████╗ ██████╗ ███████╗ ██████╗ ██████╗   ║
    ║    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔════╝██╔═══██╗██╔══██╗  ║
    ║    ███████║██║   ██║   ██║   ██║   ██║█████╗  ██║   ██║██████╔╝  ║
    ║    ██╔══██║██║   ██║   ██║   ██║   ██║██╔══╝  ██║   ██║██╔══██╗  ║
    ║    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║     ╚██████╔╝██║  ██║  ║
    ║    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝      ╚═════╝ ╚═╝  ╚═╝  ║
    ║                                                                   ║
    ║        Test-First GenAI for Automotive SDV Code Generation        ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_result(result: PipelineResult):
    """Print pipeline result summary."""
    status = "✅ SUCCESS" if result.success else "❌ FAILED"
    
    print(f"\n{'='*60}")
    print(f"Pipeline Result: {status}")
    print(f"{'='*60}")
    print(f"  Service:      {result.requirement_id}")
    print(f"  Trace ID:     {result.trace_id}")
    print(f"  Timestamp:    {result.timestamp}")
    print(f"  Retries:      {result.retry_count}")
    print(f"  Phases:       {' → '.join(p.value for p in result.phases_completed)}")
    
    if result.errors:
        print(f"\n  Errors:")
        for err in result.errors:
            print(f"    - {err}")
            
    if result.success:
        print(f"\n  Outputs saved to: output/{result.requirement_id}/")
        print(f"    - tests.py")
        print(f"    - {result.requirement_id.lower()}.py")
        print(f"    - trace.yaml")


def run_demo(demo_name: str, use_mock: bool = False):
    """Run a demo pipeline."""
    demos = {
        "vehicle-health": "input/requirements/bms_diagnostic.yaml",
        "bms": "input/requirements/bms_diagnostic.yaml",
    }
    
    if demo_name not in demos:
        print(f"Unknown demo: {demo_name}")
        print(f"Available demos: {list(demos.keys())}")
        return
        
    requirement_path = demos[demo_name]
    
    print(f"\n🚗 Running demo: {demo_name}")
    print(f"   Requirement: {requirement_path}")
    
    provider = "mock" if use_mock else "gemini"
    pipeline = Pipeline(llm_provider=provider)
    result = pipeline.run(requirement_path)
    print_result(result)


def main():
    parser = argparse.ArgumentParser(
        description="AUTOFORGE - Test-First GenAI Pipeline"
    )
    parser.add_argument(
        "--requirement", "-r",
        help="Path to requirement YAML file"
    )
    parser.add_argument(
        "--demo", "-d",
        help="Run a demo (vehicle-health, bms)"
    )
    parser.add_argument(
        "--mock", "-m",
        action="store_true",
        help="Use mock LLM (no API key needed)"
    )
    parser.add_argument(
        "--provider", "-p",
        default="gemini",
        help="LLM provider (gemini, openai, mock)"
    )
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Output directory"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Determine provider
    provider = args.provider
    if args.mock:
        provider = "mock"
        print("🔧 Using mock LLM (no API calls)")
    
    # Run demo or requirement
    if args.demo:
        run_demo(args.demo, use_mock=(provider == "mock"))
    elif args.requirement:
        if not Path(args.requirement).exists():
            print(f"❌ Requirement file not found: {args.requirement}")
            sys.exit(1)
            
        pipeline = Pipeline(
            llm_provider=provider,
            output_dir=args.output
        )
        result = pipeline.run(args.requirement)
        print_result(result)
        
        sys.exit(0 if result.success else 1)
    else:
        print("Usage:")
        print("  python main.py --requirement input/requirements/bms_diagnostic.yaml")
        print("  python main.py --demo vehicle-health")
        print("  python main.py --demo bms --mock  # No API key needed")
        print("\nFor help: python main.py --help")


if __name__ == "__main__":
    main()
