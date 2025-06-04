import streamlit as st
import random
import time
import csv
from io import StringIO
import base64

# === Sayfa Ayarı ===
st.set_page_config(page_title="Flanker Testi - Alpha", layout="centered")
st.title("🧠 Flanker Testi (Alpha 10Hz Müzik ile)")

# === Ses dosyasını göm ===
def get_audio_html(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        return f"""
        <audio autoplay loop>
            <source src="data:audio/wav;base64,{b64}" type="audio/wav">
        </audio>
        """
st.markdown(get_audio_html("Alpha_10Hz.wav"), unsafe_allow_html=True)

# === Oturum Değişkenleri ===
if "trial_index" not in st.session_state:
    st.session_state.trial_index = 0
    st.session_state.results = []
    st.session_state.start_time = 0
    st.session_state.arrow = ""
    st.session_state.dir = ""
    st.session_state.test_started = False

# === Test Başlat ===
if not st.session_state.test_started:
    st.success("🎧 Lütfen sesiniz açık olsun. Teste hazır mısınız?")
    if st.button("Teste Başla"):
        st.session_state.test_started = True
        st.session_state.trial_index = 1
        st.session_state.dir = random.choice(["left", "right"])
        st.session_state.arrow = "".join(["<", "<", "<", "<", "<"] if st.session_state.dir == "left" else [">", ">", ">", ">", ">"])
        st.session_state.arrow = st.session_state.arrow[:2] + ("<" if st.session_state.dir == "left" else ">") + st.session_state.arrow[3:]
        st.session_state.start_time = time.time()

# === Test Akışı ===
elif st.session_state.trial_index <= 20:
    st.markdown(f"<h1 style='text-align:center;font-size:72px;'>{st.session_state.arrow}</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    def process_response(key_pressed):
        rt = round((time.time() - st.session_state.start_time) * 1000)
        result = "Doğru" if key_pressed == st.session_state.dir else "Hatalı"
        st.session_state.results.append([key_pressed, st.session_state.dir, rt, result])
        st.session_state.trial_index += 1
        if st.session_state.trial_index <= 20:
            st.session_state.dir = random.choice(["left", "right"])
            arrow_chars = ["<"] * 5 if st.session_state.dir == "left" else [">"] * 5
            arrow_chars[2] = "<" if st.session_state.dir == "left" else ">"
            st.session_state.arrow = "".join(arrow_chars)
            st.session_state.start_time = time.time()

    with col1:
        if st.button("⬅️ Sol"):
            process_response("left")
    with col2:
        if st.button("➡️ Sağ"):
            process_response("right")

# === Test Sonu ===
else:
    st.success("✅ Test tamamlandı! Sonuçları aşağıdan indirebilirsiniz.")
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Basılan Tuş", "Doğru Yön", "Tepki Süresi (ms)", "Sonuç"])
    writer.writerows(st.session_state.results)
    st.download_button("📥 Sonuçları İndir (.csv)", output.getvalue(), file_name="flanker_alpha_sonuclar.csv", mime="text/csv")
