import numpy as np
import pytest

from core import analysis, metadata
from core.carriers.jpeg import JpegCarrier
from core.carriers.mp3 import Mp3Carrier
from core.carriers.png import PngCarrier


def test_analysis_stubs():
    arr = np.array([])
    with pytest.raises(NotImplementedError):
        analysis.chi_squared_test(arr)
    with pytest.raises(TypeError):
        analysis.chi_squared_test("not_array") # type: ignore

    with pytest.raises(NotImplementedError):
        analysis.compute_ssim(arr, arr)
    with pytest.raises(TypeError):
        analysis.compute_ssim("bad", arr) # type: ignore

    with pytest.raises(NotImplementedError):
        analysis.compute_psnr(arr, arr)
    with pytest.raises(TypeError):
        analysis.compute_psnr(arr, "bad") # type: ignore

    with pytest.raises(NotImplementedError):
        analysis.rs_analysis(arr)
    with pytest.raises(TypeError):
        analysis.rs_analysis("bad") # type: ignore

    with pytest.raises(NotImplementedError):
        analysis.full_analysis(arr, arr)
    with pytest.raises(TypeError):
        analysis.full_analysis(arr, "bad") # type: ignore

def test_metadata_stubs():
    with pytest.raises(NotImplementedError):
        metadata.strip_png_metadata("file.png")
    with pytest.raises(TypeError):
        metadata.strip_png_metadata(123) # type: ignore

    with pytest.raises(NotImplementedError):
        metadata.strip_jpeg_metadata("file.jpg")
    with pytest.raises(TypeError):
        metadata.strip_jpeg_metadata(123) # type: ignore

    with pytest.raises(NotImplementedError):
        metadata.strip_mp3_metadata("file.mp3")
    with pytest.raises(TypeError):
        metadata.strip_mp3_metadata(123) # type: ignore

def test_carrier_stubs():
    for carrier_cls in [PngCarrier, JpegCarrier, Mp3Carrier]:
        carrier = carrier_cls()
        with pytest.raises(NotImplementedError):
            carrier.embed("file", b"data", b"seed")
        with pytest.raises(TypeError):
            carrier.embed(123, b"data", b"seed") # type: ignore
        with pytest.raises(TypeError):
            carrier.embed("file", "data", b"seed") # type: ignore
        with pytest.raises(TypeError):
            carrier.embed("file", b"data", "seed") # type: ignore

        with pytest.raises(NotImplementedError):
            carrier.extract("file", b"seed")
        with pytest.raises(TypeError):
            carrier.extract(123, b"seed") # type: ignore
        with pytest.raises(TypeError):
            carrier.extract("file", "seed") # type: ignore

        with pytest.raises(NotImplementedError):
            carrier.capacity("file")
        with pytest.raises(TypeError):
            carrier.capacity(123) # type: ignore
