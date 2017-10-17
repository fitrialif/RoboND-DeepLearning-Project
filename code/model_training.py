import os
import glob
import sys
import tensorflow as tf

from scipy import misc
import numpy as np

from tensorflow.contrib.keras.python import keras
from tensorflow.contrib.keras.python.keras import layers, models

from tensorflow import image

from utils import scoring_utils
from utils.separable_conv2d import SeparableConv2DKeras, BilinearUpSampling2D
from utils import data_iterator
from utils import plotting_tools
from utils import model_tools


def separable_conv2d_batchnorm(input_layer, filters, strides=1):
    output_layer = SeparableConv2DKeras(filters=filters, kernel_size=3, strides=strides,
                                        padding='same', activation='relu')(input_layer)

    output_layer = layers.BatchNormalization()(output_layer)
    return output_layer


def conv2d_batchnorm(input_layer, filters, kernel_size=3, strides=1):
    output_layer = layers.Conv2D(filters=filters, kernel_size=kernel_size, strides=strides,
                                 padding='same', activation='relu')(input_layer)

    output_layer = layers.BatchNormalization()(output_layer)
    return output_layer



def bilinear_upsample(input_layer):
    output_layer = BilinearUpSampling2D((2,2))(input_layer)
    return output_layer


def encoder_block(input_layer, filters, strides):
    # TODO Create a separable convolution layer using the separable_conv2d_batchnorm() function.
    output_layer = separable_conv2d_batchnorm(input_layer, filters, strides=strides)
    return output_layer


def decoder_block(small_ip_layer, large_ip_layer, filters):
    # TODO Upsample the small input layer using the bilinear_upsample() function.
    upsampled_small_ip_layer = bilinear_upsample(small_ip_layer)

    # print("small", upsampled_small_ip_layer.get_shape())
    # print("large", large_ip_layer.get_shape())

    # TODO Concatenate the upsampled and large input layers using layers.concatenate
    concatenated = layers.concatenate([upsampled_small_ip_layer, large_ip_layer])
    # TODO Add some number of separable convolution layers
    conv_layer_1 = separable_conv2d_batchnorm(concatenated, filters)
    conv_layer_2 = separable_conv2d_batchnorm(conv_layer_1, filters)
    output_layer = separable_conv2d_batchnorm(conv_layer_2, filters)

    return output_layer


def fcn_model(inputs, num_classes):
    # print("num_classes", num_classes)
    # TODO Add Encoder Blocks.
    # Remember that with each encoder layer, the depth of your model (the number of filters) increases.
    encoder_block1 = encoder_block(inputs, 8, strides=2)
    encoder_block2 = encoder_block(encoder_block1, 16, strides=2)
    #     encoder_block3 = encoder_block(encoder_block2, 32, strides=2)
    #     encoder_block4 = encoder_block(encoder_block3, 64, strides=2)

    # TODO Add 1x1 Convolution layer using conv2d_batchnorm().
    one_by_one_conv = conv2d_batchnorm(encoder_block2, 32, kernel_size=1, strides=1)

    # TODO: Add the same number of Decoder Blocks as the number of Encoder Blocks
    decoder_block1 = decoder_block(one_by_one_conv, encoder_block1, 16)
    # print("done decode 1")
    #     decoder_block2 = decoder_block(decoder_block1, encoder_block2, 32)
    # print("done decode 2")
    #     decoder_block3 = decoder_block(decoder_block2, encoder_block1, 16)
    # print("done decode 3")
    x = decoder_block(decoder_block1, inputs, num_classes)

    # The function returns the output layer of your model. "x" is the final layer obtained from the last decoder_block()
    return layers.Conv2D(num_classes, 1, activation='softmax', padding='same')(x)


def fcn_model_3layer(inputs, num_classes, filter_set):
    enc1_filter_num = filter_set[0]
    one_by_one_filter_num = filter_set[1]

    encoder_block1 = encoder_block(inputs, enc1_filter_num, strides=2)
    one_by_one_conv = conv2d_batchnorm(encoder_block1, one_by_one_filter_num, kernel_size=1, strides=1)
    x = decoder_block(one_by_one_conv, inputs, num_classes)

    return layers.Conv2D(num_classes, 1, activation='softmax', padding='same')(x)


