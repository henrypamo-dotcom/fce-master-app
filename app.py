import streamlit as st
import pandas as pd
import time

# ==============================================================================
# 1. CONFIGURACIÓN Y ESTILOS (CSS)
# ==============================================================================
st.set_page_config(page_title="FCE Exam Simulator", page_icon="🇬🇧", layout="wide")

st.markdown("""
    <style>
    /* Estilo para las instrucciones azules */
    .instruction-box { 
        background-color: #e3f2fd; 
        padding: 15px; 
        border-radius: 8px; 
        border-left: 5px solid #2196F3; 
        margin-bottom: 20px;
        color: #0d47a1;
    }
    /* Caja del texto principal */
    .text-box { 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 10px; 
        border: 1px solid #e0e0e0; 
        font-family: 'Georgia', serif; 
        font-size: 19px; 
        line-height: 1.8; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
    }
    /* Estilos para los huecos */
    .gap-highlight { background-color: #e3f2fd; padding: 2px 6px; border-radius: 4px; border: 1px solid #90caf9; font-weight: bold; color: #1565c0; }
    .gap-correct { background-color: #e8f5e9; padding: 2px 6px; border-radius: 4px; border: 1px solid #66bb6a; font-weight: bold; color: #2e7d32; }
    
    /* Estilo para la palabra raíz en Part 3 */
    .root-word { 
        font-size: 24px; 
        color: #c2185b; 
        font-weight: 800; 
        text-align: center; 
        border: 2px solid #f8bbd0; 
        padding: 10px; 
        border-radius: 8px; 
        background-color: #fce4ec; 
    }
    /* Feedback Box */
    .result-box { background-color: #f1f8e9; padding: 15px; border-radius: 8px; border-left: 6px solid #4CAF50; margin-top: 15px; }
    .full-sentence { font-size: 18px; color: #2e7d32; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNCIÓN DE CARGA DE DATOS (ROBUSTA)
# ==============================================================================
# Modificación 1: Motor de lectura más inteligente
def load_data(filename, required_cols):
    try:
        # Usamos engine='python' y sep=None para que detecte automáticamente el separador
        # quotechar='"' ayuda a manejar las comas dentro de los textos
        df = pd.read_csv(filename, on_bad_lines='skip', engine='python', quotechar='"')
        
        # --- DEBUG VISUAL (Solo para ti) ---
        # Si ves este número bajo (ej: 1 o 2), es que el CSV sigue mal. Debería ser 6 o más.
        st.sidebar.caption(f"File: {filename} | Loaded: {len(df)} rows") 
        # -----------------------------------
        
        return df.dropna(subset=required_cols)
    except Exception:
        return None

# ==============================================================================
# 3. LÓGICA: PART 1 (MULTIPLE CHOICE)
# ==============================================================================
def run_part_1():
    st.header("🔡 Part 1: Multiple Choice Cloze")
    df = load_data('fce_part1.csv', ['Text', 'Answers', 'Options'])
    
    if df is None or df.empty:
        st.error("⚠️ Error: Could not find 'fce_part1.csv'. Please upload it to GitHub.")
        return

    # --- Setup ---
    if 'p1_active' not in st.session_state: st.session_state.p1_active = False

    if not st.session_state.p1_active:
        st.markdown("<div class='instruction-box'><b>Instructions:</b> Read the text. For each gap (1-8), choose the best word (A, B, C, or D). Focus on collocations and phrasal verbs.</div>", unsafe_allow_html=True)
        time_limit = st.slider("⏱️ Time Limit (seconds):", 60, 600, 300, 30, key="slider_p1")
        
        if st.button("🚀 Start Part 1", type="primary"):
            st.session_state.p1_data = df.sample(1).iloc[0]
            st.session_state.p1_active = True
            st.session_state.p1_start = time.time()
            st.session_state.p1_limit = time_limit
            st.rerun()

    # --- Exam ---
    else:
        row = st.session_state.p1_data
        respuestas = str(row['Answers']).split('|')
        opciones_raw = str(row['Options']).split('|')
        opciones_matriz = [opt.split('/') for opt in opciones_raw]

        # Timer
        elapsed = time.time() - st.session_state.p1_start
        remaining = max(0, st.session_state.p1_limit - elapsed)
        st.progress(min(1.0, elapsed / st.session_state.p1_limit), text=f"Time Remaining: {int(remaining)}s")

        # Header
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1: st.subheader(f"Topic: {row['Title']}")
        with col_t2: 
             if 'URL' in row and pd.notna(row['URL']): st.link_button("📖 Source", row['URL'])

        # Text Display
        texto_visual = str(row['Text'])
        for i in range(1, len(respuestas) + 1):
            texto_visual = texto_visual.replace(f"_{i}_", f"<span class='gap-highlight'>({i}) .......</span>")
        st.markdown(f"<div class='text-box'>{texto_visual}</div>", unsafe_allow_html=True)
        
        st.divider()

        # Questions Grid
        with st.form("form_p1"):
            user_ans = []
            cols = st.columns(2)
            for i in range(len(respuestas)):
                with cols[i % 2]:
                    if i < len(opciones_matriz):
                        user_ans.append(st.radio(f"**Gap {i+1}**", opciones_matriz[i], horizontal=True, index=None, key=f"p1_q{i}"))
                    else:
                        user_ans.append(None)
            
            submitted = st.form_submit_button("Submit Answers", type="primary")

        # Results
        if submitted:
            final_time = time.time() - st.session_state.p1_start
            score = 0
            
            if final_time > st.session_state.p1_limit:
                 st.error(f"⏰ TIME OUT! You took {int(final_time)}s.")
            else:
                 st.success(f"✅ Submitted in {int(final_time)}s.")

            st.write("### 📊 Results")
            for i, (u, c) in enumerate(zip(user_ans, respuestas)):
                c = c.strip()
                u = u if u else "None"
                if u == c:
                    st.write(f"Gap {i+1}: ✅ **{c}**")
                    score += 1
                else:
                    st.write(f"Gap {i+1}: ❌ You said *{u}* | Correct: **{c}**")

            st.metric("Final Score", f"{score}/{len(respuestas)}")
            
            # Full Text Reconstruction
            st.markdown("---")
            st.info("📖 **Full Corrected Text:**")
            full_text = str(row['Text'])
            for i, ans in enumerate(respuestas):
                full_text = full_text.replace(f"_{i+1}_", f"<span class='gap-correct'>{ans}</span>")
            st.markdown(f"<div class='text-box'>{full_text}</div>", unsafe_allow_html=True)

            if st.button("🔄 Try Another Text"):
                st.session_state.p1_active = False
                st.rerun()

# ==============================================================================
# 4. LÓGICA: PART 2 (OPEN CLOZE)
# ==============================================================================
def run_part_2():
    st.header("🧩 Part 2: Open Cloze")
    df = load_data('fce_open_cloze.csv', ['Text', 'Answers'])
    
    if df is None or df.empty:
        st.error("⚠️ Error: Could not find 'fce_open_cloze.csv'.")
        return

    if 'p2_active' not in st.session_state: st.session_state.p2_active = False

    if not st.session_state.p2_active:
        st.markdown("<div class='instruction-box'><b>Instructions:</b> Read the text. Think of the word which best fits each gap. Use only ONE word in each gap.</div>", unsafe_allow_html=True)
        time_limit = st.slider("⏱️ Time Limit (seconds):", 60, 600, 300, 30, key="slider_p2")
        
        if st.button("🚀 Start Part 2", type="primary"):
            st.session_state.p2_data = df.sample(1).iloc[0]
            st.session_state.p2_active = True
            st.session_state.p2_start = time.time()
            st.session_state.p2_limit = time_limit
            st.rerun()

    else:
        row = st.session_state.p2_data
        respuestas = str(row['Answers']).split('|')
        
        # Timer
        elapsed = time.time() - st.session_state.p2_start
        remaining = max(0, st.session_state.p2_limit - elapsed)
        st.progress(min(1.0, elapsed / st.session_state.p2_limit), text=f"Time Remaining: {int(remaining)}s")

        # Text
        st.subheader(f"Topic: {row['Title']}")
        if 'URL' in row and pd.notna(row['URL']): st.link_button("📖 Source", row['URL'])

        texto_visual = str(row['Text'])
        for i in range(1, len(respuestas) + 1):
            texto_visual = texto_visual.replace(f"_{i}_", f"<span class='gap-highlight'>({i}) .......</span>")
        st.markdown(f"<div class='text-box'>{texto_visual}</div>", unsafe_allow_html=True)
        
        st.divider()

        # Inputs
        with st.form("form_p2"):
            cols = st.columns(4)
            user_ans = []
            for i in range(len(respuestas)):
                with cols[i % 4]:
                    user_ans.append(st.text_input(f"Gap {i+1}", key=f"p2_q{i}"))
            submitted = st.form_submit_button("Submit Answers", type="primary")

        if submitted:
            final_time = time.time() - st.session_state.p2_start
            score = 0
            
            if final_time > st.session_state.p2_limit: st.error("⏰ TIME OUT!")
            else: st.success("✅ Submitted!")

            st.write("### 📊 Results")
            for i, (u, c) in enumerate(zip(user_ans, respuestas)):
                c = c.strip().lower()
                u = u.strip().lower()
                if u == c:
                    st.write(f"Gap {i+1}: ✅ **{c.upper()}**")
                    score += 1
                else:
                    st.write(f"Gap {i+1}: ❌ You wrote *{u}* | Correct: **{c.upper()}**")

            st.metric("Score", f"{score}/{len(respuestas)}")

             # Full Text
            st.markdown("---")
            st.info("📖 **Full Corrected Text:**")
            full_text = str(row['Text'])
            for i, ans in enumerate(respuestas):
                full_text = full_text.replace(f"_{i+1}_", f"<span class='gap-correct'>{ans}</span>")
            st.markdown(f"<div class='text-box'>{full_text}</div>", unsafe_allow_html=True)

            # 2. EL BOTÓN MÁGICO "TRY ANOTHER TEXT" (MEJORADO)
    if st.button("🔄 Try Another Text"):
        # Verificamos si hay suficientes datos para variar
        if len(df) > 1:
            # Guardamos el título actual para comparar
            titulo_actual = st.session_state.p2_data['Title']
            
            # Buscamos uno nuevo hasta que sea diferente al actual
            nuevo_row = df.sample(1).iloc[0]
            while nuevo_row['Title'] == titulo_actual:
                nuevo_row = df.sample(1).iloc[0]
            
            # Asignamos el nuevo y reiniciamos el reloj
            st.session_state.p2_data = nuevo_row
            st.session_state.p2_start = time.time()
            st.rerun()
        else:
            st.warning("Solo hay 1 ejercicio en la base de datos. Añade más en GitHub.")

# ==============================================================================
# 5. LÓGICA: PART 3 (WORD FORMATION)
# ==============================================================================
def run_part_3():
    st.header("📝 Part 3: Word Formation")
    df = load_data('fce_data.csv', ['Root', 'Sentence', 'Answer'])
    
    if df is None or df.empty:
        st.error("⚠️ Error: Could not find 'fce_data.csv'.")
        return

    # Initialize
    if 'p3_active' not in st.session_state:
        st.session_state.p3_active = False

    if not st.session_state.p3_active:
        st.markdown("<div class='instruction-box'><b>Instructions:</b> Use the word given in capitals at the end of some of the lines to form a word that fits in the gap in the same line.</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            num_q = st.number_input("Questions:", 1, len(df), min(5, len(df)))
        with col2:
            time_limit = st.slider("Time per question (s):", 5, 60, 20, key="slider_p3")

        if st.button("🚀 Start Part 3", type="primary"):
            st.session_state.p3_data = df.sample(num_q).reset_index(drop=True)
            st.session_state.p3_total = num_q
            st.session_state.p3_limit = time_limit
            st.session_state.p3_index = 0
            st.session_state.p3_score = 0
            st.session_state.p3_active = True
            st.session_state.p3_q_start = time.time()
            st.rerun()

    else:
        # Progress
        idx = st.session_state.p3_index
        row = st.session_state.p3_data.iloc[idx]
        
        st.progress(idx / st.session_state.p3_total, text=f"Question {idx+1}/{st.session_state.p3_total}")

        # Timer
        elapsed = time.time() - st.session_state.p3_q_start
        remaining = max(0, st.session_state.p3_limit - elapsed)
        st.caption(f"⏱️ Time: {int(remaining)}s")

        # Question Display
        c1, c2 = st.columns([1, 4])
        with c1: st.markdown(f"<div class='root-word'>{row['Root']}</div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='text-box'>{row['Sentence']}</div>", unsafe_allow_html=True)

        with st.form(f"p3_form_{idx}"):
            ans = st.text_input("Answer:", autocomplete="off")
            submitted = st.form_submit_button("Check")

        if submitted:
            final_time = time.time() - st.session_state.p3_q_start
            correct_ans = str(row['Answer']).strip().lower()
            user_ans = ans.strip().lower()
            
            reconstructed = str(row['Sentence']).replace("______", f"<span class='gap-correct'>{str(row['Answer']).upper()}</span>")

            if final_time > st.session_state.p3_limit:
                 st.error(f"⏰ TIME OUT! Answer: {correct_ans.upper()}")
            elif user_ans == correct_ans:
                 st.success("✅ CORRECT!")
                 st.session_state.p3_score += 1
            else:
                 st.error(f"❌ WRONG. Answer: {correct_ans.upper()}")

            st.markdown(f"<div class='result-box'>📖 <b>Full Sentence:</b><br>{reconstructed}</div>", unsafe_allow_html=True)
            
            time.sleep(2.5) # Pause to read

            if idx < st.session_state.p3_total - 1:
                st.session_state.p3_index += 1
                st.session_state.p3_q_start = time.time()
                st.rerun()
            else:
                st.session_state.p3_active = False # End session
                st.session_state.p3_finished = True
                st.rerun()

    # Final Screen for Part 3
    if 'p3_finished' in st.session_state and st.session_state.p3_finished:
        st.balloons()
        s = st.session_state.p3_score
        t = st.session_state.p3_total
        st.metric("Final Score", f"{s}/{t}", f"{(s/t)*100:.1f}%")
        if st.button("Start New Session"):
            del st.session_state.p3_finished
            st.rerun()

# ==============================================================================
# 6. MENÚ PRINCIPAL (SIDEBAR)
# ==============================================================================
def main():
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Flag_of_the_United_Kingdom.svg/640px-Flag_of_the_United_Kingdom.svg.png", width=100)
    st.sidebar.title("🇬🇧 FCE Trainer")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Select Module:",
        ["🏠 Home", "Part 1: Multiple Choice", "Part 2: Open Cloze", "Part 3: Word Formation"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("v5.0 - Final Stable Release")

    # --- CRÉDITOS DEL CREADOR (Tech Style) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
        <style>
        .dev-card {
            background-color: #1e1e1e;
            color: #00ff41; /* Verde Hacker */
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #00ff41;
            text-align: center;
            font-family: 'Courier New', monospace; /* Letra tecnológica */
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
            margin-bottom: 20px;
        }
        .dev-title {
            font-size: 12px;
            color: #ffffff;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .dev-name {
            font-size: 18px;
            font-weight: bold;
        }
        </style>
        
        <div class="dev-card">
            <div class="dev-title">🚀 Developed by</div>
            <div class="dev-name">&lt;Henry Palomino/&gt;</div>
        </div>
    """, unsafe_allow_html=True)
    
    if menu == "🏠 Home":
        st.title("Welcome to the FCE Exam Simulator")
        st.markdown("""
        ### Cambridge English: B2 First (FCE)
        Select a part from the sidebar to begin practicing.
        
        * **🔡 Part 1 (Multiple Choice Cloze):** Focus on vocabulary, idioms, collocations, phrasal verbs.
        * **🧩 Part 2 (Open Cloze):** Focus on grammar (prepositions, articles, auxiliary verbs).
        * **📝 Part 3 (Word Formation):** Focus on vocabulary (prefixes, suffixes, changing word classes).
        """)
        
    elif menu == "Part 1: Multiple Choice":
        run_part_1()
    elif menu == "Part 2: Open Cloze":
        run_part_2()
    elif menu == "Part 3: Word Formation":
        run_part_3()

if __name__ == "__main__":
    main()
