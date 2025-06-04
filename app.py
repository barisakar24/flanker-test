import streamlit as st
import random
import time
import csv
from io import StringIO
import base64

# Sayfa başlığı
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
                Tarayıcınız ses çalmayı desteklemiyor.
            </audio>
        """
st.markdown(get_audio_player("Alpha_10Hz.wav"), unsafe_allow_html=True)

# Oturum değişkenleri
if "step" not in st.session_state:
    st.session_state.step = "start"
    st.session_state.trial_index = 0
    st.session_state.results = []
    st.session_state.start_time = 0
    st.session_state.arrow = ""
    st.session_state.dir = ""
    st.session_state.waiting = False

# Başlat
if st.session_state.step == "start":
    if st.button("🎧 Başlamak için tıkla"):
        st.session_state.step = "fixation"

# Fixation süresi: 500ms
if st.session_state.step == "fixation":
    st.markdown("<h1 style='text-align:center; font-size:72px;'>+</h1>", unsafe_allow_html=True)
    time.sleep(0.5)  # 500ms
    st.session_state.step = "trial"
    st.session_state.start_time = 0
    st.experimental_rerun()

# Oklar gösteriliyor (maksimum 1500ms tepki süresi)
elif st.session_state.step == "trial" and st.session_state.trial_index < 20:
    if st.session_state.start_time == 0:
        st.session_state.dir = random.choice(["left", "right"])
        arrows = ["<"] * 5 if st.session_state.dir == "left" else [">"] * 5
        arrows[2] = "<" if st.session_state.dir == "left" else ">"
        st.session_state.arrow = "".join(arrows)
        st.session_state.start_time = time.time()
        st.session_state.waiting = True

    st.markdown(f"<h1 style='text-align:center; font-size:72px;'>{st.session_state.arrow}</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    def respond(choice):
        rt = round((time.time() - st.session_state.start_time) * 1000)
        result = "Doğru" if choice == st.session_state.dir else "Hatalı"
        st.session_state.results.append([choice, st.session_state.dir, rt, result])
        st.session_state.trial_index += 1
        st.session_state.step = "fixation"
        st.session_state.start_time = 0
        st.session_state.waiting = False
        st.experimental_rerun()

    with col1:
        if st.button("⬅️ Sol") and st.session_state.waiting:
            respond("left")
    with col2:
        if st.button("➡️ Sağ") and st.session_state.waiting:
            respond("right")

    # Otomatik zaman aşımı: 1500ms içinde yanıt gelmezse "Yanıtsız"
    if st.session_state.waiting and time.time() - st.session_state.start_time > 1.5:
        st.session_state.results.append(["Yok", st.session_state.dir, "Yanıt yok", "Yanıtsız"])
        st.session_state.trial_index += 1
        st.session_state.step = "fixation"
        st.session_state.start_time = 0
        st.session_state.waiting = False
        st.experimental_rerun()

# Test bitti
elif st.session_state.trial_index >= 20:
    st.success("✅ Test tamamlandı!")
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Basılan Tuş", "Doğru Yön", "Tepki Süresi (ms)", "Sonuç"])
    writer.writerows(st.session_state.results)
    st.download_button("📥 Sonuçları İndir (.csv)", output.getvalue(), file_name="flanker_alpha_sonuclar.csv", mime="text/csv")
