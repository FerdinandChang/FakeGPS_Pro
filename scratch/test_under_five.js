
const fs = require('fs');
global.window = global;
global.document = { createElement: () => ({ setAttribute: () => {} }), head: { appendChild: () => {} } };
global.btoa = (str) => Buffer.from(str, 'binary').toString('base64');
global.atob = (b64) => Buffer.from(b64, 'base64').toString('binary');
global.TextEncoder = require('util').TextEncoder;
global.TextDecoder = require('util').TextDecoder;
global.crypto = require('crypto').webcrypto;

async function test() {
    const initRes = await fetch('https://pipimushroom.com/ppmushroom.aspx', {
        headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    const cookies = initRes.headers.get('set-cookie') || '';

    const secCode = fs.readFileSync('scratch/live_api_sec.js', 'utf-8');
    const origFetch = global.fetch;
    global.fetch = async (url, opts = {}) => {
        let fullUrl = url.startsWith('http') ? url : 'https://pipimushroom.com/' + url;
        opts.headers = opts.headers || {};
        opts.headers['Cookie'] = cookies;
        opts.headers['Referer'] = 'https://pipimushroom.com/ppmushroom.aspx';
        opts.headers['User-Agent'] = 'Mozilla/5.0';
        return origFetch(fullUrl, opts);
    };

    eval(secCode);

    const res = await window.PikminApi.request('Handlers/PPMushroomData.ashx', {
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
    });

    console.log('未滿5人的巨大蘑菇總數:', res.summary.totalCount);
    res.items.slice(0, 5).forEach(m => {
        console.log(- []  () | 地標:  | 人數: /5 | 座標: , );
    });
}
test();
