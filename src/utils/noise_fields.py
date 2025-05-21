import numpy as np
import noise

def generate_noise_field(
    shape,
    scale,
    seeds,
    octaves=6,
    persistence=0.5,
    lacunarity=2.0,
):
    """
    Generate an N-dimensional vector-valued Perlin noise field.

    Parameters:
        shape (tuple): (height, width) of the field (H, W)
        scale (float): scale factor for frequency
        seeds (int or list of int): one or more seeds determining vector dimension
        octaves (int): number of noise octaves
        persistence (float): persistence of noise
        lacunarity (float): lacunarity of noise

    Returns:
        np.ndarray: shape (H, W, N), where N = len(seeds)
    """
    H, W = shape

    # Normalize seeds to list
    if isinstance(seeds, int):
        seeds = [seeds]

    N = len(seeds)  # Vector dimension
    field = np.zeros((H, W, N))

    for n, seed in enumerate(seeds):
        for i in range(H):
            for j in range(W):
                noise_value = noise.pnoise2(
                    i / scale, j / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=H,
                    repeaty=W,
                    base=seed
                )
                field[i, j, n] = noise_value

    return field