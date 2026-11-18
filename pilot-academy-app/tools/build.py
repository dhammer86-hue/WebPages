"""Build the hosted Pilot Academy files from the page Claude made in the artifact.

    python3 -I pilot-academy-app/tools/build.py pilot-academy-app/source/alex-pilot-academy.html

Save each new version of the artifact page over that source file first.

Run from the repository root. It writes:
  pilot-img/pN.jpg                    the museum pictures, moved out of the page
  pilot-academy-app/app.js, app.css   the app, loaded by both pages below
  pilot-academy-app/index.html        the small page pasted into Google Apps Script
  alex-math6-pilot-academy.html       the github.io link students open

Students can use the github.io link without signing in (progress stays on
the device). The Sign in button takes them to the Apps Script app, which
saves progress to their school account and merges in what was on the device.
"""
import base64, json, re, sys

SITE = 'https://dhammer86-hue.github.io/WebPages'
APP_URL = ('https://script.google.com/a/macros/cga.school/s/'
           'AKfycbzROeWNEUF1itw7WKoDnJCxLHgxmWeXtpHHNekOFsmCJodi0R2g9zjNbFZ6HDextM-Bkw/exec')
HOME_URL = SITE + '/alex-math6-pilot-academy.html'
FONTS = ('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600'
         '&family=Nunito:wght@600;700;800&display=swap')

t = open(sys.argv[1], encoding='utf-8').read()


def sub(old, new):
    global t
    assert t.count(old) == 1, 'The page changed here, so the build needs updating: ' + old[:70]
    t = t.replace(old, new)


# Museum pictures become files on the site, which keeps the app small.
lines = t.split('\n')
fi = next(i for i, l in enumerate(lines) if l.startswith('const FLEET='))
fleet = json.loads(lines[fi][len('const FLEET='):].rstrip(';'))
for key, p in fleet.items():
    m = re.match(r'data:image/jpeg;base64,(.+)$', p.get('img') or '')
    if m:
        open(f'pilot-img/{key}.jpg', 'wb').write(base64.b64decode(m.group(1)))
        p['img'] = f'{SITE}/pilot-img/{key}.jpg'
lines[fi] = 'const FLEET=' + json.dumps(fleet, ensure_ascii=False, separators=(',', ':')) + ';'
t = '\n'.join(lines)

# Work area: a tap with no movement still leaves a dot (or erases a spot).
sub('cv.addEventListener("pointerdown",e=>{down=true;[lx,ly]=pos(e);cv.setPointerCapture(e.pointerId);e.preventDefault();});',
    'cv.addEventListener("pointerdown",e=>{down=true;[lx,ly]=pos(e);cv.setPointerCapture(e.pointerId);e.preventDefault();'
    'ctx.globalCompositeOperation=erase?"destination-out":"source-over";ctx.fillStyle=color;'
    'ctx.beginPath();ctx.arc(lx,ly,(erase?26:3.5)/2,0,Math.PI*2);ctx.fill();});')

# Graded activities: no clock or suggested times on screen (they caused anxiety).
# Time is still recorded quietly and stays in the copied report for the teacher.
sub('<div class="timer" id="timer">${fmtTime(a.secs)}</div>', '')
sub('Suggested time: ${it.min} minutes${isHW?" | Points:', '${isHW?"Points:')
sub('" | Each question is worth 4 points. Show your work for partial credit."}', '"Each question is worth 4 points. Show your work for partial credit."}')
sub('<div class="meta">About ${it.min} minutes | ${esc(it.when)}</div>', '<div class="meta">${esc(it.when)}</div>')
sub('<div class="warn">About ${it.min} minutes. ${esc(rules)}', '<div class="warn">${esc(rules)}')
sub('<div class="tip">Time: about ${Math.max(1,Math.round(a.secs/60))} minutes (suggested ${it.min})</div>', '')

# Teacher resets are dated so an older copy on another device cannot bring the work back.
sub('delete S.a[b.dataset.r];save();', 'delete S.a[b.dataset.r];S.resetAt=Date.now();save();')
sub('S.p={};S.miles=0;S.drag=0;streak=0;save();', 'S.p={};S.miles=0;S.drag=0;streak=0;S.resetAt=Date.now();save();')

# Sign in or sign out button in the top bar.
sub('<div class="userchip"><span id="savestat"></span></div>',
    '<div class="userchip"><span id="savestat"></span>${acctButton()}</div>')

