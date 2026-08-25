"""
Phase 0 Smoke Test: Project imports and structure verification.
"""

def test_imports():
    from core import crypto, prng, payload, compression, metadata, analysis
    from core.carriers import PngCarrier, JpegCarrier, Mp3Carrier
    from api.routes import app as fastapi_app
    from cli.main import app as typer_app
    
    assert crypto is not None
    assert prng is not None
    assert payload is not None
    assert compression is not None
    assert metadata is not None
    assert analysis is not None
    assert PngCarrier is not None
    assert JpegCarrier is not None
    assert Mp3Carrier is not None
    assert fastapi_app is not None
    assert typer_app is not None
