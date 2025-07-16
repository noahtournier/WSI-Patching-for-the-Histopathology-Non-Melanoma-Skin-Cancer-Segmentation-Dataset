import os
import numpy as np
from PIL import Image

def get_classes(patch, cancer_priority):
    
    classes = []
    cancer = []
    background = []
    
    color_patches = {
        (108, 0, 115): "Glands",
        (145, 1, 122): "Inflammation",
        (216, 47, 148): "Hair Follicle",
        (254, 246, 242): "Hypodermis",
        (181, 9, 130): "Reticular Dermis",
        (236, 85, 157): "Papillary Dermis",
        (73, 0, 106): "Epidermis",
        (248, 123, 168): "Keratin",
        (0, 0, 0): "Background",
        (127, 255, 255): "Basal Cell Carcinoma",
        (127, 255, 142): "Squamous Cell Carcinoma",
        (255, 127, 127): "Intra-epidermal Carcinoma"
    }
    
    cancer_colors = {
        (127, 255, 255), 
        (127, 255, 142), 
        (255, 127, 127)
    }
    
    colors = patch.getcolors(maxcolors=8192)
    
    background = [c for c in colors if c[1]==(0,0,0)]
    cancer = [c for c in colors if c[1] in cancer_colors]
    colors = [c for c in colors if (c[1] in color_patches and c[1] not in cancer_colors and c[1]!=(0,0,0))]
    
    if cancer_priority :
        colors = sorted(cancer, reverse=True) + sorted(colors, reverse=True) + background
    else :
        colors = sorted(cancer + colors, reverse=True) + background
        
    for nb_px, color in colors :
        classes.append(color_patches[color])
    
    return classes


def read_folder(folder_path):
    list_path = []
    list_name = []
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        list_path.append(file_path)
        list_name.append(os.path.splitext(file_name)[0])
    return list_path, list_name


def create_WSI_folder(folder_name, file_name, keep_mask):
    WSI_path = os.path.join(folder_name, file_name)
    os.mkdir(WSI_path)
    os.mkdir(os.path.join(WSI_path, 'Images'))
    if keep_mask :
        os.mkdir(os.path.join(WSI_path, 'Masks'))
    
    
def get_1d_padding(length, patch_size):
    pad = (patch_size - length % patch_size) % patch_size
    return (pad // 2, pad - pad // 2)


def is_background(array, threshold):
    return np.std(array)<threshold


def delete_background(tiles, threshold = 1):
    kept_idx = []
    filtered_tiles = []
    
    for idx, tile in enumerate(tiles):
        if not is_background(tile, threshold):
            filtered_tiles.append(tile)
            kept_idx.append(idx)
    
    return filtered_tiles, kept_idx


def pad_for_tiling_2d(array, patch_size, channels_first = False, is_mask = False,**pad_kwargs):
    
    height, width = array.shape[1:] if channels_first else array.shape[:-1]
    padding_h = get_1d_padding(height, patch_size)
    padding_w = get_1d_padding(width, patch_size)
    padding = [padding_h, padding_w]
    channels_axis = 0 if channels_first else 2
    padding.insert(channels_axis, (0, 0))  # zero padding on channels axis
    padded_array = np.pad(array, padding, constant_values = 255 if not is_mask else 0, **pad_kwargs)
    offset = (padding_w[0], padding_h[0])
    return padded_array, np.array(offset)


def tile_array_2d(array, patch_size, channels_first = False, is_mask = False,**pad_kwargs):
    padded_array, (offset_w, offset_h) = pad_for_tiling_2d(array, patch_size, channels_first, is_mask, **pad_kwargs)
    
    if channels_first:
        channels, height, width = padded_array.shape
    else:
        height, width, channels = padded_array.shape
    n_tiles_h = height // patch_size
    n_tiles_w = width // patch_size

    if channels_first:
        intermediate_shape = (channels, n_tiles_h, patch_size, n_tiles_w, patch_size)
        axis_order = (1, 3, 0, 2, 4)  # (n_tiles_h, n_tiles_w, channels, patch_size, patch_size)
        output_shape = (n_tiles_h * n_tiles_w, channels, patch_size, patch_size)
    else:
        intermediate_shape = (n_tiles_h, patch_size, n_tiles_w, patch_size, channels)
        axis_order = (0, 2, 1, 3, 4)  # (n_tiles_h, n_tiles_w, patch_size, patch_size, channels)
        output_shape = (n_tiles_h * n_tiles_w, patch_size, patch_size, channels)
        
    tiles = padded_array.reshape(intermediate_shape)  # Split width and height axes
    tiles = tiles.transpose(axis_order)
    tiles = tiles.reshape(output_shape)  # Flatten tile batch dimension
    
    return tiles        