# Saving: the device always; the school account too when signed in.
sub('''function setStatus(t){const e=$("#savestat");if(e)e.textContent=t;}
function save(){
 S.updated=Date.now();
 try{localStorage.setItem(LS_KEY,JSON.stringify(S));setStatus("Saved in this browser");}catch(e){setStatus("Could not save in this browser");}
}''', '''const APP_URL=%s,HOME_URL=%s;
let CLOUD=false,WHO="",cloudT=null,cloudBusy=false,cloudAgain=false;
const localKey=()=>WHO?LS_KEY+":"+WHO:LS_KEY;
function setStatus(t){const e=$("#savestat");if(e)e.textContent=(WHO?WHO+" | ":"")+t;}
function acctButton(){
 if(CLOUD)return `<a class="acct ghost" href="${HOME_URL}#signout" target="_top" onclick="signOut()">Sign out</a>`;
 return `<a class="acct" href="${APP_URL}" onclick="return signIn()">Sign in to save to your account</a>`;
}
function signIn(){
 let u=APP_URL;
 try{localStorage.setItem("pilot:account","1");const s=localStorage.getItem(LS_KEY);if(s&&s.length<500000)u+="#import="+encodeURIComponent(btoa(unescape(encodeURIComponent(s))));}catch(e){}
 location.href=u;return false;
}
function signOut(){if(cloudT){clearTimeout(cloudT);pushCloud();}try{localStorage.removeItem(localKey());}catch(e){}return true;}
function save(){
 S.updated=Date.now();
 try{localStorage.setItem(localKey(),JSON.stringify(S));}catch(e){}
 if(CLOUD){setStatus("Saving...");clearTimeout(cloudT);cloudT=setTimeout(pushCloud,1500);}
 else setStatus("Saved on this device");
}
function pushCloud(){
 cloudT=null;
 if(cloudBusy){cloudAgain=true;return;}
 cloudBusy=true;
 google.script.run
  .withSuccessHandler(()=>{cloudBusy=false;setStatus("Saved to your account");if(cloudAgain){cloudAgain=false;pushCloud();}})
  .withFailureHandler(()=>{cloudBusy=false;cloudAgain=false;setStatus("Not saved yet. Check your internet connection.");clearTimeout(cloudT);cloudT=setTimeout(pushCloud,10000);})
  .saveProgress(JSON.stringify(S));
}''' % (json.dumps(APP_URL), json.dumps(HOME_URL)))
sub('function loadLocal(){try{const x=JSON.parse(localStorage.getItem(LS_KEY)||"null");',
    'function loadLocal(){try{const x=JSON.parse(localStorage.getItem(localKey())||"null");')

# Start: combine every copy of the progress so signing in never loses work.
sub('''window.addEventListener("beforeunload",()=>{try{localStorage.setItem(LS_KEY,JSON.stringify(S));}catch(e){}});

/* ===== start ===== */
const saved=loadLocal();if(saved)S=saved;
home();''', '''window.addEventListener("beforeunload",()=>{try{localStorage.setItem(localKey(),JSON.stringify(S));}catch(e){}if(CLOUD&&cloudT){clearTimeout(cloudT);pushCloud();}});

/* ===== start ===== */
function progressScore(a){if(!a)return -1;const n=o=>Object.keys(o||{}).length;return (a.submitted?1e9:0)+Object.keys(a.ok||{}).filter(k=>a.ok[k]).length*1e5+n(a.ans)*100+n(a.tries)+(a.secs||0)/1e7;}
function mergeProgress(list){
 list=list.filter(x=>x&&x.a);if(!list.length)return null;
 const reset=Math.max(0,...list.map(s=>s.resetAt||0));
 list=list.filter(s=>(s.updated||0)>=reset);
 list.sort((a,b)=>(b.updated||0)-(a.updated||0));
 const m=JSON.parse(JSON.stringify(list[0]));m.a={};m.p={};m.seen={};
 list.forEach(s=>{
  Object.keys(s.a||{}).forEach(id=>{if(progressScore(s.a[id])>progressScore(m.a[id]))m.a[id]=s.a[id];});
  Object.keys(s.p||{}).forEach(id=>{const c=m.p[id],n=s.p[id];m.p[id]=c?{done:!!(c.done||n.done),stars:Math.max(c.stars||0,n.stars||0)}:n;});
  Object.assign(m.seen,s.seen||{});
 });
 m.miles=Math.max(...list.map(s=>s.miles||0));m.drag=Math.max(...list.map(s=>s.drag||0));
 m.p=m.p||{};return m;
}
function boot(){
 CLOUD=!!(window.google&&google.script&&google.script.run);
 if(!CLOUD&&window.PILOT_SHELL&&(boot.waits=(boot.waits||0)+1)<30){setTimeout(boot,100);return;}
 if(!CLOUD){const saved=loadLocal();if(saved)S=saved;home();return;}
 app.innerHTML=topbar()+`<div class="card signin"><h2>Loading your progress...</h2></div>`;
 const fail=()=>{app.innerHTML=topbar()+`<div class="card signin"><h2>Could not load your progress</h2><p>Make sure you are signed in with your school Google account and connected to the internet, then try again.</p><div class="row" style="justify-content:center"><button id="retry">Try again</button></div></div>`;$("#retry").onclick=boot;};
 google.script.url.getLocation(loc=>{
  let carried=null;const m=/(?:^|&)import=([^&]+)/.exec(loc.hash||"");
  if(m){try{carried=JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(m[1])))));}catch(e){}try{google.script.history.replace(null,{},"");}catch(e){}}
  google.script.run.withSuccessHandler(res=>{
   WHO=res.email||"";let cloud=null;try{cloud=res.data?JSON.parse(res.data):null;}catch(e){}
   const merged=mergeProgress([cloud,loadLocal(),carried]);
   if(merged)S=merged;
   home();
  }).withFailureHandler(fail).getProgress();
 });
}
boot();''')

