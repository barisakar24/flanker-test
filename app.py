import streamlit as st
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="Flanker Testi - Alpha", layout="centered")
st.title("🧠 Flanker Testi (Alpha 10 Hz Müzik ile)")

# —————————————————————————————————————————————————————————
# HTML + JavaScript tarafı:
#  • 500 ms fixation (“+”)
#  • 1500 ms arrow stimulus
#  • Klavye ←/→ tuşunu dinle, ya da 1500 ms sonunda “Yanıtsız”
#  • 20 trial tamamlandığında CSV olarak indirilebilir.
#  • Alpha_10Hz.wav otomatik loop ile çalar.
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
    #message {
      margin-top: 40px;
      font-size: 24px;
      color: #333;
    }
    #downloadLink {
      margin-top: 30px;
      font-size: 20px;
      text-decoration: none;
      color: white;
      background-color: #007BFF;
      padding: 10px 20px;
      border-radius: 8px;
      display: none;
    }
    #downloadLink:hover {
      background-color: #0056b3;
    }
    button {
      font-size: 20px;
      padding: 10px 20px;
      margin-top: 20px;
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
      <div id="message">🎧 Lütfen sesinizi açın ve müziği başlatın.</div>
      <button id="startBtn">Teste Başla</button>
    </div>

    <!-- Fixation için + -->
    <div id="fixation" style="display:none;">+</div>

    <!-- Arrow stimulus -->
    <div id="arrow" style="display:none;"></div>

    <!-- Test tamamlandığında indirme linki -->
    <a id="downloadLink">📥 Sonuçları İndir (.csv)</a>
  </div>

  <script>
    // ===== Sabitler =====
    const totalTrials = 20;
    const fixationDuration = 500;   // ms
    const stimulusDuration = 1500;  // ms
    const directions = ["left","right"];

    let trialIndex = 0;
    let results = []; // [[choice, correctDir, RT(ms), "Doğru"/"Hatalı"/"Yanıtsız"], ...]

    let currentDirection = "";
    let arrowText = "";
    let stimulusStartTime = 0;

    // ===== DOM referansları =====
    const bgAudio      = document.getElementById("bgAudio");
    const startScreen  = document.getElementById("startScreen");
    const startBtn     = document.getElementById("startBtn");
    const fixationEl   = document.getElementById("fixation");
    const arrowEl      = document.getElementById("arrow");
    const downloadLink = document.getElementById("downloadLink");

    // ===== “Teste Başla” butonuna tıklandığında =====
    startBtn.addEventListener("click", () => {
      bgAudio.play();               // Müzik çalmaya başla
      startScreen.style.display = "none";
      runFixation();                // Fixation aşamasına geç
    });

    // ===== Fixation (500 ms) =====
    function runFixation() {
      fixationEl.style.display = "block";
      arrowEl.style.display = "none";
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

      // A) Rastgele yön seç ve arrowText hazırla
      currentDirection = directions[Math.floor(Math.random() * directions.length)];
      let arr = [];
      if (currentDirection === "left") {
        arr = ["<","<","<","<","<"];
      } else {
        arr = [">",">",">",">",">"];
      }
      arr[2] = currentDirection === "left" ? "<" : ">";
      arrowText = arr.join("");

      // B) Arrow’u göster
      arrowEl.innerText = arrowText;
      arrowEl.style.display = "block";

      // C) RT ölçümünü başlat
      stimulusStartTime = performance.now();
      let responded = false;

      // D) Klavye dinle
      function keyListener(e) {
        if (!responded && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
          responded = true;
          const rt = Math.round(performance.now() - stimulusStartTime);
          let choice = e.key === "ArrowLeft" ? "left" : "right";
          let correct = (choice === currentDirection) ? "Doğru" : "Hatalı";
          results.push([choice, currentDirection, rt, correct]);

          window.removeEventListener("keydown", keyListener);
          arrowEl.style.display = "none";
          trialIndex++;
          setTimeout(runFixation, 100);
        }
      }
      window.addEventListener("keydown", keyListener);

      // E) Zaman aşımı (1500 ms)
      setTimeout(() => {
        if (!responded) {
          responded = true;
          window.removeEventListener("keydown", keyListener);
          results.push(["Yok", currentDirection, "–", "Yanıtsız"]);
          arrowEl.style.display = "none";
          trialIndex++;
          setTimeout(runFixation, 100);
        }
      }, stimulusDuration);
    }

    // ===== Test tamamlandığında =====
    function finishTest() {
      fixationEl.style.display = "none";
      arrowEl.style.display = "none";
      const msg = document.createElement("div");
      msg.innerHTML = "<h2>✅ Test tamamlandı!</h2>";
      msg.style.marginTop = "30px";
      document.getElementById("container").appendChild(msg);

      // CSV oluştur
      let csvContent = "data:text/csv;charset=utf-8,";
      csvContent += ["Basılan","DoğruYön","RT(ms)","Sonuç"].join(",") + "\\r\\n";
      results.forEach(row => {
        csvContent += row.join(",") + "\\r\\n";
      });

      // İndirilebilir linki ayarla
      const encodedUri = encodeURI(csvContent);
      downloadLink.href = encodedUri;
      downloadLink.download = "flanker_alpha_sonuclar.csv";
      downloadLink.style.display = "inline-block";
      downloadLink.innerText = "📥 Sonuçları İndir (.csv)";
    }
  </script>

</body>
</html>
"""

# Streamlit içinde embed et
st_html(html_code, height=700)
