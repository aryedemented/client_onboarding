import os
import streamlit as st
import pandas as pd
from new_client_integ.find_duplicates import FindDuplicates
from new_client_integ.data_loaders.excel_loader import CSVDataLoader
from new_client_integ.utils import highlight_differences
from scan_text_recipes.utils.utils import read_yaml

os.environ["STREAMLIT_WATCHER_TYPE"] = "none"


class DuplicatesPage:
    def __init__(self):
        self.title = "Resolve Duplicates"
        st.set_page_config(layout="wide")

    @staticmethod
    def init_state():
        defaults = {
            "df": None,
            "columns": [],
            "name_column": None,
            "filter_config": {},
            "filter_count": 0,
            "active_filter_col": None,
            "adding_filter": False,
            "rows": [],
            "resolved": [],
            "undo_buffer": [],
            "full_config": {},
            "loaded_file": None,
            "duplicates_ready": False,
            "show_filtered": False,
            'full_inventory_list': [],
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    @staticmethod
    def reset_state():
        for key in ["df", "columns", "name_column", "filter_config", "filter_count",
                    "active_filter_col", "adding_filter", "rows", "resolved", "undo_buffer", "full_inventory_list",
                    "full_config", "loaded_file"]:
            st.session_state[key] = [] if isinstance(st.session_state.get(key), list) else None
        st.rerun()

    def load_file_and_configure(self):
        st.header("📦 Upload and Filter Client Inventory")
        col_upload, col_reset = st.columns([1, 1])
        with col_upload:
            uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="file_upload")
            if uploaded_file and st.session_state.df is None:
                df = pd.read_csv(uploaded_file)
                df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
                st.session_state.df = df
                st.session_state.columns = df.columns.tolist()
                st.session_state.loaded_file = uploaded_file
                st.success("✅ File loaded.")
        with col_reset:
            st.write("")
            st.write("")
            if st.button("🔄 Reset", key="reset_button"):
                self.reset_state()

        # Select item name column
        if st.session_state.df is not None and st.session_state.name_column is None:
            options = ["-- Select name column --"] + st.session_state.columns
            choice = st.selectbox("Select item name column", options)
            if choice != "-- Select name column --":
                st.session_state.name_column = choice

        if st.session_state.name_column:
            st.write("✅ Selected column:", st.session_state.name_column)

        # Add filters
        if st.session_state.name_column and st.button("➕ Add Filter", key="add_filter_button"):
            st.session_state.adding_filter = True

        if st.session_state.adding_filter:
            col_options = ["-- Select filter column --"] + st.session_state.columns
            selected_col = st.selectbox("Choose filter column", col_options, key="new_filter_col")
            if selected_col != "-- Select filter column --":
                st.session_state.active_filter_col = selected_col
                values = st.session_state.df[selected_col].dropna().unique().tolist()
                selected_val = st.selectbox(f"Choose value for {selected_col}", ["-- Select --"] + values, key=f"val_{selected_col}")
                if selected_val != "-- Select --":
                    st.session_state.filter_config[selected_col] = selected_val
                    st.session_state.filter_count += 1
                    st.session_state.adding_filter = False
                    st.session_state.active_filter_col = None
                    st.rerun()

        if st.session_state.filter_config:
            st.write("Active filters:")
            df = pd.DataFrame.from_dict(st.session_state.filter_config, orient="index", columns=["Value"])
            st.dataframe(df)

        # Finalize filtering
        # Finalize filtering
        if st.session_state.name_column and st.button("🔄 Show Filtered Items"):
            config = {
                "name_column": st.session_state.name_column,
                "filter_by": st.session_state.filter_config
            }
            st.session_state.full_config = config
            st.session_state.show_filtered = True
            st.rerun()

        # Show filtered items if requested
        if st.session_state.get("show_filtered", False):
            st.subheader("🧾 Filtered Items")
            loader = CSVDataLoader(st.session_state.full_config)
            items = loader.load(self.rewind_st_loaded_file())
            st.session_state.filtered_items = items
            st.write(f"✅ Found {len(items)} unique items")
            st.dataframe(pd.DataFrame(items, columns=["Item Name"]))

            # Now show "Find Duplicates" button
            if st.button("🔍 Find Duplicates"):
                dup_config = read_yaml(
                    "D:\\Projects\\Kaufmann_and_Co\\recepies\\scan_code\\ScanRecepies\\new_client_integ\\duplicates_config.yaml")
                find_duplicates = FindDuplicates(cfg=dup_config)
                find_duplicates.set_data_loader(loader)
                duplicates = find_duplicates.find_duplicates(filename=self.rewind_st_loaded_file())
                pairs_df = pd.DataFrame(duplicates, columns=["left_name", "right_name", "score", "index1", "index2"])
                st.session_state.full_inventory_list = find_duplicates.get_items_list()
                print("full inventory list ######")
                print(st.session_state.full_inventory_list)
                st.session_state.rows = pairs_df.to_dict(orient="records")
                st.session_state.resolved = []
                st.session_state.undo_buffer = []
                st.success("✅ Duplicate pairs loaded.")
                st.session_state.duplicates_ready = True
                st.rerun()

    @staticmethod
    def rewind_st_loaded_file():
        uploaded_file = st.session_state.loaded_file
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file)

    def resolve_ui(self):
        st.title(self.title)

        # Stats
        col1, col2 = st.columns([1, 1])
        with col1:
            st.metric("Rows to Resolve", len(st.session_state.rows))
        with col2:
            if st.button("↩️ Undo", key="undo_button") and st.session_state.undo_buffer:
                entry = st.session_state.undo_buffer.pop()
                st.session_state.rows.insert(0, entry["row"])
                for name in entry["resolved"]:
                    if name in st.session_state.resolved:
                        st.session_state.resolved.remove(name)
                if "previous_rows" in entry:
                    st.session_state.rows[1:] = entry["previous_rows"]
                st.rerun()

        if not st.session_state.rows:
            st.success("✅ Resolution complete!")

            clean_list = [name for name in st.session_state.full_inventory_list if name not in st.session_state.resolved]

            # 🟢 Filter the original dataframe
            if st.session_state.df is not None and st.session_state.name_column:
                print("clean list ######")
                print(clean_list)
                print("Final df ######")
                print(st.session_state.df)
                print("Final df clean ######")
                print(st.session_state.df[st.session_state.name_column].isin(clean_list))
                final_df = st.session_state.df[
                    st.session_state.df[st.session_state.name_column].isin(clean_list)
                ]
                csv_bytes = final_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="⬇️ Export Original File with Resolved Names",
                    data=csv_bytes,
                    file_name="filtered_inventory.csv",
                    mime="text/csv"
                )
            return

        row = st.session_state.rows[0]
        left, left_but, mid_but, right_but, right = st.columns([8, 1, 1, 1, 8])
        highlighted_left, highlighted_right = highlight_differences(row["left_name"], row["right_name"])
        with left:
            st.markdown(f"<div style='font-family:monospace; text-align: right; font-size:18px'>{highlighted_left}</div>", unsafe_allow_html=True)
        resolved = None
        with left_but:
            st.write("")
            if st.button("⬅️", key="choose_left"):
                resolved = [row["right_name"]]
        with mid_but:
            st.write("")
            if st.button("↔️", key="choose_both"):
                resolved = []
        with right_but:
            st.write("")
            if st.button("➡️", key="choose_right"):
                resolved = [row["left_name"]]
        with right:
            st.markdown(f"<div style='font-family:monospace; text-align: left; font-size:18px'>{highlighted_right}</div>", unsafe_allow_html=True)

        if resolved is not None:
            # Determine replacement logic
            if not resolved:  # ↔️ different items, no replacement
                st.session_state.undo_buffer.append({"row": row, "resolved": []})
                st.session_state.rows.pop(0)
                st.rerun()

            replaced = resolved[0]
            kept = row["left_name"] if replaced == row["right_name"] else row["right_name"]

            # Update all remaining rows
            updated_rows = []
            for r in st.session_state.rows[1:]:
                new_row = r.copy()
                if new_row["left_name"] == replaced:
                    new_row["left_name"] = kept
                if new_row["right_name"] == replaced:
                    new_row["right_name"] = kept
                updated_rows.append(new_row)

            # Save undo state
            st.session_state.undo_buffer.append({
                "row": row,
                "resolved": [replaced],
                "replacement": kept,
                "previous_rows": st.session_state.rows[1:]  # save state for undo
            })

            # Apply updates
            st.session_state.resolved.append(replaced)
            st.session_state.rows = [*updated_rows]
            st.rerun()

    def render(self):
        self.init_state()  # 🛠 Ensure state variables are initialized
        if not st.session_state.duplicates_ready:
            self.load_file_and_configure()
        else:
            self.resolve_ui()


if __name__ == "__main__":
    app = DuplicatesPage()
    app.render()
