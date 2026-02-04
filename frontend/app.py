import os
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_oauth import OAuth2Component
from openai import OpenAI
from datetime import datetime
import pandas as pd
import requests
import boto3
from botocore.exceptions import NoCredentialsError

BACKEND_URL = os.getenv("BACKEND_URL")

@st.cache_resource
def initialization_function():
  answers = pd.DataFrame(columns = ['Model', 'Question', 'Answer'])
  return answers

answers = initialization_function()

REDIRECT_URI = st.secrets["REDIRECT_URI"]
COOKIE_SECRET = st.secrets["COOKIE_SECRET"]
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
SERVER_METADATA_URL = st.secrets["SERVER_METADATA_URL"]
AUTHORIZE_URL = "https://accounts.google.com"
TOKEN_URL = "https://oauth2.googleapis.com"
REVOKE_URL = "https://oauth2.googleapis.com"

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_URL)

if "auth" not in st.session_state:
  result = oauth2.authorize_button(
    name = "Bejelentkezés Google-lel",
    icon = "https://www.google.com.cu",
    redirect_uri = REDIRECT_URI,
    scope = "openid email profile",
    key = "google_auth",
    use_container_width = True
  )
  st.stop()
  if result:
    st.session_state.auth = result
    st.session_state.token = result.get("token")
    st.rerun()
else:
  user = st.session_state.user_info
  st.sidebar.image(user.get("picture"), width = 50) # Profilkép
  st.sidebar.write(f"Greetings, **{user.get('name')}**!")
  st.sidebar.write(f"📧 {user.get('email')}")
  st.success("Sikeresen bejelentkeztél!")
  if st.button("Kijelentkezés"):
    del st.session_state.auth
    del st.session_state.user_info
    st.rerun()

  st.write("A tokened:", st.session_state.auth)

# if not st.user.is_logged_in:
#   st.info("If you have got an OpenAI API Key, then after sign in with Google you can use this web application with different AI models to chat and create photos and videos.")
#   st.info("You can buy credits here: https://platform.openai.com/settings/organization/billing/overview")
#   st.info("Your email address and other data like your questions and descriptions are saved into PostgreSQL database tables.")
#   st.info("Your AI generated photos and videos are stored on Amazon locally.")
#   if st.button("Login with Google"):
#     st.login()
#   st.stop()
# else:
#   st.write(f"Greetings, {st.user.name}!")
#     
#   if st.button("Logout"):
#     st.logout()

st.title('Ask AI with Python', anchor = False, help = None)
password = st.text_input('Set your OpenAI API key:', type = 'password', value = os.environ['OPENAI_API_KEY'], placeholder = "If you don't have one, then you can create here: https://platform.openai.com/api-keys", key = "my_key") 
selected = option_menu(None, ['Chat', 'Messages'], menu_icon = 'cast', default_index = 0, orientation = 'horizontal') # , 'Image', 'Picture Gallery', 'Video', 'Video Gallery'

if selected == 'Chat': 
  
  model = st.selectbox('Choose AI Model:', options = ['gpt-5.2', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano'])
  question = st.text_area('Write here your question:', placeholder = 'Ask something!', value = None)
  
  if st.button('Answer me!'): 
    try:
      with st.spinner('In progress...'):
        client = OpenAI(api_key = password)
        model = model
        response = client.chat.completions.create(model = model, messages = [{"role": "system", "content": "You are a helpful assistant. Answer as short as possible."}, {"role": "user", "content": question}], temperature = 0)
        answer = response.choices[0].message.content.strip()
        st.text(answer)
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = 'Chat' + now + '.txt'
        answers.loc[len(answers)] = [model, question, answer]
        
        if st.user.is_logged_in:
          try:
            with conn.session as session:
              res = requests.post(f"{BACKEND_URL}/chats/", json = 
              {"email": email, "model": model, "question": question, "answer": answer})
          except Exception as e:
            st.error(f"Hiba történt: {e}")
        
        st.download_button(label = 'Download Chat', data = answers.to_csv(index = False, sep = ';').encode('utf-8'), file_name = filename) # ';'.join([model, mquestion, answer])
    except Exception as e:
      st.error(f'An Error happened: {e}')

elif selected == 'Messages':
  df = requests.get(f"{BACKEND_URL}/chats/").json()
  element = st.dataframe(df, hide_index = True, column_order = ("model", "question", "answer"))


# with st.form("add_chat"):
#   email = st.text_input("Email")
#   model = st.text_input("Modell (max 30 kar.)", max_chars = 30)
#   question = st.text_area("Kérdés")
#   answer = st.text_area("Válasz")
#   if st.form_submit_button("Mentés"):
#     res = requests.post(f"{BACKEND_URL}/chats/", json={
#       "email": email, "model": model, "question": question, "answer": answer
#     })
#     st.success("Chat elmentve!")
# 
# if st.button("Frissítés / Listázás"):
#   chats = requests.get(f"{BACKEND_URL}/chats/").json()
#   for c in chats:
#     col1, col2 = st.columns([4, 1])
#     col1.write(f"**{c['email']}** ({c['model']}): {c['question']} -> {c['answer']}")
