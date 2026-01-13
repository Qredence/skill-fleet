"""API discovery logic for auto-exposing DSPy modules as FastAPI endpoints."""

from __future__ import annotations

import inspect
import logging
from typing import Any, get_type_hints

import dspy
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)


def create_pydantic_model_from_signature(
    signature: type[dspy.Signature], name: str, input: bool = True
) -> type[BaseModel]:
    """Create a Pydantic model from a DSPy signature's input or output fields."""
    fields = signature.input_fields if input else signature.output_fields

    model_fields = {}
    for field_name, _field_obj in fields.items():
        # Try to get type hint from signature class
        type_hints = get_type_hints(signature)
        field_type = type_hints.get(field_name, Any)

        model_fields[field_name] = (field_type, ...)  # ... means required

    return create_model(name, **model_fields)


def discover_and_expose(app: FastAPI, module_package: Any, prefix: str = "/api/v2/auto"):
    """Scan a package for DSPy modules and expose them as API endpoints."""
    router = APIRouter(prefix=prefix)

    def create_endpoint(
        module_class: type, request_model: type[BaseModel], response_model: type[BaseModel]
    ):
        """Factory function to create endpoint with properly captured closure variables."""

        async def dynamic_endpoint(request: request_model):
            """Dynamically created endpoint for auto-exposed DSPy modules.

            Args:
                request: Pydantic model containing the request data

            Returns:
                The result from executing the DSPy module
            """
            # Initialize module
            instance = module_class()
            # Execute
            result = instance(**request.dict())
            return result

        return dynamic_endpoint

    for name, obj in inspect.getmembers(module_package):
        if inspect.isclass(obj) and issubclass(obj, dspy.Module) and obj != dspy.Module:
            # We found a DSPy module. Let's look for its signature.
            # This logic assumes the module has a clear signature or we can infer it.
            # For simplicity, let's look for a 'signature' attribute or inspect forward()

            # If it's a Predict or CoT, it has a signature
            signature = getattr(obj, "signature", None)

            if not signature and hasattr(obj, "__init__"):
                # Try to find signature in __init__ if it's a Predict wrapper
                # This is more complex, for now let's focus on explicit signatures
                pass

            if signature:
                request_model = create_pydantic_model_from_signature(
                    signature, f"{name}Request", input=True
                )
                response_model = create_pydantic_model_from_signature(
                    signature, f"{name}Response", input=False
                )

                endpoint = create_endpoint(obj, request_model, response_model)
                router.add_api_route(
                    f"/{name.lower()}",
                    endpoint,
                    methods=["POST"],
                    response_model=response_model,
                    tags=["auto-exposed"],
                )

                logger.info(f"Exposed DSPy module {name} at {prefix}/{name.lower()}")

    app.include_router(router)
