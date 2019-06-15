# Transfer Learning and Deep Neural Network Acceleration for Image Classification

This project aims at performing image classifications (Monkey dataset and Cars dataset) using transfer learning in deep neural networks along with TensorRT inference acceleration. 

## Prerequisites

1. Pytorch (GPU Version)
2. 	TensorRT 5.x.x

## Running
### Transfer Learnin:
Using Google Colab to run jupyter notebook files is highly recommended.  
1. training:  
Open ResNet_152_Testing_on_Cars_Dataset.ipynb and run all.  
2. testing:  
Open ResNet_152_Train_on_Cars_Dataset.ipynb and run all.  
### TensorRT:  
1. Save model to xx.onnx file
2. python cars_152_build_engine.py to create tensorRT engine.
3. python cars_152_run.py to run the inferencce acceleration.

## Authors
[andrewhuang51](https://github.com/andrewhuang51)  
[arikhor](https://github.com/arikhor)  
[eebowen](https://github.com/eebowen)  
[hjyu2019](https://github.com/hjyu2019)  
[yeqinghuang516](https://github.com/yeqinghuang516)  
