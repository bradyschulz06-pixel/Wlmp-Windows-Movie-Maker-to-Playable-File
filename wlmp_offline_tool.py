#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PureWindowsPath
from xml.etree import ElementTree as ET

MEDIA_EXTENSIONS = {
    ".mp4",".wmv",".mov",".mkv",".avi",".jpg",".jpeg",".png",".gif",".bmp",".mp3",".wav",".m4a",".wma"
}

@dataclass
class ValidationResult:
    wlmp_path: Path
    referenced_paths: list[str]
    found_paths: list[Path]
    missing_paths: list[str]

class ZipSafetyError(RuntimeError):
    pass

def require_binary(binary_name: str) -> None:
    p = Path(binary_name)
    if p.exists() and p.is_file():
        return
    if shutil.which(binary_name) is None:
        raise RuntimeError(f"{binary_name} not found on PATH.")

def _safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            resolved = (destination / member.filename).resolve()
            if not str(resolved).startswith(str(destination)):
                raise ZipSafetyError(f"Unsafe ZIP entry: {member.filename}")
        zf.extractall(destination)

def extract_wlmp_from_zip(package: Path, temp_dir: Path) -> Path:
    _safe_extract_zip(package, temp_dir)
    wlmp_files = list(temp_dir.rglob("*.wlmp"))
    if not wlmp_files:
        raise RuntimeError("No .wlmp file found in package.")
    if len(wlmp_files) > 1:
        raise RuntimeError("Multiple .wlmp files found in package.")
    return wlmp_files[0]

def _contains_media_extension(text: str) -> bool:
    lower = text.lower()
    return any(ext in lower for ext in MEDIA_EXTENSIONS)

def parse_wlmp_references(wlmp_path: Path) -> list[str]:
    tree = ET.parse(wlmp_path)
    root = tree.getroot()
    refs: list[str] = []
    for e in root.iter():
        for k, v in e.attrib.items():
            if k.lower() in {"src", "source", "filename", "path"} and _contains_media_extension(v):
                refs.append(v.strip())
        t = (e.text or "").strip()
        if t and _contains_media_extension(t):
            refs.append(t)
    return sorted(set(refs))

def _to_candidate_relpath(raw_reference: str) -> Path:
    ref = raw_reference.strip().strip('"').strip("'")
    if ":\\" in ref or "\\" in ref:
        wp = PureWindowsPath(ref)
        parts = list(wp.parts)
        if parts and parts[0].endswith("\\"):
            parts = parts[1:]
        if parts and parts[0].endswith(":"):
            parts = parts[1:]
        return Path(*parts)
    return Path(ref)

def _candidate_asset_paths(temp_dir: Path, reference: str) -> list[Path]:
    rel = _to_candidate_relpath(reference)
    return [temp_dir / rel, temp_dir / rel.name, temp_dir / "media" / rel, temp_dir / "media" / rel.name]

def validate_package(package: Path) -> ValidationResult:
    with tempfile.TemporaryDirectory(prefix="wlmp_pkg_") as tmp:
        temp_dir = Path(tmp)
        wlmp = extract_wlmp_from_zip(package, temp_dir)
        references = parse_wlmp_references(wlmp)
        found: list[Path] = []
        missing: list[str] = []

        for ref in references:
            matched = None
            for candidate in _candidate_asset_paths(temp_dir, ref):
                if candidate.exists():
                    matched = candidate
                    break
            if matched is None:
                missing.append(ref)
            else:
                found.append(matched)

        return ValidationResult(
            wlmp_path=wlmp,
            referenced_paths=references,
            found_paths=found,
            missing_paths=missing,
        )

def package_project(wlmp_path: Path, media_dir: Path, output_zip: Path) -> int:
    if not wlmp_path.exists():
        raise RuntimeError(f"WLMP not found: {wlmp_path}")
    if wlmp_path.suffix.lower() != ".wlmp":
        raise RuntimeError("--wlmp must point to a .wlmp file")
    if not media_dir.exists() or not media_dir.is_dir():
        raise RuntimeError(f"Media directory not found: {media_dir}")

    media_files = [p for p in media_dir.rglob("*") if p.is_file()]
    if not media_files:
        raise RuntimeError("Media directory is empty.")

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(wlmp_path, arcname=wlmp_path.name)
        for media_file in media_files:
            arcname = Path("media") / media_file.relative_to(media_dir)
            zf.write(media_file, arcname=str(arcname))
    return len(media_files)

