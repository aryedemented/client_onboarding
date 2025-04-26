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

