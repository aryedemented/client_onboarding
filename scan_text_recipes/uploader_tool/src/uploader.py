import os
from typing import Dict, List

import networkx as nx
import pandas as pd
from pyvis.network import Network
import streamlit as st
from streamlit.components.v1 import html
import tempfile

from scan_text_recipes import PROJECT_ROOT
from scan_text_recipes.src.run_pipeline import ReadRecipePipeline
from scan_text_recipes.uploader_tool.src.recipe_scheduler_utils import build_schedule, plot_schedule
from scan_text_recipes.uploader_tool.src.st_utils import hebrew_text
from scan_text_recipes.utils.utils import read_jinja_config


class VisToolUploader:
    def __init__(self):
        st.set_page_config(layout="wide")
        self.load_data()
        col1, col2 = st.columns(2)
        with col1:
            col1_container = st.container()
            self.graph_area = col1_container.empty()
            with self.graph_area:
                self.show_graph(nx.DiGraph())
            col3, col4, _ = col1_container.columns([1, 1, 5])
            with col3:
                self.force_ingredients = st.checkbox("Force Ingredients", value=False)
            with col4:
                self.force_resources = st.checkbox("Force Resources", value=False)
            st.text("Log:")
            self.scheduler_area = st.empty()
            self.log_area = st.empty()

        with col2:
            col2_container = st.container()
            col_client, col_recipe = col2_container.columns([1, 1])
            with col_client:
                options = ['italiano', "aroma"]
                client_name = st.selectbox("Client", options)
                print(f"client_name: {client_name}")
                self.load_config(client_name=client_name)
            with col_recipe:
                hebrew_text("פריסת מתכונים", h=1)
            uploaded_file = col2_container.file_uploader("מתכון חדש", type=["txt", "yaml"])
            if uploaded_file is not None:
                col2_container.write("Upload succeeded")
                print("File Uploaded!")
                self.upload_button_callback(uploaded_file)
                if col2_container.button("סרוק מתכון"):
                    print("scanning recipe")
                    if "data" not in st.session_state:
                        st.session_state.data = {}
                    st.session_state.data['recipe_dict'] = self.parse_recipe()
                    # self.recipe_dict = read_yaml(os.path.join(PROJECT_ROOT, "..\\structured_recipes\\bruschetta.yaml"))
        with self.graph_area:
            print("displaying graph")
            graph = self.build_recipe_graph(self.recipe_dict)
            self.show_graph(graph)
        with self.scheduler_area:
            scheduler_dict = build_schedule(self.recipe_dict)
            fig = plot_schedule(scheduler_dict)
            st.pyplot(fig, clear_figure=True)

        with col2:
            if "data" in st.session_state:
                hebrew_text(st.session_state.data["recipe_name"], h=4, container=col2_container)
                hebrew_text(f"{st.session_state.data['recipe_text']}", h=6, container=col2_container)

            if "data" in st.session_state and "recipe_dict" in st.session_state.data:
                col5, col6 = col2_container.columns([1, 1])
                print("Displaying Ingredients and Resources")
                with col5:
                    list_of_ingredients = list(self.client_config['ALLOWED_INGREDIENTS'].keys())
                    print(st.session_state.data['recipe_dict']['ingredients'])
                    self.display_table(
                        "ingredients_table",
                        st.session_state.data['recipe_dict']['ingredients'],
                        list_of_items=list_of_ingredients,
                        table_place_holder=col2_container
                    )
                with col6:
                    list_of_resources = list(self.client_config['ALLOWED_RESOURCES'].keys())
                    self.display_table(
                        "resources_table",
                        st.session_state.data['recipe_dict']['resources'],
                        list_of_items=list_of_resources,
                        table_place_holder=col2_container
                    )

    def load_config(self, client_name: str):
        if self.client_name is None or self.client_name != client_name:
            print("loading client config")
            bundle_config_path = os.path.join(PROJECT_ROOT, "client_configs", client_name, "client_config.yaml")
            setup_config_path = os.path.join(PROJECT_ROOT, "client_configs", client_name, "setup_config.yaml")
            print(f"setup_config_path: {setup_config_path}")
            client_config = read_jinja_config(setup_config_path, bundle_config_path)
            self.client_config = client_config
            self.client_name = client_name
            self.bundle_config_path = bundle_config_path

    @property
    def bundle_config_path(self) -> str:
        return st.session_state.bundle_config_path if "bundle_config_path" in st.session_state else ""

    @bundle_config_path.setter
    def bundle_config_path(self, value: str):
        st.session_state.bundle_config_path = value

    @property
    def client_config(self) -> Dict:
        return st.session_state.client_config if "client_config" in st.session_state else {}

    @client_config.setter
    def client_config(self, value: Dict):
        st.session_state.client_config = value

    @property
    def client_name(self) -> str:
        return st.session_state.client_name if "client_name" in st.session_state else ""

    @client_name.setter
    def client_name(self, value: str):
        st.session_state.client_name = value

    def load_data(self):
        if "data" in st.session_state:
            if "cilent_config" in st.session_state.data:
                print("client_config found")
                self.client_config = st.session_state.data['client_config']
            if "client_name" in st.session_state.data:
                print("client_name found")
                self.client_name = st.session_state.data['client_name']
            if "bundle_config_path" in st.session_state.data:
                print("bundle_config_path found")
                self.bundle_config_path = st.session_state.data['bundle_config_path']
            if "recipe_dict" in st.session_state.data:
                print("recipe_dict found")
                self.recipe_dict = st.session_state.data['recipe_dict']
                print(self.recipe_dict)
            else:
                self.recipe_dict = {'ingredients': [], 'resources': [], 'edges': []}

    def parse_recipe(self):
        # Model config
        model_api_keys = os.path.join(PROJECT_ROOT, "config", "api_keys.yaml")
        # Database config
        db_connection_config = os.path.join(PROJECT_ROOT, "config", "db_connect_config.yaml")
        log_lines = []
        pipeline = ReadRecipePipeline(
            self.bundle_config_path,
            model_api_keys,
            db_connection_config,
            **{"logger":
                   {
                       "StreamlitLogger": {
                           "session_state": st.session_state, "log_area": self.log_area, "log_lines": log_lines
                       }
                   }
               },
        )
        # Run the pipeline on the recipe text
        _, processed_recipe = pipeline.run_pipeline(st.session_state.data['recipe_text'])
        # Save the processed recipe to the database
        pipeline.save_recipe_to_db(processed_recipe, st.session_state.data['recipe_text'])
        return processed_recipe

    @staticmethod
    def upload_button_callback(uploaded_file):
        # To read file as string:
        st.session_state.data = {
            "recipe_text": uploaded_file.getvalue().decode(),
            "recipe_name": uploaded_file.name.split(".")[0],
        }

    @property
    def recipe_dict(self):
        return st.session_state.data['recipe_dict'] if "data" in st.session_state and "recipe_dict" in st.session_state.data else {}

    @recipe_dict.setter
    def recipe_dict(self, value: Dict):
        st.session_state.data['recipe_dict'] = value

    @staticmethod
    def build_recipe_graph(recipe_dict: Dict) -> nx.DiGraph:
        graph = nx.DiGraph()
        # Add all nodes first: ingredients + resources
        for item in recipe_dict.get("ingredients", []):
            graph.add_node(
                item["id"], label=item["name"], type="ingredient", quantity=item["quantity"], remarks=item["remarks"],
                color='lightblue', size=20, shape='box'
            )

        for item in recipe_dict.get("resources", []):
            graph.add_node(
                item["id"], label=item["name"], type="resource", usage_time=item["usage_time"], remarks=item["remarks"],
                color='lightgreen', size=50, shape='box'
            )

        # Add edges with instructions
        for edge in recipe_dict.get("edges", []):
            from_node = edge["from"]
            to_node = edge["to"]
            instruction = edge.get("instructions", "")
            graph.add_edge(from_node, to_node, title=instruction)

        return graph

    @staticmethod
    def show_graph(graph: nx.DiGraph):
        net = Network(height='700px', width='100%', directed=True)
        net.from_nx(graph)
        net.set_options("""
        {
          "layout": {
            "hierarchical": {
              "enabled": true,
              "direction": "RL",
              "sortMethod": "directed",
              "nodeSpacing": 50,
              "levelSeparation": 200,
              "treeSpacing": 50,
              "margin": 0
            }
          },
          "physics": {
            "enabled": false
          }
        }
        """)        # Use a temporary HTML file just for the duration of display
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            net.write_html(tmp_file.name)
            tmp_file_path = tmp_file.name

        # Read the HTML file into memory
        with open(tmp_file_path, 'r', encoding='utf-8') as f:
            html_data = f.read()

        # Clean up the file after reading (optional but neat)
        os.remove(tmp_file_path)

        # Show in Streamlit
        html(html_data, height=800, scrolling=True)

    @staticmethod
    def expand_dict_columns(df: pd.DataFrame) -> pd.DataFrame:
        new_cols = {}
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, dict)).any():
                # For rows where it's a dict, create new columns
                expanded = df[col].dropna().apply(lambda x: x if isinstance(x, dict) else {}).apply(pd.Series)
                # Prefix new columns with original column name
                expanded.columns = [f"{k}_{col}" for k in expanded.columns]
                new_cols[col] = expanded
        # Combine everything
        for col, expanded in new_cols.items():
            df = df.drop(columns=[col])
            df = pd.concat([df, expanded], axis=1)
        return df

    def display_table(self, table_name: str, data: Dict[str, List], table_place_holder=None, list_of_items: List[str] = None):
        list_of_items = list_of_items if list_of_items is not None else []
        df = self.expand_dict_columns(pd.DataFrame(data))

        # Use data_editor for interactive edits
        with table_place_holder:
            with st.expander(f"Edit Table: {table_name}", expanded=False):
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    num_rows="dynamic",
                    key=table_name
                )

        # Recompute highlights on the edited data
        def highlight_rows(row):
            styles = [''] * len(row)
            if 'intermediate' in row and row['intermediate']:
                return styles
            if 'name' in row and row['name'] == "מוצר סופי":
                return styles
            if 'name' in row and row['name'] not in list_of_items:
                styles = ['background-color: red'] * len(row)
            elif 'quantity' in row and pd.isna(pd.to_numeric(row['quantity'], errors='coerce')):
                styles = ['background-color: lightsalmon'] * len(row)
            elif 'usage_time' in row and pd.isna(pd.to_numeric(row['usage_time'], errors='coerce')):
                styles = ['background-color: lightsalmon'] * len(row)
            elif 'temperature' in row and pd.isna(pd.to_numeric(row['temperature'], errors='coerce')):
                styles = ['background-color: lightsalmon'] * len(row)
            elif 'units' in row and row['units'] is None:
                styles = ['background-color: lightcoral'] * len(row)
            return styles

        # Show the highlighted version as a styled table below (optional)
        styled_df = edited_df.style.apply(highlight_rows, axis=1)
        st.dataframe(styled_df, use_container_width=True)

        return edited_df  # return edited DataFrame so you can save it externally


def run_app():
    VisToolUploader()


if __name__ == '__main__':
    run_app()
