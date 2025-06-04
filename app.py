import streamlit as st
import random
import time
import csv
from io import StringIO
import base64
import os

# === Sayfa Ayarı ===
st.set_page_config(page_title="Flanker Testi - Alpha", layout="centered")
st.title("🧠 Flanker Testi (Alpha 10Hz Müzik ile)")

# === Ses dosyasını göm (tarayıcıdan çalmak için) ===
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

# === Test Değişkenleri ===
total_trials = 20
trial_data = []
directions = ["left", "right"]

# === Arrow üret ===
def generate_arrow(direction):
    flankers = ["<"] * 5 if direction == "left" else [">"] * 5
    flankers[2] = "<" if direction == "left" else ">"
    return "".join(flankers)

# === Oturum Durumları ===
if "trial_index" not in st.session_state:
    st.session_state.trial_index = 0
    st.session_state.results = []
    st.session_state.start_time = 0
    st.session_state.arrow = ""
    st.session_state.dir = ""

# === Test Başlangıcı ===
if st.session_state.trial_index == 0:
    st.success("🎧 Lütfen sesiniz açık olsun. Teste hazır mısınız?")
    if st.button("Teste Başla"):
        st.session_state.trial_index += 1
        st.experimental_rerun()

# === Test Ekranı ===
elif 1 <= st.session_state.trial_index <= total_trials:
    if st.session_state.start_time == 0:
        st.session_state.dir = random.choice(directions)
        st.session_state.arrow = generate_arrow(st.session_state.dir)
        st.session_state.start_time = time.time()

    st.markdown(f"<h1 style='text-align:center;font-size:72px;'>{st.session_state.arrow}</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Sol"):
            rt = round((time.time() - st.session_state.start_time) * 1000)
            result = "Doğru" if st.session_state.dir == "left" else "Hatalı"
            st.session_state.results.append(["left", st.session_state.dir, rt, result])
            st.session_state.trial_index += 1
            st.session_state.start_time = 0
            st.experimental_rerun()
    with col2:
        if st.button("➡️ Sağ"):
            rt = round((time.time() - st.session_state.start_time) * 1000)
            result = "Doğru" if st.session_state.dir == "right" else "Hatalı"
            st.session_state.results.append(["right", st.session_state.dir, rt, result])
            st.session_state.trial_index += 1
            st.session_state.start_time = 0
            st.experimental_rerun()

# === Test Bitti ===
elif st.session_state.trial_index > total_trials:
    st.success("✅ Test tamamlandı! Sonuçları aşağıdan indirebilirsiniz.")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Basılan Tuş", "Doğru Yön", "Tepki Süresi (ms)", "Sonuç"])
    writer.writerows(st.session_state.results)

    st.download_button("📥 Sonuçları İndir (.csv)", output.getvalue(), file_name="flanker_alpha_sonuclar.csv", mime="text/csv")
