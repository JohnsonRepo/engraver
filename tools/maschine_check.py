#!/usr/bin/env python3
"""Pruefung des Gesamtmodells in fusion/Portal/Portal.py — laeuft ohne
Fusion.

Portal.py baut seit Rev. 29 die ganze Maschine: Es laedt die anderen
Skripte aus den Ordnern neben Portal/ und ruft ihre Funktionen auf
(maschine_<Ordner>). Einen falschen Funktionsnamen, eine falsche Zahl von
Argumenten oder einen Schluessel, den lage() nicht mehr liefert, merkt
Fusion erst mitten im Lauf. Diese Pruefung findet sie vorher:

  1) jeder Nachbar: Ordner mit Skript und Manifest, SKRIPT_NAME = Ordner,
     Portal.py findet ihn neben sich
  2) jede Funktion und jedes Attribut des Skripts, das Portal.py benutzt,
     existiert; die Argumente passen zur Signatur
  3) jeder Schluessel, den Portal.py aus lage() und MASSE des Skripts
     liest, ist da
  4) Lage der Gruppen: ToolheadZ in der Mitte des X-Wegs, Z im Weg
  5) Kabelhalter: KABELHALTER_Y wie tools/kabelhalter_check.py, der
     gebaute Halter steht auf einem der Plaetze, die Drehung legt ihn
     rechts dorthin, wo die Pruefung ihn annimmt
  6) Komponentennamen im Modell eindeutig
  7) eigene Materialien (PLA, PETG, ...) haben in allen Skripten dieselbe
     Dichte — im Gesamtmodell teilen sie sich ein Material
  8) der Bericht rendert, keine Zeile ueber 74 Zeichen

    python3 tools/maschine_check.py

Exit-Code 0 = alle Pruefungen bestanden.
"""

import ast
import inspect
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import kabelhalter_check as khc                       # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
FUSION = os.path.normpath(os.path.join(HIER, '..', 'fusion'))
# Funktionen von Portal.py, die fuer einen Nachbarn mit dessen Modul m
# arbeiten, ausser maschine_<Ordner> selbst
HELFER = {'ToolheadZ': ('toolhead_kaufteile',)}


def funktionen(baum):
    return {n.name: n for n in baum.body if isinstance(n, ast.FunctionDef)}


def ist_m(knoten):
    return isinstance(knoten, ast.Name) and knoten.id == 'm'


def aufrufe(knoten):
    """(Name, Zahl der Positionsargumente, Schluesselwoerter, Zeile) jedes
    Aufrufs einer Funktion von m: direkt m.f(...) oder ueber
    versuchen(protokoll, was, m.f, ...)."""
    for n in ast.walk(knoten):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Attribute) and ist_m(f.value):
            yield f.attr, len(n.args), [k.arg for k in n.keywords], n.lineno
        elif (isinstance(f, ast.Name) and f.id == 'versuchen'
              and len(n.args) >= 3 and isinstance(n.args[2], ast.Attribute)
              and ist_m(n.args[2].value)):
            yield (n.args[2].attr, len(n.args) - 3,
                   [k.arg for k in n.keywords], n.lineno)


def attribute(knoten):
    return sorted({n.attr for n in ast.walk(knoten)
                   if isinstance(n, ast.Attribute) and ist_m(n.value)})


def lage_variable(knoten):
    """Name der Variablen, der maschine_<Ordner> m.lage() zuweist."""
    for n in ast.walk(knoten):
        if (isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Attribute)
                and ist_m(n.value.func.value) and n.value.func.attr == 'lage'
                and isinstance(n.targets[0], ast.Name)):
            return n.targets[0].id
    return None


