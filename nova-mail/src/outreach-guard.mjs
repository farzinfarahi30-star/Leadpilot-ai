// Read-only pre-send verification. Gmail is the source of truth for known
// outbound history; no credentials, recipients or private history are committed.
const COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000;
const LABEL_HOLD = /(?:declined|do[ -]?not[ -]?follow|do[ -]?not[ -]?pitch|outreach hold|pause outreach|await(?:ing)? (?:buyer )?reply|do[ -]?not[ -]?contact|no (?:further|more) follow[ -]?ups?|opt[ -]?out|unsubscribe)/i;
const pending = new Set();

export function outreachRecipients(input = {}) {
  return [...new Set([input.to, input.cc, input.bcc].filter(Boolean)
    .flatMap(v => String(v).split(','))
    .map(v => v.trim().replace(/^.*<([^<>]+)>$/, '$1').toLowerCase())
    .filter(Boolean))];
}

export function reserveOutreachRecipients(recipients) {
  if (recipients.some(address => pending.has(address))) return null;
  recipients.forEach(address => pending.add(address));
  return () => recipients.forEach(address => pending.delete(address));
}

export function assessOutreachHistory({latestSent, latestInbound, heldLabels = []}, now = Date.now()) {
  if (heldLabels.length) return {allowed:false, reason:'recipient has an outreach hold or decline label', labels:heldLabels};
  if (latestSent && Number(latestSent) > now - COOLDOWN_MS &&
      (!latestInbound || Number(latestInbound) <= Number(latestSent))) {
    return {allowed:false, reason:'outgoing message within 7 days without a newer inbound reply'};
  }
  return {allowed:true};
}

async function searchLatest(gmail, query) {
  const found = await gmail('messages?maxResults=1&q=' + encodeURIComponent(query));
  const id = found.messages?.[0]?.id;
  if (!id) return null;
  return gmail('messages/' + encodeURIComponent(id) + '?format=metadata');
}

export async function preflightOutreach(input, gmail, now = Date.now()) {
  const recipients = outreachRecipients(input);
  if (recipients.length !== 1 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipients[0])) {
    return {allowed:false, reason:'outreach must have exactly one valid recipient (including cc/bcc)'};
  }
  const address = recipients[0];
  const labels = await gmail('labels');
  const labelNames = new Map((labels.labels || []).map(label => [label.id, label.name]));
  // The list API returns messages newest first. Timestamps come from metadata.
  const [sent, inbound] = await Promise.all([
    searchLatest(gmail, 'in:sent to:' + address),
    searchLatest(gmail, 'from:' + address)
  ]);
  // A decline can live on an older message rather than the latest reply or
  // latest sent item. Search all labelled history before allowing outreach.
  const holdEntries = (labels.labels || []).filter(label => LABEL_HOLD.test(label.name || ''));
  const matches = await Promise.all(holdEntries.map(label =>
    gmail('messages?maxResults=1&labelIds=' + encodeURIComponent(label.id) +
      '&q=' + encodeURIComponent('{from:' + address + ' to:' + address + '}'))
  ));
  const heldLabels = [...new Set([
    ...[...(sent?.labelIds || []), ...(inbound?.labelIds || [])]
      .map(id => labelNames.get(id)).filter(name => name && LABEL_HOLD.test(name)),
    ...holdEntries.filter((label, i) => (matches[i]?.messages || []).length > 0)
      .map(label => label.name)
  ])];
  return {...assessOutreachHistory({latestSent:sent?.internalDate,
    latestInbound:inbound?.internalDate, heldLabels}, now), recipient:address};
}
