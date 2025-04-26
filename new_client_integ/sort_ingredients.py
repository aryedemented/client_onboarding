import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA


def embed_ingredients(items_list: list[str]) -> torch.Tensor:
    tokenizer = AutoTokenizer.from_pretrained("avichr/heBERT")
    model = AutoModel.from_pretrained("avichr/heBERT")
    model.eval()
    inputs = tokenizer(
        items_list,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128
    )
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state
        attention_mask = inputs['attention_mask'].unsqueeze(-1)
        masked_embeddings = embeddings * attention_mask
        summed = masked_embeddings.sum(1)
        counts = attention_mask.sum(1)
        mean_pooled = summed / counts
        return F.normalize(mean_pooled, p=2, dim=1)  # normalize for cosine similarity


if __name__ == '__main__':
    filename = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\new_client.csv"
    df = pd.read_csv(filename)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed:")]

    ingredients = df.loc[df['מוצר בסיס/ חומר גלם'] == 'חומר גלם', 'שם הרכיב']
    items_list = list(ingredients.unique())
    items_list = [item.strip() for item in items_list]
    # keep unique items
    items_list = list(set(items_list))
    embeddings = embed_ingredients(items_list)

    # Step 1: PCA reduction
    pca = PCA(n_components=100)
    reduced = pca.fit_transform(embeddings)
    embeddings = normalize(reduced)

    similarity_matrix = cosine_similarity(embeddings)
    np.fill_diagonal(similarity_matrix, 0)

    show_similarity_matrix(similarity_matrix)
    surf_similarity_matrix(similarity_matrix)
    histogram_similarity_matrix(similarity_matrix)
    possible_replacements = get_similar_pairs(similarity_matrix, items_list, threshold=0.75)
    for ing1, ing2, score in possible_replacements:
        print(f"{ing1} <-> {ing2}: {score:.2f}")
