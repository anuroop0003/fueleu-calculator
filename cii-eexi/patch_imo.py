import re

with open('/home/anuroop-tm/Personal/fueleu-calculator/cii-eexi/imo-dcs-cii-verification-tool.html', 'r') as f:
    content = f.read()

# 1. Add getXMLString() function
export_xml_func = """function exportXML(){
  const g=id=>{const e=document.getElementById(id);return e?e.value:'';};
  const lines=['<?xml version="1.0" encoding="UTF-8"?>','<IMO_DCS_CII_Data version="1.0">'];

  // ── Ship Particulars ──"""

new_export_xml = """function getXMLString(){
  const g=id=>{const e=document.getElementById(id);return e?e.value:'';};
  const lines=['<?xml version="1.0" encoding="UTF-8"?>','<IMO_DCS_CII_Data version="1.0">'];

  // ── Ship Particulars ──"""

content = content.replace(export_xml_func, new_export_xml)

export_xml_end = """  lines.push(...collectCorrectionFactorCardStatesXML());

  lines.push('</IMO_DCS_CII_Data>');

  const blob=new Blob([lines.join('\\n')],{type:'application/xml'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  const vessel=(document.getElementById('vesselName')?.value||'vessel').replace(/\\s+/g,'_');
  const yr=document.getElementById('reportingYear')?.value||new Date().getFullYear();
  a.download=`${vessel}_CII_${yr}.xml`;
  a.click();
  URL.revokeObjectURL(a.href);
  showToast('✓ XML exported successfully');
}"""

new_export_xml_end = """  lines.push(...collectCorrectionFactorCardStatesXML());

  lines.push('</IMO_DCS_CII_Data>');
  return lines.join('\\n');
}

function exportXML(){
  const xmlStr = getXMLString();
  const blob=new Blob([xmlStr],{type:'application/xml'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  const vessel=(document.getElementById('vesselName')?.value||'vessel').replace(/\\s+/g,'_');
  const yr=document.getElementById('reportingYear')?.value||new Date().getFullYear();
  a.download=`${vessel}_CII_${yr}.xml`;
  a.click();
  URL.revokeObjectURL(a.href);
  showToast('✓ XML exported successfully');
}"""

content = content.replace(export_xml_end, new_export_xml_end)

# 2. Inject Load from Cloud button in Ship Particulars
ship_part_start = """    <div style="display:flex;gap:8px;align-items:center">
      <button class="btn btn-secondary" onclick="importXMLFile()" title="Import all tab data from a previously exported XML file" style="background:#1a5276;color:#fff;border-color:#1a5276">⬆ Import XML</button>"""

new_ship_part_start = """    <div style="display:flex;gap:8px;align-items:center">
      <button class="btn btn-secondary btn-cloud-sync" onclick="window.openCloudModal()" style="border-color:var(--teal);display:none;align-items:center;gap:6px">☁ Load from Cloud</button>
      <div id="userInfo" style="display:none;align-items:center;gap:8px;margin-right:12px">
        <img id="userAvatar" src="" style="width:28px;height:28px;border-radius:50%">
        <span id="userName" style="font-size:13px;font-weight:600;color:var(--navy)"></span>
        <button class="btn btn-secondary btn-sm" onclick="handleSignOut()" style="padding:4px 8px;font-size:11px">Sign Out</button>
      </div>
      <button class="btn btn-secondary" id="btnGoogleSignIn" onclick="handleGoogleSignIn()" style="display:inline-flex;align-items:center;gap:6px">Google Sign In</button>
      <button class="btn btn-secondary" onclick="importXMLFile()" title="Import all tab data from a previously exported XML file" style="background:#1a5276;color:#fff;border-color:#1a5276">⬆ Import XML</button>"""

content = content.replace(ship_part_start, new_ship_part_start)

# 3. Inject Save to Cloud button in Annual Report
ann_report_start = """      <button class="btn btn-secondary" onclick="exportXML()" title="Export all tab data to XML for later re-import" style="background:#155c38;color:#fff;border-color:#155c38">⬇ Export XML</button>"""

