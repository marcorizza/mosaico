import importlib
import sys

PACKS_MAP = {
    "manipulation": "mosaicolabs.packs.manipulation.main",
}


def _print_help() -> None:
    available_packs = ", ".join(sorted(PACKS_MAP))
    print("Usage: mosaicolabs.packs <pack> [args...]")
    print()
    print("Mosaico SDK Packs Runner.")
    print()
    print(f"Available packs: {available_packs}")


def run_pack_cli() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help"}:
        _print_help()
        return

    pack = argv[0]
    if pack not in PACKS_MAP:
        _print_help()
        raise SystemExit(f"Unknown pack '{pack}'")

    module = importlib.import_module(PACKS_MAP[pack])
    entry_point = getattr(module, "main", None)
    if entry_point is None:
        raise SystemExit(f"No 'main' function found in {PACKS_MAP[pack]}")

    sys.argv = [f"{sys.argv[0]} {pack}", *argv[1:]]
    entry_point()


if __name__ == "__main__":
    run_pack_cli()
