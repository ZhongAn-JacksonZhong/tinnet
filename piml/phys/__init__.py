"""collection of chemisorption models.

hammer_norskov:

newns_anderson:
"""

import os
import sys

import numpy as np
import tensorflow as tf
from ase import *


class chemisorption:

    def __init__(self, ads, f_ads, deg_ads):
        self.ads = ads # name of the adsorbate
        self.f_ads = f_ads # filling of adsorbate orbitals
        self.deg_ads = deg_ads # degeneracy of adsorbate orbitals
        self.eps_rads = eps_rads # renormalized epsilon of adsorbate states

    def hammer_norskov(self, eps_rads, f_d, dcen, vad2, alpha, sp_hyb):
        """ Hammer, PRL (1996)
        """
        self.f_d = f_d # filling of substrate d-orbitals
        self.dcen = dcen # d-band center
        self.vad2 = vad2 # interatomic coupling matrix element squared
        self.alpha = alpha # Pauli repulsion coeff
        self.sp_hyb = sp_hyb # hybridization energy with sp-states

        d_eps = self.dcen - self.eps_a

        d_hyb = - self.deg * ((self.f_a % 2 + (1 - 2*self.f_a)*self.f_d) 
                              * self.vad2/abs(d_eps)
                              - self.alpha * (self.f_a % 2 + self.f_d) 
                              * self.vad2)
        
        ads_ergy = d_hyb.sum() + self.sp_hyb
        
        return ads_ergy

    def newns_anderson(self, namodel_in, ergy, alpha_ergy, dos_sp, dos_d, num_image,
                num_datapoints):
        
        effadse = tf.tanh(namodel_in[:,0]) * 20.0 + 0.0
        vak2_sp = tf.sigmoid(namodel_in[:,1]) * 20.0 + 0.0
        vak2_d = tf.sigmoid(namodel_in[:,2]) * 20.0 + 0.0
        alpha_sp = tf.sigmoid(namodel_in[:,3]) * 1.0 + 0.0
        alpha_d = tf.sigmoid(namodel_in[:,4]) * 1.0 + 0.0
        gamma_sp = tf.sigmoid(namodel_in[:,5]) * 1.0 + 0.0
        gamma_d = tf.sigmoid(namodel_in[:,6]) * 1.0 + 0.0

        namodel_in_tf = tf.transpose(tf.convert_to_tensor([effadse, vak2_sp,
                                                           vak2_d, alpha_sp,
                                                           alpha_d, gamma_sp,
                                                           gamma_d]))
        
        de = tf.abs(effadse[:,None]-ergy[None,:])
    
        wdos = np.pi * (vak2_sp[:,None] * dos_sp[None,:]
                        * tf.exp(alpha_sp[:,None] * alpha_ergy[None,:]
                        * ergy[None,:]) * tf.exp(-gamma_sp[:,None] * de)
                        + vak2_d [:,None] * dos_d [None,:]
                        * tf.exp(alpha_d [:,None] * alpha_ergy[None,:]
                        * ergy[None,:]) * tf.exp(-gamma_d [:,None] * de))
        
        htwdos = []
        
        for i in range(num_image):
            
            af = tf.signal.fft(tf.cast(wdos[i], tf.complex64))
            h = np.zeros(num_datapoints)
            
            if num_datapoints % 2 == 0:
                h[0] = h[num_datapoints // 2] = 1
                h[1:num_datapoints // 2] = 2
            else:
                h[0] = 1
                h[1:(num_datapoints+1) // 2] = 2
                
            h = tf.convert_to_tensor(h, tf.complex64)
            htwdos += [tf.math.imag(tf.signal.ifft(af*h))]
            
        htwdos = tf.convert_to_tensor(htwdos)

        dos_ads_na = wdos / ((ergy[None,:]-effadse[:,None]-htwdos)**2
                             + wdos**2) / np.pi

        ans_namodel = dos_ads_na / tf.reduce_sum(dos_ads_na, axis=1)[:,None]
        
        return ans_namodel*100 , namodel_in_tf
