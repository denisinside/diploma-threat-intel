"""
Safe archive extraction: protects against zip bombs, path traversal, malware.
Reads files into memory, never to disk. Only text files extracted.
"""
import zipfile
import io
import os
from pathlib import PurePosixPath, PureWindowsPath
from typing import Iterator, Tuple, Optional
from loguru import logger


def _is_path_safe(member_name: str) -> bool:
    """Check for path traversal attacks (../ or absolute paths)."""
    for path_cls in (PurePosixPath, PureWindowsPath):
        p = path_cls(member_name)
        if p.is_absolute():
            return False
        for part in p.parts:
            if part == "..":
                return False
    return True


def _is_extension_safe(filename: str, safe_exts: set, dangerous_exts: set) -> bool:
    """Only allow safe text extensions, reject dangerous ones."""
    ext = PurePosixPath(filename).suffix.lstrip(".").lower()
    if ext in dangerous_exts:
        return False
    if safe_exts and ext not in safe_exts:
        return False
    return True


def iter_zip_text_files(
    archive_path: str,
    password: Optional[str] = None,
    max_total_bytes: int = 2 * 1024 * 1024 * 1024,
    max_file_count: int = 10_000,
    safe_exts: set = None,
    dangerous_exts: set = None,
) -> Iterator[Tuple[str, str]]:
    """
    Safely iterate text files inside a zip archive.
    Yields (filename, content_string) tuples.
    Reads into memory - never extracts to disk.
    """
    if safe_exts is None:
        safe_exts = {"txt", "csv", "json", "log"}
    if dangerous_exts is None:
        dangerous_exts = {"exe", "dll", "bat", "cmd", "scr", "ps1", "vbs", "js"}

    pwd_bytes = password.encode() if password else None
    total_bytes = 0
    file_count = 0

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                if not _is_path_safe(info.filename):
                    logger.warning(f"Path traversal blocked: {info.filename}")
                    continue

                if not _is_extension_safe(info.filename, safe_exts, dangerous_exts):
                    continue

                # Zip bomb check
                if info.file_size > max_total_bytes:
                    logger.warning(f"File too large, skipping: {info.filename} ({info.file_size} bytes)")
                    continue

                total_bytes += info.file_size
                if total_bytes > max_total_bytes:
                    logger.error(f"Total uncompressed size exceeds limit ({max_total_bytes}), stopping")
                    return

                file_count += 1
                if file_count > max_file_count:
                    logger.error(f"Too many files in archive (>{max_file_count}), stopping")
                    return

                try:
                    data = zf.read(info.filename, pwd=pwd_bytes)
                    text = data.decode("utf-8", errors="replace")
                    yield info.filename, text
                except Exception as e:
                    logger.warning(f"Cannot read {info.filename}: {e}")
    except zipfile.BadZipFile:
        logger.error(f"Bad zip file: {archive_path}")
    except RuntimeError as e:
        if "password" in str(e).lower() or "encrypt" in str(e).lower():
            logger.error(f"Archive encrypted and no/wrong password: {archive_path}")
        else:
            raise


def iter_7z_rar_text_files(
    archive_path: str,
    password: Optional[str] = None,
    max_total_bytes: int = 2 * 1024 * 1024 * 1024,
    max_file_count: int = 10_000,
    safe_exts: set = None,
    dangerous_exts: set = None,
) -> Iterator[Tuple[str, str]]:
    """
    Safely iterate text files inside 7z/rar archives using py7zr / rarfile.
    Falls back gracefully if libraries are not installed.
    """
    if safe_exts is None:
        safe_exts = {"txt", "csv", "json", "log"}
    if dangerous_exts is None:
        dangerous_exts = {"exe", "dll", "bat", "cmd", "scr", "ps1", "vbs", "js"}

    ext = PurePosixPath(archive_path).suffix.lstrip(".").lower()
    total_bytes = 0
    file_count = 0

    if ext == "7z":
        try:
            import py7zr
        except ImportError:
            logger.error("py7zr not installed, cannot extract .7z files")
            return

        try:
            with py7zr.SevenZipFile(archive_path, mode="r", password=password) as z:
                for name, bio in z.readall().items():
                    if not _is_path_safe(name):
                        logger.warning(f"Path traversal blocked: {name}")
                        continue
                    if not _is_extension_safe(name, safe_exts, dangerous_exts):
                        continue

                    data = bio.read() if hasattr(bio, "read") else bio
                    if isinstance(data, (bytes, bytearray)):
                        size = len(data)
                    else:
                        continue

                    total_bytes += size
                    if total_bytes > max_total_bytes:
                        logger.error("Total size exceeds limit, stopping")
                        return
                    file_count += 1
                    if file_count > max_file_count:
                        logger.error("Too many files, stopping")
                        return

                    yield name, data.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"7z extraction failed: {e}")

    elif ext == "rar":
        try:
            import rarfile
        except ImportError:
            logger.error("rarfile not installed, cannot extract .rar files")
            return

        try:
            with rarfile.RarFile(archive_path) as rf:
                if password:
                    rf.setpassword(password)
                for info in rf.infolist():
                    if info.is_dir():
                        continue
                    if not _is_path_safe(info.filename):
                        logger.warning(f"Path traversal blocked: {info.filename}")
                        continue
                    if not _is_extension_safe(info.filename, safe_exts, dangerous_exts):
                        continue

                    if info.file_size > max_total_bytes:
                        continue
                    total_bytes += info.file_size
                    if total_bytes > max_total_bytes:
                        logger.error("Total size exceeds limit, stopping")
                        return
                    file_count += 1
                    if file_count > max_file_count:
                        logger.error("Too many files, stopping")
                        return

                    try:
                        data = rf.read(info.filename)
                        yield info.filename, data.decode("utf-8", errors="replace")
                    except Exception as e:
                        logger.warning(f"Cannot read {info.filename}: {e}")
        except Exception as e:
            logger.error(f"RAR extraction failed: {e}")
