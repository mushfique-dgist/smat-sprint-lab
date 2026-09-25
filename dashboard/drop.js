'use strict';
(() => {
  const needText = document.getElementById('need');
  const form = document.getElementById('drop-form');
  const value = document.getElementById('value');
  const username = document.getElementById('username');
  const usernameLabel = document.getElementById('username-label');
  const status = document.getElementById('status');
  const link = document.getElementById('submit-link');
  const copyWrap = document.getElementById('copy-wrap');
  const sealed = document.getElementById('sealed');
  const params = new URLSearchParams(location.hash.slice(1));
  const needId = params.get('need') || '';
  const kind = params.get('kind') || '';
  const expectedFp = params.get('fp') || '';
  const repoIssue = 'https://github.com/mushfique-dgist/smat-sprint-lab/issues/new';
  const pattern = /^n-[0-9]{8}-[a-z0-9-]{1,30}-[0-9a-f]{4}$/;
  let keyData;

  function fail(message) { status.textContent = message; form.hidden = true; }
  function decode64(s) { return Uint8Array.from(atob(s), c => c.charCodeAt(0)); }
  function encode64url(bytes) {
    let binary = '';
    for (const b of bytes) binary += String.fromCharCode(b);
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function hex(bytes) { return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join(''); }
  function concat(a,b) { const out = new Uint8Array(a.length+b.length); out.set(a); out.set(b,a.length); return out; }

  async function start() {
    if (!pattern.test(needId) || !['telegram-bot-token','google-oauth-client'].includes(kind) || !/^[0-9a-f]{16}$/.test(expectedFp)) {
      fail('This link is incomplete. Open the latest need message again.'); return;
    }
    const response = await fetch('./drop-key.json?v='+expectedFp, {cache:'no-store'});
    if (!response.ok) throw new Error('key unavailable');
    const data = await response.json();
    const pub = decode64(data.public_key);
    const fp = hex(new Uint8Array(await crypto.subtle.digest('SHA-256',pub)));
    if (pub.length !== 32 || fp !== data.fingerprint || fp.slice(0,16) !== expectedFp ||
        data.issue_path !== true || data.issue_base !== repoIssue ||
        !/^[0-9a-f]{16}$/.test(data.key_id)) {
      fail('The lab key changed. Open the latest need message and use its link.'); return;
    }
    keyData = {pub, id:data.key_id};
    needText.textContent = 'Need '+needId.slice(-4)+' · '+(kind === 'telegram-bot-token' ? 'new Telegram bot token' : 'Google OAuth client');
    usernameLabel.hidden = kind !== 'telegram-bot-token';
    username.hidden = kind !== 'telegram-bot-token';
    form.hidden = false;
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    link.hidden = true; copyWrap.hidden = true;
    const secret = value.value.trim();
    const bot = username.value.trim().replace(/^@/,'');
    if (kind === 'telegram-bot-token' && (!/^\d{6,12}:[A-Za-z0-9_-]{30,50}$/.test(secret) || !/^[A-Za-z][A-Za-z0-9_]{4,31}_bot$/i.test(bot))) {
      fail('Check the bot token and username, then open the latest link again.'); return;
    }
    if (kind === 'google-oauth-client' && !/^GOCSPX-[A-Za-z0-9_-]{20,}$/.test(secret)) {
      fail('That does not look like a Google client secret.'); return;
    }
    try {
      const payload = {need_id:needId,kind,value:secret,username:bot,created_at:new Date().toISOString(),key_id:keyData.id};
      const ephemeral = nacl.box.keyPair();
      const nonce = blake2b(concat(ephemeral.publicKey,keyData.pub),null,24);
      const box = nacl.box(new TextEncoder().encode(JSON.stringify(payload)),nonce,keyData.pub,ephemeral.secretKey);
      const cipher = concat(ephemeral.publicKey,box);
      const body = 'BEGIN SMATSPRINT DROP v1\n'+encode64url(cipher)+'\nEND';
      value.value = ''; username.value = '';
      sealed.value = body;
      link.href = repoIssue+'?title='+encodeURIComponent('secret-drop '+needId)+'&body='+encodeURIComponent(body);
      link.hidden = false; copyWrap.hidden = false;
      status.textContent = 'Encrypted. Tap Submit encrypted issue, then Submit new issue on GitHub.';
      try { await navigator.clipboard.writeText(''); } catch (_) { /* best effort */ }
    } catch (_) { fail('Encryption failed. Reload the latest link and try again.'); }
  });
  document.getElementById('copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(sealed.value); status.textContent='Encrypted text copied. Clear your clipboard after submitting.'; }
    catch (_) { status.textContent='Select the encrypted text and copy it into the issue body.'; }
  });
  start().catch(() => fail('Could not check the lab key. Reload this page from the latest need message.'));
})();
