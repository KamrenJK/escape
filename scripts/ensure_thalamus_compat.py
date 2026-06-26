from __future__ import annotations

import pathlib
import sys


def _ensure_generated_protos(thalamus_root: pathlib.Path) -> None:
    generated = thalamus_root / "thalamus" / "task_controller_pb2.py"
    if generated.exists():
        return

    sys.path.insert(0, str(thalamus_root))
    from thalamus.build import generate

    cwd = pathlib.Path.cwd()
    try:
        import os

        os.chdir(thalamus_root)
        generate()
    finally:
        os.chdir(cwd)


def _ensure_pypipeline_about(thalamus_root: pathlib.Path) -> None:
    path = thalamus_root / "thalamus" / "pipeline" / "pypipeline.py"
    text = path.read_text()
    if "def about(" in text:
        return

    needle = "  def get_type_name(self, request: thalamus_pb2.StringMessage, context: grpc.ServicerContext):\n"
    replacement = (
        "  def about(self, request: thalamus_pb2.Empty, context: grpc.ServicerContext):\n"
        "    return thalamus_pb2.Text(text='Thalamus Python pipeline')\n"
        "\n"
        f"{needle}"
    )
    if needle not in text:
        raise RuntimeError(f"Could not find insertion point in {path}")
    path.write_text(text.replace(needle, replacement, 1))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: ensure_thalamus_compat.py /path/to/Thalamus/source")
    thalamus_root = pathlib.Path(sys.argv[1]).resolve()
    _ensure_generated_protos(thalamus_root)
    _ensure_pypipeline_about(thalamus_root)


if __name__ == "__main__":
    main()

