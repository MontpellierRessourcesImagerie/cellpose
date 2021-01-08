import csv
import os
import shutil
import time
import tensorflow
import yaml
import argparse
import tensorflow as tf
from csbdeep.io import save_tiff_imagej_compatible
from n2v.internals.N2V_DataGenerator import N2V_DataGenerator
from n2v.models import N2VConfig, N2V
from tensorflow.python.client import device_lib
from tifffile import imread


class ParserCreator(object):

    @classmethod
    def createArgumentParser(cls, parameterFile):
        parser = argparse.ArgumentParser()
        with open(parameterFile, 'r') as file:
            params = yaml.load(file, Loader=yaml.FullLoader)
            for key in params.keys():
                parameterSet = params[key]
                for parameter in parameterSet:
                    if parameter['type'] == 'string':
                        parser.add_argument('--' + parameter['name'], help=parameter['help'],
                                            default=parameter['default'])
                    if parameter['type'] == 'int':
                        parser.add_argument('--' + parameter['name'],
                                            help=parameter['help'],
                                            default=parameter['default'],
                                            type=int)
                    if parameter['type'] == 'float':
                        parser.add_argument('--' + parameter['name'],
                                            help=parameter['help'],
                                            default=parameter['default'],
                                            type=float)
                    if parameter['type'] == 'bool':
                        storeParam = 'store_false'
                        if parameter['default']:
                            storeParam = 'store_true'
                        parser.add_argument('--' + parameter['name'],
                                            help=parameter['help'],
                                            action=storeParam)
        return parser

class N2VNetwork(object):

    @classmethod
    def reportGPUAccess(cls):
        if tf.test.gpu_device_name() == '':
            print('You do not have GPU access.')
            print('Expect slow performance.')
        else:
            print('You have GPU access\n')

    @classmethod
    def reportDevices(cls):
        localDevices = device_lib.list_local_devices()
        print("Available devices:")
        for device in localDevices:
            print(device)

    @classmethod
    def reportTensorFlowAccess(cls):
        print("Using Tensorflow version ", tensorflow.__version__)

    def __init__(self, name):
        super(N2VNetwork, self).__init__()
        self.trainingSource = ""
        self.dataGen = N2V_DataGenerator()
        self.images = None
        self.name = name
        self.path = None
        self.numberOfEpochs = 30
        self.patchSize = 64
        self.numberOfSteps = None
        self.batchSize = 128
        self.percentValidation = 10
        self.initialLearningRate = 0.0004
        self.percentPixel = 1.6
        self.netDepth = 2
        self.kernelSize = 3
        self.uNetNFirst = 32
        self.trainingData = None
        self.validationData = None
        self.config = None
        self.model = None
        self.history = None
        self.start = None
        self.dataAugmentationActivated = False
        self.tile = (2, 1)

    def train(self):
        self.__deleteModelFromDisc()
        self.__prepareData()
        self.start = time.time()
        self.history = self.model.train(self.trainingData, self.validationData)
        print("Training done.")
        print("loss", self.history.history["loss"][-1], "validation loss", self.history.history["val_loss"][-1])

    def predict(self, inputFolder, outputFolder):
        self.model = N2V(None, self.name, basedir=self.path)
        for r, d, f in os.walk(inputFolder):
            for file in f:
                base_filename = os.path.basename(file)
                input_train = imread(os.path.join(r, file))
                pred_train = self.model.predict(input_train, axes='YX', n_tiles=(2, 1))
                save_tiff_imagej_compatible(os.path.join(outputFolder, base_filename), pred_train, axes='YX')
        print("Images saved into folder:", outputFolder)

    def saveHistory(self):
        if os.path.exists(self.path + "/" + self.name + "/Quality Control"):
            shutil.rmtree(self.path + "/" + self.name + "/Quality Control")
        os.makedirs(self.path + "/" + self.name + "/Quality Control")
        lossDataCSVPath = self.path + '/' + self.name + '/Quality Control/training_evaluation.csv'
        with open(lossDataCSVPath, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['loss', 'val_loss'])
            for i in range(len(self.history.history['loss'])):
                writer.writerow([self.history.history['loss'][i], self.history.history['val_loss'][i]])

    def printElapsedTime(self):
        dt = time.time() - self.start
        minutes, sec = divmod(dt, 60)
        hour, minutes = divmod(minutes, 60)
        print("Time elapsed:", hour, "hour(s)", minutes, "min(s)", round(sec), "sec(s)")

    def setTrainingSource(self, trainingSource):
        self.trainingSource = trainingSource

    def getTrainingImages(self):
        if not self.images:
            self.images = self.dataGen.load_imgs_from_directory(directory=self.trainingSource)
        return self.images

    def getName(self):
        return self.name

    def setPath(self, path):
        self.path = path

    def setNumberOfEpochs(self, nrOfEpochs):
        self.numberOfEpochs = nrOfEpochs

    def setPatchSize(self, size):
        self.patchSize = size

    def setNumberOfSteps(self, steps):
        self.numberOfSteps = steps

    def setBatchSize(self, batchSize):
        self.batchSize = batchSize

    def setPercentValidation(self, percent):
        self.percentValidation = percent

    def setInitialLearningRate(self, rate):
        self.initialLearningRate = rate

    def setPercentPixel(self, percent):
        self.percentPixel = percent

    def setNetDepth(self, depth):
        self.netDepth = depth

    def setKernelSize(self, size):
        self.kernelSize = size

    def setUNetNFirst(self, n):
        self.uNetNFirst = n

    def deactivateDataAugmentation(self):
        self.dataAugmentationActivated = False

    def activateDataAugmentation(self):
        self.dataAugmentationActivated = True

    def setTile(self, tile):
        self.tile = tile

    def __prepareData(self):
        # split patches from the training images
        data = self.dataGen.generate_patches_from_list(self.getTrainingImages(),
                                                       shape=(self.patchSize, self.patchSize),
                                                       augment=self.dataAugmentationActivated)
        # create a threshold (10 % patches for the validation)
        threshold = int(data.shape[0] * (self.percentValidation / 100))
        # split the patches into training patches and validation patches
        self.trainingData = data[threshold:]
        self.validationData = data[:threshold]
        if not self.numberOfSteps:
            self.numberOfSteps = int(self.trainingData.shape[0] / self.batchSize) + 1
        print(data.shape[0], "patches created.")
        print(threshold, "patch images for validation (", self.percentValidation, "%).")
        print(self.trainingData.shape[0] - threshold, "patch images for training.")
        print(self.numberOfSteps)
        # noinspection PyTypeChecker
        self.config = N2VConfig(self.trainingData,
                                unet_kern_size=self.kernelSize,
                                train_steps_per_epoch=self.numberOfSteps,
                                train_epochs=self.numberOfEpochs,
                                train_loss='mse',
                                batch_norm=True,
                                train_batch_size=self.batchSize,
                                n2v_patch_shape=(self.patchSize, self.patchSize),
                                n2v_perc_pix=self.percentPixel,
                                n2v_manipulator='uniform_withCP',
                                unet_n_depth=self.netDepth,
                                unet_n_first=self.uNetNFirst,
                                train_learning_rate=self.initialLearningRate,
                                n2v_neighborhood_radius=5)
        print(vars(self.config))
        self.model = N2V(self.config, self.name, basedir=self.path)
        print("Setup done.")
        print(self.config)

    def __deleteModelFromDisc(self):
        if os.path.exists(self.path + '/' + self.name):
            shutil.rmtree(self.path + '/' + self.name)

