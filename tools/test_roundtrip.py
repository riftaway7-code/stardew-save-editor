#!/usr/bin/env python3
"""Quick round-trip test for the web editor surgical-edit logic.

Verifies BOM detection, host <money> replacement inside first <player>, and that other bytes remain unchanged
(except the numeric characters of the replaced field).

Usage: python3 tools/test_roundtrip.py test_saves/sample_save_with_bom.xml
"""
import sys
import re
from pathlib import Path

BOM_BYTES = b"\xEF\xBB\xBF"


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def detect_and_strip_bom(bts: bytes):
    if bts.startswith(BOM_BYTES):
        return True, bts[len(BOM_BYTES):]
    return False, bts


def host_field_regex(tag):
    # matches (<player...> ... <tag>)(value)(</tag>) with the first player
    return re.compile(r"(<player(?:\\s[^>]*?)?>[\\s\\S]*?<" + re.escape(tag) + r">)([\\s\\S]*?)(</" + re.escape(tag) + r">)", re.IGNORECASE)


def replace_money_in_text(text: str, newval: str):
    re_tag = host_field_regex('money')
    m = re_tag.search(text)
    if not m:
        raise SystemExit('host <money> tag not found')
    a, b, c = m.group(1), m.group(2), m.group(3)
    return text[:m.start()] + a + newval + c + text[m.end():], (m.start(2), m.end(2))


def main(argv):
    if len(argv) < 2:
        print('Usage: test_roundtrip.py <sample-save.xml>')
        return 2
    p = Path(argv[1])
    if not p.exists():
        print('File not found:', p)
        return 2
    bts = read_bytes(p)
    had_bom, body = detect_and_strip_bom(bts)
    try:
        text = body.decode('utf-8')
    except Exception as e:
        print('Decode failed:', e); return 3
    # find first money
    new_money = '999999'
    new_text, (s_off, e_off) = replace_money_in_text(text, new_money)
    # Re-encode
    out_body = new_text.encode('utf-8')
    out = (BOM_BYTES + out_body) if had_bom else out_body

    # Compare bytes before and after except the money substring bytes.
    # Find the byte-range of the original money digits
    orig_body_bytes = body
    new_body_bytes = out_body

    # compute the byte ranges corresponding to s_off:e_off in encoded bytes
    prefix_orig = text[:s_off].encode('utf-8')
    orig_money_bytes = text[s_off:e_off].encode('utf-8')
    suffix_orig = text[e_off:].encode('utf-8')

    prefix_new = new_text[:s_off].encode('utf-8')
    new_money_bytes = new_text[s_off:e_off].encode('utf-8')
    suffix_new = new_text[e_off:].encode('utf-8')

    # sanity: prefix and suffix should be identical across original/new
    ok_prefix = prefix_orig == prefix_new
    ok_suffix = suffix_orig == suffix_new

    print('Had BOM:', had_bom)
    print('Prefix identical:', ok_prefix)
    print('Suffix identical:', ok_suffix)
    print('Original money bytes:', orig_money_bytes)
    print('New money bytes:', new_money_bytes)

    if not (ok_prefix and ok_suffix):
        print('\nERROR: non-money bytes changed. Aborting.')
        return 4

    # write out result next to original
    outp = p.with_name(p.name + '.edited')
    outp.write_bytes(out)
    print('\nWrote edited file:', outp)
    print('Round-trip test passed: only target value changed (byte-localized).')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
