#!/usr/bin/env python3
"""testout.py <results.xml> [name filter]: print each test's result and its own output lines (TestContext.WriteLine)."""
import sys, xml.etree.ElementTree as E
r = E.parse(sys.argv[1]).getroot(); flt = sys.argv[2] if len(sys.argv) > 2 else ""
for t in r.iter('test-case'):
    if flt and flt not in t.get('fullname'): continue
    out = t.find('output'); msg = t.find('.//message')
    print(f"{t.get('result'):8} {t.get('fullname')}")
    if msg is not None and t.get('result') != 'Passed': print("   ! " + (msg.text or '').strip()[:400].replace("\n", "\n   ! "))
    if out is not None and out.text: print("   " + out.text.strip()[:3000].replace("\n", "\n   "))
