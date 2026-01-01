import os
import json
import urllib.request
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)
STORAGE_DIR = 'saved_itineraries'

# Ensure storage directory exists
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# --- Injection Content ---

HTML_INJECTION = """
    <!-- Added Save/Load Functionality -->
    <div style="background:#eef; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #ccd;">
        <h4 style="margin-top:0; color:#333;">💾 Save / Load Project</h4>
        <div class="row">
            <div class="col">
                <label style="font-weight:bold; font-size:0.9rem;">Project Name</label>
                <input type="text" id="projectFilename" placeholder="e.g. Thailand_Trip_Draft">
            </div>
            <div class="col" style="align-self:end;">
                <button type="button" class="btn" style="background:#27ae60;" onclick="saveProject()">Save Project</button>
            </div>
        </div>
        <div class="row" style="margin-top:10px;">
            <div class="col">
                <label style="font-weight:bold; font-size:0.9rem;">Load Existing</label>
                <select id="savedProjectsList" style="width:100%; padding:9px;">
                    <option value="">Select a saved project...</option>
                </select>
            </div>
            <div class="col" style="align-self:end;">
                <button type="button" class="btn secondary" onclick="loadProject()">Load Project</button>
                <button type="button" class="btn secondary" onclick="refreshProjectList()">Refresh List</button>
            </div>
        </div>
        <div id="statusMsg" style="margin-top:10px; font-weight:bold;"></div>
    </div>
    <!-- End Save/Load Functionality -->
"""

JS_INJECTION = """
<script>
// --- Save / Load Logic (Injected) ---

function showStatus(msg, isErr=false){
  const el = document.getElementById('statusMsg');
  if(el){
    el.textContent = msg;
    el.style.color = isErr ? 'red' : 'green';
    setTimeout(()=> el.textContent='', 3000);
  } else {
    console.log(msg);
  }
}

async function saveProject(){
  const filename = document.getElementById('projectFilename').value;
  if(!filename){ showStatus("Please enter a project name.", true); return; }

  const form = document.getElementById('tourForm');
  const fd = new FormData(form);
  const data = {};
  fd.forEach((v,k)=> data[k]=v);
  
  // Add filename to payload
  const payload = {
      filename: filename,
      data: data
  };

  try{
    const res = await fetch('/api/save', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload)
    });
    const result = await res.json();
    if(result.success){
        showStatus("Project saved successfully!");
        refreshProjectList();
    } else {
        showStatus("Error: "+result.message, true);
    }
  } catch(e){ showStatus("Network Error: "+e, true); }
}

async function refreshProjectList(){
  try{
    const res = await fetch('/api/list');
    const result = await res.json();
    const sel = document.getElementById('savedProjectsList');
    if(sel){
        sel.innerHTML = '<option value="">Select a saved project...</option>';
        if(result.files){
            result.files.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                sel.appendChild(opt);
            });
        }
    }
  } catch(e){ console.error(e); }
}

async function loadProject(){
  const filename = document.getElementById('savedProjectsList').value;
  if(!filename){ showStatus("Select a file first.", true); return; }

  try{
    const res = await fetch('/api/load/'+filename);
    const json = await res.json();
    
    // Check if wrapped in data.data (based on save structure) or root
    const formData = json.data || json; 

    // 1. Restore Counts and Triggers
    if(formData.numDays){
        const el = document.getElementById('numDays');
        if(el) { el.value = formData.numDays; }
        if(typeof generateDayForms === 'function') generateDayForms(parseInt(formData.numDays));
    }
    if(formData.numHotels){
        const el = document.getElementById('numHotels');
        if(el) { el.value = formData.numHotels; }
        if(typeof generateHotelForms === 'function') generateHotelForms(parseInt(formData.numHotels));
    }
    if(formData.numFlights){
        const el = document.getElementById('numFlights');
        if(el) { el.value = formData.numFlights; }
        // original HTML v2 seems to imply separate functions or reuse
        if(typeof generateFlightForms === 'function') generateFlightForms(parseInt(formData.numFlights));
    }
    if(formData.numTrains){
        const el = document.getElementById('numTrains');
        if(el) { el.value = formData.numTrains; }
        if(typeof generateTrainForms === 'function') generateTrainForms(parseInt(formData.numTrains));
    }
    
    // 2. Populate all fields
    const form = document.getElementById('tourForm');
    Object.keys(formData).forEach(key => {
        const field = form.elements[key];
        if(field){
            if(field.type === 'checkbox'){
                field.checked = !!formData[key];
            } else {
                field.value = formData[key];
            }
        }
    });

    // Restore Project Name
    const pName = document.getElementById('projectFilename');
    if(pName) pName.value = json.filename ? json.filename.replace('.json','') : filename.replace('.json','');
    
    showStatus("Project loaded!");
    
  } catch(e){ showStatus("Error loading: "+e, true); }
}


// Init & Fixes
document.addEventListener('DOMContentLoaded', () => {
    refreshProjectList();
    
    // --- Fix: Ensure Day Generation Trigger Works ---
    // The user reported issues with days not populating. 
    // We re-attach the listener to ensure it works even if the original script had issues.
    const ndInput = document.querySelector('[name="numDays"]');
    if(ndInput){
        const triggerGen = () => {
             // Check global scope for the original function
             if(typeof generateDayForms === 'function'){
                 generateDayForms(parseInt(ndInput.value)||1);
             }
             if(typeof autoFillDates === 'function'){
                 autoFillDates();
             }
        };


        // Attach to both change and input to be robust
        ndInput.addEventListener('change', triggerGen);
        ndInput.addEventListener('input', triggerGen);
        
        // Also run once to ensure state is correct
        triggerGen();
    }

    // --- Fix: Ensure Start Date Triggers Auto-Fill ---
    const startDateInput = document.getElementById('startDate');
    if(startDateInput){
        startDateInput.addEventListener('change', () => {
             // Debug log
            console.log("Start date changed, calling autoFillDates");
            if(typeof autoFillDates === 'function') autoFillDates();
        });
    }

    // --- Fix: Ensure Hotel/Flight/Train Generation Works ---
    const fixBtn = (id, funcName, inputId) => {
        const btn = document.getElementById(id);
        const inp = document.getElementById(inputId);
        if(btn && inp){
            btn.addEventListener('click', () => {
                if(typeof window[funcName] === 'function'){
                    window[funcName](parseInt(inp.value)||0);
                } else {
                    console.log("Function not found: " + funcName);
                    // Fallback: try eval (dangerous, but original var might be global)
                    try { eval(funcName + "(" + (parseInt(inp.value)||0) + ")"); } catch(e){}
                }
            });
        }
    };
    
    fixBtn('genHotelsBtn', 'generateHotelForms', 'numHotels');
    fixBtn('genFlightsBtn', 'generateFlightForms', 'numFlights');
    fixBtn('genTrainsBtn', 'generateTrainForms', 'numTrains');
});
</script>
"""

