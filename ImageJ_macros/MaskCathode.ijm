//Perform mask of binary image on greyscale
//Both images must be in through plane (top down) orientation
setBatchMode("show");

GS_image_name = "2000AMST_crop_median_GS"
w = getWidth;
h = getHeight;
title = "AnodeRemoved.tif";
selectWindow(title);
run("Options...", "iterations=1 count=1 pad do=Nothing");
setAutoThreshold("Default");
//run("Threshold...");
//setThreshold(0, 128);
setOption("BlackBackground", false);
run("Convert to Mask", "method=Default background=Light");
run("Reslice [/]...", "output=1.000 start=Top avoid");
setOption("BlackBackground", false);
run("Erode", "stack");
run("Erode", "stack");
rename("CathodeDilated");
run("Calculator Plus", "i1=CathodeDilated i2=CathodeDilated operation=[Scale: i2 = i1 x k1 + k2] k1=0.00392157 k2=0 create");
selectWindow(GS_image_name);
run("Reslice [/]...", "output=1.000 start=Top avoid");
imageCalculator("Multiply create stack", "Reslice of "+GS_image_name,"Result");
selectWindow("Result of Reslice of "+GS_image_name);
run("Reslice [/]...", "output=1.000 start=Top avoid");
rename("CathodeMasked");

close("Result of Reslice of "+GS_image_name);
close("Reslice of "+GS_image_name);
close("Result");
close("CathodeDilated")
