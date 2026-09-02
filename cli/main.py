"""
Cryptonite CLI Interface — Phase 6 Production Implementation.

Commands: embed, extract, capacity, analyze, batch embed, batch extract.
Built with Typer + Rich. Zero raw tracebacks — all errors are Rich panels.

PRNG Seed Strategy
------------------
The carrier scatter position is determined by `prng_seed`, derived via PBKDF2
using a **fixed salt** ("cryptonite-cli-prng-seed-v1") so that both embed and
extract can reproduce the same scatter pattern from the passphrase alone.

Encryption (enc_key + hmac_key) still uses a **random salt** stored inside the
encrypted blob [salt(16) | iv(16) | hmac(32) | ciphertext], giving full IND-CCA2
security for the payload while keeping the carrier scatter pattern deterministic.
"""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="cryptonite",
    help="Production-grade steganography toolkit for PNG, JPEG, and MP3.",
    add_completion=False,
    no_args_is_help=True,
)

batch_app = typer.Typer(
    name="batch",
    help="Batch embed/extract across a directory of files.",
    no_args_is_help=True,
)
app.add_typer(batch_app, name="batch")

console     = Console()
err_console = Console(stderr=True)

# Fixed salt used only for PRNG seed derivation — security comes from passphrase.
_PRNG_FIXED_SALT: bytes = b"cryptonite-cli-prng-v1\x00\x00\x00\x00\x00"[:16]  # exactly 16 B

_PNG_EXTS  = frozenset({".png"})
_JPEG_EXTS = frozenset({".jpg", ".jpeg"})
_MP3_EXTS  = frozenset({".mp3", ".wav"})
_ALL_EXTS  = _PNG_EXTS | _JPEG_EXTS | _MP3_EXTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_carrier(path: str):  # type: ignore[return]
    """Return correct carrier instance based on file extension."""
    from core.carriers.jpeg import JpegCarrier
    from core.carriers.mp3 import Mp3Carrier
    from core.carriers.png import PngCarrier

    ext = Path(path).suffix.lower()
    if ext in _PNG_EXTS:
        return PngCarrier()
    if ext in _JPEG_EXTS:
        return JpegCarrier()
    if ext in _MP3_EXTS:
        return Mp3Carrier()
    supported = ", ".join(sorted(_ALL_EXTS))
    _die(f"Unsupported file type '{ext}'. Supported: {supported}")


def _die(msg: str, code: int = 1) -> None:
    """Print a red error panel and exit with the given code."""
    err_console.print(Panel(f"[bold red]✗ Error[/bold red]\n{msg}", border_style="red"))
    raise typer.Exit(code=code)


