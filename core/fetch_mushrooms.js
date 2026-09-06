/**
 * FakeGPS Pro - Pipi Mushroom Secure Query Bridge
 * Handles ApiSession.ashx token handshake, AES-GCM / HMAC crypto, and PPMushroomData.ashx parsing.
 */
const fs = require('fs');
const path = require('path');

global.window = global;
global.document = { 
    createElement: () => ({ setAttribute: () => {} }), 
    head: { appendChild: () => {} } 
};
global.btoa = (str) => Buffer.from(str, 'binary').toString('base64');
global.atob = (b64) => Buffer.from(b64, 'base64').toString('binary');
global.TextEncoder = require('util').TextEncoder;
global.TextDecoder = require('util').TextDecoder;
global.crypto = require('crypto').webcrypto;

const secPathCandidates = [
    path.join(__dirname, '..', 'gui', 'js', 'api-security.min.js'),
    path.join(__dirname, '..', 'scratch', 'live_api_sec.js'),
    path.join(process.cwd(), 'gui', 'js', 'api-security.min.js')
];

let secCode = null;
for (const p of secPathCandidates) {
    if (fs.existsSync(p)) {
        secCode = fs.readFileSync(p, 'utf-8');
        break;
    }
}

if (!secCode) {
    console.error(JSON.stringify({ ok: false, error: 'Cannot find api-security.min.js' }));
    process.exit(1);
}

async function queryMushrooms(params = {}) {
    try {
        const initRes = await fetch('https://pipimushroom.com/ppmushroom.aspx', {
            headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
        });
        const cookies = initRes.headers.get('set-cookie') || '';

        const origFetch = global.fetch;
        global.fetch = async (url, opts = {}) => {
            let fullUrl = url.startsWith('http') ? url : 'https://pipimushroom.com/' + url;
            opts.headers = opts.headers || {};
            opts.headers['Cookie'] = cookies;
            opts.headers['Referer'] = 'https://pipimushroom.com/ppmushroom.aspx';
            opts.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)';
            return origFetch(fullUrl, opts);
        };

        eval(secCode);

        const defaultPayload = {
            mode: 'list',
            regionCode: 'TW',
            city: '',
            area: '',
            type: '',
            level: '巨大',
            engagement: 'under_five',
            freshness: '1440',
            sort: 'updated',
            keyword: '',
            page: 1
        };

        const payload = Object.assign({}, defaultPayload, params);
        const res = await window.PikminApi.request('Handlers/PPMushroomData.ashx', payload);
        console.log(JSON.stringify(res));
    } catch (err) {
        console.error(JSON.stringify({ ok: false, error: String(err.message || err) }));
        process.exit(1);
    }
}

const args = process.argv.slice(2);
if (args.length > 0) {
    try {
        const inputParams = JSON.parse(args[0]);
        queryMushrooms(inputParams);
    } catch (e) {
        queryMushrooms({});
    }
} else {
    queryMushrooms({});
}
