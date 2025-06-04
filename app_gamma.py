import streamlit as st
from streamlit.components.v1 import html as st_html
import smtplib
from email.message import EmailMessage
import urllib.parse

# Sayfa ayarları
st.set_page_config(page_title="Flanker Testi - Gamma", layout="wide")
st.title("🧠 Flanker Testi (Gamma 40 Hz Müzik ile)")

# 📌 Yönerge
with st.expander("📢 Yönerge (Tıklayarak Göster/Gizle)"):
    st.markdown("""
    🎯 **TEST YÖNERGESİ**

    Bu testte ekranda önce `+` işareti, ardından örnek olarak `<<<<<`, `>>>>>`, `<<><<`, `>><>>` gibi semboller göreceksiniz.  
    **Dikkat etmeniz gereken tam ortadaki ok yönüdür.**

    - Eğer ortadaki ok **sağa bakıyorsa**, sağ alttaki butona basınız.  
    - Eğer ortadaki ok **sola bakıyorsa**, sol alttaki butona basınız.

    ⏱️ Lütfen **olabildiğince hızlı ve doğru cevap vermeye** çalışınız.  
    🔇 Müzik çalıyorsa cihazınızın sesi açıktır; arka planda 40Hz Gamma müziği oynatılacaktır.
    """)

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

# HTML ve JavaScript kodu
html_code = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    html, body {
      margin: 0; padding: 0;
      background-color: white;
      font-family: sans-serif;
      height: 100vh; overflow: hidden;
    }
    #container {
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      height: 100vh; text-align: center;
    }
    #arrow, #fixation { font-size: 60px; display: none; }
    button {
      font-size: 24px;
      padding: 10px 20px;
      margin: 10px;
      border: none;
      border-radius: 8px;
      background-color: #007BFF;
      color: white;
    }
    #leftBtn { position: absolute; bottom: 20px; left: 20px; display: none; }
    #rightBtn { position: absolute; bottom: 20px; right: 20px; display: none; }
  </style>
</head>
<body>
  <audio id="bgAudio" autoplay loop>
    <source src="https://barisakar24.github.io/flanker-test/Gamma_40Hz.wav" type="audio/wav">
  </audio>
  <div id="container">
    <div id="startScreen">
      <h2>🎧 Lütfen sesinizi açın</h2>
      <button id="startBtn">Teste Başla</button>
    </div>
    <div id="fixation">+</div>
    <div id="arrow"></div>
    <button id="leftBtn">⬅️ Sol</button>
    <button id="rightBtn">➡️ Sağ</button>
  </div>
  <script>
    const trials = 20;
    const patterns = ["<<<<<", ">>>>>", "<<><<", ">><>>"];
    const fixationTime = 300;
    const stimulusTime = 200;
    let results = [];
    let current = 0;
    let correctDir = "";
    let startTime = 0;
    let responded = false;
    const fixation = document.getElementById("fixation");
    const arrow = document.getElementById("arrow");
    const leftBtn = document.getElementById("leftBtn");
    const rightBtn = document.getElementById("rightBtn");
    document.getElementById("startBtn").onclick = () => {
      document.getElementById("startScreen").style.display = "none";
      nextTrial();
    };

    function nextTrial() {
      if (current >= trials) return finishTest();
      fixation.style.display = "block";
      arrow.style.display = "none";
      leftBtn.style.display = "none";
      rightBtn.style.display = "none";
      setTimeout(() => {
        fixation.style.display = "none";
        showStimulus();
      }, fixationTime);
    }

    function showStimulus() {
      let pat = patterns[Math.floor(Math.random() * patterns.length)];
      arrow.textContent = pat;
      arrow.style.display = "block";
      correctDir = pat[2] === ">" ? "right" : "left";
      responded = false;
      startTime = performance.now();
      setTimeout(() => {
        arrow.style.display = "none";
        leftBtn.style.display = "block";
        rightBtn.style.display = "block";
      }, stimulusTime);
    }

    function handleResponse(choice) {
      if (responded) return;
      responded = true;
      let rt = Math.round(performance.now() - startTime);
      let isCorrect = choice === correctDir ? "Doğru" : "Hatalı";
      results.push([choice, correctDir, rt, isCorrect]);
      current++;
      setTimeout(nextTrial, 200);
    }

    leftBtn.onclick = () => handleResponse("left");
    rightBtn.onclick = () => handleResponse("right");

    function finishTest() {
      document.body.innerHTML = "<h2>✅ Test tamamlandı. Sonuçlar gönderiliyor...</h2>";
      let csv = "Cevaplanan,DoğruYön,RT,Sonuç\\n";
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

# HTML gömme
st_html(html_code, height=750)

# JS → Python veri çekme ve e-posta gönderme
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
            msg["Subject"] = "Yeni Flanker Test Sonuçları (Gamma)"
            msg["From"] = smtp_email
            msg["To"] = receiver_email
            msg.set_content("Sonuçlar ektedir.")
            msg.add_attachment(csv_data.encode("utf-8"), maintype="text", subtype="csv", filename="flanker_gamma.csv")
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
            st.success("✅ Sonuçlar e-posta ile gönderildi.")
            st.session_state["flanker_results_sent"] = True
        except Exception as e:
            st.error(f"❌ E-posta gönderilemedi: {e}")
