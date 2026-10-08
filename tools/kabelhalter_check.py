#!/usr/bin/env python3
"""Rechnerische Pruefung der Kabelhalter (fusion/Kabelhalter) — laeuft ohne
Fusion.

Importiert Kabelhalter.py und Portal.py mit gestubbtem adsk-Modul, dazu die
Kabelliste (tools/verkabelung.py), und prueft: Abgleich der Bezugsmasse,
Schraube in der Hammermutter, Kopf und Inbus frei, die Rinne fuer die Kabel
jedes Abschnitts (Flaeche, und dass sie Kabel fuer Kabel hineinfallen),
Plaetze links und rechts frei von Winkeln, 2060, Traegern der Wanne Y,
Halter_Y und Y-Motorhalter, Luft zu Wanne und Fahne Y, Druck. Gibt die
Plaetze und die Stueckliste aus.

    python3 tools/kabelhalter_check.py          # pruefen
    python3 tools/kabelhalter_check.py --doku   # Tabelle in der Doku neu

Exit-Code 0 = alle Pruefungen bestanden.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bauraum                                        # noqa: E402
import verkabelung as vk                              # noqa: E402
from bauraum import Quader                            # noqa: E402
from toolhead_check import Pruefung                   # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
KABELHALTER = os.path.join(HIER, '..', 'fusion', 'Kabelhalter',
                           'Kabelhalter.py')
DOKU = os.path.join(HIER, '..', 'docs', 'kabelhalter.md')
ELEKTRONIK = os.path.join(HIER, '..', 'fusion', 'Elektronik',
                          'Elektronik.py')
BETT = 250.0           # Bambu Lab A1: 256, mit Rand
LUFT = 3.0             # Mindestfreigang zu Teilen am Rahmen
SPANNE = 100.0         # so weit duerfen zwei Halter hoechstens auseinander
SPANNE_MAX = 120.0     # ... ausnahmsweise, an einem Hindernis
FUELL_MAX = vk.FUELLGRAD_MAX
INBUS = 4.0            # M5-Zylinderkopf: Inbus SW 4
WAND_MIN = 2.0

# Aussendurchmesser ausserhalb der Ketten. Die Motorkabel behalten hier
# ihren Schlauch, die Silikonlitzen laufen einzeln (verkabelung.ADER_D).
KABEL_D = {
    'Motorkabel': (5.0, '[?] mit Schlauch, nicht gemessen'),
    'Leitung 2-adrig': (6.0, '[?] 2 × 0,75 mm², wie NotAus.py'),
    'Leitung 3-adrig': (4.5, '[?] 3 × 0,25 mm²'),
}


def laden():
    """Kabelhalter- und Portal-Modul samt Lagen."""
    km = bauraum.modul_laden(KABELHALTER, 'kabelhalter')
    pm = bauraum.modul_laden(bauraum.PORTAL, 'portal')
    em = bauraum.modul_laden(ELEKTRONIK, 'elektronik')
    return km, km.lage(), pm, pm.lage(), em.lage()


def kabel(lt):
    """Durchmesser der Kabel einer Leitung neben der 2040: [(Name, d)]."""
    art = lt['art']
    for k, (d, _) in KABEL_D.items():
        if art.startswith(k):
            return [(lt['nr'], d)]
    if art.startswith('Litzen'):
        return [(lt['nr'], vk.ADER_D[lt['mm2']])] * len(lt['adern'])
    raise ValueError('kein Durchmesser fuer {} ({})'.format(lt['nr'], art))


def abschnitte(PL, EL):
    """Die Strecken in der unteren Seitennut aussen, je Seite, mit ihren
    Kabeln — aus den Wegen der Kabelliste. Links kommen alle hinten aus dem
    Gehaeuse; die Litzen der Y-Kette gehen hinter der Wanne Y hinein, nur
    W13 laeuft bis vorn. Rechts kommen sie ueber die Rueckseite des hinteren
    2060; nach vorn laufen W2 und W14, W10 nach hinten zum Halter_Y."""
    lts = vk.leitungen()
    links = [lt for lt in lts if 'untere Nut außen am linken 2040'
             in weg(lt, lts)]
    rechts = [lt for lt in lts if 'untere Nut außen am rechten 2040'
              in weg(lt, lts)]
    wanne_hinten = PL['ywanne_y'][0]
    winkel_vorn = PL['quer_y_vorn'][0] - 20.0
    winkel_hinten = PL['quer_y_hinten'][1] + 20.0
    return [
        dict(name='links hinten', seite=-1,
             strecke=(EL['kabel_links_y'], wanne_hinten),
             leitungen=links),
        dict(name='links vorn', seite=-1, strecke=(wanne_hinten, winkel_vorn),
             leitungen=[lt for lt in links if not lt.get('kette')]),
        dict(name='rechts', seite=1, strecke=(winkel_hinten, winkel_vorn),
             leitungen=[lt for lt in rechts if 'rechten 2040 nach vorn'
                        in weg(lt, lts)]),
    ]


def weg(lt, lts):
    """Weg einer Leitung; 'wie W7 ...' wird durch den Weg von W7 ersetzt."""
    w = lt.get('weg', '')
    m = re.match(r'wie (W\d+)', w)
    if m:
        vorbild = next(x for x in lts if x['nr'] == m.group(1))
        return weg(vorbild, lts) + ' | ' + w
    return w


def hindernisse(pm, PL):
    """Teile am Rahmen neben der unteren Seitennut aussen, je Seite als
    Quader: Winkel, 2060, Wanne Y mit Traegern, Halter_Y, Y-Motorhalter,
    dazu die Fahne Y ueber den ganzen Weg."""
    w = pm.w
    teile, _ = bauraum.y_kette_rahmen(w, PL)
    links = list(teile)
    rechts = []
    for q in teile:
        if q.name.startswith('Winkel'):
            rechts.append(Quader(q.name, -q.x[1], -q.x[0], q.y[0], q.y[1],
                                 q.z[0], q.z[1], q.art))
    qx = PL['quer_x']
    for n in ('hinten', 'vorn'):
        q = Quader('2060 ' + n, qx[0], qx[1], *PL['quer_y_' + n],
                   *PL['quer_z'], 'kaufteil')
        links.append(q)
        rechts.append(q)
    rechts.append(Quader('Halter_Y', *PL['hy_boden_x'], *PL['hy_y'],
                         PL['hy_fuss_z'][0], PL['hy_boden_z'][1]))
    fx = (min(PL['fy_backe_o_x'][0], PL['fy_backe_u_x'][0]),
          max(PL['fy_wand_x'][1], PL['fy_blatt_x'][1]))
    rechts.append(Quader('Fahne_Y (ganzer Weg)', *fx, *PL['rahmen_y'],
                         PL['fy_blatt_z'][0], PL['fy_backe_o_z'][1]))
    Y, a = PL['ymh'], PL['aussen_x']
    y0 = PL['rahmen_y'][1] + Y['wange_y0']
    z0 = PL['rahmen_z0'] + Y['halter_z0']
    z1 = PL['rahmen_z0'] + Y['halter_z1']
    links.append(Quader('Y-Motorhalter links', -a - Y['wange_x1'] + 10.0, -a,
                        y0, PL['rahmen_y'][1], z0, z1))
    rechts.append(Quader('Y-Motorhalter rechts', a, a + Y['wange_x1'] - 10.0,
                         y0, PL['rahmen_y'][1], z0, z1))
    return {-1: links, 1: rechts}


def halter_quader(KL, seite, y):
    """Bauraum eines Halters mit Mitte y auf der Seite -1 (links) oder 1."""
    a0, a1 = KL['a']
    fx = KL['flaeche_x']                       # linke Aussenflaeche
    hb = (KL['y'][1] - KL['y'][0]) / 2.0
    x = (fx - a1, fx - a0) if seite < 0 else (-fx + a0, -fx + a1)
    return Quader('Kabelhalter', x[0], x[1], y - hb, y + hb, *KL['zm'])


def sperren(KL, seite, teile):
    """Y-Bereiche, in denen ein Halter an ein Teil stiesse (mit LUFT)."""
    h = halter_quader(KL, seite, 0.0)
    s = []
    for q in teile:
        if (q.x[0] < h.x[1] + LUFT and h.x[0] - LUFT < q.x[1]
                and q.z[0] < h.z[1] + LUFT and h.z[0] - LUFT < q.z[1]):
            s.append((q.y[0], q.y[1], q.name))
    return s


def plaetze_berechnen(KL, strecke, gesperrt, hb):
    """Mitten der Halter auf einer Strecke: in jeder freien Luecke so viele
    gleichmaessig verteilt, dass keine Spanne laenger als SPANNE wird;
    ganze Millimeter."""
    frei = [tuple(sorted(strecke))]
    for a, b, _ in sorted(gesperrt):
        neu = []
        for f0, f1 in frei:
            if b <= f0 or a >= f1:
                neu.append((f0, f1))
                continue
            if a > f0:
                neu.append((f0, a))
            if b < f1:
                neu.append((b, f1))
        frei = neu
    mitten = []
    for f0, f1 in frei:
        lo, hi = f0 + hb + LUFT, f1 - hb - LUFT
        if hi < lo:
            continue
        n = max(1, int(math.ceil((hi - lo) / SPANNE)))
        for i in range(n):
            mitten.append(float(round(lo + (i + 0.5) * (hi - lo) / n)))
    return mitten


def _innen(poly, a, z, r):
    """Liegt der Kreis (a, z, r) ganz im Vieleck?"""
    drin = False
    for (a0, z0), (a1, z1) in zip(poly, poly[1:] + poly[:1]):
        if (z0 > z) != (z1 > z):
            if a < a0 + (z - z0) * (a1 - a0) / (z1 - z0):
                drin = not drin
        da, dz = a1 - a0, z1 - z0
        t = max(0.0, min(1.0, ((a - a0) * da + (z - z0) * dz)
                         / (da * da + dz * dz)))
        if math.hypot(a - a0 - t * da, z - z0 - t * dz) < r - 1e-9:
            return False
    return drin


def packen(KL, durchmesser, schritt=0.1):
    """Legt die Kabel nacheinander in die Rinne, das dickste zuerst: jedes
    faellt so tief wie moeglich, bei Gleichstand dicht an die Anlage.
    Liefert [(a, z, d)] in Querschnittskoordinaten oder None, wenn eins
    nicht mehr hineinpasst."""
    poly = KL['kanal']
    a0, a1 = KL['kanal_a']
    z0, z1 = KL['kanal_z']
    lage = []
    for d in sorted(durchmesser, reverse=True):
        r = d / 2.0 + 0.05
        best = None
        n_a = int((a1 - a0 - 2 * r) / schritt) + 1
        n_z = int((z1 - z0 - 2 * r) / schritt) + 1
        for i in range(max(n_a, 0)):
            a = a0 + r + i * schritt
            for j in range(max(n_z, 0)):
                z = z0 + r + j * schritt
                if best is not None and z >= best[1] - 1e-9:
                    break
                if all(math.hypot(a - pa, z - pz) >= r + pd / 2.0 + 0.05
                       for pa, pz, pd in lage) and _innen(poly, a, z, r):
                    best = (a, z)
                    break
        if best is None:
            return None
        lage.append((best[0], best[1], d))
    return lage


def alles(km=None, KL=None, pm=None, PL=None, EL=None):
    """Abschnitte mit Kabeln, Sperren und Plaetzen — gemeinsame Quelle fuer
    Pruefung, Tabelle und Zeichnung."""
    if km is None:
        km, KL, pm, PL, EL = laden()
    hb = km.w('kh_b') / 2.0
    teile = hindernisse(pm, PL)
    ab = abschnitte(PL, EL)
    for s in ab:
        s['kabel'] = [k for lt in s['leitungen'] for k in kabel(lt)]
        s['sperren'] = [g for g in sperren(KL, s['seite'], teile[s['seite']])
                        if g[1] > min(s['strecke']) and g[0] < max(s['strecke'])]
        s['plaetze'] = plaetze_berechnen(KL, s['strecke'], s['sperren'], hb)
    nr = {-1: 0, 1: 0}
    for s in ab:
        s['namen'] = []
        for _ in s['plaetze']:
            nr[s['seite']] += 1
            s['namen'].append('{}{}'.format('L' if s['seite'] < 0 else 'R',
                                            nr[s['seite']]))
    return dict(km=km, KL=KL, pm=pm, PL=PL, EL=EL, teile=teile, ab=ab)


def de(x, stellen=0):
    return '{:.{}f}'.format(x, stellen).replace('.', ',').replace('-', '−')


def bezug(PL, y):
    """Lage eines Halters, gemessen vom hinteren 2060 (wie die Traeger)."""
    yv, yh = PL['quer_y_hinten'][1], PL['quer_y_hinten'][0]
    if y >= yv:
        return '{} mm vor der Vorderseite'.format(de(y - yv))
    return '{} mm hinter der Rückseite'.format(de(yh - y))


def tabelle(A):
    """Plaetze als Markdown-Tabelle fuer docs/kabelhalter.md."""
    z = ['| Halter | Seite | Mitte (Schraube), vom hinteren 2060 | Y | Kabel |',
         '|---|---|---|---|---|']
    for s in A['ab']:
        nrn = ' · '.join(lt['nr'] for lt in s['leitungen'])
        for n, y in zip(s['namen'], s['plaetze']):
            z.append('| **{}** | {} | {} | {} | {} |'.format(
                n, 'links' if s['seite'] < 0 else 'rechts',
                bezug(A['PL'], y), de(y), nrn))
    return '\n'.join(z)


MARKE = ('<!-- tabelle:plaetze -->', '<!-- /tabelle:plaetze -->')


def doku_tabelle(A, schreiben=False):
    """Vergleicht (oder ersetzt) die Tabelle zwischen den Marken."""
    if not os.path.exists(DOKU):
        return False
    with open(DOKU, encoding='utf-8') as f:
        text = f.read()
    i, j = text.find(MARKE[0]), text.find(MARKE[1])
    if i < 0 or j < 0:
        return False
    neu = text[:i] + MARKE[0] + '\n' + tabelle(A) + '\n' + text[j:]
    if schreiben and neu != text:
        with open(DOKU, 'w', encoding='utf-8') as f:
            f.write(neu)
        return True
    return neu == text


def main():
    A = alles()
    km, KL, pm, PL = A['km'], A['KL'], A['pm'], A['PL']
    kw, w = km.w, pm.w
    if '--doku' in sys.argv:
        doku_tabelle(A, schreiben=True)
        print('geschrieben:', os.path.relpath(DOKU))
    p = Pruefung()

    # ------------------------------------------------------------------
    p.titel('1. Abgleich mit Portal.py')
    p.ok('rahmen_z0 wie Portal.py', abs(kw('rahmen_z0') - PL['rahmen_z0']),
         0.0, '<=')
    for n in ('y_schienen_abstand', 'rahmen_b', 'rahmen_h', 'nut_lippe',
              'nut_tiefe', 'nutenstein_h', 'nut_oben', 'nut_v_t', 'nut_b', 'nut_t', 'nut_kammer_b', 'nut_kammer_t', 'kern_d'):
        p.ok('{} wie Portal.py'.format(n), abs(kw(n) - w(n)), 0.0, '<=')
    p.ok('untere Seitennut wie Portal.py (nut_u_z)',
         abs(KL['nut_z'] - PL['nut_u_z']), 0.0, '<=')
    p.ok('Aussenflaeche des linken 2040 wie Portal.py',
         abs(-KL['flaeche_x'] - PL['aussen_x']), 0.0, '<=')

    # ------------------------------------------------------------------
    p.titel('2. Schraube und Feder')
    p.info('M5x{:.0f} ohne Scheibe, Kopf auf der Anlage'.format(kw('m5_l')))
    p.ok('Spitze vor dem Nutgrund', kw('nut_tiefe') - KL['m5_spitze'], 0.3)
    p.ok('Gewinde im Nutenstein', KL['m5_eingriff'], 3.0)
    p.ok('Feder kuerzer als die Lippe (frei vom Stein)',
         kw('nut_lippe') - kw('feder_t'), 0.2)
    p.ok('Feder schmaler als die Nutoeffnung, je Seite',
         (kw('nut_b') - kw('feder_b')) / 2.0, 0.1)
    p.ok('Feder neben der Traene, laengs (je Seite)',
         kw('kh_b') / 2.0 - kw('m5_durchgang') / 2.0 * math.sqrt(2.0), 3.0)
    p.ok('Kopf auf der Anlage: Rand laengs',
         (kw('kh_b') - kw('m5_kopf_d')) / 2.0, 1.5)
    p.ok('Kopf auf der Anlage: Rand oben',
         KL['z'][1] - KL['kopf_z'][1], 1.5)
    p.ok('Kopf ueber der Rinne', KL['kopf_z'][0] - KL['kanal_z'][1], 2.0)
    p.ok('Inbus: Lippe bleibt unter dem Kopf',
         KL['kopf_z'][0] - KL['lippe_z'][1], 1.5)

    # ------------------------------------------------------------------
    p.titel('3. Rinne und Kabel')
    p.info('Rinne lichter Querschnitt', KL['kanal_flaeche'], 'mm2')
    p.info('Oeffnung oben', KL['oeffnung'])
    for k, (d, st) in KABEL_D.items():
        p.info('{}: Ø{} {}'.format(k, de(d, 1), st))
    for s in A['ab']:
        ds = [d for _, d in s['kabel']]
        fl = sum(math.pi * d * d / 4.0 for d in ds)
        nrn = ', '.join(lt['nr'] for lt in s['leitungen'])
        p.info('{}: {} ({} Kabel/Adern)'.format(s['name'], nrn, len(ds)))
        p.ok('  Fuellgrad', fl / KL['kanal_flaeche'], FUELL_MAX, '<=', '')
        p.ok('  dickstes Kabel passt durch die Oeffnung',
             KL['oeffnung'] - max(ds), 1.0)
        lage = packen(KL, ds)
        p.ja('  alle fallen Kabel fuer Kabel in die Rinne', lage is not None)
        if lage:
            p.ok('  oberstes Kabel unter der Oberkante der Lippe',
                 KL['kanal_z'][1] - max(z + d / 2.0 for _, z, d in lage),
                 0.0)
    p.ok('Rinne unter den Waenden der Traeger Y (Oberkante)',
         PL['ytr_wand_z'][0] - (KL['nut_z'] + KL['kanal_z'][1]), 1.0)

    # ------------------------------------------------------------------
    p.titel('4. Plaetze und Freiraum')
    alle_y = []
    for s in A['ab']:
        st = s['strecke']
        p.info('{}: Y {} bis {}, gesperrt: {}'.format(
            s['name'], de(st[0], 1), de(st[1], 1),
            ', '.join(sorted({g[2] for g in s['sperren']})) or '—'))
        p.ja('  mindestens ein Halter', len(s['plaetze']) > 0)
        for n, y in zip(s['namen'], s['plaetze']):
            h = halter_quader(KL, s['seite'], y)
            d, wer = min((h.abstand(q), q.name) for q in A['teile'][s['seite']])
            p.ok('  {} bei Y {}: Luft zu {}'.format(n, de(y), wer), d, LUFT)
            # Inbus von aussen an den Kopf: waagerecht, 60 mm frei
            a = KL['kopf_a'][1]
            r = INBUS / 2.0 + 1.0
            fx = KL['flaeche_x']
            x = ((fx - a - 60.0, fx - a) if s['seite'] < 0
                 else (-fx + a, -fx + a + 60.0))
            gang = Quader('Inbus', *x, y - r, y + r, KL['nut_z'] - r,
                          KL['nut_z'] + r)
            frei = min(gang.abstand(q) for q in A['teile'][s['seite']])
            p.ok('  {}: Inbus kommt von aussen an den Kopf'.format(n),
                 frei, 0.0)
            alle_y.append((s['seite'], y))
        if len(s['plaetze']) > 1:
            sp = max(b - a for a, b in zip(s['plaetze'], s['plaetze'][1:]))
            p.ok('  groesste Spanne zwischen zwei Haltern', sp, SPANNE_MAX,
                 '<=')
    links = sorted(y for sei, y in alle_y if sei < 0)
    p.ok('links: groesste Spanne ueber beide Abschnitte',
         max(b - a for a, b in zip(links, links[1:])), SPANNE_MAX, '<=')
    p.ja('Modell: kh_y ist ein Platz links',
         any(abs(kw('kh_y') - y) < 0.01 for y in links),
         ' (kh_y = {})'.format(de(kw('kh_y'))))
    wanne = min(q.z[0] for q in A['teile'][-1] if q.name == 'Kettenwanne Y')
    p.ok('Halter unter der Wanne Y', wanne - KL['zm'][1], LUFT)
    p.ok('Halter ueber dem Tisch', KL['zm'][0] - PL['tisch_z'], LUFT)

    # ------------------------------------------------------------------
    p.titel('5. Druck')
    a0, a1 = KL['a']
    z0, z1 = KL['z']
    p.ok('passt aufs Bett', max(a1 - a0, z1 - z0, kw('kh_b')), BETT, '<=')
    for n in ('kanal_wand', 'lippe_h'):
        p.ok('Wand {}'.format(n), kw(n), WAND_MIN)
    p.ok('Anlage', kw('anlage_t'), WAND_MIN)
    p.ok('Fenster dicht an der Anlage (der Binder liegt an ihr)',
         KL['binder_a'][0] - KL['anlage_a'][1], 1.0, '<=')
    p.ok('Fenster liegt in der Rinne',
         KL['kanal_a'][1] - kw('zwickel') - KL['binder_a'][1], 1.0)
    vol = (km.flaeche(KL['querschnitt']) * kw('kh_b')
           - math.pi * kw('m5_durchgang') ** 2 / 4.0 * kw('anlage_t')
           - kw('binder_b') * kw('binder_t') * kw('kanal_wand'))
    p.info('Masse je Halter (PETG, voll)', vol * 1.27 / 1000.0, 'g')

    # ------------------------------------------------------------------
    n = len(alle_y)
    print('Kabelhalter: {} Stück (links {}, rechts {})'.format(
        n, sum(1 for s, _ in alle_y if s < 0),
        sum(1 for s, _ in alle_y if s > 0)))
    print(tabelle(A))
    print('Stückliste: {0} × Kabelhalter (PETG), {0} × M5×{1:.0f} '
          'Zylinderkopf, {0} × Hammermutter M5 (Nut 6), Kabelbinder nach '
          'Bedarf (bis 3,6 mm breit)'.format(n, kw('m5_l')))
    p.titel('6. Doku')
    p.ja('Tabelle der Plaetze in docs/kabelhalter.md aktuell',
         doku_tabelle(A), ' (python3 tools/kabelhalter_check.py --doku)')
    return p.bericht()


if __name__ == '__main__':
    sys.exit(main())
