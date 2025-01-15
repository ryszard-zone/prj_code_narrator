from datetime import datetime
import streamlit as st
from streamlit_ace import st_ace

import openai
from openai import OpenAI
# , AuthenticationError

import os
from dotenv import dotenv_values, load_dotenv

from dbase import *
# from gtts import gTTS
from io import BytesIO
import httpx

st.set_page_config(page_title="Objasniacz kodu", layout="wide")

# Dodanie stylu CSS dla zakładek
st.markdown("""
    <style>
    div[data-testid="stTabs"] button {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

def get_description(text, mode, language, tokens):

    if mode == "szczegółowy":
        prompt = f"Provide a detailed line-by-line description of the following code in {language}:\n\n{text}"
    else:
        prompt = f"Provide a simple  in one sentencee description of what the following code does in {language}:\n\n{text}"

    
    # Przykład dostosowania struktury wiadomości w zależności od modelu
    if st.session_state["current_model"] == "o1-mini":
        # Jeśli model to "o1-mini", omijamy rolę system
        messages2 = [{"role": "user", "content": prompt}]
    else:
        # W przypadku innych modeli, możemy użyć roli "system"
        messages2 = [
            {"role": "system", "content": "You are a helpful assistant that describes {prg_language} code."},
            {"role": "user", "content": prompt}
        ]

    # Wywołanie API
    response = openai_client.chat.completions.create(
        model=st.session_state["current_model"],  # Bezpośrednio przekazujesz identyfikator modelu
        messages=messages2,
        max_tokens=tokens,
        temperature=0.1,
    )

    response = openai_client.chat.completions.create(
        model=st.session_state["current_model"],  # Bezpośrednio przekazujesz identyfikator modelu
        messages=[
            {"role": "system", "content": "You are a helpful assistant that describes {prg_language} code."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=tokens,
        temperature=0.1,
    )
    description = response.choices[0].message.content.strip()
    return description

def generate_speech(text, voice="onyx"):
    # OpenAI client for generating speech
    response = openai_client.audio.speech.create(
        model="tts-1",
        voice=voice,
        response_format="mp3",
        input=text,
    )
    
    # Utworzenie obiektu BytesIO do przechowywania danych audio
    audio_data = BytesIO(response.content)
    audio_data.seek(0)

    return audio_data


# Funkcja do czytania na głos
# def generate_audio(text, lang="pl"):
#     tts = gTTS(text=text, lang=lang)
#     audio_buffer = BytesIO()
#     tts.write_to_fp(audio_buffer)
#     audio_buffer.seek(0)
#     return audio_buffer


# Definicja funkcji, która zostanie wywołana po zmianie wartości w st.text_input
# def update_filename():
#     # Możesz tutaj zaktualizować wartość w session_state lub wykonać inne operacje
#     st.session_state['output_filename'] = st.session_state['audio_filename']

# def preprocess_text_for_tts(text):
#     # Zamień cyfry na ich tekstową reprezentację
#     digit_map = {
#         "0": "zero",
#         "1": "jeden",
#         "2": "dwa",
#         "3": "trzy",
#         "4": "cztery",
#         "5": "pięć",
#         "6": "sześć",
#         "7": "siedem",
#         "8": "osiem",
#         "9": "dziewięć",
#     }
#     for digit, word in digit_map.items():
#         text = text.replace(digit, word)
#     # Zamień zmienne (np. pojedyncze litery) na pełne nazwy
#     text = text.replace(" b ", " zmienna b ")
#     return text



# Ustawienie połączenia z bazą danych i utworzenie tabeli
conn = create_connection()
create_table(conn)

API_KEY = st.sidebar.text_input("Wklej swój klucz OpenAI API:", type="password")

if API_KEY:
    openai_client = OpenAI(api_key=API_KEY)
else:
    st.sidebar.warning("Wpisz klucz API, aby kontynuować")


# load_dotenv()
# API_KEY = os.environ["OPENAI_API_KEY"]
# openai_client = OpenAI(api_key=API_KEY)


def main():

    st.sidebar.markdown("<div style='height: 7px;'></div>", unsafe_allow_html=True)  # Dodatkowy odstęp   
    prg_language = st.sidebar.selectbox("Wybierz język programowania:", ["python", "sql", "c", "rust"])

    st.sidebar.markdown("<div style='height: 9px;'></div>", unsafe_allow_html=True)  # Dodatkowy odstęp przed suwakami    
    code_height = st.sidebar.slider("Wysokość okna kodu:", min_value=100, max_value=600, value=200)

    st.sidebar.markdown("<div style='height: 9px;'></div>", unsafe_allow_html=True)  # Dodatkowy odstęp przed suwakami    
    token_count = st.sidebar.slider("Ilość tokenów:", min_value=100, max_value=1200, value=300)

    # Lista dostępnych modeli
    models = {
        "gpt-4o": "GPT-4o (wysoka jakość, wyższy koszt)",
        "o1-mini": "o1-mini (tańsza alternatywa)"
    }

    # Inicjalizacja zmiennej w session_state
    if "current_model" not in st.session_state:
        st.session_state["current_model"] = "gpt-4o"  # Domyślny model

    # Sidebar do wyboru modelu
    st.sidebar.title("Ustawienia modelu")
    selected_model = st.sidebar.selectbox(
        "Wybierz model do generowania wyjaśnień:",
        options=list(models.keys()),
        format_func=lambda x: models[x]
    )

    # Zapisujemy identyfikator modelu w current_model
    st.session_state["current_model"] = selected_model
        # Wyświetlenie aktualnie wybranego modelu
        
    st.sidebar.markdown(f"**Wybrany model:** {st.session_state['current_model']}")

    st.sidebar.markdown("---")  # Linia oddzielająca
    st.sidebar.markdown("<div style='position: fixed; bottom: 10px; font-size: 12px; color: gray;'>wersja: 1.06.01</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Jak uzywać", "Kod => Opis", "Opis => kod", "Historia", ])
    
    # st.markdown("<span style='font-size:20px; font-weight:bold;'>5. Historia</span>", unsafe_allow_html=True)

    with tab1:

        st.markdown("<div style='height: 7px;'></div>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: blue;'>Jak korzystać z aplikacji:</h4>", unsafe_allow_html=True)
        st.markdown("1. podaj swój klucz API OpenAI", unsafe_allow_html=True)
        st.markdown("2. działa w 2 trybach: <span style='color: green;'>szczegółowy</span> - *opisuje każdą linię kodu* ; <span style='color: green;'>ogólny</span> - *opisuje cały kod w jednym zdaniu*", unsafe_allow_html=True)
        st.markdown("3. wyjaśnienie jest udzielane w języku <span style='color: green;'>polskim</span> lub <span style='color: green;'>angielskim</span>", unsafe_allow_html=True)
        st.markdown('4. Można pytać o kod w wybranym języku programowania', unsafe_allow_html=True)
        st.markdown('5. Historia pokazuje tylko 20 ostatnich objaśnień', unsafe_allow_html=True)

    with tab2:
        # Ustawienie wartości początkowych w session_state
        if 'description' not in st.session_state:
            st.session_state['description'] = None
        if 'code_input' not in st.session_state:
            st.session_state['code_input'] = ""
        if 'clear_code' not in st.session_state:
            st.session_state['clear_code'] = False
        if 'output_filename' not in st.session_state:
            st.session_state['output_filename'] = "wyjasnienie.mp3"


        # Display the text area with the dynamic height, bind it to the session state
        # if st.session_state['clear_code']:
        #     code_input = st.text_area("Tu wprowadź kod:", value="", height=code_height, key="code_input_area")
        # else:
        #     code_input = st.text_area("Tu wprowadź kod:", value=st.session_state['code_input'], height=code_height, key="code_input_area")


        st.text("Wpisz / wklej kod programu:")

        if st.session_state['clear_code']:
            code_input = st_ace(
                language=prg_language,
                theme='monokai', 
                value="", 
                font_size = 18,
                height=code_height,
                auto_update=True,
                key="code_input_area"
            )       
        else:
            code_input = st_ace(
                language=prg_language,
                theme='monokai', 
                value=st.session_state['code_input'], 
                font_size = 18,
                height=code_height,
                auto_update=True,
                key="code_input_area"
            )       

        # Create columns for buttons and radio selections
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

# Po kliknięciu "Wyjaśnij kod", ustaw `clear_code` na False, aby przywrócić normalne działanie
        with col1:
            if st.button("Wyjaśnij kod"):
                if not API_KEY:
                    st.warning("Proszę wprowadzić klucz OpenAI API.")
                elif code_input:
                    st.session_state['code_input'] = code_input
                    st.session_state['token_count'] = token_count
                    st.session_state['clear_code'] = False
                    description = get_description(code_input, st.session_state['desc_mode'], st.session_state['desc_lang'], st.session_state['token_count'])
                    st.session_state['description'] = description
                    insert_history(conn, code_input, description)
                else:
                    st.warning("Brak kodu do objaśnienia")

        with col2:
            # Radio button for selecting the description mode
            mode_names = ['szczegółowy', 'ogólny']
            desc_mode = st.radio('Tryb:', mode_names, index=0, key='desc_mode', horizontal=True)

        with col3:
            # Radio button for selecting the description language
            lang_names = ['polski', 'angielski']
            desc_lang = st.radio('Język:', lang_names, index=0, key='desc_lang', horizontal=True)

        with col4:
            if st.button("Usuń wyjaśnienie"):
                st.session_state['code_input'] = ""
                st.session_state['description'] = None
                st.session_state['clear_code'] = True
                # code_input = ""None""
                # st.rerun()

        # Display the description if it exists
        if st.session_state['description']:
            col_desc, col_read_aloud = st.columns([3, 1])
            with col_desc:
                st.subheader("Wyjaśnienie kodu:")

            with col_read_aloud:
                # if st.button("Przeczytaj tekst na głos"):
                #     # st.session_state['description'] = description
                #     read_aloud(st.session_state['description'])
                #     # st.success("Tekst został przeczytany na głos.")   

                # if st.button("Przeczytaj tekst na głos"):
                #     # st.session_state['description'] = description
                #     audio_file = generate_audio(st.session_state['description'], lang="pl")  # "pl"
                #     st.audio(audio_file, format="audio/mp3")

            #    if st.button("Przeczytaj tekst na głos"):
            #         # preprocessed_text = preprocess_text_for_tts(original_text)
            #         st.session_state['description'] = preprocess_text_for_tts(st.session_state['description'])
            #         audio_file = generate_audio(st.session_state['description'], lang="pl")  # "pl"
            #         st.audio(audio_file, format="audio/mp3")

                if st.button("Przeczytaj tekst na głos"):
                    # Generowanie mowy za pomocą OpenAI
                    try:
                        audio_file = generate_speech(st.session_state['description'], voice="onyx")
                        st.audio(audio_file, format="audio/mp3")
                        # st.success("Tekst został przeczytany na głos.")
                    except Exception as e:
                        st.error(f"Wystąpił błąd podczas generowania mowy: {e}")

            st.write(st.session_state['description'])               

    with tab3:
        pass

    with tab4:
        # Historia wyjaśnień
        st.subheader("Historia wyjaśnień")
        # Trim history to ensure only the latest 20 entries are kept
        trim_history(conn)
        history_data = fetch_history(conn)
        if history_data:
            for record in history_data:
                st.markdown(f"**ID:** {record[0]}")
                st.markdown(f"**Code Input:**")
                st.code(record[1], language="python")
                st.markdown(f"**Description:** {record[2]}")
                st.markdown(f"**Timestamp:** {record[3]}")
                st.markdown("---")
        else:
            st.info("Brak zapisanej historii.")
    
# Uruchomienie aplikacji
if __name__ == "__main__":
    main()
