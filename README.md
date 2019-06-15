# Transfer Learning and Inference Acceleration

This project aims at performing image classifications (Monkey dataset and Cars dataset) using transfer learning in deep neural networks along with TensorRT inference acceleration. 

## Prerequisites

1. Pytorch (GPU Version)
2. 	TensorRT 5.x.x

## Running
###Transfer Learnin:  
Open .ipynb and run all.  
Using Google Colab to run jupyter notebook files is highly recommended.
###TensorRT:  
1. Save model to xx.onnx file
2. python cars_152_build_engine.py to create tensorRT engine.
3. python cars_152_run.py to run the inferencce acceleration.