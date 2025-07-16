# -*- coding: utf-8 -*-

import os
import json
from utils import *
from tifffile import imsave 
from PIL import Image
import cv2 
import argparse

def get_arguments():
    
    parser = argparse.ArgumentParser()
    
    # Path Arguments
    parser.add_argument('--source', type=str, default='path/to/DATA_DIRECTORY', help='Path to the original WSI dataset')
    parser.add_argument('--save_dir', type=str, default='path/to/RESULTS_DIRECTORY', help='name of the new folder')
    
    # Main arguments
    parser.add_argument('--keep_background', type=bool, default=False, help='Keep the background of the WSI (patches where there is only black/white)')
    parser.add_argument('--keep_mask', type=bool, default=False, help='Keep the folder with mask patches')
    parser.add_argument('--patch_size', type=int, default=256, help='Size of the patches in px')
    parser.add_argument('--cancer_priority', type=bool, default=True, help='In a patch with a cancer and other classes, prioritizing the cancer class over the others')
    parser.add_argument('--patch_level', type=str, default='1x', choices=['1x','2x','5x','10x'])
    
    args = parser.parse_args()
    
    return args

def main():
    
    args = get_arguments()
    
    folder_name = args.save_dir
    
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    
    initial_dataset_Images = os.path.join(args.source, 'data', args.patch_level,'Images')
    initial_dataset_Masks = os.path.join(args.source, 'data', args.patch_level,'Masks')
    
    list_paths_img, list_names = read_folder(initial_dataset_Images)
    list_paths_masks, _ = read_folder(initial_dataset_Masks)
    
    for img_path, mask_path, img_name in zip(list_paths_img, list_paths_masks ,list_names) :
        # Loading each WSI and mask before dividing them into patches
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(mask_path)
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
        
        # Creation of a folder to put the patches and the annotations
        create_WSI_folder(folder_name, img_name, args.keep_mask)
        
        # Creation of the patches with a padding of 0 (for the img) or 255 (for the mask)
        img_tiles = tile_array_2d(img, args.patch_size)
        mask_tiles = tile_array_2d(mask, args.patch_size, is_mask=True)
        
        if not args.keep_background :
            img_tiles, kept_idx = delete_background(img_tiles)
            mask_tiles = [mask_tiles[i] for i in kept_idx]
        
        # Saving of the patches for the WSI and the Mask
        # Patches are saved under the folders ~/folder_name/img_name/Images & ~/folder_name/img_name/Masks
        
        wsi_annotations = {
            "wsi_name": img_name,
            "patch_size": args.patch_size,
            "annotations": []
            }
        
        for idx, (patch_img, patch_mask) in enumerate(zip(img_tiles, mask_tiles)) :
            # TIFF Images
            output_path_img  = os.path.join(folder_name, img_name, 'Images', f'patch_{idx}.tif')
            imsave(output_path_img, patch_img)

            # PNG Masks
            mask_pil = Image.fromarray(patch_mask)
            classes = get_classes(mask_pil, args.cancer_priority)
            
            patch_name = f'patch_{idx}'
            wsi_annotations["annotations"].append({
                "patch_name": patch_name,
                "classes": classes
            })
            
            json_path = os.path.join(folder_name, img_name,'annotations.json')
            
            if args.keep_mask :
                # Keep a folder with all of the patches for all of the Masks
                output_path_mask = os.path.join(folder_name, img_name, 'Masks', f'mask_{idx}.png')
                mask_pil.save(output_path_mask, format='PNG')
        
        # Saving the annotations in a .json file
        # File structure is :
        # { 
        #   "wsi_name" : img_name
        #   "patch_size" : args.patch_size
        #   "annotations" : [
        #   { 
        #       "patch_name" : "patch_0"
        #       "classes" : [
        #           "Hypodermis",
        #           "..."
        #       ]
        #   }, ... ]}
        
        with open(json_path, 'w') as output_file:
            json.dump(wsi_annotations, output_file, indent=4)
            
if __name__ == '__main__':
    main()
