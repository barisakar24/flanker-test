import streamlit as st
from streamlit.components.v1 import html as st_html
import base64
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
    st.warning("⚠️ SMTP ayarları bulunamadı. E-posta gönderimi devre dışı bırakıldı.")
    use_smtp = False

# —————————————————————————————————————————————————————————
# 3) HTML + JavaScript
#    • 500 ms fixation (“+”)
#    • 150 ms arrow (<<<<<, >>>>>, <<><<, >><>> rastgele)
#    • Arrow sonrası boş ekranda butonlar beklemede
#    • 20 trial bittiğinde sonuçlar Python’a postMessage ile gidiyor
#    • Müzik base64 olarak embed edildi, loop şeklinde çalacak
# —————————————————————————————————————————————————————————

# 3A) Alpha_10Hz.wav’ı base64’e çeviriyoruz:
#     (Kodun bu kısmını değiştirmeyeceksiniz; dosya yeri önemli değil.)
with open("Alpha_10Hz.wav", "rb") as f:
    audio_bytes = f.read()
audio_b64 = base64.b64encode(audio_bytes).decode()

html_code = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <title>Flanker Testi (Alpha 10 Hz)</title>
  <style>
    html, body {{
      margin: 0; padding: 0;
      background-color: white;
      font-family: Arial, sans-serif;
      height: 100vh; overflow: hidden;
    }}
    #container {{
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      user-select: none;
    }}
    #fixation, #arrow {{
      font-size: 72px;
      text-align: center;
      width: 100%;
    }}
    #startMessage {{
      font-size: 24px;
      color: #333;
      text-align: center;
    }}
    button {{
      font-size: 20px;
      padding: 10px 20px;
      margin: 10px;
      border: none;
      border-radius: 8px;
      background-color: #007BFF;
      color: white;
    }}
    button:active {{
      background-color: #0056b3;
    }}
    /* Alt köşelere yerleştirilecek butonlar */
    #leftBtn {{
      position: absolute;
      bottom: 20px;
      left: 20px;
    }}
    #rightBtn {{
      position: absolute;
      bottom: 20px;
      right: 20px;
    }}
  </style>
