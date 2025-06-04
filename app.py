import streamlit as st
import random
import time
import csv
from io import StringIO
import base64

# Sayfa ayarı
st.set_page_config(page_title="Flanker Testi - Alpha", layout="centered")
st.title("🧠 Flanker Testi (Alpha 10Hz Müzik ile)")

# Ses oynatıcı
def get_audio_player(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        return f"""
            <audio controls autoplay loop style="width: 100%;">
                <source src="data:audio/wav;base64,{b64}" type="audio/wav">
                Tarayıcınız ses etiketini desteklemiyor.
            </audio>
        """
st.markdown(get_audio_player("Alpha_10Hz.wav"), unsafe_allow_html=True)

# Oturum değişkenleri
if "trial_index" not in st.session_state:
    st.session_state.trial_index = 0
    st.session_state.results = []
    st.session_state.arrow = ""
    st.session_state.dir = ""
    st.session_state.step = "start"
    st.session_state.start_time = 0

# Test başlat
if st.session_state.step == "start":
    st.info("🎧 Lütfen sesi açın ve alttaki müziği başlatın.")
    if st.button("Teste Başla"):
        st.session_state.step = "fixation"

# + işareti
if st.session_state.step == "fixation":
    placeholder = st.empty()
    placeholder.markdown("<h1 style='text-align:center; font-size:72px;'>+</h1>", unsafe_allow_html=True)
    time.sleep(1)
    placeholder.empty()
    st.session_state.step = "trial"
    st.experimental_set_query_params(reload="1")  # Sayfayı sıfırdan yüklemeden geçiş hilesi

# Deneme aşaması
if st.session_state.step == "trial" and st.session_state.trial_index < 20:
    if st.session_state.start_time == 0:
        st.session_state.dir = random.choice(["left", "right"])
        arrows = ["<"] * 5 if st.session_state.dir == "left" else [">"] * 5
        arrows[2] = "<" if st.session_state.dir == "left" else ">"
        st.session_state.arrow = "".join(arrows)
        st.session_state.start_time = time.time()

    st.markdown(f"<h1 style='text-align:center; font-size:72px;'>{st.session_state.arrow}</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    def respond(side):
        rt = round((time.time() - st.session_state.start_time) * 1000)
        result = "Doğru" if side == st.session_state.dir else "Hatalı"
        st.session_state.results.append([side, st.session_state.dir, rt, result])
        st.session_state.trial_index += 1
        st.session_state.start_time = 0
        st.session_state.step = "fixation"

    with col1:
        if st.button("⬅️ Sol"):
            respond("left")
    with col2:
        if st.button("➡️ Sağ"):
            respond("right")

# Test bitti
if st.session_state.trial_index >= 20 and st.session_state.step != "done":
    st.session_state.step = "done"
    st.success("✅ Test tamamlandı!")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Basılan Tuş", "Doğru Yön", "Tepki Süresi (ms)", "Sonuç"])
    writer.writerows(st.session_state.results)

    st.download_button("📥 Sonuçları İndir (.csv)", output.getvalue(), file_name="flanker_alpha_sonuclar.csv", mime="text/csv")
