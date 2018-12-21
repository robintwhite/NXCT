
//Last update 04/11/17 by Robin White

	html = "<html>"
	 +"<h3>For volume calculation at each slice of stack use already segmented 8-bit image stack</h3>"
	 +"<h3>"
	 +"<h3>Image must have pixel as units, output is in nano litres based on given pixel size in micrometers</h3>"
     +"<font size=-1>
     +"Written by Robin White, last updated 04/11/2017<br>"
     +"</font>";
	Dialog.create("Help");
	
	title = getTitle();
	Dialog.create("Water Volume calculator v0.1");
	Dialog.setInsets(0, 10, 0)
	Dialog.addMessage("Stack directions:\n 1 = Through plane view\n 2 = In-plane from Top\n 3 = In-plane from Left");
	Dialog.addString("Title:", title,15);
	Dialog.addString("Pixel size:", "1.5",15);
	Dialog.addChoice("Direction:", newArray("1", "2", "3"));
	Dialog.addCheckbox("Convert to 8-bit", true);
	Dialog.addHelp(html);
	Dialog.show();
	
	OrigImageName = Dialog.getString();
	dir = Dialog.getChoice();
	pixel = parseFloat(Dialog.getString());
	convert = Dialog.getCheckbox();
	
	selectWindow(OrigImageName);
	setBatchMode(true);

if (convert == true){
	run("8-bit");
}

macro "Plot" {
	
		ok = checkImageDepth();
    	if (!ok)
    		showMessage("Thresholded image or 8-bit binary image required");
    	else {
    		if (dir == "1"){
	    		run("Duplicate...", "duplicate");
			    n = nSlices();
			    x = newArray(n);
			    y = newArray(n);
			    for (i=0; i<n; i++) {
			    	setSlice(i+1);
			        x[i] = i;
			        y[i] = measureBinaryImage(pixel);
			        showProgress(i, n);
			    }
    		}
    		else if (dir == "2"){
    			run("Reslice [/]...", "output=1.000 start=Top avoid");
    			n = nSlices();
			    x = newArray(n);
			    y = newArray(n);
			    for (i=0; i<n; i++) {
			    	setSlice(i+1);
			        x[i] = i;
			        y[i] = measureBinaryImage(pixel);
			        showProgress(i, n);
			    }
    		}
    		else{
    			run("Reslice [/]...", "output=1.000 start=Left avoid");
    			n = nSlices();
			    x = newArray(n);
			    y = newArray(n);
			    for (i=0; i<n; i++) {
			    	setSlice(i+1);
			        x[i] = i;
			        y[i] = measureBinaryImage(pixel);
			        showProgress(i, n);
			    }
    		}
			Plot_in_direction(x,y,dir);
			Array.getStatistics(y, min, max, mean, std);
			//print("Stack average porosity: " + mean);
			//run("Set Measurements...", "decimal=4");
			i = nResults;
			setResult("Label", i, "Average");
			setResult("X", i, mean);
			updateResults(); //print to output
    	}
}
	
	

function Plot_in_direction(x,y,dir) {
	Plot.create("Scatter Plot in direction "+ dir, "Slice number", "Water Volume [nl]");
	//Plot.setLimits(0, n, 0, 100);
	Plot.add("circles", x, y);
    return ;
}

function measureBinaryImage(pixel) {
      getStatistics(m, mean, min, max, std, histogram);
      //return count for pixels with value 255
      	volume = histogram[255]*(pixel*pixel*pixel)*0.000001;
      	
      return volume;
}

function checkImageDepth() {
      if (bitDepth!=8) return false;
      getStatistics(m, mean, min, max, std, histogram);
      //check binarized
      if (m != histogram[0]+histogram[255])
          return false;
      return true;
}