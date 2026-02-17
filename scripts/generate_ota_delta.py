#!/usr/bin/env python3
"""
Generate OTA delta evidence artifacts (compliance-focused).

This script computes a chunk-level binary delta between:
- base artifact (v1.0)
- target artifact (v1.1)

Outputs:
- delta_manifest.json
- delta_chunks.json
- verification.json

The generated delta is verifiable by reconstructing target bytes from base+chunks.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_delta(base: bytes, target: bytes, chunk_size: int) -> List[Dict[str, object]]:
    chunks: List[Dict[str, object]] = []
    max_len = max(len(base), len(target))
    for offset in range(0, max_len, chunk_size):
        b = base[offset : offset + chunk_size]
        t = target[offset : offset + chunk_size]
        if b != t:
            chunks.append(
                {
                    "offset": offset,
                    "length": len(t),
                    "sha256": sha256_bytes(t),
                    "data_b64": base64.b64encode(t).decode("ascii"),
                }
            )
    return chunks


def apply_delta(base: bytes, chunks: List[Dict[str, object]], target_size: int) -> bytes:
    reconstructed = bytearray(base)
    if len(reconstructed) < target_size:
        reconstructed.extend(b"\x00" * (target_size - len(reconstructed)))
    else:
        reconstructed = reconstructed[:target_size]

    for chunk in chunks:
        offset = int(chunk["offset"])
        length = int(chunk["length"])
        payload = base64.b64decode(str(chunk["data_b64"]).encode("ascii"))
        reconstructed[offset : offset + length] = payload
    return bytes(reconstructed)


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OTA delta artifacts")
    parser.add_argument("--service", default="BMSDiagnosticService")
    parser.add_argument("--base-version", default="1.0.0")
    parser.add_argument("--target-version", default="1.1.0")
    parser.add_argument("--base-image", default="autoforge/bms:1.0.0")
    parser.add_argument("--target-image", default="autoforge/bms:1.1.0")
    parser.add_argument("--base-file", required=True, help="Base artifact path (v1.0)")
    parser.add_argument("--target-file", required=True, help="Target artifact path (v1.1)")
    parser.add_argument("--chunk-size", type=int, default=1024)
    parser.add_argument(
        "--output-dir",
        default="output/ota_delta/BMSDiagnosticService_v1.0.0_to_v1.1.0",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_path = Path(args.base_file)
    target_path = Path(args.target_file)
    output_dir = Path(args.output_dir)

    if not base_path.exists():
        raise FileNotFoundError(f"Base file not found: {base_path}")
    if not target_path.exists():
        raise FileNotFoundError(f"Target file not found: {target_path}")
    if args.chunk_size <= 0:
        raise ValueError("--chunk-size must be > 0")

    base_bytes = base_path.read_bytes()
    target_bytes = target_path.read_bytes()
    delta_chunks = compute_delta(base_bytes, target_bytes, args.chunk_size)

    changed_bytes = sum(int(c["length"]) for c in delta_chunks)
    target_size = len(target_bytes)
    reduction = (1.0 - (changed_bytes / target_size)) * 100.0 if target_size else 0.0

    delta_manifest = {
        "ota_delta": {
            "service": args.service,
            "from_version": args.base_version,
            "to_version": args.target_version,
            "base_container": args.base_image,
            "target_container": args.target_image,
            "base_artifact": str(base_path),
            "target_artifact": str(target_path),
            "base_sha256": sha256_file(base_path),
            "target_sha256": sha256_file(target_path),
            "base_size_bytes": len(base_bytes),
            "target_size_bytes": target_size,
            "chunk_size": args.chunk_size,
            "changed_chunk_count": len(delta_chunks),
            "changed_bytes": changed_bytes,
            "delta_efficiency_percent": round(reduction, 2),
        }
    }

    write_json(output_dir / "delta_manifest.json", delta_manifest)
    write_json(
        output_dir / "delta_chunks.json",
        {
            "service": args.service,
            "from_version": args.base_version,
            "to_version": args.target_version,
            "chunks": delta_chunks,
        },
    )

    reconstructed = apply_delta(base_bytes, delta_chunks, target_size)
    verification = {
        "target_sha256": sha256_bytes(target_bytes),
        "reconstructed_sha256": sha256_bytes(reconstructed),
        "verified": reconstructed == target_bytes,
    }
    write_json(output_dir / "verification.json", verification)

    print(f"[OTA] Base: {base_path} ({len(base_bytes)} bytes)")
    print(f"[OTA] Target: {target_path} ({target_size} bytes)")
    print(f"[OTA] Changed chunks: {len(delta_chunks)}")
    print(f"[OTA] Changed bytes: {changed_bytes}")
    print(f"[OTA] Delta manifest: {output_dir / 'delta_manifest.json'}")
    print(f"[OTA] Verification: {verification['verified']}")
    return 0 if verification["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
