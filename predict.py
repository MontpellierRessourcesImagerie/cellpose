import os
import sys
from dl4mic.cliparser import ParserCreator
from cellpose import models, io

def main(argv):
    parser = ParserCreator.createArgumentParser("./predict.yml")
    if len(argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args(argv[1:])
    print(args)
    model = models.Cellpose(gpu=args.gpu, model_type=args.modelType)
    files = [os.path.join(args.dataPath, image) for image in os.listdir(args.dataPath)
             if (image.lower().endswith(".tif")
             or image.lower().endswith(".jpg")
             or image.lower().endswith(".png"))
             and not image.lower().endswith("_cp_masks.png")]
    channels = [[args.segChannel, args.nucleiChannel]] * len(files)
    diameter = args.diameter
    if diameter == 0:
        diameter = None
    for channel, filename in zip(channels, files):
        img = io.imread(filename)
        masks, flows, styles, diams = model.eval(img, diameter=diameter, channels=channel)
        newFilename = filename.split(".")[0]+"_c"+str(args.segChannel)+"."+filename.split(".")[1]
        io.save_to_png(img, masks, flows, newFilename)


if __name__ == '__main__':
    main(sys.argv)
