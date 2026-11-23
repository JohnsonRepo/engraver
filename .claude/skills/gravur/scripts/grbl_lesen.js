// Liest GRBL-Einstellungen, Lage und Nullpunkt aus CNCjs auf dem Pi.
// Nur lesend: GET /api/controllers. Es geht nichts an den Uno.
//
// Vom Mac aus (Ausgabe JSON fuer gcode_check.py --pi):
//   ssh -i ~/.ssh/id_ed25519_claude -o IdentitiesOnly=yes laser@laser.local 'node -' \
//       < grbl_lesen.js > zustand.json
//
// Das Token wird wie beim cncjs-pendant mit dem secret aus ~/.cncrc signiert
// (HS256, mit Node-Bordmitteln). CNCjs muss mit dem Uno verbunden sein
// (im Browser einmal "Open"), sonst gibt es keinen Zustand.
'use strict';
const fs = require('fs');
const os = require('os');
const http = require('http');
const crypto = require('crypto');

const PORT = Number(process.env.CNCJS_PORT || 8000);
const HOST = process.env.CNCJS_HOST || '127.0.0.1';
const CNCRC = process.env.CNCRC || os.homedir() + '/.cncrc';

function b64url(daten) {
  return Buffer.from(daten).toString('base64')
    .replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function token(secret) {
  const jetzt = Math.floor(Date.now() / 1000);
  const kopf = b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const last = b64url(JSON.stringify({ id: '', name: 'cncjs-pendant', iat: jetzt, exp: jetzt + 600 }));
  const sig = b64url(crypto.createHmac('sha256', secret).update(kopf + '.' + last).digest());
  return kopf + '.' + last + '.' + sig;
}

function holen(pfad, tok) {
  return new Promise((ok, fehl) => {
    const req = http.get({
      host: HOST, port: PORT, path: pfad + '?token=' + encodeURIComponent(tok),
      headers: { Authorization: 'Bearer ' + tok }, timeout: 8000,
    }, (res) => {
      let text = '';
      res.setEncoding('utf8');
      res.on('data', (t) => { text += t; });
      res.on('end', () => {
        if (res.statusCode !== 200) {
          fehl(new Error('HTTP ' + res.statusCode + ' von CNCjs: ' + text.slice(0, 200)));
          return;
        }
        try { ok(JSON.parse(text)); } catch (e) { fehl(e); }
      });
    });
    req.on('timeout', () => req.destroy(new Error('CNCjs antwortet nicht (Port ' + PORT + ')')));
    req.on('error', fehl);
  });
}

function zahl(v) {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : null;
}

function lage(p) {
  p = p || {};
  return { x: zahl(p.x), y: zahl(p.y), z: zahl(p.z) };
}

function ende(objekt, code) {
  process.stdout.write(JSON.stringify(objekt, null, 2) + '\n');
  process.exit(code);
}

(async () => {
  let cfg;
  try {
    cfg = JSON.parse(fs.readFileSync(CNCRC, 'utf8'));
  } catch (e) {
    ende({ fehler: CNCRC + ' nicht lesbar: ' + e.message }, 2);
  }
  if (!cfg.secret) ende({ fehler: 'Kein secret in ' + CNCRC }, 2);
  let liste;
  try {
    liste = await holen('/api/controllers', token(cfg.secret));
  } catch (e) {
    ende({ fehler: e.message }, 2);
  }
  if (!Array.isArray(liste) || liste.length === 0) {
    ende({ fehler: 'CNCjs ist nicht mit dem Uno verbunden: im Browser Port oeffnen, dann noch einmal' }, 3);
  }
  const c = liste[0];
  const ctl = c.controller || c;
  const st = ctl.settings || {};
  const einstellungen = st.settings || (Object.keys(st).some((k) => k.startsWith('$')) ? st : {});
  const state = ctl.state || {};
  const status = state.status || {};
  const mpos = lage(status.mpos);
  const wpos = lage(status.wpos);
  const wco = {};
  for (const a of ['x', 'y', 'z']) {
    wco[a] = (mpos[a] !== null && wpos[a] !== null) ? Math.round((mpos[a] - wpos[a]) * 1000) / 1000 : null;
  }
  const modal = (state.parserstate && state.parserstate.modal) || {};
  const workflow = c.workflow && typeof c.workflow === 'object' ? c.workflow.state : c.workflow;
  ende({
    zeit: new Date().toISOString(),
    port: c.port || null,
    einstellungen,
    parameter: st.parameters || null,
    status: { activeState: status.activeState || null, mpos, wpos },
    wco,
    wcs: modal.wcs || null,
    workflow: workflow || null,
  }, 0);
})();