# Split into the shared stylesheet and script.
css = t[t.index('<style>') + 7:t.index('</style>')]
css += ('\n.acct{display:inline-block;padding:6px 14px;border-radius:12px;background:var(--accent);'
        'color:var(--accent-ink);font-weight:800;font-size:16px;text-decoration:none}'
        '\n.acct.ghost{background:transparent;color:var(--ink);border:3px solid var(--line)}\n')
js = t[t.index('<script>\n/* =====') + 8:t.rindex('</script>')]
open('pilot-academy-app/app.css', 'w', encoding='utf-8').write(css)
open('pilot-academy-app/app.js', 'w', encoding='utf-8').write(js)

LOADING = ('<div id="app"><p id="pilotmsg" style="text-align:center;margin-top:60px;font-size:20px;color:#4a5a75;'
           'background:#eef5fb;padding:20px;border-radius:12px">Loading Pilot Academy...</p></div>\n'
           '<div id="modal" hidden></div>')
PROBLEM = '''function pilotProblem(text) {
  var m = document.getElementById("pilotmsg");
  if (m) m.textContent = "Pilot Academy could not start. Please send this to your teacher: " + text;
}
window.addEventListener("error", function (e) { pilotProblem(e.message || "a file did not load"); });'''
APP_TAG = f'<script src="{SITE}/pilot-academy-app/app.js" onerror="pilotProblem(\'app.js did not load\')"></script>'

# The page pasted into Apps Script (signed in).
open('pilot-academy-app/index.html', 'w', encoding='utf-8').write(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<base target="_top">
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="{SITE}/pilot-academy-app/app.css">
</head>
<body style="font-family:system-ui,sans-serif">
{LOADING}
<script>
window.PILOT_SHELL = true;
{PROBLEM}
</script>
{APP_TAG}
</body>
</html>
''')

# The github.io page (no sign-in needed). Anyone who signed in before goes straight to their account.
open('alex-math6-pilot-academy.html', 'w', encoding='utf-8').write(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alex’s Pilot Academy: Math 6</title>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="{SITE}/pilot-academy-app/app.css">
</head>
<body style="font-family:system-ui,sans-serif">
{LOADING}
<script>
{PROBLEM}
(function () {{
  try {{
    // Before sign-in was optional this link always went to the account, so anyone with
    // progress saved here from back then keeps going to their account.
    var old = localStorage.getItem("m6t1:alex");
    if (location.hash === "#signout") {{
      localStorage.removeItem("pilot:account");
      localStorage.removeItem("m6t1:alex");
      history.replaceState(null, "", location.pathname);
    }} else if (!localStorage.getItem("pilot:v2") && old) {{
      localStorage.setItem("pilot:account", "1");
    }}
    localStorage.setItem("pilot:v2", "1");
    if (localStorage.getItem("pilot:account") === "1") {{
      var u = {json.dumps(APP_URL)}, s = localStorage.getItem("m6t1:alex");
      if (s && s.length < 500000) u += "#import=" + encodeURIComponent(btoa(unescape(encodeURIComponent(s))));
      window.PILOT_LEAVING = true;
      location.replace(u);
    }}
  }} catch (e) {{}}
}})();
</script>
<script>if (!window.PILOT_LEAVING) document.write({json.dumps(APP_TAG).replace('</', '<\\/')});</script>
</body>
</html>
''')
print('built: pictures', sum(1 for p in fleet.values() if (p.get('img') or '').startswith('http')),
      '| app.js', len(js.encode()), 'bytes')