new_ann_report_start = """      <button class="btn btn-secondary btn-cloud-sync" onclick="window.openCloudModal()" style="border-color:var(--teal);display:none;align-items:center;gap:6px">☁ Cloud Sync</button>
      <button class="btn btn-secondary" onclick="exportXML()" title="Export all tab data to XML for later re-import" style="background:#155c38;color:#fff;border-color:#155c38">⬇ Export XML</button>"""

content = content.replace(ann_report_start, new_ann_report_start)

# 4. Add Firebase UI Modals and script tags at the end of body
firebase_scripts = """
<!-- Cloud Sync Modal -->
<div id="cloudModal" role="dialog" aria-modal="true" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.5); z-index:9999; align-items:center; justify-content:center;">
  <div class="card" style="width:100%; max-width:600px; max-height:80vh; overflow-y:auto; background:#fff; padding:20px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <h3 style="margin:0; color:var(--navy);">☁ Cloud Sync - IMO DCS CII Verification</h3>
      <button class="btn btn-secondary btn-sm" onclick="closeCloudModal()">✕</button>
    </div>
    
    <div style="margin-bottom:20px;">
      <h4>Save Current Data</h4>
      <div style="display:flex; gap:8px;">
        <input type="text" id="cloudCaseName" placeholder="Enter case name (e.g. VesselName_2024)" style="flex:1;">
        <button class="btn btn-primary" onclick="saveToFirestore()">Save to Cloud</button>
      </div>
    </div>
    
    <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
    
    <div>
      <h4>Load Saved Data</h4>
      <div id="cloudCasesList" style="display:flex; flex-direction:column; gap:8px; max-height:300px; overflow-y:auto;">
        <div style="color:var(--muted); font-size:13px;">Loading cases...</div>
      </div>
    </div>
  </div>
</div>

<script src="https://accounts.google.com/gsi/client" async defer></script>
<script src="../config.js"></script>
<script type="module">
  import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
  import { getAuth, GoogleAuthProvider, signInWithCredential, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
  import { getFirestore, collection, addDoc, getDocs, doc, setDoc, getDoc, query, where, serverTimestamp, deleteDoc } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

  let auth, db, currentUser = null;

  window.initFirebase = function() {
    if (!window.firebaseConfig) {
      console.warn("No firebaseConfig found.");
      return;
    }
    const app = initializeApp(window.firebaseConfig);
    auth = getAuth(app);
    db = getFirestore(app);

    onAuthStateChanged(auth, (user) => {
      currentUser = user;
      if (user) {
        const btn = document.getElementById('btnGoogleSignIn');
        if (btn) btn.style.display = 'none';
        const uInfo = document.getElementById('userInfo');
        if (uInfo) {
            uInfo.style.display = 'inline-flex';
            document.getElementById('userName').textContent = user.displayName;
            document.getElementById('userAvatar').src = user.photoURL;
        }
        const cloudBtns = document.querySelectorAll('.btn-cloud-sync');
        cloudBtns.forEach(b => b.style.display = 'inline-flex');
      } else {
        const btn = document.getElementById('btnGoogleSignIn');
        if (btn) btn.style.display = 'inline-flex';
        const uInfo = document.getElementById('userInfo');
        if (uInfo) uInfo.style.display = 'none';
        const cloudBtns = document.querySelectorAll('.btn-cloud-sync');
        cloudBtns.forEach(b => b.style.display = 'none');
      }
    });
  };

  window.handleGoogleSignIn = function() {
    google.accounts.id.initialize({
      client_id: window.firebaseConfig.clientId,
      callback: handleCredentialResponse
    });
    google.accounts.id.prompt();
  };

  function handleCredentialResponse(response) {
    const credential = GoogleAuthProvider.credential(response.credential);
    signInWithCredential(auth, credential).catch(err => {
       console.error("Sign-in error:", err);
       alert("Google Sign-In failed.");
    });
  }

  window.handleSignOut = function() {
    signOut(auth).catch(err => console.error("Sign-out error:", err));
  };

  window.openCloudModal = function() {
    if(!currentUser) {
      alert("Please sign in first.");
      return;
    }
    document.getElementById('cloudModal').style.display = 'flex';
    loadFirestoreCases();
  };
  
  window.closeCloudModal = function() {
    document.getElementById('cloudModal').style.display = 'none';
  };

  window.saveToFirestore = async function() {
    if(!currentUser) return;
    const caseName = document.getElementById('cloudCaseName').value.trim();
    if(!caseName) {
       alert("Please enter a case name.");
       return;
    }
    
    const xmlStr = window.getXMLString();
    
    try {
      showToast('Saving to cloud...');
      const casesRef = collection(db, "imo_cii_cases");
      await addDoc(casesRef, {
        userId: currentUser.uid,
        name: caseName,
        xmlData: xmlStr,
        updatedAt: serverTimestamp()
      });
      document.getElementById('cloudCaseName').value = '';
      showToast('✓ Saved to cloud successfully');
      loadFirestoreCases();
    } catch (err) {
      console.error(err);
      alert("Error saving to cloud.");
    }
  };

  window.loadFirestoreCases = async function() {
    if(!currentUser) return;
    const listEl = document.getElementById('cloudCasesList');
    listEl.innerHTML = '<div style="color:var(--muted); font-size:13px;">Loading cases...</div>';
    
    try {
      const q = query(collection(db, "imo_cii_cases"), where("userId", "==", currentUser.uid));
      const querySnapshot = await getDocs(q);
      
      listEl.innerHTML = '';
      if(querySnapshot.empty) {
        listEl.innerHTML = '<div style="color:var(--muted); font-size:13px;">No saved cases found.</div>';
        return;
      }
      
      querySnapshot.forEach((docSnap) => {
        const data = docSnap.data();
        const div = document.createElement('div');
        div.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:10px; border:1px solid #eee; border-radius:6px;';
        
        const nameSpan = document.createElement('span');
        nameSpan.style.fontWeight = '600';
        nameSpan.textContent = data.name;
        
        const actions = document.createElement('div');
        actions.style.display = 'flex';
        actions.style.gap = '8px';
        
        const loadBtn = document.createElement('button');
        loadBtn.className = 'btn btn-primary btn-sm';
        loadBtn.textContent = 'Load';
        loadBtn.onclick = () => {
          loadCaseFromFirestore(data.xmlData);
          closeCloudModal();
        };
        
        const delBtn = document.createElement('button');
        delBtn.className = 'btn btn-secondary btn-sm';
        delBtn.textContent = 'Delete';
        delBtn.onclick = async () => {
          if(confirm('Delete this case?')) {
            await deleteDoc(doc(db, "imo_cii_cases", docSnap.id));
            loadFirestoreCases();
          }
        };
        
        actions.appendChild(loadBtn);
        actions.appendChild(delBtn);
        
        div.appendChild(nameSpan);
        div.appendChild(actions);
        listEl.appendChild(div);
      });
    } catch (err) {
      console.error(err);
      listEl.innerHTML = '<div style="color:red; font-size:13px;">Error loading cases.</div>';
    }
  };

  window.loadCaseFromFirestore = function(xmlStr) {
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(xmlStr, 'application/xml');
      const err = doc.querySelector('parsererror');
      if(err){
         showToast('⚠ Cloud XML parse error.');
         return;
      }
      window._applyXMLDoc(doc);
      showToast('✓ Data loaded successfully from Cloud');
    } catch(ex) {
      console.error(ex);
      showToast('⚠ Load failed: ' + ex.message);
    }
  };

  // Initialize firebase when DOM loads
  window.addEventListener('DOMContentLoaded', () => {
    initFirebase();
  });
</script>
"""

content = content.replace('<!-- Excel Import Loading Overlay -->', firebase_scripts + '\n<!-- Excel Import Loading Overlay -->')

with open('/home/anuroop-tm/Personal/fueleu-calculator/cii-eexi/imo-dcs-cii-verification-tool.html', 'w') as f:
    f.write(content)

print("File patched successfully.")
