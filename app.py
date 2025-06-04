import streamlit as st
import random
import time
import csv
from io import StringIO
import base64

# Sayfa ayarı
st.set_page_config(page_title="Flanker Testi - Alpha", layout="centered")

# Başlık
st.title("🧠 Flanker Testi (Alpha 10Hz Müzik ile)")

# Ses oynatıcı (otomatik çalmayı engellemeden)
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

# Gövdeye ses player yerleştir
st.markdown(get_audio_player("Alpha_10Hz.wav"), unsafe_allow_html=True)

# Oturum değişkenleri
if "trial_index" not in st.session_state:
    st.session_state.trial_index = 0
    st.session_state.results = []
    st.session_state.start_time = 0
    st.session_state.arrow = ""
    st.session_state.dir = ""
    st.session_state.step = "start"

# Test başlamadıysa
if st.session_state.step == "start":
    st.info("🎧 Lütfen sesinizi açın ve alttan müziği başlatın.")
    if st.button("Teste Başla"):
        st.session_state.step = "fixation"

# Fixation ekranı (“+” işareti göster)
elif st.session_state.step == "fixation":
    st.markdown("<h1 style='text-align:center; font-size:72px;'>+</h1>", unsafe_allow_html=True)
    time.sleep(1)  # 1 saniye beklet
    st.session_state.step = "trial"
    st.experimental_rerun()

# Test devam ediyorsa
elif st.session_state.step == "trial" and st.session_state.trial_index < 20:
    if st.session_state.start_time == 0:
        st.session_state.dir = random.choice(["left", "right"])
        arrow_chars = ["<"] * 5 if st.session_state.dir == "left" else [">"] * 5
        arrow_chars[2] = "<" if st.session_state.dir == "left" else ">"
        st.session_state.arrow = "".join(arrow_chars)
        st.session_state.start_time = time.time()

    st.markdown(f"<h1 style='text-align:center; font-size:72px;'>{st.session_state.arrow}</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    def handle_response(response):
        rt = round((time.time() - st.session_state.start_time) * 1000)
        correctness = "Doğru" if response == st.session_state.dir else "Hatalı"
        st.session_state.results.append([response, st.session_state.dir, rt, correctness])
        st.session_state.trial_index += 1
        st.session_state.start_time = 0
        st.session_state.step = "fixation"
        st.experimental_rerun()

    with col1:
        if st.button("⬅️ Sol"):
            handle_response("left")
    with col2:
        if st.button("➡️ Sağ"):
            handle_response("right")

# Test tamamlandıysa
elif st.session_state.trial_index >= 20:
    st.success("✅ Test tamamlandı! Aşağıdan sonuçları indirebilirsiniz.")
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Basılan Tuş", "Doğru Yön", "Tepki Süresi (ms)", "Sonuç"])
    writer.writerows(st.session_state.results)
    st.download_button("📥 Sonuçları İndir (.csv)", output.getvalue(), file_name="flanker_alpha_sonuclar.csv", mime="text/csv")
