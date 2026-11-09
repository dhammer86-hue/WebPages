/**
 * Pilot Academy: saves each student's progress to the "Progress" tab of the
 * Google Sheet this script is attached to, one row per school Google account.
 *
 * Deploy as a web app with "Execute as: Me" and "Who has access: Anyone
 * within" your school, so only signed-in school accounts can open it and
 * each student can only read and write their own row.
 */

const SHEET_NAME = 'Progress';
const CHUNK = 45000; // a Sheets cell holds up to 50,000 characters

function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('Alex’s Pilot Academy: Math 6')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function currentEmail_() {
  const email = Session.getActiveUser().getEmail();
  if (!email) throw new Error('Not signed in with a school Google account.');
  return email.toLowerCase();
}

function sheet_() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(['Student email', 'Last saved', 'Progress data (do not edit)']);
    sh.setFrozenRows(1);
  }
  return sh;
}

function findRow_(sh, email) {
  const last = sh.getLastRow();
  if (last < 2) return 0;
  const emails = sh.getRange(2, 1, last - 1, 1).getValues();
  for (let i = 0; i < emails.length; i++) {
    if (String(emails[i][0]).toLowerCase() === email) return i + 2;
  }
  return 0;
}

function getProgress() {
  const email = currentEmail_();
  const sh = sheet_();
  const row = findRow_(sh, email);
  let data = null;
  if (row && sh.getLastColumn() >= 3) {
    // Each piece is stored with a leading "~" so Sheets never reads it as a number or formula.
    const parts = sh.getRange(row, 3, 1, sh.getLastColumn() - 2).getDisplayValues()[0];
    const json = parts.filter(String).map(p => p.replace(/^~/, '')).join('');
    if (json) data = json;
  }
  return { email: email, data: data };
}

function saveProgress(json) {
  const email = currentEmail_();
  if (typeof json !== 'string' || json.length > 2000000) throw new Error('Progress data is not valid.');
  JSON.parse(json);
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sh = sheet_();
    const row = findRow_(sh, email) || sh.getLastRow() + 1;
    const parts = [];
    for (let i = 0; i < json.length; i += CHUNK) parts.push('~' + json.slice(i, i + CHUNK));
    const width = Math.max(sh.getLastColumn(), parts.length + 2);
    const values = [email, new Date()].concat(parts);
    while (values.length < width) values.push('');
    const range = sh.getRange(row, 1, 1, width);
    sh.getRange(row, 3, 1, width - 2).setNumberFormat('@');
    range.setValues([values]);
  } finally {
    lock.releaseLock();
  }
  return true;
}