def fcn_model_5layer(inputs, num_classes, filter_set):
    enc1_filter_num = filter_set[0]
    enc2_filter_num = filter_set[1]
    one_by_one_filter_num = filter_set[2]
    dec1_filter_num = filter_set[1]

    encoder_block1 = encoder_block(inputs, enc1_filter_num, strides=2)
    encoder_block2 = encoder_block(encoder_block1, enc2_filter_num, strides=2)

    one_by_one_conv = conv2d_batchnorm(encoder_block2, one_by_one_filter_num, kernel_size=1, strides=1)

    decoder_block1 = decoder_block(one_by_one_conv, encoder_block1, dec1_filter_num)
    x = decoder_block(decoder_block1, inputs, num_classes)

    # The function returns the output layer of your model. "x" is the final layer obtained from the last decoder_block()
    return layers.Conv2D(num_classes, 1, activation='softmax', padding='same')(x)


def fcn_model_7layer(inputs, num_classes, filter_set):
    enc1_filter_num = filter_set[0]
    enc2_filter_num = filter_set[1]
    enc3_filter_num = filter_set[2]
    one_by_one_filter_num = filter_set[3]
    dec1_filter_num = filter_set[2]
    dec2_filter_num = filter_set[1]

    encoder_block1 = encoder_block(inputs, enc1_filter_num, strides=2)
    encoder_block2 = encoder_block(encoder_block1, enc2_filter_num, strides=2)
    encoder_block3 = encoder_block(encoder_block2, enc3_filter_num, strides=2)

    one_by_one_conv = conv2d_batchnorm(encoder_block3, one_by_one_filter_num, kernel_size=1, strides=1)

    decoder_block1 = decoder_block(one_by_one_conv, encoder_block2, dec1_filter_num)
    decoder_block2 = decoder_block(decoder_block1, encoder_block1, dec2_filter_num)
    x = decoder_block(decoder_block2, inputs, num_classes)

    # The function returns the output layer of your model. "x" is the final layer obtained from the last decoder_block()
    return layers.Conv2D(num_classes, 1, activation='softmax', padding='same')(x)


def fcn_model_9layer(inputs, num_classes, filter_set):
    enc1_filter_num = filter_set[0]
    enc2_filter_num = filter_set[1]
    enc3_filter_num = filter_set[2]
    enc4_filter_num = filter_set[3]
    one_by_one_filter_num = filter_set[4]
    dec1_filter_num = filter_set[3]
    dec2_filter_num = filter_set[2]
    dec3_filter_num = filter_set[1]

    encoder_block1 = encoder_block(inputs, enc1_filter_num, strides=2)
    encoder_block2 = encoder_block(encoder_block1, enc2_filter_num, strides=2)
    encoder_block3 = encoder_block(encoder_block2, enc3_filter_num, strides=2)
    encoder_block4 = encoder_block(encoder_block3, enc4_filter_num, strides=2)

    one_by_one_conv = conv2d_batchnorm(encoder_block4, one_by_one_filter_num, kernel_size=1, strides=1)

    decoder_block1 = decoder_block(one_by_one_conv, encoder_block3, dec1_filter_num)
    decoder_block2 = decoder_block(decoder_block1, encoder_block2, dec2_filter_num)
    decoder_block3 = decoder_block(decoder_block2, encoder_block1, dec3_filter_num)
    x = decoder_block(decoder_block3, inputs, num_classes)

    # The function returns the output layer of your model. "x" is the final layer obtained from the last decoder_block()
    return layers.Conv2D(num_classes, 1, activation='softmax', padding='same')(x)

"""
DON'T MODIFY ANYTHING IN THIS CELL THAT IS BELOW THIS LINE
"""

image_hw = 160
image_shape = (image_hw, image_hw, 3)
inputs = layers.Input(image_shape)
num_classes = 3

