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
# 2) E-posta Ayarları (Streamlit Secrets üzerinden doldurulacak)
#    secrets.toml dosyanız şu anahtarları içermeli:
#
#    [smtp]
#    email         = "sizin_email@gmail.com"
#    password      = "gmail_app_password"   # Gmail için "App Şifresi"
#    smtp_server   = "smtp.gmail.com"
#    smtp_port     = 587
#    receiver      = "alici_email@domain.com"  # Sonuçları alacak araştırmacı e-posta
# —————————————————————————————————————————————————————————
smtp_email      = st.secrets["smtp"]["email"]
smtp_password   = st.secrets["smtp"]["password"]
smtp_server     = st.secrets["smtp"]["smtp_server"]
smtp_port       = st.secrets["smtp"]["smtp_port"]
receiver_email  = st.secrets["smtp"]["receiver"]

# —————————————————————————————————————————————————————————
# 3) HTML + JavaScript (Mobil uyumlu, butonlar alt köşede, zamanlama JS ile)
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
      <div id="startMessage">🎧 Lütfen sesinizi açın ve “Teste Başla” tuşuna basın.</div>
      <button id="startBtn">Teste Başla</button>
    </div>

    <!-- Fixation için + -->
    <div id="fixation" style="display:none;">+</div>

    <!-- Arrow stimulus -->
    <div id="arrow" style="display:none;"></div>

    <!-- Alt köşe butonları -->
    <button id="leftBtn" style="display:none;">⬅️ Sol</button>
    <button id="rightBtn" style="display:none;">➡️ Sağ</button>

    <!-- Test tamamlandığında gösterilecek indirme veya gönderme linki-->
    <a id="downloadLink">📥 Sonuçları İndir (.csv)</a>
  </div>

  <script>
    // ===== Sabitler =====
    const totalTrials       = 20;
    const fixationDuration  = 500;   // ms (fixation için)
    const stimulusDuration  = 1500;  // ms (arrow stimulus için)
    const directions        = ["left","right"];

    let trialIndex          = 0;
    let results             = [];    // [ [choice, correctDir, RT(ms), outcome], ... ]

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
      // 1) Müzik çalmayı başlat
      bgAudio.play();

      // 2) Başlangıç ekranını gizle, fixation’a geç
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

      // 6) Zaman aşımı: 1500 ms içinde bir tıklama olmazsa “Yanıtsız”
      setTimeout(() => {
        if (!responded) {
          responded = true;
          results.push(["Yok", currentDirection, "–", "Yanıtsız"]);
          cleanupAndNext();
        }
      }, stimulusDuration);
    }

    // ===== Trial tamamlandığında butonları ve arrow’u gizle, bir sonraki fixation’a geç =====
    function cleanupAndNext() {
      arrowEl.style.display  = "none";
      leftBtn.style.display  = "none";
      rightBtn.style.display = "none";
      trialIndex++;
      setTimeout(runFixation, 100);  // Kısa bir gecikme sonrası fixation  
    }

    // ===== 20 trial bitince sonuçları hazırlayıp geri yolla =====
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

      // 1) CSV verisini oluştur
      let csvContent = "data:text/csv;charset=utf-8,";
      csvContent += ["Basılan","DoğruYön","RT(ms)","Sonuç"].join(",") + "\\r\\n";
      results.forEach(row => {
        csvContent += row.join(",") + "\\r\\n";
      });

      // 2) CSV’yi base64’e çevir
      const encodedUri = encodeURI(csvContent);
      downloadLink.href = encodedUri;
      downloadLink.download = "flanker_alpha_sonuclar.csv";
      // Ama indirme linki kullanıcıya gösterilmeyecek:
      downloadLink.style.display = "none";

      // 3) Node olarak “hiddenLink” ekleyelim, sonra Streamlit’e JS → Python köprüsünden gönderelim
      downloadLink.id = "hiddenDownload";
      container.appendChild(downloadLink);

      // 4) Sonuçları Python tarafına POST’la → “Streamlit message” olayı
      //    (Streamlit içinde window.parent.postMessage(...) kullanılacak):
      window.parent.postMessage(
        { type: "flanker_results", data: csvContent },
        "*"
      );
    }
  </script>

</body>
</html>
"""

# —————————————————————————————————————————————————————————
# 4) Streamlit içine bu HTML + JS’i embed et (yukarıdaki kodu göm)
# —————————————————————————————————————————————————————————
st_html(html_code, height=800)

# —————————————————————————————————————————————————————————
# 5) Streamlit → JavaScript’tan gelen “flanker_results” postMessage’ı yakala
#    ve e-posta ile gönder
# —————————————————————————————————————————————————————————
if "flanker_results_sent" not in st.session_state:
    st.session_state["flanker_results_sent"] = False

# Bu helper fonksiyon, JS→Python köprüsü için kullanılacak.
def receive_results():
    import json
    # JS tarafı window.parent.postMessage ile “data”yı gönderdiğinde
    # Streamlit, bu callback’i çağırır. Burada e-posta ile gönderimi yapacağız.
    # Note: `st.experimental_get_query_params()` kullanarak posta okuyacağız.
    # Ancak, tarayıcıda postMessage kullanan Streamlit, bu veriyi “st.experimental_get_query_params”’e
    # “?flanker_results=...” gibi ekler. Aşağıda buna göre parse ediyoruz.

    params = st.experimental_get_query_params()
    if "flanker_results" in params and not st.session_state["flanker_results_sent"]:
        csv_data = params["flanker_results"][0]  # URI encoded CSV içeriği

        # 1) URI decode edin
        import urllib.parse
        decoded = urllib.parse.unquote(csv_data)

        # 2) “data:text/csv;charset=utf-8,” kısmını çıkar
        prefix = "data:text/csv;charset=utf-8,"
        if decoded.startswith(prefix):
            decoded = decoded[len(prefix):]

        # 3) decoded içinde, her satır “\r\n” ayracı ile
        #    Örneğin şu formatta: "Basılan,DoğruYön,RT(ms),Sonuç\r\nSol,left,345,Doğru\r\n..."
        #    E-posta gönderimi için plain text olarak kullanacağız.

        # 4) E-postayı hazırla ve gönder
        try:
            msg = EmailMessage()
            msg["Subject"] = "Yeni Flanker Alpha Test Sonuçları"
            msg["From"] = smtp_email
            msg["To"] = receiver_email
            msg.set_content(decoded)

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.send_message(msg)

            st.success("✅ Sonuçlar başarılı bir şekilde gönderildi.")
        except Exception as e:
            st.error(f"❌ E-posta gönderilirken bir hata oluştu: {e}")

        st.session_state["flanker_results_sent"] = True

# 6) “JS → Python” mesajını kontrol et
receive_results()
