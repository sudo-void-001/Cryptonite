"""
Cryptonite Architecture Smoke Tests: Verifies package structure, exports, and core interfaces.
"""

import typer
from fastapi import FastAPI

from api.routes import app as fastapi_app
from cli.main import app as typer_app
from core import analysis, compression, crypto, metadata, payload, prng
from core.carriers import BaseCarrier, JpegCarrier, Mp3Carrier, PngCarrier


def test_core_package_exports():
    """Verify all core submodules export required public functions and classes."""
    assert hasattr(crypto, "derive_keys")
    assert hasattr(crypto, "encrypt")
    assert hasattr(crypto, "verify_and_decrypt")
    assert hasattr(prng, "generate_permutation")
    assert hasattr(payload, "pack")
    assert hasattr(payload, "unpack")
    assert hasattr(compression, "compress")
    assert hasattr(compression, "decompress")
    assert hasattr(metadata, "strip_png_metadata")
    assert hasattr(metadata, "strip_jpeg_metadata")
    assert hasattr(metadata, "strip_mp3_metadata")
    assert hasattr(analysis, "chi_squared_test")


def test_carrier_hierarchy():
    """Verify all carrier implementations inherit from BaseCarrier interface."""
    for carrier_cls in (PngCarrier, JpegCarrier, Mp3Carrier):
        assert issubclass(carrier_cls, BaseCarrier)
        instance = carrier_cls()
        assert hasattr(instance, "embed")
        assert hasattr(instance, "extract")
        assert hasattr(instance, "capacity")


def test_application_entrypoints():
    """Verify FastAPI and Typer application instances are properly configured."""
    assert isinstance(fastapi_app, FastAPI)
    assert isinstance(typer_app, typer.Typer)
