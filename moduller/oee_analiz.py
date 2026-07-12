import streamlit as st
from moduller import uretim

def goster():
    """OEE analizini ayrı sayfa olarak sunar."""
    st.info("ℹ️ OEE hesabı üretim kayıtlarından beslenir. Bu sayfa, Üretim modülündeki OEE analizinin hızlı erişim halidir.")
    uretim.goster()