</head>
<body>

  <!-- 1) Base64 olarak embed edilmiş Alpha_10Hz.wav (loop) -->
  <audio id="bgAudio" loop>
    <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav" />
    Tarayıcınız ses çalmayı desteklemiyor.
  </audio>

  <div id="container">
    <!-- Başlangıç ekranı -->
    <div id="startScreen">
      <div id="startMessage">🎧 Lütfen sesi açın ve “Teste Başla” butonuna basın.</div>
      <button id="startBtn">Teste Başla</button>
    </div>

    <!-- Fixation (+) -->
    <div id="fixation" style="display:none;">+</div>

    <!-- Arrow Stimulus -->
    <div id="arrow" style="display:none;"></div>

    <!-- Alt köşe butonları -->
    <button id="leftBtn" style="display:none;">⬅️ Sol</button>
    <button id="rightBtn" style="display:none;">➡️ Sağ</button>

    <!-- Python’a postMessage için gizli link -->
    <a id="downloadLink" style="display:none;"></a>
  </div>

  <script>
    // ===== Sabitler =====
    const totalTrials       = 20;
    const fixationDuration  = 500;   // ms
    const stimulusDuration  = 150;   // ms (200 ms’den daha kısa)
    const patterns          = ["<<<<<", ">>>>>", "<<><<", ">><>>"];

    let trialIndex          = 0;
    let results             = [];    // [[choice, correctDir, RT, outcome], ...]

    let currentPattern      = "";
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

    // ===== “Teste Başla” butonuna tıklanınca =====
    startBtn.addEventListener("click", () => {{
      bgAudio.play();
      startScreen.style.display = "none";
      runFixation();
    }});

    // ===== Fixation: 500 ms “+” =====
    function runFixation() {{
      fixationEl.style.display = "block";
      arrowEl.style.display    = "none";
      leftBtn.style.display    = "none";
      rightBtn.style.display   = "none";

      setTimeout(() => {{
        fixationEl.style.display = "none";
        runStimulus();
      }}, fixationDuration);
    }}

    // ===== Stimulus: 150 ms Arrow (<<<<<, >>>>>, <<><< veya >><>>) =====
    function runStimulus() {{
      if (trialIndex >= totalTrials) {{
        finishTest();
        return;
      }}

      // 1) Rastgele pattern seç
      currentPattern = patterns[Math.floor(Math.random() * patterns.length)];

      // 2) Ekrana yaz
      arrowEl.innerText = currentPattern;
      arrowEl.style.display  = "block";
      leftBtn.style.display  = "none";
      rightBtn.style.display = "none";

      // 3) RT ölçümü başlat
      stimulusStartTime = performance.now();
      responded = false;

      // 4) 150 ms sonra “arrow”u gizle, butonları göster (boş ekran)
      setTimeout(() => {{
        arrowEl.style.display = "none";
        leftBtn.style.display  = "block";
        rightBtn.style.display = "block";
        attachResponseHandlers();
      }}, stimulusDuration);
    }}

    // ===== Buton dinleyicilerini ekleyelim =====
    function attachResponseHandlers() {{
      leftBtn.onclick = () => {{
        if (!responded) {{
          responded = true;
          const rt = Math.round(performance.now() - stimulusStartTime);
          // middle char: currentPattern[2]
          const correctDir = (currentPattern[2] === "<") ? "left" : "right";
          const outcome    = (correctDir === "left") ? "Doğru" : "Hatalı";
          results.push(["left", correctDir, rt, outcome]);
          cleanupAndNext();
        }}
      }};

      rightBtn.onclick = () => {{
        if (!responded) {{
          responded = true;
          const rt = Math.round(performance.now() - stimulusStartTime);
          const correctDir = (currentPattern[2] === "<") ? "left" : "right";
          const outcome    = (correctDir === "right") ? "Doğru" : "Hatalı";
          results.push(["right", correctDir, rt, outcome]);
          cleanupAndNext();
        }}
      }};
    }}

    // ===== Trial tamamlandığında temizleyip bir sonraki fixation =====
    function cleanupAndNext() {{
      leftBtn.style.display  = "none";
      rightBtn.style.display = "none";
      trialIndex++;
      setTimeout(runFixation, 100);
    }}

    // ===== 20 Trial Bittiğinde Sonuçları Python’a Gönder =====
    function finishTest() {{
      fixationEl.style.display = "none";
      arrowEl.style.display    = "none";
      leftBtn.style.display    = "none";
      rightBtn.style.display   = "none";

      // Mesaj: “Test tamamlandı”
      const msg = document.createElement("div");
      msg.innerHTML = "<h2>✅ Test tamamlandı!</h2>";
      msg.style.marginTop = "30px";
      container.appendChild(msg);

      // 1) CSV verisini hazırla
      let csvContent = "data:text/csv;charset=utf-8,";
      csvContent += ["Basılan","DoğruYön","RT(ms)","Sonuç"].join(",") + "\\r\\n";
      results.forEach(row => {{
        csvContent += row.join(",") + "\\r\\n";
      }});

      // 2) CSV’yi URI encode edip postMessage ile Python’a gönder
      const encodedUri = encodeURI(csvContent);
      window.parent.postMessage(
        {{ type: "flanker_results", data: encodedUri }},
        "*"
      );

      // 3) Gizli link’i ayarla
      downloadLink.href = encodedUri;
      downloadLink.download = "flanker_alpha_sonuclar.csv";
      downloadLink.style.display = "none";
    }}
  </script>

</body>
</html>
"""

# —————————————————————————————————————————————————————————
# 4) Yukarıdaki HTML+JS’i embed et (height = 800 veya ihtiyaca göre arttırın)
# —————————————————————————————————————————————————————————
st_html(html_code, height=800)

# —————————————————————————————————————————————————————————
# 5) JS → Python postMessage köprüsü: st.query_params kullanıyoruz
# —————————————————————————————————————————————————————————
if "flanker_sent" not in st.session_state:
    st.session_state["flanker_sent"] = False

def receive_results():
    params = st.query_params  # st.experimental_get_query_params yerine st.query_params
    if "flanker_results" in params and not st.session_state["flanker_sent"]:
        encoded_csv = params["flanker_results"][0]
        import urllib.parse
        decoded = urllib.parse.unquote(encoded_csv)

        # “data:text/csv;charset=utf-8,” prefix’ini çıkar
        prefix = "data:text/csv;charset=utf-8,"
        if decoded.startswith(prefix):
            decoded = decoded[len(prefix):]

        # E-posta gönderimi (Secrets tanımlıysa)
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

receive_results()
