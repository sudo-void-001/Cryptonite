"""
Cryptonite CLI Interface.

Powered by Typer and Rich.
"""

import typer
from rich.console import Console

app = typer.Typer(
    name="cryptonite",
    help="Production-grade steganography toolkit for PNG, JPEG, and MP3.",
    add_completion=False,
)
console = Console()


@app.command()
def embed(
    carrier: str = typer.Option(..., "--carrier", "-c", help="Path to cover carrier file"),
    payload: str = typer.Option(..., "--payload", "-p", help="Path to secret payload file"),
    passphrase: str = typer.Option(
        ..., "--passphrase", prompt="Secret passphrase", hide_input=True, help="Secret passphrase"
    ),
    output: str = typer.Option(..., "--output", "-o", help="Output path for stego file"),
) -> None:
    """Embed an encrypted payload inside a carrier file."""
    if not all(isinstance(x, str) for x in (carrier, payload, passphrase, output)):
        raise TypeError("All arguments must be strings")
    console.print(f"[yellow]Embedding payload from {payload} into {carrier}...[/yellow]")
    raise NotImplementedError("Phase 6 CLI implementation pending")


@app.command()
def extract(
    stego: str = typer.Option(..., "--stego", "-s", help="Path to stego carrier file"),
    passphrase: str = typer.Option(
        ..., "--passphrase", prompt="Secret passphrase", hide_input=True, help="Secret passphrase"
    ),
    output: str = typer.Option(..., "--output", "-o", help="Output path for recovered payload"),
) -> None:
    """Extract and decrypt a hidden payload from a stego file."""
    if not all(isinstance(x, str) for x in (stego, passphrase, output)):
        raise TypeError("All arguments must be strings")
    console.print(f"[yellow]Extracting payload from {stego}...[/yellow]")
    raise NotImplementedError("Phase 6 CLI implementation pending")


@app.command()
def capacity(
    carrier: str = typer.Option(..., "--carrier", "-c", help="Path to carrier file"),
) -> None:
    """Calculate maximum payload capacity for a carrier file."""
    if not isinstance(carrier, str):
        raise TypeError("carrier must be a string")
    console.print(f"[yellow]Calculating capacity for {carrier}...[/yellow]")
    raise NotImplementedError("Phase 6 CLI implementation pending")


@app.command()
def analyze(
    cover: str = typer.Option(..., "--cover", help="Path to original cover file"),
    stego: str = typer.Option(..., "--stego", help="Path to stego file"),
) -> None:
    """Run steganalysis scoring suite on media files."""
    if not isinstance(cover, str) or not isinstance(stego, str):
        raise TypeError("cover and stego must be strings")
    console.print("[yellow]Running steganalysis suite...[/yellow]")
    raise NotImplementedError("Phase 6 CLI implementation pending")


if __name__ == "__main__":
    app()