def _human_bytes(n: int) -> str:
    """Return a human-readable byte size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n //= 1024
    return f"{n:.1f} TB"


def _derive_prng_seed(passphrase: str) -> bytes:
    """Derive the carrier scatter seed from the passphrase using a fixed salt."""
    from core.crypto import derive_keys
    _enc_key, _hmac_key, prng_seed = derive_keys(passphrase, _PRNG_FIXED_SALT)
    return prng_seed


def _encrypt_payload(passphrase: str, payload_path: str) -> bytes:
    """
    Full encrypt pipeline: read file → compress → pack → AES-256-CBC encrypt.

    Returns the encrypted blob bytes:
        [salt(16)] [iv(16)] [hmac(32)] [ciphertext(variable)]
    """
    from core.compression import compress
    from core.crypto import compute_hmac, derive_keys, encrypt, pack_encrypted_blob
    from core.payload import pack

    p = Path(payload_path)
    if not p.exists():
        _die(f"Payload file not found: {payload_path}")

    raw                      = p.read_bytes()
    compressed, was_compressed = compress(raw)
    packed                   = pack(p.name, compressed, is_compressed=was_compressed)

    enc_salt                     = os.urandom(16)
    enc_key, hmac_key, _prng    = derive_keys(passphrase, enc_salt)
    iv, ciphertext               = encrypt(packed, enc_key)
    hmac_digest                  = compute_hmac(iv + ciphertext, hmac_key)
    return pack_encrypted_blob(enc_salt, iv, hmac_digest, ciphertext)


def _decrypt_blob(passphrase: str, blob: bytes) -> tuple[str, bytes]:
    """
    Full decrypt pipeline: unpack blob → derive keys → verify HMAC → decrypt → unpack.

    Returns (original_filename, raw_payload_bytes).
    Raises ValueError on HMAC failure (wrong passphrase or corruption).
    """
    from core.compression import decompress
    from core.crypto import derive_keys, unpack_encrypted_blob, verify_and_decrypt
    from core.payload import unpack

    enc_salt, iv, hmac_digest, ciphertext = unpack_encrypted_blob(blob)
    enc_key, hmac_key, _prng              = derive_keys(passphrase, enc_salt)
    plaintext                             = verify_and_decrypt(iv, ciphertext, enc_key, hmac_key, hmac_digest)
    filename, data, is_compressed         = unpack(plaintext)
    data = decompress(data, is_compressed)
    return filename, data


# ---------------------------------------------------------------------------
# embed
# ---------------------------------------------------------------------------

@app.command()
def embed(
    carrier: str = typer.Option(..., "--carrier", "-c", help="Path to cover carrier file"),
    payload: str = typer.Option(..., "--payload", "-p", help="Path to secret payload file"),
    passphrase: str | None = typer.Option(
        None, "--passphrase", help="Secret passphrase (prompted if omitted)"
    ),
    output: str = typer.Option(..., "--output", "-o", help="Output path for stego file"),
) -> None:
    """Encrypt a payload and hide it inside a carrier file."""
    if not Path(carrier).exists():
        _die(f"Carrier file not found: {carrier}")
    if not Path(payload).exists():
        _die(f"Payload file not found: {payload}")

    if passphrase is None:
        passphrase = typer.prompt("Secret passphrase", hide_input=True)

    c          = _get_carrier(carrier)
    prng_seed  = _derive_prng_seed(passphrase)

    with console.status("[cyan]Deriving keys and encrypting…[/cyan]", spinner="dots"):
        try:
            blob = _encrypt_payload(passphrase, payload)
        except Exception as e:
            _die(f"Encryption failed: {e}")

    cap = c.capacity(carrier)
    if len(blob) > cap:
        _die(
            f"Payload too large for carrier.\n"
            f"  Need: {_human_bytes(len(blob))}  Available: {_human_bytes(cap)}"
        )

    with console.status("[cyan]Embedding into carrier…[/cyan]", spinner="dots"):
        try:
            stego_bytes = c.embed(carrier, blob, prng_seed)
        except Exception as e:
            _die(f"Embed failed: {e}")

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(stego_bytes)

    pct   = len(blob) / cap * 100 if cap else 0.0
    tbl   = Table(show_header=False, box=None, padding=(0, 1))
    tbl.add_row("[dim]Carrier[/dim]",  f"[white]{carrier}[/white]")
    tbl.add_row("[dim]Output[/dim]",   f"[white]{output}[/white]")
    tbl.add_row("[dim]Blob size[/dim]", f"[white]{_human_bytes(len(blob))}[/white]")
    tbl.add_row("[dim]Capacity[/dim]", f"[white]{_human_bytes(cap)} ({pct:.1f}% used)[/white]")
    console.print(Panel(tbl, title="[bold green]✓ Embed Successful[/bold green]", border_style="green"))


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

@app.command()
def extract(
    stego: str = typer.Option(..., "--stego", "-s", help="Path to stego carrier file"),
    passphrase: str | None = typer.Option(
        None, "--passphrase", help="Secret passphrase (prompted if omitted)"
    ),
    output: str = typer.Option(..., "--output", "-o", help="Output path for recovered payload"),
) -> None:
    """Extract and decrypt a hidden payload from a stego file."""
    if not Path(stego).exists():
        _die(f"Stego file not found: {stego}")

    if passphrase is None:
        passphrase = typer.prompt("Secret passphrase", hide_input=True)

    c         = _get_carrier(stego)
    prng_seed = _derive_prng_seed(passphrase)

    with console.status("[cyan]Extracting hidden data…[/cyan]", spinner="dots"):
        try:
            blob = c.extract(stego, prng_seed)
        except Exception as e:
            _die(f"Extraction failed: {e}")

    with console.status("[cyan]Decrypting payload…[/cyan]", spinner="dots"):
        try:
            filename, data = _decrypt_blob(passphrase, blob)
        except ValueError as e:
            _die(f"Decryption failed (wrong passphrase or corrupted stego):\n  {e}")
        except Exception as e:
            _die(f"Unexpected error during decryption: {e}")

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)

    tbl = Table(show_header=False, box=None, padding=(0, 1))
    tbl.add_row("[dim]Stego[/dim]",             f"[white]{stego}[/white]")
    tbl.add_row("[dim]Output[/dim]",            f"[white]{output}[/white]")
    tbl.add_row("[dim]Original filename[/dim]", f"[white]{filename}[/white]")
    tbl.add_row("[dim]Recovered size[/dim]",    f"[white]{_human_bytes(len(data))}[/white]")
    console.print(Panel(tbl, title="[bold green]✓ Extract Successful[/bold green]", border_style="green"))


# ---------------------------------------------------------------------------
# capacity
# ---------------------------------------------------------------------------

@app.command()
def capacity(
    carrier: str = typer.Option(..., "--carrier", "-c", help="Path to carrier file"),
) -> None:
    """Show maximum payload capacity for a carrier file."""
    if not Path(carrier).exists():
        _die(f"Carrier file not found: {carrier}")

    c = _get_carrier(carrier)

    with console.status("[cyan]Calculating capacity…[/cyan]", spinner="dots"):
        try:
            cap_bytes = c.capacity(carrier)
        except Exception as e:
            _die(f"Capacity check failed: {e}")

    usable = max(0, cap_bytes - 100)  # rough overhead: salt+iv+hmac+header ≈ 100B
    tbl    = Table(show_header=False, box=None, padding=(0, 1))
    tbl.add_row("[dim]Carrier[/dim]",      f"[white]{carrier}[/white]")
    tbl.add_row("[dim]Max capacity[/dim]",  f"[bold cyan]{_human_bytes(cap_bytes)}[/bold cyan]")
    tbl.add_row("[dim]Usable (est.)[/dim]", f"[white]{_human_bytes(usable)}[/white]")
    tbl.add_row("[dim]File size[/dim]",     f"[white]{_human_bytes(Path(carrier).stat().st_size)}[/white]")
    console.print(Panel(tbl, title="[bold cyan]📦 Carrier Capacity[/bold cyan]", border_style="cyan"))


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

@app.command()
def analyze(
    cover: str = typer.Option(..., "--cover", help="Path to original cover file"),
    stego: str = typer.Option(..., "--stego", help="Path to stego file"),
) -> None:
    """Run full steganalysis suite on cover vs stego and display forensic metrics."""
    import numpy as np
    from PIL import Image

    from core.analysis import full_analysis

    for label, path in (("cover", cover), ("stego", stego)):
        if not Path(path).exists():
            _die(f"{label} file not found: {path}")

    ext = Path(cover).suffix.lower()
    if ext not in _PNG_EXTS | _JPEG_EXTS:
        _die("analyze only supports PNG and JPEG files (image-based steganalysis).")

    with console.status("[cyan]Loading images…[/cyan]", spinner="dots"):
        try:
            cover_arr = np.array(Image.open(cover).convert("RGB"))
            stego_arr = np.array(Image.open(stego).convert("RGB"))
        except Exception as e:
            _die(f"Failed to load images: {e}")

    with console.status("[cyan]Running steganalysis suite…[/cyan]", spinner="dots"):
        try:
            result = full_analysis(cover_arr, stego_arr)
        except Exception as e:
            _die(f"Analysis failed: {e}")

    verdict_color = {"SAFE": "green", "MODERATE": "yellow", "HIGH_RISK": "red"}.get(
        result.verdict, "white"
    )
    verdict_icon  = {"SAFE": "✅", "MODERATE": "⚠️ ", "HIGH_RISK": "🚨"}.get(result.verdict, "")

    tbl = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    tbl.add_column("Metric",        style="dim", width=28)
    tbl.add_column("Value",         justify="right")
    tbl.add_column("Interpretation", style="dim")

    p         = result.chi_squared_p_value
    chi_note  = "Pairs equalized (stego)" if p > 0.95 else ("Borderline" if p > 0.50 else "Natural dist.")
    tbl.add_row("Chi-Squared p-value", f"{p:.6f}", chi_note)

    ssim_note = "Excellent" if result.ssim_score > 0.99 else ("Good" if result.ssim_score > 0.95 else "Poor")
    tbl.add_row("SSIM", f"{result.ssim_score:.6f}", ssim_note)

    psnr_str  = "∞ dB" if result.psnr_db == float("inf") else f"{result.psnr_db:.2f} dB"
    psnr_note = "Identical" if result.psnr_db == float("inf") else (
        "High quality" if result.psnr_db > 40 else "Degraded"
    )
    tbl.add_row("PSNR", psnr_str, psnr_note)

    rs_note = "Clean" if result.rs_score < 0.10 else ("Suspect" if result.rs_score < 0.25 else "Likely stego")
    tbl.add_row("RS Analysis", f"{result.rs_score:.6f}", rs_note)

    console.print(tbl)
    console.print()
    console.print(Panel(
        f"[bold {verdict_color}]{verdict_icon} VERDICT: {result.verdict}[/bold {verdict_color}]",
        border_style=verdict_color,
    ))


# ---------------------------------------------------------------------------
# batch embed
# ---------------------------------------------------------------------------

@batch_app.command(name="embed")
def batch_embed(
    carriers_dir: str = typer.Option(
        ..., "--carriers-dir", "-c", help="Directory of carrier files"
    ),
    payload: str = typer.Option(..., "--payload", "-p", help="Payload file to embed"),
    passphrase: str | None = typer.Option(
        None, "--passphrase", help="Secret passphrase (prompted if omitted)"
    ),
    output_dir: str = typer.Option(
        ..., "--output-dir", "-o", help="Directory for stego output files"
    ),
) -> None:
    """Embed the same payload into every carrier file in a directory."""
    if not Path(carriers_dir).is_dir():
        _die(f"Not a directory: {carriers_dir}")
    if not Path(payload).exists():
        _die(f"Payload file not found: {payload}")

    if passphrase is None:
        passphrase = typer.prompt("Secret passphrase", hide_input=True)

    carriers = sorted(
        f for f in Path(carriers_dir).iterdir()
        if f.is_file() and f.suffix.lower() in _ALL_EXTS
    )
    if not carriers:
        console.print(Panel("[yellow]No supported carrier files found.[/yellow]", border_style="yellow"))
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    prng_seed = _derive_prng_seed(passphrase)
    success, failed = 0, 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Batch embedding…", total=len(carriers))
        for carrier_path in carriers:
            progress.update(task, description=f"[cyan]Embedding {carrier_path.name}…")
            try:
                c    = _get_carrier(str(carrier_path))
                blob = _encrypt_payload(passphrase, payload)
                cap  = c.capacity(str(carrier_path))
                if len(blob) > cap:
                    err_console.print(f"[yellow]  SKIP {carrier_path.name}: payload exceeds capacity[/yellow]")
                    failed += 1
                else:
                    out_file = Path(output_dir) / carrier_path.name
                    out_file.write_bytes(c.embed(str(carrier_path), blob, prng_seed))
                    success += 1
            except Exception as e:
                err_console.print(f"[red]  FAIL {carrier_path.name}: {e}[/red]")
                failed += 1
            progress.advance(task)

    color = "green" if failed == 0 else "yellow"
    console.print(Panel(
        f"[bold {color}]Batch embed complete — Success: {success}  Failed/Skipped: {failed}[/bold {color}]",
        border_style=color,
    ))


# ---------------------------------------------------------------------------
# batch extract
# ---------------------------------------------------------------------------

@batch_app.command(name="extract")
def batch_extract(
    stego_dir: str = typer.Option(..., "--stego-dir", "-s", help="Directory of stego files"),
    passphrase: str | None = typer.Option(
        None, "--passphrase", help="Secret passphrase (prompted if omitted)"
    ),
    output_dir: str = typer.Option(
        ..., "--output-dir", "-o", help="Directory for recovered payloads"
    ),
) -> None:
    """Extract and decrypt payloads from every stego file in a directory."""
    if not Path(stego_dir).is_dir():
        _die(f"Not a directory: {stego_dir}")

    if passphrase is None:
        passphrase = typer.prompt("Secret passphrase", hide_input=True)

    stego_files = sorted(
        f for f in Path(stego_dir).iterdir()
        if f.is_file() and f.suffix.lower() in _ALL_EXTS
    )
    if not stego_files:
        console.print(Panel("[yellow]No supported stego files found.[/yellow]", border_style="yellow"))
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    prng_seed = _derive_prng_seed(passphrase)
    success, failed = 0, 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Batch extracting…", total=len(stego_files))
        for stego_path in stego_files:
            progress.update(task, description=f"[cyan]Extracting {stego_path.name}…")
            try:
                c        = _get_carrier(str(stego_path))
                blob     = c.extract(str(stego_path), prng_seed)
                filename, data = _decrypt_blob(passphrase, blob)
                (Path(output_dir) / filename).write_bytes(data)
                success += 1
            except Exception as e:
                err_console.print(f"[red]  FAIL {stego_path.name}: {e}[/red]")
                failed += 1
            progress.advance(task)

    color = "green" if failed == 0 else "yellow"
    console.print(Panel(
        f"[bold {color}]Batch extract complete — Success: {success}  Failed: {failed}[/bold {color}]",
        border_style=color,
    ))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
