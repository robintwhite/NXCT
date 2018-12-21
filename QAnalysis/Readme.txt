The set of scripts runs as follows
webscrape NIST to obtain range of mass attenuation values for search area of loading. Loading converted to molar ratio so various loading will give the same molar ratio. However in subsequent calculations the loading will be affected by density from thickness. See excel sheet for easier user inputs to play with effect of loading and molar ratio.

After this, run fitting script which uses regression by SVM ML to fit data to model. This model is then saved to be used in subsequent calculations.

Image flattening (projection) scripts take a stack of tiff, and stack of thresholded images to create mask and average projection as well as thickness map from segmented images.

MAX image and thickness image used in calculation script which runs a optimization algorithm to determine the values required for Pt and I loading, taking GSV and thickness as inputs. It calcualtes the GSV from loading, mass attenuation and thickness (density) and adjusts the loading as necessary to match GSV with experimental GSV from input. Pixel by Pixel.

Cycled calculations use BOL calculated values as input - run as a seperate script

To avoid deprecation issues see requirements.txt

Install with
conda create -n <env_name> --file requirements.txt