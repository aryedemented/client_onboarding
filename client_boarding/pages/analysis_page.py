import streamlit as st
from client_boarding.base_page import BasePage


class AnalysisPage(BasePage):
    def __init__(self):
        super().__init__()
        self.title = "Inventory Stats"

    def render(self):
        st.title(self.title)
        return
        uploaded_file = st.file_uploader("Upload client inventory CSV")
        if uploaded_file:
            # Load CSV and find duplicates
            import pandas as pd
            st.write("Duplicates page")
            df = pd.read_csv(uploaded_file)
            # result = matching_inventory(df)
            # st.write("Duplicates Found:", result)
