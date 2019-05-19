import tensorflow as tf

class Simple(tf.keras.Model):

    '''
        Simple : Simplified VGG-19 Architecture for task 1.
    '''

    def __init__(self, num_features, weight_decay, initializer):

        super(Simple, self).__init__()
        
        self.num_features = num_features
        
        self.conv1 = tf.keras.layers.Convolution2D(self.num_features, 3, 1, 'same', activation='relu', kernel_initializer=initializer, kernel_regularizer=tf.keras.regularizers.l2(weight_decay))
        self.max_pool1 = tf.keras.layers.MaxPooling2D(2, 2, 'same')
        self.conv2 = tf.keras.layers.Convolution2D(self.num_features, 3, 1, 'same', activation='relu', kernel_initializer=initializer, kernel_regularizer=tf.keras.regularizers.l2(weight_decay))
        self.max_pool2 = tf.keras.layers.MaxPooling2D(2, 2, 'same')
        self.conv3 = tf.keras.layers.Convolution2D(self.num_features * 2, 3, 1, 'same', activation='relu', kernel_initializer=initializer, kernel_regularizer=tf.keras.regularizers.l2(weight_decay))
        self.max_pool3 = tf.keras.layers.MaxPooling2D(2, 2, 'same')
        self.conv4 = tf.keras.layers.Convolution2D(self.num_features * 2, 3, 1, 'same', activation='relu', kernel_initializer=initializer, kernel_regularizer=tf.keras.regularizers.l2(weight_decay))
        self.max_pool4 = tf.keras.layers.MaxPooling2D(2, 2, 'same')
        
        self.flatten = tf.keras.layers.Flatten()
        
        self.fc1 = tf.keras.layers.Dense(self.num_features * 4, activation='relu', kernel_initializer=initializer, kernel_regularizer=tf.keras.regularizers.l2(weight_decay))
        self.fc2 = tf.keras.layers.Dense(3, activation='relu', kernel_initializer=initializer, kernel_regularizer=tf.keras.regularizers.l2(weight_decay))

    def call(self, x, training=True):
        
        x = self.conv1(x)
        x = self.max_pool1(x)
        x = self.conv2(x)
        x = self.max_pool2(x)
        x = self.conv3(x)
        x = self.max_pool3(x)
        x = self.conv4(x)
        x = self.max_pool4(x)
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.fc2(x)
        
        return x
        