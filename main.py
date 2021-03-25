# imports
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # or any {'0', '1', '2'}

import scipy.stats
from sklearn.metrics import roc_curve, auc

import numpy as np
import matplotlib.pyplot as plt

import autoencoder as AE
import loss

import time
#%% note
"""
Modellen met methode 2 trainen (als het niet te lang duurt)
loss = "MeanSquaredError":
[16,32,64,128]dense(36*16)A
[16,32,64,128]dense(36*8)A
"""
#%% settings
# Toggels
train_model = False

show_summary = True
plot_healthy = True
plot_diseased = True

plot_ROC = True
plot_probability_density = True

#%% configuration settings
path_images = '../../Images/' # navigate to ~/source/Images from ~/source/Github/autoencoder.py
path_models = './models/'

# settings for tarining / loading models
# comment away any unused variables:
AE_settings = {
#    'input_shape' : (96,96,3),
    'filters'     : [16,32,64,128], #[64, 32, 16],
#    'kernel_size' : (3,3),
#    'pool_size'   : (2,2),
#    'activation'  : 'relu',
#    'padding'     : 'same',
#    'model_name'  : None,
    'dense_bn'    : 8,
    }
Train_settings = {
    'num_epochs' : 10,
    'loss'       : 'MeanSquaredError',
#    'optimizer'  : 'adam',
    }
# end

load_model_name = 'AE_v2_F128.64.32.32_K3.3_P2.2_Dbn-None_W_E10_L-MeanSquaredError_D23-03-2021_17-43-11.hdf5'

# settings for ROC & probabiliy density curves
n_image_sets = 32 # for 16*32 = 512 images per group
analysis_loss = loss.perceptual_loss # pick some form of loss from loss.py


#%% end settings
if __name__ == '__main__':
    print(f'[info] starting. starting time: {time.ctime()}')
    if train_model:
        model = AE.AutoEncoder(**AE_settings)
        train_gen, val_gen = AE.ImageGeneratorsTrain(path_images)
        history = AE.TrainModel(model, train_gen, val_gen, **Train_settings)
    else:
        model = AE.LoadModel(load_model_name)
    if show_summary: model.summary()

    test_gen_H, test_gen_D = AE.ImageGeneratorsTest(path_images)

    if plot_healthy:  AE.plot(model,test_gen_H)
    if plot_diseased: AE.plot(model,test_gen_D)

    if plot_ROC or plot_probability_density:
        # generate the healthy / unhealthy predictions for a 50/50 sample set.
        Hl = AE.score(model, test_gen_H, analysis_loss, verbose=True, n=n_image_sets)
        Dl = AE.score(model, test_gen_D, analysis_loss, verbose=True, n=n_image_sets)

        # the used loss function is NOT between 1 & 0 so normalize the data.
        # tmp = np.max([Hl,Dl])
        # Hl /= tmp
        # Dl /= tmp
        over1 = np.sum(np.concatenate((Hl,Dl))>1)
        print(f'[info] the numer of values above 1: {over1:.0f}/{2*32*n_image_sets:.0f} or {over1/(2*32*n_image_sets):.2%}')
        # end normalization

        if plot_ROC:
            labels = np.concatenate((np.zeros(Hl.size),np.ones(Dl.size)))
            predictions = np.concatenate((Hl,Dl))

            fpr1, tpr1, thresholds = roc_curve(labels, predictions)
            AUC = auc(fpr1, tpr1); print(AUC)
            #plotting ROC from random classifier
            plt.figure()
            plt.plot([0, 1], [0, 1], 'k--')
            plt.plot(fpr1, tpr1)
            plt.legend(["random","model"])

        if plot_probability_density:
            plt.figure()
            color = {0:['green','springgreen','healthy'], 1:['red','tomato','diseased']}
            for T,data in enumerate([Hl,Dl]):
                bw =  None #0.1 # How smooth/rough the line can be, lower is rougher. None = default
                kde = scipy.stats.gaussian_kde(data,bw_method=bw)
                # plot (normalized) histogram of the data
                plt.hist(data, 50, density=1, facecolor=color[T][0], alpha=0.5);
                # plot density estimates
                t_range = np.linspace(0,1,200)
                plt.plot(t_range,kde(t_range),lw=2,
                         label=f'{color[T][0]} = {color[T][2]}',color=color[T][1])
                plt.xlim(0,1)
                plt.legend(loc='best')
    print(f'[info] finished. finished time: {time.ctime()}')