# Call fcn_model()
output_layer = fcn_model(inputs, num_classes)


learning_rate = 0.01
batch_size = 5
num_epochs = 2
steps_per_epoch = 200
validation_steps = 50
workers = 2


"""
DON'T MODIFY ANYTHING IN THIS CELL THAT IS BELOW THIS LINE
"""
# Define the Keras model and compile it for training
model = models.Model(inputs=inputs, outputs=output_layer)

model.compile(optimizer=keras.optimizers.Adam(learning_rate), loss='categorical_crossentropy')

# Data iterators for loading the training and validation data
train_iter = data_iterator.BatchIteratorSimple(batch_size=batch_size,
                                               data_folder=os.path.join('..', 'data', 'train'),
                                               image_shape=image_shape,
                                               shift_aug=True)

val_iter = data_iterator.BatchIteratorSimple(batch_size=batch_size,
                                             data_folder=os.path.join('..', 'data', 'validation'),
                                             image_shape=image_shape)

logger_cb = plotting_tools.LoggerPlotter()
callbacks = [logger_cb]

model.fit_generator(train_iter,
                    steps_per_epoch = steps_per_epoch, # the number of batches per epoch,
                    epochs = num_epochs, # the number of epochs to train for,
                    validation_data = val_iter, # validation iterator
                    validation_steps = validation_steps, # the number of batches to validate on
                    callbacks=callbacks,
                    workers = workers)


# Save your trained model weights
weight_file_name = 'model_weights'
model_tools.save_network(model, weight_file_name)

# If you need to load a model which you previously trained you can uncomment the codeline that calls the function below.

# weight_file_name = 'model_weights'
# restored_model = model_tools.load_network(weight_file_name)


run_num = 'run_1'

val_with_targ, pred_with_targ = model_tools.write_predictions_grade_set(model,
                                        run_num,'patrol_with_targ', 'sample_evaluation_data')

val_no_targ, pred_no_targ = model_tools.write_predictions_grade_set(model,
                                        run_num,'patrol_non_targ', 'sample_evaluation_data')

val_following, pred_following = model_tools.write_predictions_grade_set(model,
                                        run_num,'following_images', 'sample_evaluation_data')


# images while following the target
im_files = plotting_tools.get_im_file_sample('sample_evaluation_data','following_images', run_num)
for i in range(3):
    im_tuple = plotting_tools.load_images(im_files[i])
    plotting_tools.show_images(im_tuple)

# images while at patrol without target
im_files = plotting_tools.get_im_file_sample('sample_evaluation_data', 'patrol_non_targ', run_num)
for i in range(3):
    im_tuple = plotting_tools.load_images(im_files[i])
    plotting_tools.show_images(im_tuple)

# images while at patrol with target
im_files = plotting_tools.get_im_file_sample('sample_evaluation_data','patrol_with_targ', run_num)
for i in range(3):
    im_tuple = plotting_tools.load_images(im_files[i])
    plotting_tools.show_images(im_tuple)


# Scores for while the quad is following behind the target.
true_pos1, false_pos1, false_neg1, iou1 = scoring_utils.score_run_iou(val_following, pred_following)

# Scores for images while the quad is on patrol and the target is not visable
true_pos2, false_pos2, false_neg2, iou2 = scoring_utils.score_run_iou(val_no_targ, pred_no_targ)

# This score measures how well the neural network can detect the target from far away
true_pos3, false_pos3, false_neg3, iou3 = scoring_utils.score_run_iou(val_with_targ, pred_with_targ)

# Sum all the true positives, etc from the three datasets to get a weight for the score
true_pos = true_pos1 + true_pos2 + true_pos3
false_pos = false_pos1 + false_pos2 + false_pos3
false_neg = false_neg1 + false_neg2 + false_neg3

weight = true_pos/(true_pos+false_neg+false_pos)
print(weight)

# The IoU for the dataset that never includes the hero is excluded from grading
final_IoU = (iou1 + iou3)/2
print(final_IoU)

# And the final grade score is
final_score = final_IoU * weight
print(final_score)