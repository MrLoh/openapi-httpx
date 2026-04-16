from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import ParseResult, urlparse

from datamodel_code_generator import PythonVersion

from . import Config, generate


def main(argv: list[str] | None = None) -> None:
    arg_parser = ArgumentParser(description="Generate a typed HTTPX client from an OpenAPI specification")
    arg_parser.add_argument("--input", required=True, help="OpenAPI specification file path or URL")
    arg_parser.add_argument("--output", required=True, help="Output file path")
    arg_parser.add_argument(
        "--target-python-version",
        choices=[v.value for v in PythonVersion],
        default=PythonVersion.PY_311.value,
        help="Target Python version (default: 3.11)",
    )
    arg_parser.add_argument("--client-class-name", help="Name of the generated HTTPX client class")
    arg_parser.add_argument("--async-client", action="store_true", help="Generate an async client (httpx.AsyncClient)")
    arg_parser.add_argument("--use-closed-typed-dict", action="store_true", help="Generate closed TypedDicts (PEP 728)")
    args = arg_parser.parse_args(argv if argv is not None else sys.argv[1:])

    source: ParseResult | Path = (
        urlparse(args.input)
        if args.input.startswith(("http://", "https://"))
        else Path(args.input).expanduser().resolve()
    )
    output: Path = Path(args.output).expanduser().resolve()

    config_dict = {k: v for k, v in vars(args).items() if k not in ("input", "output") and v is not None and v != ""}
    config = Config.model_validate(config_dict)

    result = generate(source, config)
    with open(output, "w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    main()
