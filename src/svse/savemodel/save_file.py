"""Round-trip-safe loading and writing of a single Stardew save XML file.

Design principle (see project plan): never reconstruct the file from a
schema. Parse with lxml, mutate only the specific nodes a given edit needs,
and re-serialize preserving the original BOM/declaration exactly. Plain
`xml.etree.ElementTree` was tried first and rejected - it silently drops the
save's redundant `xmlns:xsd` declaration on re-serialization, breaking byte
parity even with zero edits. lxml preserves that, and needs exactly one
mechanical fixup (it omits the space lxml before `/>` on self-closing tags
that the game's own serializer includes) to achieve a true byte-identical
round trip - verified against a real pulled save file.
"""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

_BOM = b"\xef\xbb\xbf"
_SELF_CLOSE_SPACE_RE = re.compile(rb"(?<!\s)/>")


class MalformedSaveError(Exception):
    """The file doesn't look like a Stardew save (missing BOM/declaration)."""


class SaveFile:
    """Wraps one parsed save XML document (main save or SaveGameInfo)."""

    def __init__(self, declaration: bytes, root: etree._Element):
        self._declaration = declaration
        self.root = root

    @classmethod
    def loads(cls, raw: bytes) -> "SaveFile":
        if not raw.startswith(_BOM):
            raise MalformedSaveError("Missing UTF-8 BOM at start of file")
        body = raw[len(_BOM) :]
        try:
            decl_end = body.index(b"?>") + 2
        except ValueError as exc:
            raise MalformedSaveError("Missing XML declaration") from exc
        declaration = body[:decl_end]
        xml_body = body[decl_end:]

        parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
        root = etree.fromstring(xml_body, parser=parser)
        return cls(declaration, root)

    @classmethod
    def load(cls, path: Path) -> "SaveFile":
        return cls.loads(Path(path).read_bytes())

    def dumps(self) -> bytes:
        body = etree.tostring(self.root, encoding="utf-8", xml_declaration=False)
        body = _SELF_CLOSE_SPACE_RE.sub(b" />", body)
        return _BOM + self._declaration + body

    def dump(self, path: Path) -> None:
        Path(path).write_bytes(self.dumps())

    def find(self, path: str) -> etree._Element | None:
        return self.root.find(path)

    def findall(self, path: str) -> list[etree._Element]:
        return self.root.findall(path)
