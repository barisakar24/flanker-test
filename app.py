import streamlit as st
from streamlit.components.v1 import html as st_html
import smtplib
from email.message import EmailMessage

# —————————————————————————————————————————————————————————
# 1) Streamlit Sayfa Ayarları
# —————————————————————————————————————————————————————————
st.set_page_config(page_title="Flanker Testi - Alpha", layout="wide")
st.title("🧠 Flanker Testi (Alpha 10 Hz Müzik ile)")

# —————————————————————————————————————————————————————————
# 2) E-posta Ayarları (Secrets varsa, yoksa pas geçecek)
#    Eğer Streamlit Cloud’da kaldıysanız .streamlit/secrets.toml’a şunu ekleyebilirsiniz:
#
#    [smtp]
#    email         = "sizin_email@gmail.com"
#    password      = "gmail_app_password"   # Gmail App Şifresi
#    smtp_server   = "smtp.gmail.com"
#    smtp_port     = 587
#    receiver      = "alici_email@domain.com"
#
#    Eğer bu alanı eklemezseniz, e-posta kısmı otomatik atlanacak.
# —————————————————————————————————————————————————————————
use_smtp = False
try:
    smtp_email     = st.secrets["smtp"]["email"]
    smtp_password  = st.secrets["smtp"]["password"]
    smtp_server    = st.secrets["smtp"]["smtp_server"]
    smtp_port      = st.secrets["smtp"]["smtp_port"]
    receiver_email = st.secrets["smtp"]["receiver"]
    use_smtp = True
except:
    # Secrets tanımlı değilse, e-posta gönderimini atla
    st.warning("⚠️ SMTP ayarları bulunamadı. E-posta gönderimi devre dışı bırakıldı.")
    use_smtp = False

# —————————————————————————————————————————————————————————
# 3) HTML + JavaScript (Mobil uyumlu, alt köşelerde buton, zamanlama JS ile)
# —————————————————————————————————————————————————————————
html_code = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <title>Flanker Testi (Alpha 10 Hz)</title>
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
    }
    #downloadLink {
      display: none;
      margin-top: 30px;
      font-size: 20px;
      text-decoration: none;
      color: white;
      background-color: #007BFF;
      padding: 10px 20px;
      border-radius: 8px;
    }
    #downloadLink:hover {
      background-color: #0056b3;
    }
    button {
      font-size: 20px;
      padding: 10px 20px;
      margin: 10px;
      border: none;
      border-radius: 8px;
      background-color: #007BFF;
      color: white;
    }
    button:active {
      background-color: #0056b3;
    }
    /* Alt köşelere yerleştirilecek butonlar */
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

  <!-- 1. Alpha müziği (loop) -->
  <audio id="bgAudio" loop>
    <source src="Alpha_10Hz.wav" type="audio/wav" />
    Tarayıcınız ses çalmayı desteklemiyor.
  </audio>

  <div id="container">
    <!-- Başlangıç ekranı -->
    <div id="startScreen">
      <div id="startMessage">🎧 Lütfen sesi açın ve “Teste Başla” tuşuna basın.</div>
      <button id="startBtn">Teste Başla</button>
    </div>

    <!-- Fixation için + -->
    <div id="fixation" style="display:none;">+</div>

    <!-- Arrow stimulus -->
    <div id="arrow" style="display:none;"></div>

    <!-- Alt köşe butonları -->
    <button id="leftBtn" style="display:none;">⬅️ Sol</button>
    <button id="rightBtn" style="display:none;">➡️ Sağ</button>

    <!-- Test tamamlandığında gösterilecek indirme linki (gizli) -->
    <a id="downloadLink">📥 Sonuçları İndir (.csv)</a>
  </div>

  <script>
    // ===== Sabitler =====
    const totalTrials       = 20;
    const fixationDuration  = 500;   // ms (fixation)
    const stimulusDuration  = 1500;  // ms (arrow stimulus)
    const directions        = ["left","right"];

    let trialIndex          = 0;
    let results             = [];    // [[choice, correctDir, RT(ms), outcome], ...]

    let currentDirection    = "";
    let arrowText           = "";
    let stimulusStartTime   = 0;
    let responded           = false;

    // ===== DOM Elementleri =====
    const bgAudio      = document.getElementById("bgAudio");
    const startScreen  = document.getElementById("startScreen");
    const startBtn     = document.getElementById("startBtn");
    const fixationEl   = document.getElementById("fixation");
    const arrowEl      = document.getElementById("arrow");
    const leftBtn      = document.getElementById("leftBtn");
    const rightBtn     = document.getElementById("rightBtn");
    const downloadLink = document.getElementById("downloadLink");
    const container    = document.getElementById("container");

    // ===== “Teste Başla” butonuna tıklandığında =====
    startBtn.addEventListener("click", () => {
      bgAudio.play();               // Müzik çalmaya başla
      startScreen.style.display = "none";
      runFixation();
    });

    // ===== Fixation (500 ms) =====
    function runFixation() {
      fixationEl.style.display = "block";
      arrowEl.style.display    = "none";
      leftBtn.style.display    = "none";
      rightBtn.style.display   = "none";

      setTimeout(() => {
        fixationEl.style.display = "none";
        runStimulus();
      }, fixationDuration);
    }

    // ===== Arrow stimulus (1500 ms) =====
    function runStimulus() {
      if (trialIndex >= totalTrials) {
        finishTest();
        return;
      }

      // 1) Rastgele yön seç ve arrowText hazırla
      currentDirection = directions[Math.floor(Math.random() * directions.length)];
      let arr = currentDirection === "left"
                ? ["<","<","<","<","<"]
                : [">",">",">",">",">"];
      arr[2] = currentDirection === "left" ? "<" : ">";
      arrowText = arr.join("");

      // 2) Arrow’u göster
      arrowEl.innerText = arrowText;
      arrowEl.style.display  = "block";
      leftBtn.style.display  = "block";
      rightBtn.style.display = "block";

      // 3) RT ölçümünü başlat
      stimulusStartTime = performance.now();
      responded = false;

      // 4) “Sol” butonuna tıklandığında
      leftBtn.onclick = () => {
        if (!responded) {
          responded = true;
          const rt  = Math.round(performance.now() - stimulusStartTime);
          const correct = (currentDirection === "left") ? "Doğru" : "Hatalı";
          results.push(["left", currentDirection, rt, correct]);
          cleanupAndNext();
        }
      };

      // 5) “Sağ” butonuna tıklandığında
      rightBtn.onclick = () => {
        if (!responded) {
          responded = true;
          const rt  = Math.round(performance.now() - stimulusStartTime);
          const correct = (currentDirection === "right") ? "Doğru" : "Hatalı";
          results.push(["right", currentDirection, rt, correct]);
          cleanupAndNext();
        }
      };

      // 6) Zaman aşımı: 1500 ms içinde tıklanmazsa “Yanıtsız”
      setTimeout(() => {
        if (!responded) {
          responded = true;
          results.push(["Yok", currentDirection, "–", "Yanıtsız"]);
          cleanupAndNext();
        }
      }, stimulusDuration);
    }

    // ===== Trial tamamlandığında butonları/arrow’u gizle, bir sonraki fixation’a geç =====
    function cleanupAndNext() {
      arrowEl.style.display  = "none";
      leftBtn.style.display  = "none";
      rightBtn.style.display = "none";
      trialIndex++;
      setTimeout(runFixation, 100);
    }

    // ===== 20 trial bitince sonuçları Python’a yolla =====
    function finishTest() {
      fixationEl.style.display = "none";
      arrowEl.style.display    = "none";
      leftBtn.style.display    = "none";
      rightBtn.style.display   = "none";

      // “Test tamamlandı” mesajı
      const msg = document.createElement("div");
      msg.innerHTML = "<h2>✅ Test tamamlandı!</h2>";
      msg.style.marginTop = "30px";
      container.appendChild(msg);

      // 1) CSV verisini hazırla
      let csvContent = "data:text/csv;charset=utf-8,";
      csvContent += ["Basılan","DoğruYön","RT(ms)","Sonuç"].join(",") + "\\r\\n";
      results.forEach(row => {
        csvContent += row.join(",") + "\\r\\n";
      });

      // 2) CSV’yi URI encode edip postMessage ile Python’a gönder
      const encodedUri = encodeURI(csvContent);
      window.parent.postMessage(
        { type: "flanker_results", data: encodedUri },
        "*"
      );
    }
  </script>

