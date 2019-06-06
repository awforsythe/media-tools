# Forsythe Media Tools

This repository is a collection of custom tools that I've written to help me capture, process, and catalog a large archive of family photos and other printed and audiovisual artifacts.

![copystand](doc/copystand.jpg)

These command-line tools are currently available:

- `fma list [<collection-type>]`: Lists all collections of a certain type (defaults to 'photos'), where collections are directories kept in `$FMA_ROOT/<collection-type>/<collection-name>`. Also indicates which of those collections (if any) is currently selected.

- `fma select [-t <collection-type>] <collection-name>`: Selects the specified collection, making it the target of subsequent commands. Configuration state is saved to `$FMA_ROOT/config.json`. e.g. if `FMA_ROOT` is `Q:\media`, then `fma select album_02` will make `Q:\media\photos\album_02` the selected collection.

- `fma shoot [<subdir>]`: Begins a guided process for capturing photos in the currently-selected collection. A subdirectory can be specified to sort shots into distinctly-numbered sets (e.g. "artifact" for images of a photo album, and "images" for the actual photos in the album). This process uses Canon's EOS Utility 3 and automates the process of configuring the output paths and filenames, as well as closing and launching Remote Live View as necessary. Photos are captured by pressing one of the arrow keys to indicate the orientation of the photo, so that rotating and cropping can later be batched without user input.

- `fma orient <directory>`: Displays all images in the given directory to the user, one by one. The user presses an arrow key (up, down, left or right) to indicate which edge of the subject is the top edge: i.e., for a photo shot upside-down the top edge is *down*; for a photo that's already in the correct orientation, the top edge is *up*. Pressing any other key will reverse to allow mistakes to be corrected. Orientation data is saved in `.params/<image_name>.json`.

- `fma crop <directory>`: Uses darktable to regenerate XMP files for all images in the given directory _**(note that this will destroy any prior adjustments made in the darktable GUI)**_, then auto-crops each image, writing the new cropping parameters into the XMP files. In darktable's core options menu, _"look for updated xmp files on startup"_ must be enabled in order to allow XMP reloads.

Functionality for these tools is implemented across several Python modules:

- **forsythe.collections**: Basic filesystem abstraction for dealing with individual collections that fit into a particular folder structure (with the environment variable `FMA_ROOT` specifying the root path). A photo album would be a single collection containing multiple images. An audio tape would be another collection consisting of multiple audio and image files.

- **forsythe.images**: Organization and file handling for images, including cached conversion from .CR2 RAW to JPEG for intermediate processing.

- **forsythe.eos**: Automation support for Canon's EOS Utility 3, for use with a Canon EOS Rebel T6 camera. Provides code for ensuring that the camera is connected, closing and opening the Remote Live View window for camera capture, and seamlessly modifying the application config in order to set output paths.

- **forsythe.darktable**: Utilities for working with [darktable](https://www.darktable.org/), an open-source version of Lightroom. Handles launching darktable, clearing and regenerating .XMP sidecar files, and adding image operations to XMPs.

- **forsythe.cropper**: Uses OpenCV to detect the subject (i.e. the physical photo print) in an image captured on a copystand. Assumes a solid-colored background suitable for color keying.

Install Python 3 and pipenv, then run `pipenv install` to create a virtualenv with the prerequisite modules. From there, you can use `fma <command>` to run commands _(or, failing that, `pipenv run python main.py <command>`)_.

This is a hobby project.
