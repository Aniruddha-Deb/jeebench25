import os
import csv
from flask import Flask, request, jsonify, send_from_directory, abort

# -------------------------------------------------
# Configuration
# -------------------------------------------------
PAPER_NUM = 2
DATA_DIR  = "dataset"
DATA_FILE = f"{DATA_DIR}/jeea25_p{PAPER_NUM}.csv"
IMAGE_DIR = f"{DATA_DIR}/images"
PORT       = 5000

os.makedirs(IMAGE_DIR, exist_ok=True)

# -------------------------------------------------
# Helpers – CSV handling
# -------------------------------------------------

def load_dataset():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"{DATA_FILE} not found – create it or rename your file.")
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save_dataset(rows):
    if not rows:
        return
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)

rows = load_dataset()

# -------------------------------------------------
# Flask app
# -------------------------------------------------
app = Flask(__name__, static_folder="static", static_url_path="/static")

# -------------------------------------------------
# HTML / JS UI
# -------------------------------------------------
INDEX_HTML = r"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>Dataset Annotator</title>
<meta name='viewport' content='width=device-width,initial-scale=1'>

<!-- Markdown parser -->
<script src='https://cdn.jsdelivr.net/npm/marked/marked.min.js'></script>
<!-- MathJax 3 for LaTeX rendering -->
<script>
  window.MathJax = {
    tex: { inlineMath: [['$', '$'], ['\\(', '\\)']] },
    svg: { fontCache: 'global' }
  };
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

