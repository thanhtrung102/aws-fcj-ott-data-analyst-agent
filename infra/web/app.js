const form = document.getElementById("form");
const promptEl = document.getElementById("prompt");
const log = document.getElementById("log");
const sendBtn = document.getElementById("send");
let sessionId = null;

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function addMsg(role, html) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = html;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function renderMd(md) {
  const lines = md.split(/\n/);
  let html = "";
  let inTable = false;
  let inCode = false;
  let codeBuf = [];

  const flushCode = () => {
    if (codeBuf.length) {
      html += "<pre><code>" + esc(codeBuf.join("\n")) + "</code></pre>";
      codeBuf = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith("```")) {
      if (inCode) { flushCode(); inCode = false; }
      else { inCode = true; }
      continue;
    }
    if (inCode) { codeBuf.push(line); continue; }

    if (/^\s*\|.*\|\s*$/.test(line) && /^\s*\|[-:\s|]+\|\s*$/.test(lines[i + 1] || "")) {
      const headers = line.split("|").slice(1, -1).map(c => c.trim());
      html += "<table><thead><tr>" + headers.map(h => "<th>" + esc(h) + "</th>").join("") + "</tr></thead><tbody>";
      i += 1;
      while (i + 1 < lines.length && /^\s*\|.*\|\s*$/.test(lines[i + 1])) {
        i += 1;
        const cells = lines[i].split("|").slice(1, -1).map(c => c.trim());
        html += "<tr>" + cells.map(c => "<td>" + esc(c) + "</td>").join("") + "</tr>";
      }
      html += "</tbody></table>";
      inTable = true;
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      if (!html.endsWith("</li></ul>") && !html.endsWith("</li>")) html += "<ul>";
      html += "<li>" + esc(line.replace(/^\s*[-*]\s+/, "")) + "</li>";
      if (!(lines[i + 1] && /^\s*[-*]\s+/.test(lines[i + 1]))) html += "</ul>";
      continue;
    }

    if (/^#{1,4}\s/.test(line)) {
      const level = line.match(/^#+/)[0].length;
      html += `<h${level}>` + esc(line.replace(/^#+\s/, "")) + `</h${level}>`;
      continue;
    }

    if (line.trim() === "") { html += "<br>"; continue; }

    let escd = esc(line);
    escd = escd.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    escd = escd.replace(/`([^`]+)`/g, "<code>$1</code>");
    html += escd + "<br>";
  }
  flushCode();
  return html;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = promptEl.value.trim();
  if (!prompt) return;
  if (!window.API_URL) {
    addMsg("agent", "<span class='err'>API_URL is not configured.</span>");
    return;
  }
  addMsg("user", esc(prompt));
  promptEl.value = "";
  sendBtn.disabled = true;
  const thinking = addMsg("agent", "<em>Thinking… writing SQL and scanning Athena (typically 8–30s).</em>");
  try {
    const res = await fetch(window.API_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ prompt, sessionId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "HTTP " + res.status);
    sessionId = data.sessionId || sessionId;
    thinking.innerHTML = renderMd(data.answer || "(no answer)");
  } catch (err) {
    thinking.innerHTML = "<span class='err'>Error: " + esc(String(err.message || err)) + "</span>";
  } finally {
    sendBtn.disabled = false;
  }
});
