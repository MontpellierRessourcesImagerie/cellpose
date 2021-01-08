from ij import IJ;
from ij.plugin.frame import RoiManager;
from ij.gui import PolygonRoi, WaitForUserDialog;
from ij.gui import Roi;
from java.awt import FileDialog
import os

EXCLUDE_ON_EDGES = True

folder = IJ.getDirectory("")

files = [os.path.join(folder, image) for image in os.listdir(folder) if image.lower().endswith("_cp_outlines.txt")]
images = [os.path.join(folder, image) for image in os.listdir(folder)
             if (image.lower().endswith(".tif")
             or image.lower().endswith(".jpg")
             or image.lower().endswith(".png"))
             and not image.lower().endswith("_cp_masks.png")]
ext = images[0].split(".")[1]
RM = RoiManager()
rm = RM.getRoiManager()

for aFile in files:
	imageFile = aFile.replace("_cp_outlines.txt", "."+ext)
	IJ.open(imageFile)
	IJ.run("Remove Overlay", "")
	imp = IJ.getImage()
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
				if (bounds.x<4 or bounds.y<4 or bounds.x+bounds.width>width-4 or bounds.y+bounds.height>height-4):
					continue
			imp.setRoi(roi)
			roi = imp.getRoi()
			rm.addRoi(roi)
	rm.runCommand("Associate", "true")	 
	rm.runCommand("Show All with labels")
	IJ.run("From ROI Manager", "")
	rm.reset()
	IJ.save(imp, imageFile)
	imp.close()
