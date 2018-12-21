/*To do
 * - option for black or white phase
*/

//Last update 06/7/17 by Robin White

	html = "<html>"
	 +"<h3>For porosity calculation at each slice of stack use already segmented 8-bit image stack</h3>"
	 +"<h3>For average pore size, use local thickness on segmented stack first;<br> found in Analyze>Local Thickness</h3>"
	 +"<h3>All units in pixels</h3>"
     +"<font size=-1>
     +"Written by Robin White, last updated 06/7/2017<br>"
     +"</font>";
	Dialog.create("Help");
	
	title = getTitle();
	Dialog.create("Slice by slice calculator v0.1");
	Dialog.setInsets(0, 10, 0)
	Dialog.addMessage("Stack directions:\n 1 = Through plane view\n 2 = In-plane from Top\n 3 = In-plane from Left");
	Dialog.addString("Title:", title,15);
	Dialog.addChoice("Type:", newArray("Porosity", "Average Pore size"));
	Dialog.addChoice("Direction:", newArray("1", "2", "3"));
	Dialog.addChoice("Phase:", newArray("White", "Black"));
	Dialog.addHelp(html);
	Dialog.show();
	
	OrigImageName = Dialog.getString();
	type = Dialog.getChoice();
	dir = Dialog.getChoice();
	phase = Dialog.getChoice();
	
	selectWindow(OrigImageName);
	setBatchMode(true);

macro "Plot" {
	
	if (type=="Porosity"){
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
			        y[i] = measureBinaryImage(phase);
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
			        y[i] = measureBinaryImage(phase);
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
			        y[i] = measureBinaryImage(phase);
			        showProgress(i, n);
			    }
    		}
			Plot_in_direction(x,y,type,dir);
			Array.getStatistics(y, min, max, mean, std);
			//print("Stack average porosity: " + mean);
			//run("Set Measurements...", "decimal=4");
			i = nResults;
			setResult("Label", i, "Stack porosity");
			setResult("X", i, mean);
			updateResults();
    	}
	}
	
	else {
		ok = checkImageDepth();
    	if (ok)
    		showMessage("Image should be 32-bit with pore size calculated");
    	else {
			if (dir == "1"){
	    		run("Duplicate...", "duplicate");
			    n = nSlices();
			    x = newArray(n);
			    y = newArray(n);
			    for (i=0; i<n; i++) {
			    	setSlice(i+1);
			        x[i] = i;
			        y[i] = measurePSDImage();
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
			        y[i] = measurePSDImage();
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
			        y[i] = measurePSDImage();
			        showProgress(i, n);
			    }
    		}
			Plot_in_direction(x,y,type,dir);
		}
	}
}

function Plot_in_direction(x,y,type,dir) {
	Plot.create("Scatter Plot in direction "+ dir, "Slice number", type);
	//Plot.setLimits(0, n, 0, 100);
	Plot.add("circles", x, y);
    return ;
}

function measureBinaryImage(phase) {
      getStatistics(m, mean, min, max, std, histogram);
      if (phase == "white")
      	percent = histogram[255]/m;
      else
      	percent = histogram[0]/m;
      	
      return percent;
}

function measurePSDImage() {
	xmax = getWidth();
	ymax = getHeight();
	for(x=0;x<xmax;x++){
		for(y=0;y<ymax;y++){
			test=getPixel(x,y);
		if(test==0){setPixel(x,y,NaN);}
		}} 
      getStatistics(m, mean, min, max, std, histogram);
      avg_PSD = mean;
      return avg_PSD;
}

function checkImageDepth() {
      if (bitDepth!=8) return false;
      getStatistics(m, mean, min, max, std, histogram);
      if (m != histogram[0]+histogram[255])
          return false;
      return true;
}