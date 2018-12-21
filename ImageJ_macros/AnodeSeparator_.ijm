/*This macro will remove the cathode (and other fractional GDL parts).
The input image is a segmented stack of the anode catalyst layer 
 after masking away the cathode + parts surrounding GDL
The Macro will then perform slight smoothing and speckle removal
followed by a script to remove the anode; output as "AnodeRemoved"
It will finally also perform a SUM over pixels and output as a pixel wise thickness map*/

/*The image to be run through this macro should have it's name changed so as to remove
any file type association such as .tif*/

/*Requires BoneJ particle analyzer to perform labelling. If BoneJ does not work it is most likely
due to the Java8 update and removal of Java 3Dviewer. Reverting back to life line version of Fiji
should fix this issue.*/

/* Image stack needs to already be segmented for cathode catayst and in through plane view
 * GUI inputs:
 * 
 * Title: Image to be run
 * Gaussian Sigma: The level of blurring to join cathode irrespective of cracks
 * Select threshold: Manual selection of threshold after blurring. This should be chosen to 
 * completely include the anode without any artifacts. Check over multiple slices
 * Gaussian threshold: If the above manual selection has already been determined and is unchecked
 * Get Thickness: Perform SUM Z-project and count pixels for local thickness calculation (in pixels)
 * Keep images: If unchecked, will close all windows except for CathodeRemoved stack and PixelThickness
 if Get thickness is selected
 */
//Version 0.1
//Last update 15/11/17 by Robin White

html = "<html>"
	 +"
	 +"<h3>Image stack needs to already be segmented for anode catayst and in through plane view</h3>"
     +"<h3>GUI inputs:</h3>"
     +"<font size=-1>
     +"<b>Gaussian Sigma:</b> The level of blurring to join anode irrespective of cracks or breaks<br>"
     +"<b>Select threshold:</b> Manual selection of threshold after blurring. This should be chosen to<br>"
     +"completely include the anode without any artifacts.<br>"
     +"<b>Gaussian threshold:</b> If the above manual selection has already been determined and is unchecked<br>"
     +"<b>Get Thickness:</b> Perform SUM Z-project and count pixels for local thickness calculation (in pixels)<br>"
     +"<b>Keep images:</b> If unchecked, will close all windows except for CathodeRemoved stack and PixelThickness if Get thickness is selected<br>"
     +"</font>";
Dialog.create("Help");

title = getTitle();
Dialog.create("Anode separator v0.1");
Dialog.setInsets(0, 10, 0)
Dialog.addMessage(" The image to be run through this macro\n should have it's name changed so as to remove\n any file type association such as .tif");
Dialog.addString("Title:", title,15);
Dialog.addNumber("Gaussian Sigma:", 20); //Value for blurring to form connected objects
Dialog.addCheckbox("Select threshold", true); //Manually choose threshold after blurring
Dialog.addNumber("Gaussian Threshold:", 93); //Value used if above is unchecked
Dialog.addCheckbox("Get thickness", true); //Calculate thickness
Dialog.addCheckbox("Keep images", false); //Don't close windows
Dialog.addMessage("Don't forget to save your images");
Dialog.addHelp(html);
Dialog.show();
OrigImageName = Dialog.getString();
sigma = Dialog.getNumber();
select_thresh = Dialog.getCheckbox();
thresh = Dialog.getNumber();
get_thickness = Dialog.getCheckbox();
keep_images = Dialog.getCheckbox();

setBatchMode("show");
selectWindow(OrigImageName);
run("Duplicate...", "duplicate");
run("Dilate", "stack");
run("Median 3D...", "x=2 y=2 z=2");
//setAutoThreshold("Otsu dark stack");
setThreshold(128, 255);
run("Make Binary", "background=Dark black");
run("Options...", "iterations=1 count=1 pad do=Nothing");
run("Erode", "stack");
run("Duplicate...", "duplicate");

//Gaussian blur to connect cathode for labelling
run("Select All");
run("Gaussian Blur...", "sigma="+sigma+" stack");
run("Reslice [/]...", "output=1.000 start=Top avoid");

if (select_thresh == true){
	run("Threshold...");
	waitForUser( "Pause","Set the threshold and press OK");
}
else{
setThreshold(thresh, 255);
}
run("Convert to Mask", "background=Dark black");
run("Particle Analyser", "  min=0.000 max=Infinity surface_resampling=2 show_size surface=Gradient split=0.000 volume_resampling=2 labelling=Mapped slices=2");
getMinAndMax(min, max);
setThreshold(max, max);
//setOption("BlackBackground", true);
run("Convert to Mask", "background=Default black");
run("Erode", "stack");

//AND logic to keep only labelled cathode from original threshold
run("Select All");
selectWindow("Reslice_volume");
//selectWindow("Reslice_parts");
run("Select All");
run("Reslice [/]...", "output=1.000 start=Top avoid");
imageCalculator("AND create stack", OrigImageName+"-1","Reslice of Reslice_volume");
selectWindow("Result of "+OrigImageName+"-1");
rename("CathodeRemoved");

if (get_thickness == true) {
run("Z Project...", "projection=[Sum Slices]");
run("Calculator Plus", "i1=SUM_CathodeRemoved i2=SUM_CathodeRemoved operation=[Scale: i2 = i1 x k1 + k2] k1=0.0039216 k2=0 create");
selectWindow("Result");
rename("PixelThickness");
}

//Closing windows
if (keep_images == false) {
	if (get_thickness == true) {
		selectWindow("SUM_CathodeRemoved");
		close();}
selectWindow(OrigImageName+"-1");
close();
selectWindow(OrigImageName+"-2");
close();
selectWindow("Reslice of "+OrigImageName+"-2");
close();
selectWindow("Reslice_volume");
close();
selectWindow("Reslice of Reslice_volume"); 
close();
}