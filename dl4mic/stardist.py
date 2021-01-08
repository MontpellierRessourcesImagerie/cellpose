import os
import shutil
import Augmentor

W = '\033[0m'  # white (normal)
R = '\033[31m'  # red

def augmentData(Training_source, Training_target, Multiply_dataset_by, Save_augmented_images, Saving_path,
                rotate_90_degrees=0.5,
                rotate_270_degrees=0.5,
                flip_left_right=0.5,
                flip_top_bottom=0.5,
                random_zoom=0,
                random_distortion=0,
                random_zoom_magnification=0.9,
                image_shear=0,
                max_image_shear=10,
                skew_image=0,
                skew_image_magnitude=0):

    list_files = os.listdir(Training_source)
    Nb_files = len(list_files)

    Nb_augmented_files = (Nb_files * Multiply_dataset_by)

    if not Save_augmented_images:
        Saving_path = "/content"

    Augmented_folder = Saving_path + "/Augmented_Folder"
    if os.path.exists(Augmented_folder):
        shutil.rmtree(Augmented_folder)
    os.makedirs(Augmented_folder)

    # Training_source_augmented = "/content/Training_source_augmented"
    Training_source_augmented = Saving_path + "/Training_source_augmented"

    if os.path.exists(Training_source_augmented):
        shutil.rmtree(Training_source_augmented)
    os.makedirs(Training_source_augmented)

    # Training_target_augmented = "/content/Training_target_augmented"
    Training_target_augmented = Saving_path + "/Training_target_augmented"

    if os.path.exists(Training_target_augmented):
        shutil.rmtree(Training_target_augmented)
    os.makedirs(Training_target_augmented)

    # Here we generate the augmented images
    # Load the images
    p = Augmentor.Pipeline(Training_source, Augmented_folder)

    # Define the matching images
    p.ground_truth(Training_target)
    # Define the augmentation possibilities
    if not rotate_90_degrees == 0:
        p.rotate90(probability=rotate_90_degrees)

    if not rotate_270_degrees == 0:
        p.rotate270(probability=rotate_270_degrees)

    if not flip_left_right == 0:
        p.flip_left_right(probability=flip_left_right)

    if not flip_top_bottom == 0:
        p.flip_top_bottom(probability=flip_top_bottom)

    if not random_zoom == 0:
        p.zoom_random(probability=random_zoom, percentage_area=random_zoom_magnification)

    if not random_distortion == 0:
        p.random_distortion(probability=random_distortion, grid_width=4, grid_height=4, magnitude=8)

    if not image_shear == 0:
        p.shear(probability=image_shear, max_shear_left=max_image_shear, max_shear_right=max_image_shear)

    if not skew_image == 0:
        p.skew(probability=skew_image, magnitude=skew_image_magnitude)

    p.sample(int(Nb_augmented_files))

    print(int(Nb_augmented_files), "matching images generated")

    # Here we sort through the images and move them back to augmented trainning source and targets folders

    augmented_files = os.listdir(Augmented_folder)

    for f in augmented_files:

        if f.startswith("_groundtruth_(1)_"):
            shortname_noprefix = f[17:]
            shutil.copyfile(Augmented_folder + "/" + f, Training_target_augmented + "/" + shortname_noprefix)
        if not (f.startswith("_groundtruth_(1)_")):
            shutil.copyfile(Augmented_folder + "/" + f, Training_source_augmented + "/" + f)

    for filename in os.listdir(Training_source_augmented):
        os.chdir(Training_source_augmented)
        os.rename(filename, filename.replace('_original', ''))

    # Here we clean up the extra files
    shutil.rmtree(Augmented_folder)
