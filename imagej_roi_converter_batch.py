from ij import IJ;
from ij.plugin.frame import RoiManager;
from java.awt import Color
from ij.gui import PolygonRoi, WaitForUserDialog;
from ij.gui import Roi;
from java.awt import FileDialog
import os

EXCLUDE_ON_EDGES = True
NUCLEI_GROUP = 2
CYTOPLASM_GROUP = 1 
COLORS = [Color.cyan, Color.magenta]
DISTANCE_TO_BORDER = 5
Roi.setGroupName(NUCLEI_GROUP, "nuclei")
Roi.setGroupName(CYTOPLASM_GROUP, "cytoplasm")
Roi.saveGroupNames()

folder = IJ.getDirectory("")

files=[[], [], [], []]
for c in range(0, 4):
	files[c] = [os.path.join(folder, image) for image in os.listdir(folder) if image.lower().endswith("_c"+str(c)+"_cp_outlines.txt")]
if(not files[0] and not files[1] and not files[2] and not files[3]):
	files[0] = [os.path.join(folder, image) for image in os.listdir(folder) if image.lower().endswith("_cp_outlines.txt")]
images = [os.path.join(folder, image) for image in os.listdir(folder)
             if (image.lower().endswith(".tif")
             or image.lower().endswith(".jpg")
             or image.lower().endswith(".png"))
             and not image.lower().endswith("_cp_masks.png")]
ext = images[0].split(".")[1]
RM = RoiManager()
rm = RM.getRoiManager()

c = 0
first = True
g = 0
for channel in files:
	if not channel:
		c = c + 1
		continue 	
	g = g + 1
	for aFile in channel:
		imageFile = aFile.replace("_c"+str(c)+"_cp_outlines.txt", "."+ext)
		IJ.open(imageFile)
		if first:
			IJ.run("Remove Overlay", "")
		imp = IJ.getImage()
		channel = max(1, c);
		imp.setC(c);
		width = imp.getWidth()
		height = imp.getHeight()
		with open(aFile, 'r') as textfile:
			for line in textfile:
				xy = map(int, line.rstrip().split(','))
				X = xy[::2]
				Y = xy[1::2]
				roi = PolygonRoi(X, Y, Roi.POLYGON)	
				if EXCLUDE_ON_EDGES:
					bounds = roi.getBounds()
					if (bounds.x<DISTANCE_TO_BORDER or bounds.y<DISTANCE_TO_BORDER or bounds.x+bounds.width>width-DISTANCE_TO_BORDER or bounds.y+bounds.height>height-DISTANCE_TO_BORDER):
						continue
				imp.setRoi(roi)
				roi.setStrokeColor(Color.yellow)
				roi = imp.getRoi()
				roi.setGroup(g)
				rm.addRoi(roi)
		rm.runCommand("Associate", "true")	 
		rm.runCommand("Show All with labels")		
		IJ.run("From ROI Manager", "")
		imp.getOverlay().setStrokeColor(COLORS[g-1])
		rm.reset()
		IJ.save(imp, imageFile)
		imp.close()
	c = c + 1	
	first = False