"""CLI: `grounding-seed status|resolve|confirm|scan`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from grounding_seed.ladder import confirm, resolve
from grounding_seed.location import detect_ecosystem
from grounding_seed.scan import scan
from grounding_seed.store import LocalStore


def _print(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="grounding-seed", description="Standalone-Bootstrap fuer isolierte Module.")
    parser.add_argument("--root", required=True, help="Wurzel des lokalen Speichers (Pflicht -- kein globaler Default)")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("status", help="Ecosystem-Erkennung (Sensorik)")

    r = commands.add_parser("resolve", help="Rolle aufloesen")
    r.add_argument("rolle")
    r.add_argument("--discovery-root", action="append", default=[])

    c = commands.add_parser("confirm", help="Fund auf Stufe 0 heben")
    c.add_argument("rolle")
    c.add_argument("quelle_json")
    c.add_argument("--stufe-herkunft", type=int, default=2)

    s = commands.add_parser("scan", help="Wissen+Ressourcen scannen")
    s.add_argument("--program", action="append", default=[], help="Wiederholbar, z.B. --program ffmpeg")

    args = parser.parse_args(argv)
    root = Path(args.root)
    store = LocalStore(root)

    if args.command == "status":
        status = detect_ecosystem(hint_root=root)
        _print({
            "connected": status.connected,
            "source_resolver_version": status.source_resolver_version,
            "hint_findings": status.hint_findings,
        })
        return 0

    if args.command == "resolve":
        result = resolve(args.rolle, store=store, discovery_roots=[Path(p) for p in args.discovery_root])
        _print(result.to_dict())
        return 0 if result.status == "resolved" else 2

    if args.command == "confirm":
        quelle_path = Path(args.quelle_json)
        quelle = json.loads(quelle_path.read_text(encoding="utf-8")) if quelle_path.exists() else json.loads(args.quelle_json)
        entry = confirm(args.rolle, quelle, store=store, stufe_herkunft=args.stufe_herkunft)
        _print(entry.to_dict())
        return 0

    if args.command == "scan":
        result = scan(root, resource_programs=args.program)
        _print({
            "knowledge_found": [str(p) for p in result.knowledge_found],
            "resources_found": result.resources_found,
            "resources_missing": result.resources_missing,
        })
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
