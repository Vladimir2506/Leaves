﻿import tensorflow as tf
import numpy as np
import os
import pdb
import cv2

from Archs import create_model

class Solver1(object):

    def __init__(self, opt):

        self.opt = opt
        self.train_opt = opt['solver']
        self.data_opt = opt['datasets']
        self.model_opt = opt['networks']

        # Image Properties
        self.img_size = opt['img_size']
        self.img_channels = opt['img_channels']

        # Training Options
        self.batch_size = self.train_opt['batch_size']
        self.learning_rate_init = self.train_opt['lr_init']
        self.optimizer_type = self.train_opt['optimizer_type'].upper()
        self.learning_rate_decay = self.train_opt['lr_decay']
        self.decay_steps = self.train_opt['decay_steps']
        self.save_steps = self.train_opt['save_steps']
        self.learning_rate = tf.Variable(self.learning_rate_init, name='learning_rate')
        self.global_step = tf.Variable(1, name='global_step')
        self.max_steps = self.train_opt['max_steps']
        self.resume = self.train_opt['resume']

        if self.optimizer_type == 'ADAM':
            self.optimizer = tf.train.AdamOptimizer(self.learning_rate)
        elif self.optimizer_type == 'MOMENTUM':
            self.optimizer = tf.train.MomentumOptimizer(self.learning_rate, 0.95)
        elif self.optimizer_type == 'RMSPROP':
            self.optimizer = tf.train.RMSPropOptimizer(self.learning_rate)
        elif self.optimizer_type == 'SGD':
            self.optimizer = tf.train.GradientDescentOptimizer(self.learning_rate)
        else:
            raise NotImplementedError('Optimizer [%s] not supported!' % self.optimizer_type)
        
        # Dataset Options
        self.cpu_threads = self.opt['cpu_threads']
        self.train_dir = self.data_opt['train']['dir']
        self.train_dataset = tf.data.TFRecordDataset([self.train_dir], None, None, self.cpu_threads)
        self.train_dataset = self.train_dataset.map(self._parse_function, self.cpu_threads).map(self._augment, self.cpu_threads)
        self.train_dataset = self.train_dataset.repeat(-1).shuffle(5000).batch(self.batch_size).prefetch(self.batch_size)
        self.val_dir = self.data_opt['val']['dir']
        self.val_dataset = tf.data.TFRecordDataset([self.val_dir], None, None, self.cpu_threads)
        self.val_dataset = self.val_dataset.map(self._parse_function, self.cpu_threads).batch(self.batch_size).prefetch(self.batch_size)

        # Model Options
        self.model = create_model(self.opt)
        self.loss = tf.losses.sparse_softmax_cross_entropy
        

    def _parse_function(self, example_proto):
        
        features = {'image': tf.FixedLenFeature((), tf.string, ''), 'label': tf.FixedLenFeature((), tf.int64, -1)}
        
        parsed_features = tf.parse_single_example(example_proto, features)
        
        lbl = parsed_features['label']
        img_raw = parsed_features['image']
        
        image = tf.decode_raw(img_raw, tf.uint8)
        image = tf.reshape(image, [self.img_size, self.img_size, self.img_channels])
        image = tf.cast(image, tf.float32)
        label = tf.cast(lbl, tf.int32)
        
        return image, label
    
    def _normalize_image(self, image_in):

        image_out = image_in / 127.5 - 1

        return image_out

    def _denormalize_image(self, image_in):

        image_out = (image_in + 1) * 127.5
        image_out[image_out > 255.0] = 255.0
        image_out[image_out < 0.0] = 0.0

        return image_out
    
    def _augment(self, images, labels):

        images = tf.image.random_flip_left_right(images)
        images = tf.image.random_flip_up_down(images)
        #images = tf.image.random_brightness(images, 127.5)

        return images, labels

    def metric(self, labels, logits):

        pred_result = tf.math.softmax(logits)
        pred_result = tf.math.argmax(pred_result, 1)
        pred_result = tf.cast(pred_result, tf.int32)
        compare = tf.cast(tf.equal(pred_result, labels), tf.float32)
        acc = tf.reduce_mean(compare)

        return acc

    def _save_checkpoint(self):
        
        checkpoint_dir = self.train_opt['ckpt_dir'] + '%03d/' % self.train_opt['ckpt_id']
        os.makedirs(checkpoint_dir, exist_ok=True)
        checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
        ckpt = tf.train.Checkpoint(optimizer=self.optimizer, model=self.model, optimizer_step=self.global_step)
        ckpt.save(checkpoint_prefix)
    
    def _load_checkpoint(self):

        checkpoint_dir = self.train_opt['ckpt_dir'] + '%03d/' % self.train_opt['ckpt_id']
        print('Loading checkpoint from [%s]' % checkpoint_dir)
        ckpt = tf.train.Checkpoint(optimizer=self.optimizer, model=self.model, optimizer_step=self.global_step)
        ckpt.restore(tf.train.latest_checkpoint(checkpoint_dir))

    def train(self):
        
        print('===> Training starts.')

        if self.resume:
            self._load_checkpoint()
        
        for step, train_batch in enumerate(self.train_dataset):
            
            self.global_step.assign(step)

            if self.global_step > self.max_steps:
                break
            
            images, labels = train_batch

            '''test_img = images[0].numpy().astype(np.uint8)
            test_img = cv2.cvtColor(test_img, cv2.COLOR_RGB2BGR)
            cv2.imshow('test', test_img)
            cv2.waitKey(0)
            pdb.set_trace()'''
            images = self._normalize_image(images)            
            
            with tf.GradientTape() as tape:
                logits = self.model(images)
                loss = self.loss(labels, logits)
            
            train_acc = self.metric(labels, logits) * 100

            grads = tape.gradient(loss, self.model.variables)
            
            self.optimizer.apply_gradients(zip(grads, self.model.variables), global_step=self.global_step)

            print('[Step %d] Training loss = %.4f, Training Accuracy = %.2f%%.' % (self.global_step, loss, train_acc), end='\r')
            
        
        print('===> Training ends.')
        
    
    def test(self):

        print('Testing starts.')

        self._load_checkpoint()

        print('Testing ends.')
