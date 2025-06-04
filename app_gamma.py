import streamlit as st
from streamlit.components.v1 import html as st_html
import smtplib
from email.message import EmailMessage
import urllib.parse

st.set_page_config(page_title="Flanker Testi - Gamma", layout="wide")
st.title("🧠 Flanker Testi (Gamma 40 Hz Müzik ile)")

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

html_code = """
<!DOCTYPE html>
<html lang=\"tr\">
<head>
  <meta charset=\"UTF-8\" />
  <title>Flanker Testi (Gamma 40 Hz)</title>
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
      text-align: center;
    }
    #fixation, #arrow {
      font-size: 72px;
      text-align: center;
      width: 100%;
    }
    #instruction {
      font-size: 20px;
      color: #333;
      margin-bottom: 40px;
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
<audio id=\"bgAudio\" loop autoplay>
  <source src=\"https://barisakar24.github.io/flanker-test/Gamma_40Hz.wav\" type=\"audio/wav\">
</audio>
<div id=\"container\">
  <div id=\"instruction\">
    🎧 Lütfen kulaklık takın ve sesinizi açın.<br><br>
    Ekranda önce bir + işareti göreceksiniz, ardından <<<<<, >>>>> gibi simgeler gelecektir.<br>
    Odaklanmanız gereken tam ortadaki semboldür.<br>
    Ortadaki ok sağa bakıyorsa sağ butona, sola bakıyorsa sol butona basınız.<br>
    Tepkiniz ne kadar hızlı olursa o kadar iyi.<br><br>
    Arka planda GAMMA frekansında bir müzik çalacaktır.
  </div>
  <button id=\"startBtn\">Teste Başla</button>
  <div id=\"fixation\" style=\"display:none;\">+</div>
  <div id=\"arrow\" style=\"display:none;\"></div>
  <button id=\"leftBtn\" style=\"display:none;\">⬅️ Sol</button>
  <button id=\"rightBtn\" style=\"display:none;\">➡️ Sağ</button>
</div>
<script>
const trials = 20;
const fixationDuration = 300;
const stimulusDuration = 200;
const patterns = [\"<<<<<\", \">>>>>", \"<<><<\", \">><>>\"];
let current = 0;
let results = [];
let direction = \"\";
let startTime = 0;
let responded = false;
const fixation = document.getElementById(\"fixation\");
const arrow = document.getElementById(\"arrow\");
const startBtn = document.getElementById(\"startBtn\");
const instruction = document.getElementById(\"instruction\");
const leftBtn = document.getElementById(\"leftBtn\");
const rightBtn = document.getElementById(\"rightBtn\");

startBtn.onclick = () => {
  startBtn.style.display = \"none\";
  instruction.style.display = \"none\";
  nextFixation();
};

function nextFixation() {
  if (current >= trials) return finish();
  fixation.style.display = \"block\";
  arrow.style.display = \"none\";
  leftBtn.style.display = \"none\";
  rightBtn.style.display = \"none\";
  setTimeout(() => {
    fixation.style.display = \"none\";
    showStimulus();
  }, fixationDuration);
}

function showStimulus() {
  const pat = patterns[Math.floor(Math.random() * patterns.length)];
  arrow.innerText = pat;
  arrow.style.display = \"block\";
  const centerChar = pat.charAt(2);
  direction = (centerChar === \"<\") ? \"left\" : \"right\";
  startTime = performance.now();
  responded = false;
  setTimeout(() => {
    arrow.style.display = \"none\";
    leftBtn.style.display = \"block\";
    rightBtn.style.display = \"block\";
  }, stimulusDuration);
}

function handleResponse(choice) {
  if (responded) return;
  responded = true;
  const rt = Math.round(performance.now() - startTime);
  const correct = (choice === direction) ? \"Doğru\" : \"Hatalı\";
  results.push([choice, direction, rt, correct]);
  current++;
  setTimeout(nextFixation, 100);
}

leftBtn.onclick = () => handleResponse(\"left\");
rightBtn.onclick = () => handleResponse(\"right\");

function finish() {
  document.body.innerHTML = \"<h2>✅ Test tamamlandı! Sonuçlar gönderiliyor...</h2>\";
  let csv = \"Basılan,DoğruYön,RT(ms),Sonuç\\n\";
  results.forEach(r => { csv += r.join(\",\") + \"\\n\"; });
  const encoded = encodeURIComponent(csv);
  const iframe = document.createElement(\"iframe\");
  iframe.style.display = \"none\";
  iframe.src = \"?flanker_results=\" + encoded;
  document.body.appendChild(iframe);
}
</script>
</body>
</html>
"""

st_html(html_code, height=800)

if smtp_ready and "flanker_results_sent" not in st.session_state:
    st.session_state["flanker_results_sent"] = False

if smtp_ready and not st.session_state["flanker_results_sent"]:
    params = st.query_params
    if "flanker_results" in params:
        csv_data = urllib.parse.unquote(params["flanker_results"])
        try:
            msg = EmailMessage()
            msg["Subject"] = "Yeni Flanker Gamma Testi Sonuçları"
            msg["From"] = smtp_email
            msg["To"] = receiver_email
            msg.add_attachment(csv_data.encode("utf-8"), maintype="text", subtype="csv", filename="flanker_gamma.csv")
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
            st.success("✅ Gamma testi sonuçları e-posta ile gönderildi.")
            st.session_state["flanker_results_sent"] = True
        except Exception as e:
            st.error(f"❌ E-posta gönderilemedi: {e}")