</body>
</html>
"""

# —————————————————————————————————————————————————————————
# 4) Bu HTML+JS’i Streamlit sayfasına göm
# —————————————————————————————————————————————————————————
st_html(html_code, height=800)

# —————————————————————————————————————————————————————————
# 5) JavaScript → Python postMessage köprüsünü dinle
#    Sonuç geldiğinde e-posta ile gönder, Secrets yoksa pas geç
# —————————————————————————————————————————————————————————
if "flanker_sent" not in st.session_state:
    st.session_state["flanker_sent"] = False

def receive_results():
    # JS tarafında window.parent.postMessage ile “flanker_results” tipi yollanmışken
    # Streamlit, bunu URL query parametreleri (“?flanker_results=…”) içine ekler.
    params = st.experimental_get_query_params()
    if "flanker_results" in params and not st.session_state["flanker_sent"]:
        # 1) URI-encoded CSV içeriğini al
        encoded_csv = params["flanker_results"][0]
        import urllib.parse
        decoded = urllib.parse.unquote(encoded_csv)

        # 2) “data:text/csv;charset=utf-8,” prefix’ini çıkart
        prefix = "data:text/csv;charset=utf-8,"
        if decoded.startswith(prefix):
            decoded = decoded[len(prefix):]

        # 3) decoded hali şu formatta: 
        #    "Basılan,DoğruYön,RT(ms),Sonuç\r\nSol,left,345,Doğru\r\n..."
        #    bunu e-posta içeriği olarak kullanacağız.

        # 4) Eğer SMTP ayarları aktifse, e-posta gönder:
        if use_smtp:
            try:
                msg = EmailMessage()
                msg["Subject"] = "Yeni Flanker Alpha Test Sonuçları"
                msg["From"]    = smtp_email
                msg["To"]      = receiver_email
                msg.set_content(decoded)

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_email, smtp_password)
                    server.send_message(msg)

                st.success("✅ Sonuçlar e-posta ile gönderildi.")
            except Exception as e:
                st.error(f"❌ E-posta gönderilirken hata: {e}")
        else:
            st.info("ℹ️ SMTP yapılandırması yapılmadığı için sonuçlar e-posta gönderilmedi.")

        st.session_state["flanker_sent"] = True

# 6) Yukarıdaki JS mesajını kontrol et, geldiyse receive_results() çağrılır
receive_results()
