from datetime import datetime
import streamlit as st
from streamlit_ace import st_ace
from openai import OpenAI
from dotenv import dotenv_values
from dbase import *
from io import BytesIO

st.set_page_config(page_title="Objasniacz kodu", layout="wide")

# def get_description(api_key, text, mode, language):
def get_description(text, mode, language):

    if mode == "szczegółowy":
        prompt = f"Provide a detailed line-by-line description of the following code in {language}:\n\n{text}"
    else:
        prompt = f"Provide a simple  in one sentencee description of what the following code does in {language}:\n\n{text}"

    # response = openai.ChatCompletion.create(
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that describes {prg_language} code."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.1,
    )
    description = response.choices[0].message.content.strip()
    return description

def generate_speech(text, voice, output_filename):
    # OpenAI client for generating speech
    response = openai_client.audio.speech.create(
        model="tts-1",
        voice='onyx',
        response_format="mp3",
        input=text,
    )
    
    # Create a BytesIO object to hold the audio data
    audio_data = BytesIO(response.content)
    audio_data.seek(0)

    return audio_data, output_filename

# Definicja funkcji, która zostanie wywołana po zmianie wartości w st.text_input
def update_filename():
    # Możesz tutaj zaktualizować wartość w session_state lub wykonać inne operacje
    st.session_state['output_filename'] = st.session_state['audio_filename']

# Ustawienie połączenia z bazą danych i utworzenie tabeli
conn = create_connection()
create_table(conn)

# env = dotenv_values(".env")
# API_KEY = env["OPENAI_API_KEY"]

# st.sidebar.title(":blue[Objaśniacz kodu]")

# st.sidebar.header("Wklej swój klucz OpenAI API:")
API_KEY = st.sidebar.text_input("Wklej swój klucz OpenAI API:", type="password")

openai_client = OpenAI(api_key=API_KEY)

def main():

    # Nowa postać instrukcji na lewym panelu
    st.sidebar.markdown("<div style='height: 7px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("<h4 style='color: blue;'>Jak korzystać z aplikacji:</h4>", unsafe_allow_html=True)
    st.sidebar.markdown("1. podaj swój klucz API OpenAI", unsafe_allow_html=True)
    st.sidebar.markdown("2. działa w 2 trybach: <span style='color: green;'>szczegółowy</span> - *opisuje każdą linię kodu* ; <span style='color: green;'>ogólny</span> - *opisuje cały kod w jednym zdaniu*", unsafe_allow_html=True)
    st.sidebar.markdown("3. wyjaśnienie jest udzielane w języku <span style='color: green;'>polskim</span> lub <span style='color: green;'>angielskim</span>", unsafe_allow_html=True)
    st.sidebar.markdown('4. Można pytać o kod w wybranym języku programowania', unsafe_allow_html=True)
    st.sidebar.markdown('5. "Usuń kod" naciskamy dwukrotnie', unsafe_allow_html=True)
    st.sidebar.markdown('6. Historia pokazuje tylko 20 ostatnich objaśnień', unsafe_allow_html=True)

    st.sidebar.markdown("<div style='height: 7px;'></div>", unsafe_allow_html=True)  # Dodatkowy odstęp   
    prg_language = st.sidebar.selectbox("Wybierz język programowania:", ["python", "sql", "c", "rust"])

    st.sidebar.markdown("<div style='height: 9px;'></div>", unsafe_allow_html=True)  # Dodatkowy odstęp przed suwakami    
    code_height = st.sidebar.slider("Wysokość okna kodu:", min_value=100, max_value=600, value=200)

    # Zakładki: "Wyjaśnianie kodu" i "Historia"
    tab1, tab2 = st.tabs(["Wyjaśnianie kodu", "Historia"])

    with tab1:
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


        st.text("Wpisz / wklej kod:")

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
                    st.session_state['clear_code'] = False
                    description = get_description(code_input, st.session_state['desc_mode'], st.session_state['desc_lang'])
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
            if st.button("Usuń kod"):
                st.session_state['code_input'] = ""
                st.session_state['description'] = None
                st.session_state['clear_code'] = True
                # code_input = ""None""
                # st.rerun()

        # Display the description if it exists
        if st.session_state['description']:
            col_desc, col_download = st.columns([3, 1])
            with col_desc:
                st.subheader("Wyjaśnienie kodu:")

            with col_download:
                default_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp3"
                filename = default_filename
                audio_data, output_filename = generate_speech(
                    st.session_state['description'],
                    voice="onyx",
                    output_filename=filename
                )
                
                if st.download_button(
                        label="Pobierz audio wyjasnienia",
                        data=audio_data,
                        file_name=output_filename,
                        mime="audio/mpeg"
                    ): i=0

            st.write(st.session_state['description'])

    with tab2:
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
