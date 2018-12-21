//run("Close All");
html = "<html>"
 +"<h3>To correct for tilt in dataset in through-plane direction</h3>"
 +"<h3>Image stack should have units in pixels</h3>"
 +"<font size=-1>
 +"Written by Robin White and Sebastian Eberhardt, last updated 06/7/2017<br>"
 +"</font>";
Dialog.create("Help");

title = getTitle();
Dialog.create("Front-back Translation v0.1");
Dialog.setInsets(0, 10, 0)
Dialog.addMessage("Reminder: image stack units in pixels");
Dialog.addString("Title:", title, 15);
Dialog.addHelp(html);
Dialog.show();

OrigImageName = Dialog.getString();
selectWindow(OrigImageName);



setBatchMode(false)

macro "translate_IP" {
	
	//apply translation in case of misalignment
	selectWindow(OrigImageName);
	getDimensions(width_1, height_1, channels_1, slices_1, frames_1);
	run("Properties...", "channels="+channels_1+" slices="+slices_1+" frames=1 unit=pixel pixel_width=1 pixel_height=1 voxel_depth=1");
	setSlice(1);
	waitForUser("Draw a line from the bottom to the edge of center flow field land (on current slice)");
	run("Measure");
	length1 = getResult('Length', nResults-1);
	setSlice(slices_1);
	waitForUser("Draw a line from the bottom to the edge of center flow field land (on current slice)");
	run("Measure");
	length2 = getResult('Length', nResults-1);
	slope=(length1-length2)/(1-slices_1);
	print(slope);
	
	selectWindow(OrigImageName);
	for (i=1; i<=slices_1; i++) 
	{
	setSlice(i);
	shift=i*slope;
	run("Translate...", "x=0 y="+shift+" interpolation=Bilinear slice");
	}

}
