"""
ONNX Wrapper Generator

Generates a C++ ONNX Runtime inference wrapper based on requirement metadata.
"""

from __future__ import annotations

from typing import Dict, Any
from pathlib import Path

from llm.client import get_client
from llm.prompts import ML_WRAPPER_TEMPLATE


class ONNXWrapperGenerator:
    """Generate ONNX Runtime C++ wrappers."""

    def __init__(self, llm_provider: str = "gemini"):
        self.llm = get_client(llm_provider)

    def generate(self, requirement: Dict[str, Any]) -> str:
        ml = requirement.get("ml", {})
        model_name = ml.get("model_name", "model.onnx")
        model_path = ml.get("model_path", f"models/{model_name}")
        inputs = ml.get("inputs", [])
        outputs = ml.get("outputs", [])

        prompt = ML_WRAPPER_TEMPLATE.format(
            model_name=model_name,
            model_path=model_path,
            inputs=inputs,
            outputs=outputs,
        )
        return self.llm.generate(prompt)
