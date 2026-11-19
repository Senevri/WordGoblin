#!/usr/bin/env python
"""Mojibake cleanup - convert corrupted text to standard ASCII equivalents."""
import sys
import argparse
from pathlib import Path

# Common mojibake patterns (UTF-8 bytes interpreted as Latin-1/Windows-1252)
MOJIBAKE_MAP = {
    # Smart quotes
    chr(0x2018): chr(39),  # LEFT SINGLE QUOTATION MARK -> apostrophe
    chr(0x2019): chr(39),  # RIGHT SINGLE QUOTATION MARK -> apostrophe
    chr(0x201c): chr(34),  # LEFT DOUBLE QUOTATION MARK -> quote
    chr(0x201d): chr(34),  # RIGHT DOUBLE QUOTATION MARK -> quote
    chr(0x2014): chr(45),  # EM DASH -> hyphen
    chr(0x2013): chr(45),  # EN DASH -> hyphen
    chr(0x2026): '...',    # HORIZONTAL ELLIPSIS
    chr(0x00a0): ' ',      # NO-BREAK SPACE -> space
    chr(0x2009): ' ',      # THIN SPACE -> space
    chr(0x200a): ' ',      # HAIR SPACE -> space
    chr(0x200b): '',       # ZERO WIDTH SPACE -> remove
    chr(0xfeff): '',       # ZERO WIDTH NO-BREAK SPACE (BOM) -> remove
    # Currency
    chr(0x00a3): 'GBP',    # POUND SIGN
    chr(0x20ac): 'EUR',    # EURO SIGN
    chr(0x00a5): 'YEN',    # YEN SIGN
    chr(0x00a2): 'c',      # CENT SIGN
    # Math/symbols
    chr(0x00d7): '*',      # MULTIPLICATION SIGN
    chr(0x00f7): '/',      # DIVISION SIGN
    chr(0x00b1): '+/-',    # PLUS-MINUS
    chr(0x00b2): '2',      # SUPERSCRIPT TWO
    chr(0x00b3): '3',      # SUPERSCRIPT THREE
    chr(0x00b9): '1',      # SUPERSCRIPT ONE
    chr(0x00bc): '1/4',    # VULGAR FRACTION ONE QUARTER
    chr(0x00bd): '1/2',    # VULGAR FRACTION ONE HALF
    chr(0x00be): '3/4',    # VULGAR FRACTION THREE QUARTERS
    chr(0x2153): '1/3',    # VULGAR FRACTION ONE THIRD
    chr(0x2154): '2/3',    # VULGAR FRACTION TWO THIRDS
    chr(0x2155): '1/5',    # VULGAR FRACTION ONE FIFTH
    chr(0x2156): '2/5',    # VULGAR FRACTION TWO FIFTHS
    chr(0x2157): '3/5',    # VULGAR FRACTION THREE FIFTHS
    chr(0x2158): '4/5',    # VULGAR FRACTION FOUR FIFTHS
    chr(0x2159): '1/6',    # VULGAR FRACTION ONE SIXTH
    chr(0x215a): '5/6',    # VULGAR FRACTION FIVE SIXTHS
    chr(0x215b): '1/8',    # VULGAR FRACTION ONE EIGHTH
    chr(0x215c): '3/8',    # VULGAR FRACTION THREE EIGHTHS
    chr(0x215d): '5/8',    # VULGAR FRACTION FIVE EIGHTHS
    chr(0x215e): '7/8',    # VULGAR FRACTION SEVEN EIGHTHS
    # Accented characters (common ones)
    chr(0x00e0): 'a', chr(0x00e1): 'a', chr(0x00e2): 'a', chr(0x00e3): 'a',
    chr(0x00e4): 'a', chr(0x00e5): 'a', chr(0x00e6): 'ae',
    chr(0x00e7): 'c', chr(0x00e8): 'e', chr(0x00e9): 'e', chr(0x00ea): 'e',
    chr(0x00eb): 'e', chr(0x00ec): 'i', chr(0x00ed): 'i', chr(0x00ee): 'i',
    chr(0x00ef): 'i', chr(0x00f0): 'd', chr(0x00f1): 'n',
    chr(0x00f2): 'o', chr(0x00f3): 'o', chr(0x00f4): 'o', chr(0x00f5): 'o',
    chr(0x00f6): 'o', chr(0x00f8): 'o', chr(0x00f9): 'u', chr(0x00fa): 'u',
    chr(0x00fb): 'u', chr(0x00fc): 'u', chr(0x00fd): 'y', chr(0x00ff): 'y',
    chr(0x00c0): 'A', chr(0x00c1): 'A', chr(0x00c2): 'A', chr(0x00c3): 'A',
    chr(0x00c4): 'A', chr(0x00c5): 'A', chr(0x00c6): 'AE',
    chr(0x00c7): 'C', chr(0x00c8): 'E', chr(0x00c9): 'E', chr(0x00ca): 'E',
    chr(0x00cb): 'E', chr(0x00cc): 'I', chr(0x00cd): 'I', chr(0x00ce): 'I',
    chr(0x00cf): 'I', chr(0x00d0): 'D', chr(0x00d1): 'N',
    chr(0x00d2): 'O', chr(0x00d3): 'O', chr(0x00d4): 'O', chr(0x00d5): 'O',
    chr(0x00d6): 'O', chr(0x00d8): 'O', chr(0x00d9): 'U', chr(0x00da): 'U',
    chr(0x00db): 'U', chr(0x00dc): 'U', chr(0x00dd): 'Y', chr(0x00de): 'TH',
    chr(0x00df): 'ss',
}

def clean_mojibake(text):
    """Apply mojibake cleanup to text."""
    result = []
    for char in text:
        if char in MOJIBAKE_MAP:
            result.append(MOJIBAKE_MAP[char])
        else:
            result.append(char)
    return ''.join(result)

def main():
    parser = argparse.ArgumentParser(description='Clean mojibake from text files')
    parser.add_argument('input', help='Input text file')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print('Error: ' + str(input_path) + ' not found', file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding='utf-8', errors='replace')

    # Count changes
    original_chars = len(text)
    cleaned = clean_mojibake(text)
    cleaned_chars = len(cleaned)
    changes = original_chars - cleaned_chars

    print('Processed ' + str(original_chars) + ' characters')
    print('Removed/replaced ' + str(changes) + ' characters')

    if args.dry_run:
        print('')
        print('First 500 chars of cleaned text:')
        print(cleaned[:500])
    elif args.output:
        Path(args.output).write_text(cleaned, encoding='utf-8')
        print('Written to ' + str(args.output))
    else:
        print(cleaned)

if __name__ == '__main__':
    main()
