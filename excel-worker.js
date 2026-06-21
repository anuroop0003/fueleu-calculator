self.importScripts('https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js');

// Utility functions mirroring the main page's logic
function cleanText(v) {
  return v === undefined || v === null ? "" : String(v).trim();
}

function cleanKey(k) {
  return String(k || '').toLowerCase().replace(/[^a-z0-9]/g, '').trim();
}

function getByAliases(obj, aliases) {
  if (!obj) return "";
  const keys = Object.keys(obj);
  for (const alias of aliases) {
    const cleanAlias = cleanKey(alias);
    const found = keys.find(k => cleanKey(k) === cleanAlias);
    if (found !== undefined) return obj[found];
  }
  return "";
}

function normaliseYesNo(v, defaultVal = "NO") {
  const txt = cleanText(v).toUpperCase();
  if (["YES", "Y", "1", "TRUE"].includes(txt)) return "YES";
  if (["NO", "N", "0", "FALSE"].includes(txt)) return "NO";
  return defaultVal;
}

function normaliseFromList(v, list, defaultVal) {
  const txt = cleanText(v).toLowerCase().replace(/[^a-z0-9]/g, "");
  for (const item of list) {
    if (String(item).toLowerCase().replace(/[^a-z0-9]/g, "") === txt) return item;
  }
  return defaultVal;
}

function toNumberText(v) {
  if (v === undefined || v === null || v === "") return "";
  const num = Number(v);
  return Number.isFinite(num) ? String(num) : "";
}

function normaliseMode(v) {
  const txt = cleanText(v).toLowerCase();
  if (txt === "custom") return "custom";
  return "base";
}

self.onmessage = function(e) {
  const { arrayBuffer, scopeValues, iceValues } = e.data;
  
  try {
    const data = new Uint8Array(arrayBuffer);
    const workbook = XLSX.read(data, { type: "array" });
    
    // Find the relevant sheet
    const voyageSheetName = workbook.SheetNames.find(n => ["voyagedeatils", "voyagedetails"].includes(cleanKey(n)));
    const preferred = workbook.SheetNames.find(n => String(n).toLowerCase() === "part b import") || voyageSheetName || workbook.SheetNames[0];
    const sheet = workbook.Sheets[preferred];
    
    const isVoyageDetailsSheet = ["voyagedeatils", "voyagedetails"].includes(cleanKey(preferred));
    
    let rawRows;
    if (isVoyageDetailsSheet) {
      rawRows = XLSX.utils.sheet_to_json(sheet, { defval: "" }).filter(function(r) {
        const fuel = cleanText(getByAliases(r, ["Fuel type"]));
        const amount = cleanText(getByAliases(r, ["Fuel amount [m tonnes]", "Fuel amount"]));
        return fuel !== "" && amount !== "";
      });
    } else {
      rawRows = XLSX.utils.sheet_to_json(sheet, { defval: "", range: 3 }).filter(r => Object.values(r).some(v => cleanText(v) !== ""));
      if (!rawRows.length) {
        rawRows = XLSX.utils.sheet_to_json(sheet, { defval: "" }).filter(r => Object.values(r).some(v => cleanText(v) !== ""));
      }
    }
    
    const totalRows = rawRows.length;
    if (totalRows === 0) {
      self.postMessage({ type: "error", error: "No Part B rows found in the selected Excel file." });
      return;
    }
    
    self.postMessage({ type: "start", total: totalRows });
    
    const CHUNK_SIZE = 500;
    let processedCount = 0;
    
    while (processedCount < totalRows) {
      const chunk = rawRows.slice(processedCount, processedCount + CHUNK_SIZE);
      const mappedChunk = chunk.map((r, idx) => {
        const globalIdx = processedCount + idx;
        const voyageNo = cleanText(getByAliases(r, ["Voyage No.", "Voyage No", "VOYAGE NO.", "VoyageNo", "Voyage"]));
        const fuelName = getByAliases(r, ["Fuel type", "Pathway name / Consumer", "Pathway name", "Consumer", "Fuel Pathway", "Fuel pathway", "Fuel", "Fuel Name"]);
        const pos = normaliseYesNo(getByAliases(r, ["PoS/PoC available", "POS/POC AVAILABLE", "PoS PoC available", "POS POC", "PoC available", "PoS available"]), "NO");
        const scope = normaliseFromList(getByAliases(r, ["Voyages/ Ports", "Voyages/ Ports scope", "VOYAGES/ PORTS SCOPE", "Voyages Ports scope", "Scope", "Voyage Scope", "Voyage Type"]), scopeValues, "EEA-EEA");
        const iceClass = normaliseFromList(getByAliases(r, ["ICE Class correction factor is using", "Ice Class", "ICE CLASS"]), iceValues, "NA");
        const throughIce = normaliseYesNo(getByAliases(r, ["Through Ice", "THROUGH ICE"]), "NO");
        const distanceNm = toNumberText(getByAliases(r, ["Distance NM", "DISTANCE NM", "Distance"]));
        const iceDistanceNm = toNumberText(getByAliases(r, ["Dice conditions (Distance in ice)", "Ice distance NM", "ICE DISTANCE NM", "Ice Distance"]));
        const amount = toNumberText(getByAliases(r, ["Fuel amount [m tonnes]", "FUEL AMOUNT [M TONNES]", "Fuel Amount", "Fuel amount", "Amount", "Tonnes"]));

        const importedLcv = toNumberText(getByAliases(r, ["Lower calorific value (LCV) (as per PoS/PoC)", "Custom LCV MJ/g", "CUSTOM LCV MJ/G", "Custom LCV"]));
        const eAvailable = normaliseYesNo(getByAliases(r, ["PoS/PoC E value available", "POS/POC E VALUE AVAILABLE", "E Value Mode", "E value mode", "E Mode"]), "NO");
        const importedE = toNumberText(getByAliases(r, ["E value as per PoS/PoC", "Custom E Value gCO2eq/MJ", "CUSTOM E VALUE GCO2EQ/MJ", "Custom E Value", "Manual E Value gCO2eq/MJ", "Manual E Value", "E Value gCO2eq/MJ"]));
        const euAvailable = normaliseYesNo(getByAliases(r, ["PoS/PoC eu value available", "POS/POC EU VALUE AVAILABLE", "EU Mode", "EU mode"]), "NO");
        const importedEu = toNumberText(getByAliases(r, ["eu value as per PoS/PoC", "EU value as per PoS/PoC", "Custom EU Value gCO2eq/MJ", "Custom EU Value", "EU Value gCO2eq/MJ"]));
        
        let lcvMode = normaliseMode(getByAliases(r, ["LCV Mode", "LCV mode"]));
        if (pos === "YES" && importedLcv !== "") lcvMode = "custom";
        
        const eMode = eAvailable === "YES" ? "custom" : "base";
        const euMode = euAvailable === "YES" ? "custom" : "base";
        
        return {
          voyageNo: voyageNo || String(globalIdx + 1),
          fuelName,
          pos,
          scope,
          iceClass,
          throughIce,
          distanceNm,
          iceDistanceNm,
          amount,
          importedLcv,
          lcvMode,
          eMode,
          importedE,
          euMode,
          importedEu
        };
      });
      
      processedCount += chunk.length;
      self.postMessage({
        type: "chunk",
        rows: mappedChunk,
        processed: processedCount,
        percent: Math.round((processedCount / totalRows) * 100)
      });
    }
    
    self.postMessage({ type: "complete" });
    
  } catch (err) {
    self.postMessage({ type: "error", error: err.message || "Failed to parse Excel file" });
  }
};