@app.route('/')
def index():
    github_url = "https://raw.githubusercontent.com/pratikparshetti/happyholidayz/main/generator/tour-generator-yellow-finalv2.html"
    try:
        # Fetch fresh content from GitHub
        with urllib.request.urlopen(github_url) as response:
            html_content = response.read().decode('utf-8')
        
        # Inject HTML (Before '<h3>Customer Details</h3>')
        target_str = '<h3>Customer Details</h3>'
        if target_str in html_content:
            html_content = html_content.replace(target_str, HTML_INJECTION + target_str)
        
        # Inject JS (At the end of body) - careful to replace only the LAST </body> 
        # because the user's JS contains "</body>" in a string literal.
        if '</body>' in html_content:
            parts = html_content.rpartition('</body>')
            html_content = parts[0] + JS_INJECTION + '</body>' + parts[2]
        
        return make_response(html_content)
        
    except Exception as e:
        return f"<h1>Error fetching remote template</h1><p>{str(e)}</p>", 500

@app.route('/api/save', methods=['POST'])
def save_itinerary():
    try:
        data = request.json
        filename = data.get('filename')
        if not filename:
             filename = f"itinerary_{data.get('destination', 'draft')}.json"
        
        # Basic sanitization
        filename = os.path.basename(filename)
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = os.path.join(STORAGE_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        
        return jsonify({"success": True, "message": "Itinerary saved successfully!", "filename": filename})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/list', methods=['GET'])
def list_itineraries():
    try:
        files = [f for f in os.listdir(STORAGE_DIR) if f.endswith('.json')]
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/load/<filename>', methods=['GET'])
def load_itinerary(filename):
    try:
        filename = os.path.basename(filename)
        filepath = os.path.join(STORAGE_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"success": False, "message": "File not found"}), 404
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        return jsonify(data)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
