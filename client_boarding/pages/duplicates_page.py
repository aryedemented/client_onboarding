import streamlit as st
import pandas as pd

from new_client_integ.find_duplicates import FindDuplicates
from scan_text_recipes.utils.utils import read_yaml


class DuplicatesPage:
    def __init__(self):
        self.title = "Resolve Duplicates"
        st.set_page_config(layout="wide")

    def process_client_data(self, file_path):
        config = read_yaml(
            "D:\\Projects\\Kaufmann_and_Co\\recepies\\scan_code\\ScanRecepies\\new_client_integ\\duplicates_config.yaml")
        # file_path = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\new_client.csv"
        find_duplicates = FindDuplicates(cfg=config)
        possible_replacements = find_duplicates.find_duplicates(filename=file_path)
        pairs = pd.DataFrame(possible_replacements, columns=["ing1", "ing2"])

    def render(self):
        st.title(self.title)

        # 🔄 Initialize session state ONCE
        for key in ['rows', 'resolved', 'undo_buffer']:
            if key not in st.session_state:
                st.session_state[key] = []

        upload_col, count_col = st.columns([1, 1])
        with upload_col:
            st.write("Upload CSV to resolve duplicates")
            uploaded_file = st.file_uploader("Load Client List", type=["csv"])
            if uploaded_file and len(st.session_state.resolved) == 0:
                df = pd.read_csv(uploaded_file)
                st.session_state.rows = df.to_dict(orient="records")
                st.session_state.resolved = []
                st.session_state.undo_buffer = []

        with count_col:
            st.write("Total Rows to Resolve:")
            st.metric(label="Rows", value=len(st.session_state.rows))
            reset_col, undo_col = st.columns([1, 1])
            with reset_col:
                if st.button("🔄 Reset"):
                    st.session_state.rows = []
                    st.session_state.resolved = []
                    st.session_state.undo_buffer = []
                    st.rerun()
            with undo_col:
                if st.button("↩️ Undo") and st.session_state.undo_buffer:
                    undo_entry = st.session_state.undo_buffer.pop()
                    st.session_state.rows.insert(0, undo_entry["row"])
                    for val in undo_entry["resolved"]:
                        if val in st.session_state.resolved:
                            st.session_state.resolved.remove(val)
                    st.rerun()

        if not st.session_state.rows and not st.session_state.resolved:
            st.info("Please upload a CSV to begin.")
            return

        # Show one row at a time for resolution
        if st.session_state.rows:
            row = st.session_state.rows[0]
            left, left_but, mid_but, right_but, right = st.columns([8, 1, 1, 1, 8])
            with left:
                st.text_input("Left", value=row['left_name'], disabled=True)
            resolved = []
            with left_but:
                st.write("")
                st.write("")
                if st.button("⬅️"):
                    resolved = [row['left_name']]
            with right_but:
                st.write("")
                st.write("")
                if st.button("➡️"):
                    resolved = [row['right_name']]
            with mid_but:
                st.write("")
                st.write("")
                if st.button("↔️"):
                    resolved = [row['left_name'], row['right_name']]
            with right:
                st.text_input("Right", value=row['right_name'], disabled=True)

            if resolved:
                st.session_state.undo_buffer.append({"row": row, "resolved": resolved})
                st.session_state.resolved.extend(resolved)
                st.session_state.rows.pop(0)
                st.rerun()
        else:
            st.success("✅ Resolution complete!")
            clean_list = [name for name in st.session_state.resolved if name]
            st.download_button(
                label="Export Fixed List",
                data="\n".join(clean_list),
                file_name="resolved_inventory.csv",
                mime="text/csv"
            )


if __name__ == '__main__':
    page = DuplicatesPage()
    page.render()
