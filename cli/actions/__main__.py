"""Entry point for auxiliary CLI subcommands."""

from __future__ import annotations

import argparse

from server import serv_config as cfg
from . import list_installed_packages, run_server


def main(argv: list[str] | None = None) -> None:
    """Minimal CLI for auxiliary commands."""
    parser = argparse.ArgumentParser(description="Rotterdam utilities")
    sub = parser.add_subparsers(dest="cmd")

    p_serve = sub.add_parser("serve", help="start API server")
    p_serve.add_argument("--host", default=cfg.HOST)
    p_serve.add_argument("--port", type=int, default=cfg.PORT)

    p_list = sub.add_parser("list-packages", help="list installed packages")
    p_list.add_argument("serial", help="device serial")
    p_list.add_argument("--user", action="store_true", help="show only user apps")
    p_list.add_argument("--system", action="store_true", help="show only system apps")
    p_list.add_argument(
        "--high-value", action="store_true", help="show only high-value apps"
    )
    p_list.add_argument("--regex", help="filter packages by regex")
    p_list.add_argument("--csv", help="export results to CSV at path")
    p_list.add_argument("--json", dest="json_path", help="export results to JSON")
    p_list.add_argument("--limit", type=int, help="limit number of results")

    args = parser.parse_args(argv)
    if args.cmd == "serve":
        run_server(args.host, args.port)
    elif args.cmd == "list-packages":
        list_installed_packages(
            args.serial,
            user=args.user,
            system=args.system,
            high_value=args.high_value,
            regex=args.regex,
            csv_path=args.csv,
            json_path=args.json_path,
            limit=args.limit,
        )
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()