def main():
    pfad_portal = bauraum.PORTAL
    pm = bauraum.modul_laden(pfad_portal, 'portal')
    L = pm.lage()
    quelle = open(pfad_portal, encoding='utf-8').read()
    baum = ast.parse(quelle)
    fn = funktionen(baum)
    p = Pruefung()

    # ------------------------------------------------------------------
    p.titel('1) Nachbarn: Ordner, Skript, Manifest')
    p.info('Portal Rev. {}, MASCHINE = {}'.format(pm.REVISION, pm.MASCHINE))
    module = {}
    for name in pm.NACHBARN:
        ordner = os.path.join(FUSION, name)
        py = os.path.join(ordner, name + '.py')
        p.ja('{}: {}.py und {}.manifest'.format(name, name, name),
             os.path.isfile(py)
             and os.path.isfile(os.path.join(ordner, name + '.manifest')))
        p.ja('{}: Portal.py findet ihn neben sich'.format(name),
             os.path.normpath(pm.nachbar_pfad(name)) == os.path.normpath(py))
        try:
            m = bauraum.modul_laden(py, 'nachbar_' + name.lower())
        except Exception as exc:
            p.ja('{}: laesst sich laden ({})'.format(name, exc), False)
            continue
        module[name] = m
        p.ja('{}: SKRIPT_NAME = Ordnername, REVISION = {}'.format(
            name, m.REVISION), m.SKRIPT_NAME == name
             and isinstance(m.REVISION, int))
        p.ja('{}: maschine_{}() in Portal.py'.format(name, name),
             'maschine_' + name in fn)

    # ------------------------------------------------------------------
    p.titel('2) Aufrufe in die Skripte: Funktion da, Argumente passen')
    for name, m in module.items():
        knoten = [fn[n] for n in ('maschine_' + name,) + HELFER.get(name, ())
                  if n in fn]
        n_auf = 0
        for k in knoten:
            for attr in attribute(k):
                if not hasattr(m, attr):
                    p.ja('{}: {} existiert'.format(name, attr), False)
            for attr, n_pos, kws, zeile in aufrufe(k):
                n_auf += 1
                f = getattr(m, attr, None)
                if f is None:
                    continue                    # oben schon gemeldet
                try:
                    inspect.signature(f).bind(
                        *([None] * n_pos), **{kw: None for kw in kws})
                    gut = True
                except TypeError as exc:
                    gut, grund = False, exc
                p.ja('{}.{} mit {} Argument(en) (Zeile {})'.format(
                    name, attr, n_pos + len(kws), zeile), gut,
                    '' if gut else ': {}'.format(grund))
        p.ja('{}: {} Aufrufe, alle Attribute vorhanden'.format(name, n_auf),
             all(hasattr(m, a) for k in knoten for a in attribute(k)))

    # ------------------------------------------------------------------
    p.titel('3) Schluessel aus lage() und MASSE der Skripte')
    for name, m in module.items():
        knoten = [fn[n] for n in ('maschine_' + name,) + HELFER.get(name, ())
                  if n in fn]
        var = lage_variable(fn['maschine_' + name]) if (
            'maschine_' + name) in fn else None
        teile = [ast.get_source_segment(quelle, k) for k in knoten]
        text = '\n'.join(teile)
        lage_m = m.lage()
        if var:
            fehlt = sorted({s for s in re.findall(
                r"\b{}\['([^']+)'\]".format(var), text)} - set(lage_m))
            p.ja('{}: alle {}[...] von lage() geliefert'.format(name, var),
                 not fehlt, '' if not fehlt else ': fehlt ' + ', '.join(fehlt))
        masse = set(re.findall(r"\btw\('([^']+)'\)", text)) | set(
            re.findall(r"m\.MASSE\['([^']+)'\]", text))
        fehlt = sorted(masse - set(m.MASSE))
        if masse:
            p.ja('{}: alle {} gelesenen Masse in MASSE'.format(
                name, len(masse)), not fehlt,
                '' if not fehlt else ': fehlt ' + ', '.join(fehlt))

    # ------------------------------------------------------------------
    p.titel('4) Lage der Gruppen')
    if 'ToolheadZ' in module:
        tm = module['ToolheadZ']
        T = tm.lage()
        dx, dy, dz = pm.gruppe_versatz('ToolheadZ', L)
        p.ok('ToolheadZ: X-Wagenmitte = Mitte des X-Wegs', abs(
            dx - (L['xw_min'] + L['xw_max']) / 2.0), 0.0, '<=')
        p.ok('ToolheadZ: in Y und Z nicht verschoben', abs(dy) + abs(dz),
             0.0, '<=')
        zc = (T['zc_min'] + T['zc_max']) / 2.0
        p.info('ToolheadZ: Z-Wagen in der Mitte des Wegs (zc)', zc)
        p.ok('ToolheadZ: zc im Weg (ueber zc_min)', zc - T['zc_min'], 0.0)
        p.ok('ToolheadZ: zc im Weg (unter zc_max)', T['zc_max'] - zc, 0.0)
        for schl in ('x_wagen_laenge', 'x_wagen_breite'):
            p.ok('ToolheadZ: {} wie Portal.py'.format(schl),
                 abs(tm.w(schl) - pm.w(schl)), 0.0, '<=')
    for name in module:
        if name != 'ToolheadZ':
            p.ok('{}: Gruppe am Ursprung (Koordinaten wie Portal.py)'.format(
                name), sum(abs(v) for v in pm.gruppe_versatz(name, L)), 0.0,
                '<=')

    # ------------------------------------------------------------------
    p.titel('5) Kabelhalter: Plaetze und Drehung')
    if 'Kabelhalter' in module:
        A = khc.alles()
        KL = A['KL']
        ky = A['km'].w('kh_y')
        for s, n in ((-1, 'links'), (1, 'rechts')):
            soll = sorted(y for ab in A['ab'] if ab['seite'] == s
                          for y in ab['plaetze'])
            ist = sorted(pm.KABELHALTER_Y[s])
            p.ja('{}: {} Halter wie kabelhalter_check.py'.format(n, len(ist)),
                 len(soll) == len(ist))
            if len(soll) == len(ist):
                p.ok('{}: groesste Abweichung der Plaetze'.format(n),
                     max(abs(a - b) for a, b in zip(soll, ist)), 0.5, '<=')
        p.ja('der gebaute Halter (kh_y = {:.0f}) steht auf einem Platz '
             'links'.format(ky),
             any(abs(y - ky) < 1e-6 for y in pm.KABELHALTER_Y[-1]))
        # Drehung um die Senkrechte durch X = 0, Y = (ky + y) / 2: aus
        # (x, Y) wird (-x, ky + y - Y). Der linke Halter bei ky muss dann
        # dort landen, wo kabelhalter_check.py den rechten annimmt.
        links = khc.halter_quader(KL, -1, ky)
        for y in pm.KABELHALTER_Y[1][:1]:
            rechts = khc.halter_quader(KL, 1, y)
            gedreht_x = sorted((-links.x[1], -links.x[0]))
            gedreht_y = sorted((ky + y - links.y[1], ky + y - links.y[0]))
            p.ok('rechts gedreht: X wie kabelhalter_check.py',
                 max(abs(a - b) for a, b in zip(gedreht_x, rechts.x)), 0.01,
                 '<=')
            p.ok('rechts gedreht: Y wie kabelhalter_check.py',
                 max(abs(a - b) for a, b in zip(gedreht_y, rechts.y)), 0.01,
                 '<=')

    # ------------------------------------------------------------------
    p.titel('6) Komponentennamen (soweit im Quelltext fest)')
    # Portal selbst: die beiden Namenstupel in run() und die Referenz
    run_text = ast.get_source_segment(quelle, fn['run'])
    namen = ['Referenz_nicht_drucken']
    for t in re.findall(r"for name in \((.*?)\):", run_text, re.S):
        namen += re.findall(r"'([^']+)'", t)
    for name in module:
        k = fn.get('maschine_' + name)
        if k is None:
            continue
        seg = ast.get_source_segment(quelle, k)
        namen += re.findall(r"teil\(g, '([^']+)'\)", seg)
        tup = re.search(r"for name in \((.*?)\):", seg, re.S)
        if tup:
            namen += re.findall(r"'([^']+)'", tup.group(1))
        m = module[name]
        namen.append('{}_r{}'.format(m.SKRIPT_NAME, m.REVISION))
    if 'Opferplatte' in module:
        om = module['Opferplatte']
        namen += ['Fuss_{}_{}'.format(s, e) for s in om.SEITEN
                  for e in om.ENDEN]
    doppelt = sorted({n for n in namen if namen.count(n) > 1})
    p.info('{} Namen gefunden'.format(len(set(namen))))
    p.ja('keine Komponente heisst wie eine andere', not doppelt,
         '' if not doppelt else ': ' + ', '.join(doppelt))

    # ------------------------------------------------------------------
    # Im Gesamtmodell teilen sich alle Skripte ein Design und damit jedes
    # eigene Material gleichen Namens. Jedes Skript misst die Dichte nach
    # und skaliert sie; mit verschiedenen Zielwerten wuerden sie sich
    # gegenseitig verstellen.
    p.titel('7) Eigene Materialien: gleicher Name, gleiche Dichte')
    dichte = {}
    for name, m in [('Portal', pm)] + list(module.items()):
        for mat, d in getattr(m, 'ZIELDICHTE', {}).items():
            dichte.setdefault(mat, {})[name] = d
    for mat in sorted(dichte):
        werte = dichte[mat]
        p.ja('{}: {:.2f} g/cm3 in {} Skript(en)'.format(
            mat, max(werte.values()), len(werte)),
            max(werte.values()) - min(werte.values()) < 1e-9,
            '' if len(set(werte.values())) == 1 else ': ' + ', '.join(
                '{} {:.2f}'.format(k, v) for k, v in sorted(werte.items())))

    # ------------------------------------------------------------------
    p.titel('8) Bericht des Fusion-Skripts (Gesamtmodell)')
    try:
        zeilen = pm.hinweise_bauen(L, [], ['  Beispiel_r1: gebaut'])
        lang = [z for z in zeilen if len(z) > 74]
        p.ja('Hinweise rendern, keine Zeile ueber 74 Zeichen', not lang,
             '' if not lang else ': ' + lang[0])
    except Exception as exc:
        p.ja('Hinweise rendern ({})'.format(exc), False)

    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
