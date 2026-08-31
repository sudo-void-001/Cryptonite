"""
Stub / Phase-pending feature tests for Cryptonite.
As phases complete, stub tests are removed and replaced by full test suites.
Only stubs that have NOT yet been implemented belong here.
"""

import numpy as np
import pytest

from core import analysis


def test_analysis_stubs():
    """Analysis module functions are Phase 5 stubs — all raise NotImplementedError."""
    arr = np.array([])
    with pytest.raises(NotImplementedError):
        analysis.chi_squared_test(arr)
    with pytest.raises(TypeError):
        analysis.chi_squared_test("not_array")  # type: ignore

    with pytest.raises(NotImplementedError):
        analysis.compute_ssim(arr, arr)
    with pytest.raises(TypeError):
        analysis.compute_ssim("bad", arr)  # type: ignore

    with pytest.raises(NotImplementedError):
        analysis.compute_psnr(arr, arr)
    with pytest.raises(TypeError):
        analysis.compute_psnr(arr, "bad")  # type: ignore

    with pytest.raises(NotImplementedError):
        analysis.rs_analysis(arr)
    with pytest.raises(TypeError):
        analysis.rs_analysis("bad")  # type: ignore

    with pytest.raises(NotImplementedError):
        analysis.full_analysis(arr, arr)
    with pytest.raises(TypeError):
        analysis.full_analysis(arr, "bad")  # type: ignore