def ffmpeg_command(input_path: Path, output_path: Path, mode: str, ffmpeg_bin: str = "ffmpeg") -> list[str]:
    base = [ffmpeg_bin, "-y", "-i", str(input_path)]
    if mode == "best":
        return base + [
            "-map_metadata", "0",
            "-c:v", "libx264", "-preset", "veryslow", "-crf", "14", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-movflags", "+faststart", str(output_path)
        ]
    if mode == "web":
        return base + [
            "-map_metadata", "0",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(output_path)
        ]
    if mode == "archive":
        return base + [
            "-map_metadata", "0",
            "-c:v", "ffv1", "-level", "3", "-g", "1",
            "-c:a", "pcm_s24le", str(output_path)
        ]
    raise ValueError(f"Unknown mode: {mode}")

def run_conversion(input_path: Path, output_path: Path, mode: str, ffmpeg_bin: str = "ffmpeg") -> None:
    require_binary(ffmpeg_bin)
    cmd = ffmpeg_command(input_path, output_path, mode, ffmpeg_bin)
    subprocess.run(cmd, check=True)

def _result_to_json_payload(result: ValidationResult) -> dict[str, object]:
    payload = asdict(result)
    payload["wlmp_path"] = str(result.wlmp_path)
    payload["found_paths"] = [str(p) for p in result.found_paths]
    return payload

def main() -> int:
    parser = argparse.ArgumentParser(description="Offline WLMP package validator and transcoder")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_p = sub.add_parser("validate", help="Validate package ZIP contents against WLMP references")
    validate_p.add_argument("--package", required=True, type=Path)
    validate_p.add_argument("--report-json", type=Path, default=None)

    package_p = sub.add_parser("package", help="Create a standard ZIP package from WLMP + media directory")
    package_p.add_argument("--wlmp", required=True, type=Path)
    package_p.add_argument("--media-dir", required=True, type=Path)
    package_p.add_argument("--output-zip", required=True, type=Path)

    convert_p = sub.add_parser("convert", help="Convert renderable media to output format")
    convert_p.add_argument("--input", required=True, type=Path)
    convert_p.add_argument("--output", required=True, type=Path)
    convert_p.add_argument("--mode", choices=["best", "web", "archive"], default="best")
    convert_p.add_argument("--ffmpeg-bin", default="ffmpeg")

    args = parser.parse_args()

    try:
        if args.command == "validate":
            if not args.package.exists():
                raise RuntimeError(f"Package not found: {args.package}")
            result = validate_package(args.package)
            print(f"WLMP file: {result.wlmp_path.name}")
            print(f"Referenced assets: {len(result.referenced_paths)}")
            print(f"Found assets: {len(result.found_paths)}")
            print(f"Missing assets: {len(result.missing_paths)}")

            if args.report_json is not None:
                args.report_json.parent.mkdir(parents=True, exist_ok=True)
                args.report_json.write_text(json.dumps(_result_to_json_payload(result), indent=2), encoding="utf-8")
                print(f"Validation report written: {args.report_json}")

            if result.missing_paths:
                print("\nMissing references:")
                for m in result.missing_paths:
                    print(f" - {m}")
                return 2

            print("\nValidation passed: all discovered references were found.")
            return 0

        if args.command == "package":
            count = package_project(args.wlmp, args.media_dir, args.output_zip)
            print(f"Package created: {args.output_zip}")
            print(f"Media files included: {count}")
            return 0

        if args.command == "convert":
            if not args.input.exists():
                raise RuntimeError(f"Input not found: {args.input}")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            run_conversion(args.input, args.output, args.mode, args.ffmpeg_bin)
            print(f"Conversion complete: {args.output}")
            return 0

        raise RuntimeError("No command selected.")

    except subprocess.CalledProcessError as exc:
        print(f"FFmpeg failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
