#
# Copyright 1993-2019 NVIDIA Corporation.  All rights reserved.
#
# NOTICE TO LICENSEE:
#
# This source code and/or documentation ("Licensed Deliverables") are
# subject to NVIDIA intellectual property rights under U.S. and
# international Copyright laws.
#
# These Licensed Deliverables contained herein is PROPRIETARY and
# CONFIDENTIAL to NVIDIA and is being provided under the terms and
# conditions of a form of NVIDIA software license agreement by and
# between NVIDIA and Licensee ("License Agreement") or electronically
# accepted by Licensee.  Notwithstanding any terms or conditions to
# the contrary in the License Agreement, reproduction or disclosure
# of the Licensed Deliverables to any third party without the express
# written consent of NVIDIA is prohibited.
#
# NOTWITHSTANDING ANY TERMS OR CONDITIONS TO THE CONTRARY IN THE
# LICENSE AGREEMENT, NVIDIA MAKES NO REPRESENTATION ABOUT THE
# SUITABILITY OF THESE LICENSED DELIVERABLES FOR ANY PURPOSE.  IT IS
# PROVIDED "AS IS" WITHOUT EXPRESS OR IMPLIED WARRANTY OF ANY KIND.
# NVIDIA DISCLAIMS ALL WARRANTIES WITH REGARD TO THESE LICENSED
# DELIVERABLES, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY,
# NONINFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
# NOTWITHSTANDING ANY TERMS OR CONDITIONS TO THE CONTRARY IN THE
# LICENSE AGREEMENT, IN NO EVENT SHALL NVIDIA BE LIABLE FOR ANY
# SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THESE LICENSED DELIVERABLES.
#
# U.S. Government End Users.  These Licensed Deliverables are a
# "commercial item" as that term is defined at 48 C.F.R. 2.101 (OCT
# 1995), consisting of "commercial computer software" and "commercial
# computer software documentation" as such terms are used in 48
# C.F.R. 12.212 (SEPT 1995) and is provided to the U.S. Government
# only as a commercial end item.  Consistent with 48 C.F.R.12.212 and
# 48 C.F.R. 227.7202-1 through 227.7202-4 (JUNE 1995), all
# U.S. Government End Users acquire the Licensed Deliverables with
# only those rights set forth herein.
#
# Any use of the Licensed Deliverables in individual and commercial
# software must include, in the user documentation and internal
# comments to the code, the above Disclaimer and U.S. Government End
# Users Notice.
#

# This sample uses an ONNX ResNet50 Model to create a TensorRT Inference Engine
import random
from PIL import Image
import numpy as np

import pycuda.driver as cuda
# This import causes pycuda to automatically manage CUDA context creation and cleanup.
import pycuda.autoinit

import tensorrt as trt
import scipy.io
import sys, os
sys.path.insert(1, os.path.join(sys.path[0], ".."))
import common
import time
class ModelData(object):
    MODEL_PATH = "resnet152v1.onnx"
    INPUT_SHAPE = (3, 224, 224)
    # We can convert TensorRT data types to numpy types with trt.nptype()
    DTYPE = trt.float16

# You can set the logger severity higher to suppress messages (or lower to display more messages).
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

# Allocate host and device buffers, and create a stream.
def allocate_buffers(engine):
    # Determine dimensions and create page-locked memory buffers (i.e. won't be swapped to disk) to hold host inputs/outputs.
    h_input = cuda.pagelocked_empty(trt.volume(engine.get_binding_shape(0)), dtype=trt.nptype(ModelData.DTYPE))
    h_output = cuda.pagelocked_empty(trt.volume(engine.get_binding_shape(1)), dtype=trt.nptype(ModelData.DTYPE))
    # Allocate device memory for inputs and outputs.
    d_input = cuda.mem_alloc(h_input.nbytes)
    d_output = cuda.mem_alloc(h_output.nbytes)
    # Create a stream in which to copy inputs/outputs and run inference.
    stream = cuda.Stream()
    return h_input, d_input, h_output, d_output, stream

def do_inference(context, h_input, d_input, h_output, d_output, stream):
    # Transfer input data to the GPU.
    cuda.memcpy_htod_async(d_input, h_input, stream)
    # Run inference.
    context.execute_async(bindings=[int(d_input), int(d_output)], stream_handle=stream.handle)
    # Transfer predictions back from the GPU.
    cuda.memcpy_dtoh_async(h_output, d_output, stream)
    # Synchronize the stream
    stream.synchronize()

# The Onnx path is used for Onnx models.
def build_engine_onnx(model_file):
    with trt.Builder(TRT_LOGGER) as builder, builder.create_network() as network, trt.OnnxParser(network, TRT_LOGGER) as parser:
        builder.max_workspace_size = common.GiB(1)
        # Load the Onnx model and parse it in order to populate the TensorRT network.
        with open(model_file, 'rb') as model:
            parser.parse(model.read())
            #parser.parse returns a bool, and we were not checking it originally.
            # if not parser.parse(model.read()):
            #     print(parser.get_error(0))
            # print(network.get_layer(network.num_layers -1).get_output(0).shape)
            network.mark_output(network.get_layer(network.num_layers -1).get_output(0))
        return builder.build_cuda_engine(network)

def load_normalized_test_case(test_image, pagelocked_buffer):
    # Converts the input image to a CHW Numpy array
    def normalize_image(image):
        # Resize, antialias and transpose the image to CHW.
        c, h, w = ModelData.INPUT_SHAPE
        image_arr = np.asarray(image.resize((w, h), Image.ANTIALIAS)).transpose([2, 0, 1]).astype(trt.nptype(ModelData.DTYPE)).ravel()
        # This particular ResNet50 model requires some preprocessing, specifically, mean normalization.
        return (image_arr / 255.0 - 0.45) / 0.225

    # Normalize the image and copy to pagelocked memory.
    image = Image.open(test_image).convert('RGB')
    # image = 
    # np.copyto(pagelocked_buffer, normalize_image(Image.open(test_image)))
    np.copyto(pagelocked_buffer, normalize_image(image))

    return test_image

