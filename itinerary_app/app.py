import os
import json
import urllib.request
from flask import Flask, render_template, request, jsonify, make_response
import google.generativeai as genai
from datetime import datetime, timedelta

# Helper to load configuration from startup.bat or .env file
def load_env_config():
    # 1. Parse startup.bat for set GEMINI_API_KEY=...
    startup_bat = os.path.join(os.path.dirname(__file__), 'startup.bat')
    if os.path.exists(startup_bat):
        try:
            with open(startup_bat, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.lower().startswith(('rem', '::')):
                        if 'GEMINI_API_KEY' in line and '=' in line:
                            if line.lower().startswith('set '):
                                line = line[4:].strip()
                            k, v = line.split('=', 1)
                            key_name = k.strip().strip('"\'')
                            val_name = v.strip().strip('"\'')
                            if key_name == 'GEMINI_API_KEY' and val_name and not val_name.startswith('AIzaSy...'):
                                os.environ['GEMINI_API_KEY'] = val_name
                                break
        except Exception as e:
            print(f"Warning: Failed to parse startup.bat: {e}")

    # 2. Fallback to .env file if present
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        key_name = k.strip()
                        val_name = v.strip().strip('"\'')
                        if (key_name not in os.environ or not os.environ[key_name]) and val_name:
                            os.environ[key_name] = val_name
        except Exception as e:
            print(f"Warning: Failed to parse .env file: {e}")

load_env_config()

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

def repair_truncated_json(s: str) -> str:
    """Attempts to repair truncated JSON strings by closing open quotes, lists, and objects."""
    s = s.strip()
    if not s:
        return s

    in_string = False
    escaped = False
    new_chars = []
    
    for char in s:
        if escaped:
            escaped = False
            new_chars.append(char)
            continue
        if char == '\\':
            escaped = True
            new_chars.append(char)
            continue
        if char == '"':
            in_string = not in_string
        new_chars.append(char)
        
    fixed_s = "".join(new_chars)
    if in_string:
        fixed_s += '"'
        
    fixed_s = re.sub(r',\s*([}\]])', r'\1', fixed_s)

    stack = []
    in_str = False
    esc = False
    
    for char in fixed_s:
        if esc:
            esc = False
            continue
        if char == '\\':
            esc = True
            continue
        if char == '"':
            in_str = not in_str
            continue
        if not in_str:
            if char in '{[':
                stack.append(char)
            elif char == '}':
                if stack and stack[-1] == '{':
                    stack.pop()
            elif char == ']':
                if stack and stack[-1] == '[':
                    stack.pop()
                    
    for open_char in reversed(stack):
        if open_char == '{':
            fixed_s += '}'
        elif open_char == '[':
            fixed_s += ']'
            
    return fixed_s

def robust_json_parse(text: str) -> dict:
    """Robustly extracts and parses JSON even if wrapped in markdown or truncated by model max tokens."""
    if not text or not text.strip():
        raise ValueError("Empty response received from AI model.")
        
    cleaned = re.sub(r'```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'```', '', cleaned).strip()
    
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace+1]
    elif first_brace != -1:
        candidate = cleaned[first_brace:]
    else:
        candidate = cleaned

    candidate_cleaned = re.sub(r',\s*([}\]])', r'\1', candidate)
    
    try:
        return json.loads(candidate_cleaned)
    except json.JSONDecodeError:
        pass
        
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
        
    repaired = repair_truncated_json(candidate)
    repaired_cleaned = re.sub(r',\s*([}\]])', r'\1', repaired)
    
    try:
        return json.loads(repaired_cleaned)
    except json.JSONDecodeError:
        pass
        
    cleaned_ctrl = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', repaired_cleaned)
    return json.loads(cleaned_ctrl)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_itinerary():
    try:
        data = request.json or {}
        destination = data.get('destination')
        days = int(data.get('days', 3))
        
        # Refresh environment configuration from startup.bat or .env
        load_env_config()
        api_key = os.getenv('GEMINI_API_KEY', '').strip()
        
        if not destination:
            return jsonify({"success": False, "message": "Destination is required"}), 400

        if not api_key or api_key == "your_gemini_api_key_here":
            return jsonify({
                "success": False, 
                "message": "GEMINI_API_KEY is not set. Please set your key in startup.bat (e.g. set GEMINI_API_KEY=your_key) or .env file."
            }), 400
        
        if len(api_key) < 10:
            return jsonify({
                "success": False, 
                "message": "The key provided appears to be invalid or incomplete. Please check GEMINI_API_KEY in startup.bat."
            }), 400

        genai.configure(api_key=api_key)

        prompt = f"""
        Generate a comprehensive {days}-day travel itinerary for {destination}. 
        Return ONLY valid JSON in the following format:
        
        {{
            "tourName": "Creative Tour Name for {destination}",
            "overview": "A brief 2-3 sentence overview of the trip.",
            "inclusions": "Comprehensive list of 5-8 inclusions separated by semicolons (e.g. 3 Star Hotel Accommodation; Daily Breakfast; Airport Transfers; English Speaking Guide; All Entry Fees; GST; Taxes)",
            "exclusions": "Comprehensive list of 5-8 exclusions separated by semicolons (e.g. International Flights; Visa Fees; Travel Insurance; Personal Expenses like laundry/tips; Lunch and Dinner; Optional Tours; Early Check-in)",
            "days": [
                {{
                    "title": "Title ONLY (e.g. Arrival & City Tour). Do NOT include 'Day 1' prefix.",
                    "description": "Detailed activities for the day."
                }}
            ]
        }}
        
        IMPORTANT CRITICAL RULES:
        - Must generate exactly {days} day items inside the "days" array.
        - Ensure every string property is properly closed with quotes.
        - Do not include markdown formatting like ```json or ```. Just raw JSON.
        """
        
        models_to_try = [
            'gemini-3.6-flash', 
            'gemini-3.5-flash', 
            'gemini-flash-latest', 
            'gemini-3.1-pro-preview', 
            'gemini-2.5-flash'
        ]
        response = None
        last_err = None
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=8192
                    ),
                    request_options={"timeout": 35}
                )
                if response and hasattr(response, 'text'):
                    break
            except Exception as e:
                last_err = e
                err_msg = str(e)
                # Catch auth/permission error immediately to prevent long retry hang loops
                if any(tok in err_msg.lower() for tok in ["401", "400", "403", "api_key_invalid", "unauthenticated", "permission_denied"]):
                    return jsonify({
                        "success": False,
                        "message": f"Gemini API Auth Error: {err_msg}"
                    }), 400
                continue

        if not response or not hasattr(response, 'text'):
            raise last_err or Exception("Failed to generate content with available models.")

        text = response.text.strip()
        itinerary_data = robust_json_parse(text)
        return jsonify({"success": True, "data": itinerary_data})

    except Exception as e:
        print(f"Error generating itinerary: {e}")
        err_str = str(e)
        if "401" in err_str or "Unauthenticated" in err_str or "API_KEY_INVALID" in err_str or "invalid authentication" in err_str.lower():
            return jsonify({"success": False, "message": "Authentication failed: Invalid Gemini API Key."}), 401
        return jsonify({"success": False, "message": f"Failed to parse AI output: {err_str}"}), 500

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
