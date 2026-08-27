"""
Cryptonite Lossless Metadata Sanitization Module.

Strips identifying EXIF/ID3/XMP tags without lossy re-encoding.
"""


def strip_png_metadata(image_path: str) -> bytes:
    """
    Remove all ancillary PNG chunks (tEXt, iTXt, zTXt, eXIf, tIME, etc.)
    while preserving critical chunks (IHDR, PLTE, IDAT, IEND, tRNS).
    """
    if not isinstance(image_path, str):
        raise TypeError(f"image_path must be str, got {type(image_path).__name__}")
    raise NotImplementedError("Phase 2 implementation pending")


def strip_jpeg_metadata(image_path: str) -> bytes:
    """
    Losslessly remove all APP markers (EXIF, IPTC, XMP) and COM comments from JPEG
    at the binary stream level. Never re-encodes through PIL.
    """
    if not isinstance(image_path, str):
        raise TypeError(f"image_path must be str, got {type(image_path).__name__}")
    raise NotImplementedError("Phase 2 implementation pending")


def strip_mp3_metadata(audio_path: str) -> bytes:
    """
    Remove ID3v1, ID3v2, and APE tags from MP3 while preserving audio frame streams.
    """
    if not isinstance(audio_path, str):
        raise TypeError(f"audio_path must be str, got {type(audio_path).__name__}")
    raise NotImplementedError("Phase 2 implementation pending")
