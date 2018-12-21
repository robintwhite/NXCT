/* Written by Sebastian Eberhardt
 *  Edit by Robin White
 *  22/11/2017
 */


title = getTitle()
selectWindow(title);
slc = toString(getSliceNumber())

Dialog.create("Z Shift Check v0.1");
Dialog.setInsets(0, 10, 0)
Dialog.addMessage("Single reference image should have title ref");
Dialog.addString("Title:", "ref",15);
Dialog.addString("Title:", "target",15);
Dialog.addString("Center slice:", slc,15);
Dialog.addString("Slice range:", "2",15);
Dialog.addHelp("https://github.com/robintwhite/NXCT/blob/master/ImageJ_macros/StackAlignment_Procedure.pdf");
Dialog.show();

ref_image = Dialog.getString();
wet_image = Dialog.getString();

center = parseInt(Dialog.getString());
range = parseInt(Dialog.getString());

wet_startslice=center-range;
wet_endslice=center+range;
dry_slc = "1";

for (i=wet_startslice; i<=wet_endslice; i++) 
//var wetslice=85
{
selectWindow(ref_image);
setSlice(parseInt(dry_slc));
run("Duplicate...", "title="+ref_image+dry_slc);
selectWindow(wet_image);
setSlice(i);
run("Duplicate...", "title="+wet_image+i+"");
run("Concatenate...", "  title="+ref_image+dry_slc+wet_image+i+" image1="+ref_image+dry_slc+" "+ "image2="+wet_image+i+" image3=[-- None --]");
run("StackReg", "transformation=[Rigid Body]");
run("Duplicate...", "title="+ref_image+dry_slc);
selectWindow(ref_image+dry_slc+wet_image+i+"");
run("Next Slice [>]");
run("Duplicate...", "title="+wet_image+i+"");
selectWindow(ref_image+dry_slc+wet_image+i+"");

selectWindow(wet_image+i+"");
imageCalculator("Subtract create 32-bit", wet_image+i+"",ref_image+dry_slc);
selectWindow("Result of "+wet_image+i+"");
close(ref_image+dry_slc);
close(wet_image+i+"");
}