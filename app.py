import streamlit as st
import random
import time
import csv
from io import StringIO
import base64

st.set_page_config(page_title="Flanker Testi - Alpha", layout="centered")
st.title("🧠 Flanker Testi (Alpha 10Hz Müzik ile)")

# ——————————————————————————————————————————————
# 1) Ses oynatıcı bölümü (kullanıcı manuel başlatacak)
# ——————————————————————————————————————————————
def get_audio_player(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        return f"""
            <audio controls loop style="width: 100%;">
                <source src="data:audio/wav;base64,{b64}" type="audio/wav">
                Tarayıcınız ses çalmayı desteklemiyor.
            </audio>
        """

st.markdown(get_audio_player("Alpha_10Hz.wav"), unsafe_allow_html=True)
st.markdown("---")

# ——————————————————————————————————————————————
# 2) Session State tanımlamaları
# ——————————————————————————————————————————————
if "step" not in st.session_state:
    st.session_state.step = "start"
    st.session_state.trial_index = 0
    st.session_state.results = []      # [["Sol"|"Sağ"|"Yok", doğru yön, RT(ms), sonuç], ...]
    st.session_state.waiting_arrow = False
    st.session_state.start_time = 0
    st.session_state.dir = ""          # O denemedeki doğru yön
    st.session_state.arrow_text = ""   # <<<><<<< gibi ok gösterimi

# ——————————————————————————————————————————————
# 3) Akış Kontrolü
# ——————————————————————————————————————————————

# 3.1) BAŞLANGIÇ EKRANI
if st.session_state.step == "start":
    st.info("🎧 Lütfen sesinizi açın. Aşağıdaki müziği oynatın, sonra testi başlatın.")
    if st.button("Teste Başla"):
        st.session_state.step = "fixation"
        st.experimental_rerun()  # Bu kadar

# 3.2) FIXATION EKRANI: önce “+” işareti gösteriyoruz, 500ms sabitlemiyoruz,
#      bunun yerine kullanıcı “+” gördüğünü onaylasın diyoruz.
elif st.session_state.step == "fixation":
    st.markdown("<h1 style='text-align:center; font-size:72px;'>+</h1>", unsafe_allow_html=True)
    st.write("**“+” işaretini gördüğünüzde aşağıdaki “Görüldü” butonuna tıklayın.**")
    if st.button("✅ Görüldü"):
        # “+” ekranı bitti, okları göstereceğiz
        st.session_state.step = "trial"
        st.session_state.waiting_arrow = True
        st.experimental_rerun()

# 3.3) DENEME AŞAMASI
#      - “waiting_arrow” True iken okları gösteriyoruz ve RT ölçüyoruz.
#      - Kullanıcı “Sol” veya “Sağ” veya “Yanıtsız” butonuna tıkladığında yanıt kaydedilip
#        bir sonraki denemeye (fixation) geçiyoruz.
elif st.session_state.step == "trial" and st.session_state.trial_index < 20:

    # 3.3.1) Eğer henüz ok göstermedikse, önce “dir” ve “arrow_text” atayıp
    #         start_time=şu an olarak kaydedelim.
    if st.session_state.waiting_arrow:
        st.session_state.dir = random.choice(["left", "right"])
        arrows = ["<"] * 5 if st.session_state.dir == "left" else [">"] * 5
        arrows[2] = "<" if st.session_state.dir == "left" else ">"
        st.session_state.arrow_text = "".join(arrows)
        st.session_state.start_time = time.time()
        st.session_state.waiting_arrow = False

    # 3.3.2) Arrow’ı göster
    st.markdown(f"<h1 style='text-align:center; font-size:72px;'>{st.session_state.arrow_text}</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("⬅️ Sol"):
            rt = round((time.time() - st.session_state.start_time)*1000)
            result = "Doğru" if st.session_state.dir == "left" else "Hatalı"
            st.session_state.results.append(["Sol", st.session_state.dir, rt, result])
            st.session_state.trial_index += 1
            st.session_state.step = "fixation"
            st.experimental_rerun()

    with col2:
        if st.button("➡️ Sağ"):
            rt = round((time.time() - st.session_state.start_time)*1000)
            result = "Doğru" if st.session_state.dir == "right" else "Hatalı"
            st.session_state.results.append(["Sağ", st.session_state.dir, rt, result])
            st.session_state.trial_index += 1
            st.session_state.step = "fixation"
            st.experimental_rerun()

    with col3:
        if st.button("⏱️ Yanıtsız"):
            st.session_state.results.append(["Yok", st.session_state.dir, "–", "Yanıtsız"])
            st.session_state.trial_index += 1
            st.session_state.step = "fixation"
            st.experimental_rerun()

    # 3.3.3) OTOMATİK ZAMAN AŞIMI
    #         (Eğer kullanıcı 1500 ms içinde hiç tıklamazsa,
    #          “Yanıtsız” kabul edip bir sonraki denemeye geçiyoruz.)
    if time.time() - st.session_state.start_time > 1.5 and st.session_state.step == "trial":
        st.session_state.results.append(["Yok", st.session_state.dir, "–", "Yanıtsız"])
        st.session_state.trial_index += 1
        st.session_state.step = "fixation"
        st.experimental_rerun()

# 3.4) TEST BİTTİKTE SONUÇ EKRANI
elif st.session_state.trial_index >= 20:
    st.success("✅ Test tamamlandı! Sonuçları aşağıdan indirebilirsiniz.")
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Basılan Tuş", "Doğru Yön", "Tepki Süresi (ms)", "Sonuç"])
    writer.writerows(st.session_state.results)
    st.download_button("📥 Sonuçları İndir (.csv)", output.getvalue(),
                       file_name="flanker_alpha_sonuclar.csv", mime="text/csv")