def main():
#     data_root = '/datasets/home/62/062/boz004/TensorRT-5.1.5.0/data/cars_restnet152/ILSVRC/Data/DET/test/'
    data_root = '/datasets/home/62/062/boz004/ece228/project/car/devkit/'
    image_root = '/datasets/home/62/062/boz004/ece228/project/car/cars_train/'
#     image_root = '/home/cvrr/opt/TensorRT-5.0.2.6/python/data/cars_resnet152/tiny-imagenet-200/val/images/'
#     text_file = open(data_root + "val_annotations.txt", "r")
#     anno = [line.split("\t") for line in text_file.readlines()]

#     label_file = open(data_root + "labels.txt", "r")
#     find_labels = [line.split(" ") for line in label_file.readlines()]
    
#     cars_annos_all = scipy.io.loadmat(data_root + 'cars_train_annos.mat')
#     cars_annos = cars_annos_all['annotations']
#     cars_annos = np.transpose(cars_annos)

    

    # Set the data path to the directory that contains the trained models and test images for inference.
#     data_path, data_files = common.find_sample_data(description="Runs a ResNet152 on Cars dataset network with a TensorRT inference engine.", subfolder="cars_resnet152", find_files=["00001.jpg", "00002.jpg","00003.jpg","00004.jpg","00005.jpg", "00006.jpg","00007.jpg","00008.jpg","00009.jpg","00010.jpg", ModelData.MODEL_PATH, "cars_labels.txt"])
#     # Get test images, models and labels.
#     test_images = data_files[0:10]
#     onnx_model_file, labels_file = data_files[10:]
#     labels = open(labels_file, 'r').read().split('\n')
#     print(len(labels))
    # print(labels)
    # add the weight of the last layer
#     fc_weights = np.load('/home/cvrr/opt/TensorRT-5.0.2.6/python/data/cars_resnet152/last_layer_weights.npy') # (196, 2048)
#     print(onnx_model_file)
    # Build a TensorRT engine.
    engine_name = 'resnet152v1.engine'
    with open(engine_name, 'rb') as f, trt.Runtime(TRT_LOGGER) as runtime:
        engine = runtime.deserialize_cuda_engine(f.read())
    # with build_engine_onnx(onnx_model_file) as engine:
    # Inference is the same regardless of which parser is used to build the engine, since the model architecture is the same.
    # Allocate buffers and create a CUDA stream.
    h_input, d_input, h_output, d_output, stream = allocate_buffers(engine)
    # Contexts are used to perform inference.
    with engine.create_execution_context() as context:
        t1 = time.time()
        total_time = 0
        right_count = 0
        

        for i in range(1000):
#             test_image = image_root + 'ILSVRC2017_test_%08d.JPEG' % (i+1)
            test_image = image_root + "%05d.jpg" % (i + 1)
            # 'ILSVRC2017_test_00002752.JPEG'
            
#             true_label = anno[i][1]

            # bbox_x1 = cars_annos[i][0][0][0][0]
            # bbox_y1 = cars_annos[i][0][1][0][0]
            # bbox_x2 = cars_annos[i][0][2][0][0]
            # bbox_y2 = cars_annos[i][0][3][0][0]
            # true_label = int(cars_annos[i][0][4][0][0])
            
#             print('true label', true_label)
            image = Image.open(test_image).convert('RGB')
            # image = image.crop([max(0 , bbox_x1 - 16), max(0, bbox_y1 - 16), min(image.size[0], bbox_x2 + 16), min(image.size[1], bbox_y2 + 16)])
            # image.show()
            c, h, w = ModelData.INPUT_SHAPE
            image_arr = np.asarray(image.resize((w, h), Image.ANTIALIAS)).transpose([2, 0, 1]).astype(trt.nptype(ModelData.DTYPE)).ravel()
            a = (image_arr / 255.0 - 0.45) / 0.225
            np.copyto(h_input, a)
            # h, w = img.size
            # dim_diff = np.abs(h - w)
            # print(test_image)
        # for test_image in test_images:
            # Load a normalized test case into the host input page-locked buffer.
            # test_image = random.choice(test_images)
            # test_case = load_normalized_test_case(test_image, h_input)
            # Run the engine. The output will be a 1D tensor of length 1000, where each value represents the
            # probability that the image corresponds to that label
            t_gpu_1 = time.time()
            do_inference(context, h_input, d_input, h_output, d_output, stream)
            t_gpu_2 = time.time()
            gpu_time_diff = t_gpu_2 - t_gpu_1
            total_time += gpu_time_diff
            # print(h_output.shape)
            # We use the highest probability as our prediction. Its index corresponds to the predicted label.
            # output = fc_weights @ h_output
            output = h_output
            # print(output)
#             print('predition:', np.argmax(output))    
#             pred = find_labels[np.argmax(output)][0]
#             if true_label == pred:
#                 right_count += 1
            # print('predition:',pred)
#         print(right_count)
        t2 = time.time()
        print('total time:', t2-t1)
        print('gpu time:', total_time)
        # pred = 0
        # if "_".join(pred.split()) in os.path.splitext(os.path.basename(test_case))[0]:
        #     print("Correctly recognized " + test_case + " as " + pred)
        # else:
        #     print("Incorrectly recognized " + test_case + " as " + pred)

if __name__ == '__main__':
    main()
