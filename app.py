import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as gen_ai
from io import BytesIO



# Configure Streamlit page settings
st.set_page_config(
    page_title="Data Sweeper with AI Chatbot",
    page_icon="🤖",
    layout="wide",
)




st.title ("Data Sweeper")
st.write("Transform your files between CSV and Excel formats with built-in data cleaning and visualization.")


# # Google Gemini-Pro API Key
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# Configure AI Model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-2.0-flash')

# Initialize Chat Session
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# Sidebar User Input
st.sidebar.title("User Input")
user_name = st.sidebar.text_input("Enter Your Name")

uploaded_files = st.sidebar.file_uploader(
    "Upload your files (CSV or Excel):",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

# Chatbot Toggle Button
if "show_chatbot" not in st.session_state:
    st.session_state.show_chatbot = False  # Default: Chatbot hidden

if st.sidebar.button("💬 Open Chatbot"):
    st.session_state.show_chatbot = not st.session_state.show_chatbot  # Toggle Chatbot

if user_name:
    st.sidebar.success(f"Welcome, {user_name}!")

# File Processing Section
if uploaded_files:
    st.subheader(f"Uploaded Files by {user_name}")
    for file in uploaded_files:
        file_ext = os.path.splitext(file.name)[-1].lower()

        if file_ext == ".csv":
            df = pd.read_csv(file)
        elif file_ext == ".xlsx":
            df = pd.read_excel(BytesIO(file.getvalue()), engine="openpyxl")
        else:
            st.error(f"Unsupported file type: {file_ext}")
            continue

        if df.empty:
            st.warning(f"{file.name} is empty! Please upload a valid file.")
            continue

        st.write(f"**File Name:** {file.name}")
        st.write(f"**File Size:** {file.size / 1024:.2f} KB")

        st.write("Preview:")
        st.dataframe(df, height=300)

        st.subheader(f"Data Cleaning for {file.name}")
        if st.checkbox(f"Clean Data for {file.name}"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Remove Duplicates from {file.name}"):
                    df.drop_duplicates(inplace=True)
                    st.write("Duplicates Removed ✅")

            with col2:
                if st.button(f"Fill Missing Values for {file.name}"):
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                    st.write("Missing Values Filled ✅")

        st.subheader(f"Select Columns for {file.name}")
        if not df.columns.empty:
            selected_columns = st.multiselect(
                f"Choose Columns", df.columns.tolist(), default=df.columns.tolist()
            )
            df = df[selected_columns]

        st.subheader(f"Visualization for {file.name}")
        if st.checkbox(f"Show Bar Chart for {file.name}"):
            st.bar_chart(df.select_dtypes(include='number').iloc[:, :2])

        st.subheader(f"Convert {file.name}")
        conversion_type = st.radio(
            f"Convert {file.name} to:", ["CSV", "Excel"], key=f"{file.name}_{user_name}"
        )

        if st.button(f"Convert {file.name}"):
            buffer = BytesIO()
            if conversion_type == "CSV":
                df.to_csv(buffer, index=False)
                file_name = file.name.replace(file_ext, ".csv")
                mime_type = "text/csv"
            elif conversion_type == "Excel":
                df.to_excel(buffer, index=False, engine='openpyxl')
                file_name = file.name.replace(file_ext, ".xlsx")
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            buffer.seek(0)
            st.download_button(
                label=f"Download {file.name} as {conversion_type}",
                data=buffer,
                file_name=file_name,
                mime=mime_type
            )

            # 🎈 Show balloons after file conversion
            st.balloons()
            
            

# ✅ Chatbot Section (Only Show if Sidebar Button Clicked)
if st.session_state.show_chatbot:
    st.markdown("<h2 style='text-align: center;'>🤖 Chat with Gemini-Pro</h2>", unsafe_allow_html=True)

    # Display Chat History
    for message in st.session_state.chat_session.history:
        with st.chat_message("assistant" if message.role == "model" else "user"):
            st.markdown(message.parts[0].text)

    # Chat Input
    user_prompt = st.chat_input("Ask Gemini-Pro...")
    if user_prompt:
        st.chat_message("user").markdown(user_prompt)
        gemini_response = st.session_state.chat_session.send_message(user_prompt)

        with st.chat_message("assistant"):
            st.markdown(gemini_response.text)
