import streamlit as st
from streamlit.components.v1 import html as st_html
import smtplib
from email.message import EmailMessage
import urllib.parse

# Sayfa ayarları
st.set_page_config(page_title="Flanker Testi - Alpha", layout="wide")
st.title("🧠 Flanker Testi (Alpha 10 Hz Müzik ile)")

# SMTP ayarları
smtp_ready = False
try:
    smtp_email = st.secrets["smtp"]["email"]
    smtp_password = st.secrets["smtp"]["password"]
    smtp_server = st.secrets["smtp"]["smtp_server"]
    smtp_port = st.secrets["smtp"]["smtp_port"]
    receiver_email = st.secrets["smtp"]["receiver"]
    smtp_ready = True
except:
    st.warning("⚠️ SMTP ayarları bulunamadı. E-posta gönderimi devre dışı.")

# HTML ve JavaScript
html_code = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Flanker</title>
<style>
  html, body {
    margin: 0; padding: 0;
    height: 100vh;
    font-family: Arial;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: white;
  }
  #arrow, #fixation {
    font-size: 72px;
    margin: 20px;
  }
  #startMessage {
    font-size: 18px;
    text-align: center;
    margin-bottom: 20px;
  }
  button {
    padding: 12px 24px;
    font-size: 20px;
    border: none;
    border-radius: 8px;
    margin: 10px;
    background-color: #007bff;
    color: white;
  }
  #leftBtn, #rightBtn {
    position: fixed;
    bottom: 10px;
    width: 40%;
  }
  #leftBtn { left: 10px; }
  #rightBtn { right: 10px; }
</style>
</head>
<body>
<audio id="bgAudio" loop>
  <source src="https://barisakar24.github.io/flanker-test/Alpha_10Hz.wav" type="audio/wav">
</audio>

<div id="startScreen">
  <div id="startMessage">
    🎧 Kulaklık takınız.<br><br>
    Ekranda + işareti ve ardından simgeler belirecektir.<br>
    Ortadaki oka odaklanın.<br>
    Sağa bakıyorsa sağ butona, sola bakıyorsa sol butona basın.<br>
    Hızlı ve doğru olunuz. Müzik çalmıyorsa sesi açınız.
  </div>
  <button onclick="startTest()">Teste Başla</button>
</div>

<div id="fixation" style="display:none;">+</div>
<div id="arrow" style="display:none;"></div>
<button id="leftBtn" style="display:none;" onclick="handleResponse('left')">⬅️ Sol</button>
<button id="rightBtn" style="display:none;" onclick="handleResponse('right')">➡️ Sağ</button>

<script>
const patterns = ["<<<<<", ">>>>>", "<<><<", ">><>>"];
const trials = 20;
let current = 0;
let results = [];
let direction = "";
let startTime = 0;
let responded = false;

function startTest() {
  document.getElementById("startScreen").style.display = "none";
  document.getElementById("bgAudio").play();
  nextFixation();
}

function nextFixation() {
  if (current >= trials) return finish();
  document.getElementById("fixation").style.display = "block";
  document.getElementById("arrow").style.display = "none";
  document.getElementById("leftBtn").style.display = "none";
  document.getElementById("rightBtn").style.display = "none";
  setTimeout(() => {
    document.getElementById("fixation").style.display = "none";
    showStimulus();
  }, 300);
}

function showStimulus() {
  const pat = patterns[Math.floor(Math.random() * patterns.length)];
  document.getElementById("arrow").innerText = pat;
  document.getElementById("arrow").style.display = "block";
  direction = pat.charAt(2) === ">" ? "right" : "left";
  startTime = performance.now();
  responded = false;
  setTimeout(() => {
    document.getElementById("arrow").style.display = "none";
    document.getElementById("leftBtn").style.display = "block";
    document.getElementById("rightBtn").style.display = "block";
  }, 200);
}

function handleResponse(choice) {
  if (responded) return;
  responded = true;
  const rt = Math.round(performance.now() - startTime);
  const correct = (choice === direction) ? "Doğru" : "Hatalı";
  results.push([choice, direction, rt, correct]);
  current++;
  setTimeout(nextFixation, 300);
}

function finish() {
  document.body.innerHTML = "<h2>✅ Test tamamlandı. Sonuçlar gönderiliyor...</h2>";
  let csv = "Basılan,DoğruYön,RT(ms),Sonuç\\n";
  results.forEach(r => { csv += r.join(",") + "\\n"; });
  const encoded = encodeURIComponent(csv);
  const iframe = document.createElement("iframe");
  iframe.style.display = "none";
  iframe.src = "?flanker_results=" + encoded;
  document.body.appendChild(iframe);
}
</script>
</body>
</html>
"""

# HTML bileşeni ekle
st_html(html_code, height=700)

# Python tarafında gelen CSV verisini yakalayıp mail at
if smtp_ready and "flanker_results_sent" not in st.session_state:
    st.session_state["flanker_results_sent"] = False

if smtp_ready and not st.session_state["flanker_results_sent"]:
    params = st.query_params
    if "flanker_results" in params:
        csv_data = urllib.parse.unquote(params["flanker_results"])
        try:
            msg = EmailMessage()
            msg["Subject"] = "Yeni Flanker Test Sonuçları"
            msg["From"] = smtp_email
            msg["To"] = receiver_email
            msg.set_content("Sonuçlar ekteki dosyada yer almaktadır.")
            msg.add_attachment(csv_data.encode("utf-8"), maintype="text", subtype="csv", filename="flanker_sonuc.csv")
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
            st.success("✅ Sonuçlar e-posta ile gönderildi.")
            st.session_state["flanker_results_sent"] = True
        except Exception as e:
            st.error(f"❌ E-posta gönderilemedi: {e}")