<!--<style>
 :root{ --gap:.75rem; --border:#d0d0d0; }
 *{box-sizing:border-box;}
 body,html{height:100%;margin:0;font-family:system-ui,sans-serif;}
 body{display:flex;flex-direction:column;}
 header{display:flex;align-items:center;gap:var(--gap);padding:var(--gap);border-bottom:1px solid var(--border);} 
 header select,header button,header input{font-size:1rem;padding:.25rem .5rem;}
 header label{display:flex;align-items:center;gap:.25rem;}
 #main{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);padding:var(--gap);} 
 textarea{width:100%;height:100%;resize:vertical;font:inherit;padding:.5rem;border:1px solid var(--border);border-radius:4px;}
 .preview{border:1px solid var(--border);padding:.5rem;overflow:auto;border-radius:4px;}
 #optWrap{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--gap);height:7rem;}
 #optWrap>.field{display:flex;flex-direction:column;gap:.25rem;}
 #optWrap textarea{height:4rem;}
 #optPreview{display:grid;grid-template-columns:repeat(2,1fr);grid-template-rows:repeat(2,1fr);gap:var(--gap);height:100%;}
 #dropzone{border:2px dashed var(--border);border-radius:4px;text-align:center;padding:1rem;margin-top:var(--gap);color:#666;}
 @media(max-width:900px){#main{grid-template-columns:1fr;grid-template-rows:auto auto;}}
</style>-->

<style>
 :root{ --gap:.75rem; --border:#d0d0d0; }
 *{box-sizing:border-box;}
 body,html{height:100%;margin:0;font-family:system-ui,sans-serif;}
 body{display:flex;flex-direction:column;}
 header{display:flex;align-items:center;gap:var(--gap);padding:var(--gap);border-bottom:1px solid var(--border);} 
 header select,header button,header input{font-size:1rem;padding:.25rem .5rem;}
 header label{display:flex;align-items:center;gap:.25rem;}
 #main{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);padding:var(--gap);} 
 textarea{width:100%;resize:vertical;font:inherit;padding:.5rem;border:1px solid var(--border);border-radius:4px;}
 .preview{border:1px solid var(--border);padding:.5rem;overflow:auto;border-radius:4px;background:#fff;}
 #optWrap{display:grid;grid-template-columns:1fr;gap:var(--gap);}
 #optWrap>.field{display:flex;flex-direction:column;gap:.25rem;}
 #optWrap textarea{height:4rem;}
 #optPreview{display:flex;flex-direction:column;gap:var(--gap);flex:1;}
 #optPreview .preview{flex:1;min-height:4rem;}
 #dropzone{border:2px dashed var(--border);border-radius:4px;text-align:center;padding:1rem;margin-top:var(--gap);color:#666;}
 @media(max-width:900px){#main{grid-template-columns:1fr;grid-template-rows:auto auto;}}
</style>
</head>
<body>
<header>
    <button id='prevBtn'>&larr;</button>
    <select id='qSelect'></select>
    <button id='nextBtn'>&rarr;</button>

    <label>Type
        <select id='typeSelect'>
            <option>SCA</option><option>MCA</option><option>NT</option><option>M</option>
        </select>
    </label>

    <label>Answer <input id='answerInput' style='width:8rem'></label>
    <button id='saveBtn'>Save (Ctrl+S)</button>
</header>

<div id='main'>
    <div style='display:flex;flex-direction:column;gap:var(--gap);height:100%;'>
        <textarea id='questionText' placeholder='Question markdown...' style='flex:1'></textarea>
        <div id='optWrap'>
            <div class='field'><b>A</b><textarea id='optA'></textarea></div>
            <div class='field'><b>B</b><textarea id='optB'></textarea></div>
            <div class='field'><b>C</b><textarea id='optC'></textarea></div>
            <div class='field'><b>D</b><textarea id='optD'></textarea></div>
        </div>
        <div id='dropzone'>Drag images here (they'll auto‑insert)</div>
    </div>

    <div style='display:flex;flex-direction:column;gap:var(--gap);height:100%;'>
        <div class='preview' id='questionPreview' style='flex:1'></div>
        <div id='optPreview'>
            <div class='preview' id='optAPrev'></div>
            <div class='preview' id='optBPrev'></div>
            <div class='preview' id='optCPrev'></div>
            <div class='preview' id='optDPrev'></div>
        </div>
    </div>
</div>

<script>
let qData=[],cur=0;
const $=id=>document.getElementById(id);
const md=txt=>marked.parse(txt||"");

function typeset(elList){
  if(window.MathJax){ MathJax.typesetPromise(elList).catch(console.error); }
}

// Load dataset & populate dropdown
fetch('/questions').then(r=>r.json()).then(d=>{
  qData=d;
  const sel=$('qSelect');
  d.forEach((q,i)=>{
    const o=document.createElement('option');
    o.value=i; o.textContent=`#${q.num} – ${q.subject||''}`; sel.appendChild(o);
  });
  open(0);
});

function open(i){
  cur=i; $('qSelect').value=i;
  const q=qData[i];
  $('typeSelect').value=q.type||'SCA'; $('answerInput').value=q.ans||''; $('questionText').value=q.text||'';
  ['A','B','C','D'].forEach(l=>$("opt"+l).value=q["opt"+l]||'');
  handleTypeVis(); renderPreview();
}

function renderPreview(){
  $('questionPreview').innerHTML=md($('questionText').value);
  ['A','B','C','D'].forEach(l=>$("opt"+l+'Prev').innerHTML=md($("opt"+l).value));
  // Queue MathJax
  typeset([$ ('questionPreview'), $('optAPrev'), $('optBPrev'), $('optCPrev'), $('optDPrev')]);
}

['questionText','optA','optB','optC','optD'].forEach(id=>$(id).addEventListener('input',renderPreview));
$('typeSelect').addEventListener('change',handleTypeVis);
function handleTypeVis(){
  const hide=$('typeSelect').value==='NT';
  $('optWrap').style.display=hide?'none':'grid';
  $('optPreview').style.display=hide?'none':'grid';
}

function collect(){
  const q={...qData[cur]};
  q.type=$('typeSelect').value.trim();
  q.text=$('questionText').value.trim();
  q.optA=$('optA').value.trim(); q.optB=$('optB').value.trim(); q.optC=$('optC').value.trim(); q.optD=$('optD').value.trim();
  q.ans=$('answerInput').value.trim();
  return q;
}

function save(cb){
  fetch(`/save_question/${cur}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(collect())})
    .then(r=>{if(!r.ok) alert('Save failed'); else { qData[cur]=collect(); cb&&cb(); }});
}
$('saveBtn').onclick=()=>save();
document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='s'){e.preventDefault();save();}});

$('qSelect').onchange=()=>{save(()=>open(parseInt($('qSelect').value)));};
$('prevBtn').onclick=()=>{ if(cur>0) save(()=>open(cur-1)); };
$('nextBtn').onclick=()=>{ if(cur<qData.length-1) save(()=>open(cur+1)); };

// Drag‑and‑drop images
const dz=$('dropzone');
dz.ondragover=e=>{e.preventDefault(); dz.style.background='#f7f7f7';};
dz.ondragleave=()=>{dz.style.background='';};
dz.ondrop=e=>{
  e.preventDefault(); dz.style.background='';
  [...e.dataTransfer.files].forEach(f=>{
    const fd=new FormData(); 
    fd.append('file',f); 
    fd.append('qnum',qData[cur].num); 
    fd.append('subject',qData[cur].subject);
    fetch('/upload_image',{method:'POST',body:fd}).then(r=>r.json()).then(j=>{
      $('questionText').value += `\n\n![](${j.path})\n`; renderPreview();
    });
  });
};
</script>
</body>
</html>"""

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route('/')
def root():
    return INDEX_HTML

@app.route('/questions')
def questions():
    return jsonify(rows)

@app.route('/save_question/<int:index>', methods=['POST'])
def save_question(index):
    if not (0 <= index < len(rows)):
        abort(404)
    rows[index] = request.json
    save_dataset(rows)
    return ('',204)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        abort(400,'file missing')
    f=request.files['file']
    qnum=request.form.get('qnum','unk')
    subject=request.form.get('subject','unknown')
    ext=os.path.splitext(f.filename)[1] or '.png'
    name=f"jeea25_p{PAPER_NUM}_{subject}_q{qnum}_{len(os.listdir(IMAGE_DIR))+1}{ext}"
    dest=os.path.join(IMAGE_DIR,name)
    f.save(dest)
    return jsonify({"path":f"/images/{name}"})

@app.route('/images/<path:fn>')
def serve_img(fn):
    return send_from_directory(IMAGE_DIR,fn)

# -------------------------------------------------
if __name__ == '__main__':
    print(f"⚡ running on http://127.0.0.1:{PORT}")
    app.run(debug=True,port=PORT)

