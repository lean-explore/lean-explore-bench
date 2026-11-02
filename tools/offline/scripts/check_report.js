// Smoke-test report logic without a browser or external dependencies.
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");
const path = process.argv[2];
if (!path) throw new Error("Usage: node scripts/check_report.js path/to/index.html");
const html = fs.readFileSync(path, "utf8");
const code = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join("\n");
const data = JSON.parse(code.match(/const D=([\s\S]*?);\nconst \$/)[1]);
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
const elements = new Map(ids.map(id => [id, {
  value: ({window:"full", view:"requests", channel:"all"})[id] || "",
  innerHTML: "", textContent: "", checked: false,
  addEventListener(name, fn) { this[name] = fn; },
  querySelector() { return {}; }
}]));
const context = vm.createContext({document: {getElementById(id) {
  assert(elements.has(id), "Missing element: " + id);
  return elements.get(id);
}}});
vm.runInContext(code, context);
for (const w of Object.keys(data.windows)) {
  if (!data.windows[w].all) continue;
  elements.get("window").value = w;
  elements.get("window").change();
  for (const v of ["requests","distinct"]) {
    elements.get("view").value = v;
    elements.get("view").change();
    for (const c of ["all", ...Object.keys(data.windows[w].channels)]) {
      elements.get("channel").value = c;
      elements.get("channel").change();
      for (const id of ["channels","length","surface","frequency"]) {
        const content = elements.get(id).innerHTML;
        assert(!/NaN|undefined|Infinity/.test(content), id + " contains invalid values");
      }
    }
  }
  elements.get("channel").value = "all";
}
elements.get("hidefirst").checked = true;
elements.get("hidefirst").change();
assert(!elements.get("daily").innerHTML.includes(data.first_day.slice(5)), "First day still visible");
assert(!elements.get("daily").innerHTML.includes("NaN"));
console.log("Report logic passed: windows, views, channels, and daily rescaling.");
