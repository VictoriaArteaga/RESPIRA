"""Lector XLSX en streaming, solo lectura (stdlib). Copia sin cambios funcionales de data/scripts/quinta_auditoria/xlsx_stream.py."""
import zipfile, re
import xml.etree.ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def col_idx(ref):
    s = re.match(r'[A-Z]+', ref).group(0)
    n = 0
    for ch in s:
        n = n * 26 + ord(ch) - 64
    return n


def sheets(path):
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid = {r.get('Id'): r.get('Target') for r in rels}
    out = {}
    for s in wb.iter(NS + 'sheet'):
        t = rid[s.get(RNS + 'id')]
        t = t.lstrip('/')
        if not t.startswith('xl/'):
            t = 'xl/' + t
        out[s.get('name')] = t
    return z, out


def shared_strings(z):
    if 'xl/sharedStrings.xml' not in z.namelist():
        return []
    out = []
    for ev, el in ET.iterparse(z.open('xl/sharedStrings.xml'), events=('end',)):
        if el.tag == NS + 'si':
            out.append(''.join(t.text or '' for t in el.iter(NS + 't')))
            el.clear()
    return out


def rows(z, target, sst, max_rows=None):
    """Genera (numero_fila, {col_idx: valor})."""
    n = 0
    for ev, el in ET.iterparse(z.open(target), events=('end',)):
        if el.tag == NS + 'row':
            r = {}
            for c in el.iter(NS + 'c'):
                v = c.find(NS + 'v')
                t = c.get('t')
                if t == 'inlineStr':
                    val = ''.join(x.text or '' for x in c.iter(NS + 't'))
                elif v is None or v.text is None:
                    continue
                elif t == 's':
                    val = sst[int(v.text)]
                else:
                    val = v.text
                r[col_idx(c.get('r'))] = val
            yield int(el.get('r')), r
            el.clear()
            n += 1
            if max_rows and n >= max_rows:
                return
