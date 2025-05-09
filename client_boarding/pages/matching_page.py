import os
import streamlit as st
import pandas as pd
import sys

# Add the repo root (parent of client_boarding) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from client_boarding.utils.paths import PROJECT_ROOT
from client_boarding.pages.duplicates_page import DuplicatesPage
from new_client_integ.find_matches import FindMatches
from new_client_integ.data_loaders.excel_loader import CSVDataLoader, InventoryLoader
from scan_text_recipes.utils.utils import read_yaml


os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
NEW_ITEM_MARKER = "__NEW_ITEM__"


class MatchPage(DuplicatesPage):
    def __init__(self):
        super().__init__()
        self.title = "Match Ingredients to Inventory"

    def init_state(self):
        st.session_state.setdefault("save_path", None)
        super().init_state()
        defaults = {
            "all_matches": None,
            "matches": None,
            "matcher": None,
            "inventory_df": None,
            "client_df": None,
            "inv_columns": [],
            "client_columns": [],
            "inv_name_col": None,
            "inv_id_col": None,
            "client_name_col": None,
            "client_filter_config": {},
            "unresolved_indices": [],
            "certain_threshold": None,
            "min_display_threshold": None,
            "save_path": None,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    @staticmethod
    def render_inventory_section():
        st.header("📦 Step 1: Upload and Configure Inventory")
        inv_file = st.file_uploader("Upload Inventory CSV", type="csv", key="inv_file")

        if inv_file and st.session_state.inventory_df is None:
            inv_df = pd.read_csv(inv_file, encoding='utf-8')
            inv_df = inv_df.loc[:, ~inv_df.columns.str.startswith("Unnamed")]
            st.session_state.inventory_df = inv_df
            st.session_state.inv_columns = inv_df.columns.tolist()

        if st.session_state.inventory_df is not None:
            st.session_state.inv_name_col = st.selectbox("Inventory Name Column", st.session_state.inv_columns)
            st.session_state.inv_id_col = st.selectbox("Inventory ID Column", st.session_state.inv_columns)

    @staticmethod
    def render_client_section():
        st.header("🧾 Step 2: Upload and Configure Client List")
        client_file = st.file_uploader("Upload Client CSV", type="csv", key="client_file")

        if client_file and st.session_state.client_df is None:
            client_df = pd.read_csv(client_file, encoding='utf-8')
            client_df = client_df.loc[:, ~client_df.columns.str.startswith("Unnamed")]
            st.session_state.client_df = client_df
            st.session_state.client_columns = client_df.columns.tolist()

        if st.session_state.client_df is not None:
            st.session_state.client_name_col = st.selectbox("Client Name Column", st.session_state.client_columns)

            filter_config = {}
            with st.expander("⚙️ Filter Client Items (optional)"):
                for col in st.session_state.client_columns:
                    unique_values = st.session_state.client_df[col].dropna().unique().tolist()
                    if len(unique_values) < 50:
                        selected = st.multiselect(f"Filter by {col}", unique_values)
                        if selected:
                            filter_config[col] = selected
            st.session_state.client_filter_config = filter_config

    @staticmethod
    def run_matcher():
        if 'matched_id' not in st.session_state.client_df.columns:
            st.session_state.client_df['matched_id'] = ""

        if not all([
            st.session_state.inventory_df is not None,
            st.session_state.client_df is not None,
            st.session_state.inv_name_col,
            st.session_state.inv_id_col,
            st.session_state.client_name_col
        ]):
            return

        cfg = read_yaml(os.path.join(PROJECT_ROOT, "new_client_integ", "matcher_config.yaml"))
        st.session_state.config = cfg
        st.session_state.matcher = FindMatches(cfg=cfg)

        inv_loader = InventoryLoader({
            "name_column": st.session_state.inv_name_col,
            "id_column": st.session_state.inv_id_col
        })
        client_loader = CSVDataLoader({
            "name_column": st.session_state.client_name_col,
            "filter_by": st.session_state.client_filter_config or {}
        })

        st.session_state.matcher.inventory = inv_loader.load(st.session_state.inventory_df)
        client_items = client_loader.load(st.session_state.client_df)

        matches = st.session_state.matcher.find_matches(client_inventory_list=client_items)
        resolved_ids = list(st.session_state.client_df['matched_id'])  # Existing matches
        unresolved_matches = []
        unresolved_indices = []

        name_to_index = {
            name: idx for idx, name in enumerate(st.session_state.client_df[st.session_state.client_name_col])
        }

        for match in matches:
            item_name = match['client_item']
            match_score = match['matches']['score'].iloc[0]
            match_id = match['matches']['_id'].iloc[0]

            if item_name not in name_to_index:
                continue  # skip if not found (safety)

            idx = name_to_index[item_name]
            existing_val = resolved_ids[idx]

            if pd.notna(existing_val) and existing_val not in ["", None]:
                continue
            elif match_score >= st.session_state.config['certain_threshold']:
                resolved_ids[idx] = match_id
            else:
                resolved_ids[idx] = None
                unresolved_matches.append(match)
                unresolved_indices.append(idx)

        st.session_state.all_matches = matches
        st.session_state.matches = unresolved_matches
        st.session_state.unresolved_indices = unresolved_indices
        st.session_state.resolved_ids = resolved_ids
        st.session_state.match_index = 0
        st.session_state.undo_buffer = []

        st.session_state.client_df['matched_id'] = resolved_ids
        st.rerun()

    def render_run_matcher_button(self):
        if st.button("🔍 Run Matcher"):
            self.run_matcher()

    @staticmethod
    def render_intermediate_save_controls():
        st.markdown("### 💾 Save Progress")
        if 'save_path' not in st.session_state:
            st.session_state.save_path = None
        if st.session_state.save_path is None:
            save_file = st.text_input("Save to CSV path (full path):")
            if save_file:
                st.session_state.save_path = save_file

        if st.session_state.save_path and st.button("💾 Save Now"):
            st.session_state.client_df['matched_id'] = st.session_state.resolved_ids
            st.session_state.client_df.to_csv(st.session_state.save_path, index=False, encoding='utf-8-sig')
            st.success(f"Saved to {st.session_state.save_path}")


    def render_match_resolution(self):
        self.render_intermediate_save_controls()
        matches = st.session_state.matches
        idx = st.session_state.match_index
        auto_resolved = len(st.session_state.client_df) - len(st.session_state.unresolved_indices)
        st.markdown(
            f"🔢 Remaining: **{len(matches) - idx}** of **{len(matches)}**, 🧠 Auto-resolved: **{auto_resolved}**")

        if idx >= len(matches):
            st.success("✅ Matching complete!")
            final_df = st.session_state.client_df.copy()
            final_df['matched_id'] = st.session_state.resolved_ids

            # Optional: clean up NEW_ITEM_MARKER before export
            export_df = final_df.copy()
            export_df['matched_id'] = export_df['matched_id'].replace(NEW_ITEM_MARKER, "")

            csv_bytes = export_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="⬇️ Download Matched Client List",
                data=csv_bytes,
                file_name="client_with_matches.csv",
                mime="text/csv"
            )
            return

        match = matches[idx]
        actual_index = st.session_state.unresolved_indices[idx]

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"### Client Item:")
            st.markdown(
                f"<div style='border:1px solid #ccc; padding:10px; direction:rtl; font-size:18px'>{match['client_item']}</div>",
                unsafe_allow_html=True)

        with col2:
            st.markdown("### Top Matches:")
            top_matches = match['matches'][match['matches']['score'] >= st.session_state.config['min_display_threshold']]
            if top_matches.empty:
                top_matches = match['matches'].iloc[:1]

            for i, row in top_matches.iterrows():
                label = row['_name']
                but, lbl = st.columns([1, 8])
                with lbl:
                    if st.button(label, key=f"match_btn_{actual_index}_{i}"):
                        st.session_state.undo_buffer.append((actual_index, st.session_state.resolved_ids[actual_index]))
                        st.session_state.resolved_ids[actual_index] = row['_id']
                        st.session_state.match_index += 1
                        st.rerun()
                with but:
                    st.markdown(f"{row['score']:.2f}", unsafe_allow_html=True)

            if st.button("🆕 New Item", key=f"new_item_btn_{actual_index}_new"):
                st.session_state.undo_buffer.append((actual_index, st.session_state.resolved_ids[actual_index]))
                st.session_state.resolved_ids[actual_index] = NEW_ITEM_MARKER
                st.session_state.match_index += 1
                st.rerun()

        if st.button("↩️ Undo") and st.session_state.undo_buffer:
            last_idx, last_val = st.session_state.undo_buffer.pop()
            st.session_state.resolved_ids[last_idx] = last_val
            if last_idx in st.session_state.unresolved_indices:
                st.session_state.match_index = st.session_state.unresolved_indices.index(last_idx)
            st.rerun()

    def render(self):
        self.init_state()
        if not st.session_state.matches:
            self.render_inventory_section()
            self.render_client_section()
            self.render_run_matcher_button()
        else:
            self.render_match_resolution()


if __name__ == "__main__":
    app = MatchPage()
    app.render()
