import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # This activates 3D plotting
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.ion()  # Interactive mode on


def histogram_similarity_matrix(similarity_matrix):
    similarity_no_diag = similarity_matrix[~np.eye(similarity_matrix.shape[0], dtype=bool)]
    plt.figure(figsize=(8, 5))
    plt.hist(similarity_no_diag, bins=50, color='skyblue', edgecolor='black')
    plt.title("Distribution of Cosine Similarities (excluding self-similarity)")
    plt.xlabel("Cosine Similarity")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def show_similarity_matrix(similarity_matrix):
    plt.figure()
    plt.imshow(similarity_matrix, cmap='viridis')
    plt.colorbar()
    plt.title("Cosine Similarity")
    plt.show()


def surf_similarity_matrix(similarity_matrix):
    # Assuming similarity_matrix is already computed and diagonal is zeroed
    X = np.arange(similarity_matrix.shape[0])
    Y = np.arange(similarity_matrix.shape[1])
    X, Y = np.meshgrid(X, Y)

    Z = similarity_matrix

    # Create figure and 3D axes
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Plot the surface
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')

    # Add color bar and labels
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    ax.set_title('Cosine Similarity Surface')
    ax.set_xlabel('Embedding Index')
    ax.set_ylabel('Embedding Index')
    ax.set_zlabel('Cosine Similarity')

    plt.show()


def roc_curve_display(similarity_matrix):
    import numpy as np
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, auc

    # Example: assume you already have your similarity matrix
    # similarity_matrix = np.array([...])

    # Optionally, mask the diagonal
    np.fill_diagonal(similarity_matrix, 0)

    # Flatten the upper triangle only to avoid duplicates (matrix is symmetric)
    triu_indices = np.triu_indices_from(similarity_matrix, k=1)
    similarity_scores = similarity_matrix[triu_indices]

    # Build a pseudo ground truth
    # For now, let's assume that very high similarity (> 0.8) is "true"
    # (You can adjust this or use your own labels if you have)
    true_labels = (similarity_scores > 0.8).astype(int)

    # Plot ROC
    fpr, tpr, thresholds = roc_curve(true_labels, similarity_scores)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f"ROC curve (AUC = {roc_auc:.2f})")
    plt.plot([0, 1], [0, 1], 'k--', label='Random guess')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve from Similarity Matrix')
    plt.legend(loc='lower right')
    plt.grid()
    plt.show()

    # Optional: Find the optimal threshold
    optimal_idx = np.argmax(tpr - fpr)
    optimal_threshold = thresholds[optimal_idx]
    print(f"Optimal threshold: {optimal_threshold:.2f}")
