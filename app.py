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
#    .streamlit/secrets.toml’da [smtp] bölümü varsa getirmeye çalışacağız.
# —————————————————————————————————————————————————————————
use_smtp = False
try:
    smtp_email     = st.secrets["smtp"]["email"]
    smtp_password  = st.secrets["smtp"]["password"]
    smtp_server    = st.secrets["smtp"]["smtp_server"]
    smtp_port      = st.secrets["smtp"]["smtp_port"]
    receiver_email = st.secrets["smtp"]["receiver"]
    use_smtp = True
except KeyError:
    # Secrets tanımlı değilse, e-posta gönderimini atla (sadece uyarı göster)
    st.warning("⚠️ SMTP ayarları bulunamadı. E-posta gönderimi devre dışı bırakıldı.")
    use_smtp = False

# —————————————————————————————————————————————————————————
# 3) HTML + JavaScript (Mobil uyumlu, alt köşede butonlar, zamanlama JS ile)
#    • Fixation: 500 ms
#    • Arrow stimulus: 200 ms (sonra ortada boş ekran, butonlar beklemede)
#    • “Sol”/“Sağ” butonları alt köşe
#    • 20 trial bittiğinde CSV → Python’a postMessage
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
    /* Alt köşe butonları */
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

  <!-- 1) Alpha müziği (loop) -->
  <audio id="bgAudio" loop>
    <source src="Alpha_10Hz.wav" type="audio/wav" />
    Tarayıcınız ses çalmayı desteklemiyor.
  </audio>

  <div id="container">
    <!-- Başlangıç ekranı -->
    <div id="startScreen">
      <div id="startMessage">🎧 Lütfen sesi açın ve “Teste Başla” butonuna basın.</div>
      <button id="startBtn">Teste Başla</button>
    </div>

    <!-- Fixation: + -->
    <div id="fixation" style="display:none;">+</div>

    <!-- Arrow stimulus -->
    <div id="arrow" style="display:none;"></div>

    <!-- Alt köşe butonları -->
    <button id="leftBtn" style="display:none;">⬅️ Sol</button>
    <button id="rightBtn" style="display:none;">➡️ Sağ</button>

    <!-- Sonuçları Python’a postlamak için gizli link -->
    <a id="downloadLink"></a>
  </div>

  <script>
    // ===== Temel Sabitler =====
    const totalTrials       = 20;
    const fixationDuration  = 500;   // ms
    const stimulusDuration  = 200;   // ms → arrow 200 ms göster
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
      // 1) Müzik çalmayı başlat (user interaction gerektiriyor)
      bgAudio.play();

      // 2) Başlangıç ekranını gizle, fixation aşamasına geç
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

    // ===== Arrow Stimulus (200 ms) =====
    function runStimulus() {
      if (trialIndex >= totalTrials) {
        finishTest();
        return;
      }

      // 1) Rastgele bir yön seç ve arrowText hazırla
      currentDirection = directions[Math.floor(Math.random() * directions.length)];
      let arr = currentDirection === "left"
                ? ["<","<","<","<","<"]
                : [">",">",">",">",">"];
      arr[2] = currentDirection === "left" ? "<" : ">";
      arrowText = arr.join("");

      // 2) Arrow’u ekranda göster
      arrowEl.innerText = arrowText;
      arrowEl.style.display  = "block";
      leftBtn.style.display  = "none";  // arrow süresince buton gizli
      rightBtn.style.display = "none";

      // 3) RT’yi başlat
      stimulusStartTime = performance.now();
      responded = false;

      // 4) Arrow 200 ms gösteriliyor, sonra arrow’u gizle, BUTONLARI aç (blank ekran)
      setTimeout(() => {
        arrowEl.style.display = "none";
        leftBtn.style.display  = "block";
        rightBtn.style.display = "block";

        // 5) Butonlara tıklanmayı dinlemeye hazırla
        leftBtn.onclick = () => {
          if (!responded) {
            responded = true;
            const rt  = Math.round(performance.now() - stimulusStartTime);
            const correct = (currentDirection === "left") ? "Doğru" : "Hatalı";
            results.push(["left", currentDirection, rt, correct]);
            cleanupAndNext();
          }
        };

        rightBtn.onclick = () => {
          if (!responded) {
            responded = true;
            const rt  = Math.round(performance.now() - stimulusStartTime);
            const correct = (currentDirection === "right") ? "Doğru" : "Hatalı";
            results.push(["right", currentDirection, rt, correct]);
            cleanupAndNext();
          }
        };

        // 6) Zaman aşımı: Eğer kullanıcı butonlara tıklamazsa, Timeout yok
        //    (kullanıcıya sonsuzca bekliyor). Bu nedenle otomatik “Yanıtsız” yok.
        //    Eğer istenirse otomatik zaman aşımı eklenebilirdi, ama talimatınıza
        //    “boş ekran kalacak, kullanıcı cevaplayana kadar beklesin” dediniz.

      }, stimulusDuration);
    }

    // ===== Trial tamamlandığında: butonları gizle, sıradaki fixation için bekle =====
    function cleanupAndNext() {
      leftBtn.style.display  = "none";
      rightBtn.style.display = "none";
      trialIndex++;
      setTimeout(runFixation, 100);  // Küçük bir gecikmeyle bir sonraki fixation
    }

    // ===== 20 trial bittiğinde sonuçları Python’a yolla =====
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

      // 3) İndirilebilir linki hazırlıyoruz (kullanıcıya gösterilmeyecek)
      downloadLink.href = encodedUri;
      downloadLink.download = "flanker_alpha_sonuclar.csv";
      downloadLink.style.display = "none";
    }
  </script>

</body>
</html>
"""

# —————————————————————————————————————————————————————————
# 4) HTML+JS bileşenini Streamlit sayfasına göm
# —————————————————————————————————————————————————————————
st_html(html_code, height=800)

# —————————————————————————————————————————————————————————
# 5) JS → Python postMessage köprüsünü dinle: st.query_params kullan
#    Gelen CSV’yi decode edip e-posta olarak gönder
# —————————————————————————————————————————————————————————
if "flanker_sent" not in st.session_state:
    st.session_state["flanker_sent"] = False

def receive_results():
    # Streamlit, JS'ten gelen postMessage verisini "query_params" içine ekler
    params = st.query_params
    if "flanker_results" in params and not st.session_state["flanker_sent"]:
        encoded_csv = params["flanker_results"][0]  # URI encoded CSV
        import urllib.parse
        decoded = urllib.parse.unquote(encoded_csv)

        # "data:text/csv;charset=utf-8," önekini çıkar
        prefix = "data:text/csv;charset=utf-8,"
        if decoded.startswith(prefix):
            decoded = decoded[len(prefix):]

        # Eğer SMTP yapılandırması varsa e-posta gönder
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

# JS mesajını kontrol et
receive_results()
