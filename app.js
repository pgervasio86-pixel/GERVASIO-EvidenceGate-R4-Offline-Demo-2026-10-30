/* EvidenceGate browser UI. Static GitHub Pages preview works without a server.
   The offline engine *only* finds text in the user's supplied source document.
   It never claims independent truth or calls an AI API. */
"use strict";
const $ = (id) => document.getElementById(id);
let lastReport = null;
let backendAvailable = false;
let liveAvailable = false;

function compact(text) { return String(text).trim().replace(/\s+/g, " "); }
function terms(text) {
  const stops = new Set(["the", "with", "this", "that", "and", "are", "from", "have", "has", "for", "was", "were", "di", "del", "della", "sono", "una", "per", "con", "dei"]);
  return new Set((String(text).toLocaleLowerCase().match(/[\p{L}\p{N}]+/gu) || [])
    .filter(t => t.length > 1 && !/^\d+$/.test(t) && !stops.has(t)));
}
function numbers(text) { return new Set(String(text).match(/(?<![\p{L}\p{N}_])\d+(?:[.,]\d+)?(?![\p{L}\p{N}_])/gu) || []); }
function intersectionSize(a, b) { return [...a].filter(x => b.has(x)).length; }
function excerpt(text, index, length) {
  const start = Math.max(0, index - 45), end = Math.min(text.length, Math.max(start + 260, index + length + 45));
  return (start ? "..." : "") + text.substring(start, end) + (end < text.length ? "..." : "");
}
async function sha256(text) {
  if (!window.crypto || !window.crypto.subtle) return "unavailable in this browser context";
  const bytes = await window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, "0")).join("");
}
async function offlineVerify(payload) {
  const source = payload.evidence[0];
  const lower = compact(source.content).toLocaleLowerCase();
  const results = payload.claims.map((claim, idx) => {
    const needle = compact(claim).toLocaleLowerCase(), loc = lower.indexOf(needle);
    const match = loc >= 0 ? [{id:source.id, title:source.title, source_url:source.source_url, excerpt:excerpt(lower,loc,needle.length)}] : [];
    const cn = numbers(claim), sn = numbers(lower);
    const conflict = !match.length && intersectionSize(terms(claim),terms(lower)) >= 2 && cn.size && sn.size && ![...cn].some(n=>sn.has(n));
    const possible_conflicts = conflict ? [{id:source.id, title:source.title, source_url:source.source_url, excerpt:excerpt(lower,0,0)}] : [];
    return {claim_id:`C${idx+1}`,claim,verdict:match.length?"SOURCE_TEXT_MATCH":conflict?"POSSIBLE_NUMERIC_CONFLICT":"INSUFFICIENT_EVIDENCE",matches:match,possible_conflicts,note:"Text matches do not establish external truth or document authenticity."};
  });
  return {project:"GERVASIO 5.0 EvidenceGate",engine:"browser-extractive-preview-v1",timestamp_utc:new Date().toISOString(),
    input_sha256:await sha256(JSON.stringify(payload)),results,caveat:"Browser preview only: no external truth verification or Nebius inference.",nemotron:{status:"not_requested"}};
}
function make(tag, cls, text) {
  const node=document.createElement(tag); if(cls) node.className=cls; if(text!==undefined)node.textContent=String(text); return node;
}
function citationBlock(container, list, heading) {
  if(!list.length)return;
  const wrap=make("div","citations");wrap.appendChild(make("strong",null,heading));
  for(const cite of list){wrap.appendChild(make("div",null,`${cite.id} — ${cite.title}`));if(cite.excerpt)wrap.appendChild(make("div","excerpt",cite.excerpt));
    if(cite.source_url){const link=make("a",null,"Open supplied source");link.href=cite.source_url;link.target="_blank";link.rel="noopener noreferrer";wrap.appendChild(link);}}
  container.appendChild(wrap);
}
function showResults(report) {
  lastReport=report; const root=$("results");root.replaceChildren();
  const summary=make("div","review-summary");
  const counts=[
    [report.results.filter(x=>x.verdict==="SOURCE_TEXT_MATCH").length,"TEXT MATCHES"],
    [report.results.filter(x=>x.verdict.includes("CONFLICT")||x.verdict.includes("MIXED")).length,"REVIEW FLAGS"],
    [report.results.filter(x=>x.verdict==="INSUFFICIENT_EVIDENCE").length,"UNVERIFIED"],
  ];
  for(const [count,title] of counts){const card=make("div","summary-item");card.appendChild(make("strong",null,count));card.appendChild(make("span",null,title));summary.appendChild(card);}root.appendChild(summary);
  for(const entry of report.results){const card=make("article","review-card");card.appendChild(make("div","claim-label",`CLAIM ${entry.claim_id}`));card.appendChild(make("div","claim-text",entry.claim));
    let label="TEXT FOUND IN SOURCE",color="";
    if(entry.verdict==="POSSIBLE_NUMERIC_CONFLICT"){label="POSSIBLE NUMERIC CONFLICT";color="review";}
    if(entry.verdict==="MIXED_EVIDENCE_REVIEW"){label="MIXED EVIDENCE — REVIEW";color="review";}
    if(entry.verdict==="INSUFFICIENT_EVIDENCE"){label="NOT EVIDENCED";color="missing";}
    card.appendChild(make("div","verdict "+color,label));
    citationBlock(card,entry.matches,"MATCHING SOURCE TEXT");citationBlock(card,entry.possible_conflicts,"POTENTIAL CONFLICT — HUMAN REVIEW REQUIRED");
    if(!entry.matches.length&&!entry.possible_conflicts.length)card.appendChild(make("div","citations","No direct match in the provided source. Do not treat this claim as verified."));root.appendChild(card);
  }
  if(report.nemotron&&report.nemotron.note){root.appendChild(make("div","advisory",`NVIDIA Nemotron advisory (not verification):\n${report.nemotron.note}`));}
  const receipt=make("div","digest");receipt.appendChild(make("strong",null,"EVIDENCE FINGERPRINT / SHA-256"));receipt.appendChild(make("span",null,report.input_sha256));root.appendChild(receipt);
  root.appendChild(make("p","input-info","Scope: user-supplied text only. Neither source authenticity nor physical product characteristics have been independently checked."));
  $("export").disabled=false;
}
function collect() {
  const claims=$("claims").value.split(/\r?\n/).map(compact).filter(Boolean);
  const text=compact($("evidence").value),title=compact($("source-title").value);
  if(!claims.length||claims.length>8)throw new Error("Enter between 1 and 8 claims, one per line.");
  if(claims.some(x=>x.length>500))throw new Error("A claim exceeds 500 characters.");
  if(!text||text.length>12000)throw new Error("Evidence text is required (maximum 12,000 characters).");
  if(!title||title.length>160)throw new Error("A source title is required (maximum 160 characters).");
  const url=compact($("source-url").value);
  if(url&&!/^https?:\/\/[^\s<>"']+$/.test(url))throw new Error("Source URL must begin with http:// or https://.");
  return {claims,evidence:[{id:"DOC1",title,content:text,source_url:url}],use_nemotron:liveAvailable&&$("use-nemotron").checked};
}
async function analyze() {
  const button=$("verify");$("error").hidden=true;button.disabled=true;button.textContent="Reviewing source...";
  try{
    const payload=collect();let report;
    if(backendAvailable){const response=await fetch("api/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
      const result=await response.json();if(!response.ok)throw new Error(result.error||"Verification failed");report=result;
    }else{report=await offlineVerify(payload);}
    showResults(report);
  }catch(err){$("error").textContent=err.message||"Unable to complete verification.";$("error").hidden=false;}
  finally{button.disabled=false;button.replaceChildren(make("span","button-symbol","↗"),document.createTextNode(" Run evidence check"));}
}
async function probeBackend(){
  try{const r=await fetch("api/status",{signal:AbortSignal.timeout(1500)});if(!r.ok)throw Error("no backend");const info=await r.json();backendAvailable=info.api==="ok";liveAvailable=Boolean(info.live_enabled);
    if(liveAvailable){$("live-row").hidden=false;$("mode-pill").textContent="SERVER + OPTIONAL NEMOTRON";}
    else{$("mode-pill").textContent="SERVER · NO LIVE CHARGES";}}
  catch{$("mode-pill").textContent="BROWSER DEMO · OFFLINE";}
}
function sample(){
  $("claims").value="Demo trailer X7 has four close-coupled axles.\nDemo trailer X7 supports 12 tonnes of ramp load.\nDemo trailer X7 has a tested ABS certification.";
  $("source-title").value="Synthetic engineering note - demonstration only";
  $("evidence").value="Demo trailer X7 has four close-coupled axles. This is fabricated sample data for demonstration, not a real vehicle specification. Demo trailer X7 supports 10 tonnes of ramp load in this fictional example. No braking-system test report or certification is provided.";
  $("source-url").value="";$("error").hidden=true;
}
function download(){if(!lastReport)return;const blob=new Blob([JSON.stringify(lastReport,null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="GERVASIO_EvidenceGate_report.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),500);}
window.addEventListener("DOMContentLoaded",()=>{$("verify").addEventListener("click",analyze);$("sample").addEventListener("click",sample);$("export").addEventListener("click",download);sample();probeBackend();});
