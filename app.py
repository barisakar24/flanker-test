import streamlit as st
from streamlit.components.v1 import html as st_html
import smtplib
from email.message import EmailMessage
import urllib.parse

# Sayfa ayarları
st.set_page_config(page_title="Flanker Testi - Alpha", layout="wide")
st.title("🧠 Flanker Testi (Alpha 10 Hz Müzik ile)")

# SMTP ayarları kontrolü
smtp_ready = False
try:
    smtp_email = st.secrets["smtp"]["email"]
    smtp_password = st.secrets["smtp"]["password"]
    smtp_server = st.secrets["smtp"]["smtp_server"]
    smtp_port = st.secrets["smtp"]["smtp_port"]
    receiver_email = st.secrets["smtp"]["receiver"]
    smtp_ready = True
except:
    st.warning("⚠️ SMTP ayarları bulunamadı. E-posta gönderimi devre dışı bırakıldı.")

# HTML + JS (yönerge dahil)
html_code = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <title>Flanker Testi</title>
  <style>
    html, body {
      margin: 0; padding: 0;
      background-color: white;
      font-family: Arial, sans-serif;
      height: 100vh; overflow: hidden;
    }
    #container {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      user-select: none;
      padding: 20px;
    }
    #fixation, #arrow {
      font-size: 72px;
      text-align: center;
      width: 100%;
    }
    #startMessage {
      font-size: 24px;
      color: #333;
      text-align: center;
      margin-bottom: 20px;
    }
    #instructions {
      font-size: 18px;
      color: #555;
      max-width: 700px;
      text-align: justify;
      margin-bottom: 25px;
      background-color: #f3f3f3;
      padding: 15px;
      border-radius: 10px;
    }
    button {
      font-size: 20px;
      padding: 10px 20px;
      border: none;
      border-radius: 8px;
      background-color: #007BFF;
      color: white;
    }
    #leftBtn {
      position: absolute;
      bottom: 20px;
      left: 20px;
    }
    #rightBtn {
      position: absolute;
      bottom: 20px;
      right: 20px;
    }
  </style>
</head>
<body>
<audio id="bgAudio" loop autoplay>
  <source src="https://barisakar24.github.io/flanker-test/Alpha_10Hz.wav" type="audio/wav">
</audio>
<div id="container">
  <div id="startScreen">
    <div id="startMessage">🎧 Lütfen kulaklığınızı takın ve sessiz bir ortamda teste başlayın.</div>
    <div id="instructions">
      <b>Yönerge:</b> Testte ekranda önce bir <b>+ işareti</b> görünecek, ardından kısa bir süreliğine <b><<><<</b>, <b>>>></b> gibi semboller belirecektir.<br><br>
      Sizin odaklanmanız gereken <b>ortadaki ok</b> yönüdür. Bu oka göre hareket edin:<br><br>
      Eğer ortadaki ok <b>sağ</b>a bakıyorsa <b>sağ</b> butonuna, <b>sol</b>a bakıyorsa <b>sol</b> butonuna basın.<br><br>
      <u>Hızlı ve doğru cevap vermeye çalışın.</u><br><br>
      Arka planda odaklanmanıza yardımcı olacak <b>10 Hz Alpha dalgası</b> çalacaktır.
    </div>
    <button id="startBtn">Teste Başla</button>
  </div>
  <div id="fixation" style="display:none;">+</div>
  <div id="arrow" style="display:none;"></div>
  <button id="leftBtn" style="display:none;">⬅️ Sol</button>
  <button id="rightBtn" style="display:none;">➡️ Sağ</button>
</div>
<script>
const trials = 20;
const fixationDuration = 300;
const stimulusDuration = 200;
const patterns = ["<<<<<", ">>>>>", "<<><<", ">><>>"];
let current = 0;
let results = [];
let direction = "";
let startTime = 0;
let responded = false;
const fixation = document.getElementById("fixation");
const arrow = document.getElementById("arrow");
const startBtn = document.getElementById("startBtn");
const startScreen = document.getElementById("startScreen");
const leftBtn = document.getElementById("leftBtn");
const rightBtn = document.getElementById("rightBtn");
startBtn.onclick = () => { startScreen.style.display = "none"; nextFixation(); };
function nextFixation() {
  if (current >= trials) return finish();
  fixation.style.display = "block";
  arrow.style.display = "none";
  leftBtn.style.display = "none";
  rightBtn.style.display = "none";
  setTimeout(() => {
    fixation.style.display = "none";
    showStimulus();
  }, fixationDuration);
}
function showStimulus() {
  const pat = patterns[Math.floor(Math.random() * patterns.length)];
  arrow.innerText = pat;
  arrow.style.display = "block";
  direction = pat.charAt(2) === ">" ? "right" : "left";  // Orta oka göre karar ver
  startTime = performance.now();
  responded = false;
  setTimeout(() => {
    arrow.style.display = "none";
    leftBtn.style.display = "block";
    rightBtn.style.display = "block";
  }, stimulusDuration);
}
function handleResponse(choice) {
  if (responded) return;
  responded = true;
  const rt = Math.round(performance.now() - startTime);
  const correct = (choice === direction) ? "Doğru" : "Hatalı";
  results.push([choice, direction, rt, correct]);
  current++;
  setTimeout(nextFixation, 100);
}
leftBtn.onclick = () => handleResponse("left");
rightBtn.onclick = () => handleResponse("right");
function finish() {
  document.body.innerHTML = "<h2>✅ Test tamamlandı! Sonuçlar gönderiliyor...</h2>";
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

# Embed HTML
st_html(html_code, height=750)

# JS→Python veri aktarımı ve mail
if smtp_ready and "flanker_results_sent" not in st.session_state:
    st.session_state["flanker_results_sent"] = False

if smtp_ready and not st.session_state["flanker_results_sent"]:
    params = st.query_params
    if "flanker_results" in params:
        csv_data = urllib.parse.unquote(params["flanker_results"])
        if csv_data.startswith("data:text/csv;charset=utf-8,"):
            csv_data = csv_data[len("data:text/csv;charset=utf-8,"):]
        try:
            msg = EmailMessage()
            msg["Subject"] = "Yeni Flanker Test Sonuçları"
            msg["From"] = smtp_email
            msg["To"] = receiver_email
            msg.set_content(csv_data)
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
            st.success("✅ Sonuçlar e-posta ile gönderildi.")
            st.session_state["flanker_results_sent"] = True
        except Exception as e:
            st.error(f"❌ E-posta gönderilemedi: {e}")
