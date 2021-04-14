# -*- coding: utf-8 -*-
"""word2word-seq2seq-nmt.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1z-gbYCh9_TaLeMPg4rAbXp9gPt0r2XCY
"""

import tensorflow as tf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import string
from string import digits

from google.colab import drive
drive.mount('/content/gdrive')

data_path='/content/gdrive/MyDrive/Seq2Seq Content/data/fra.txt'

lines=open(data_path).read().split('\n')

lines





s_lines= pd.read_table(data_path, names=['eng', 'fr','_'])
s_lines

s_lines.eng=s_lines.eng.apply(lambda x: x.lower())
s_lines.fr=s_lines.fr.apply(lambda x: x.lower())

exclude = set(string.punctuation)
s_lines.eng=s_lines.eng.apply(lambda x: ''.join(ch for ch in x if ch not in exclude))
s_lines.fr=s_lines.fr.apply(lambda x: ''.join(ch for ch in x if ch not in exclude))

remove_digits = str.maketrans('', '', digits)
s_lines.eng=s_lines.eng.apply(lambda x: x.translate(remove_digits))
s_lines.fr=s_lines.fr.apply(lambda x: x.translate(remove_digits))

s_lines

s_lines.fr = s_lines.fr.apply(lambda x : '<GO> '+ x + ' <STOP>')

s_lines

s_lines[0:10]







total_samples=20000
input_texts=list(s_lines.eng)[:total_samples]
target_texts=list(s_lines.fr)[:total_samples]

input_words=set()
target_words=set()

    

for eng in input_texts:
    for word in eng.split():
        if word not in input_words:
            input_words.add(word)

for fr in target_texts:
    for word in fr.split():
        if word not in target_words:
            target_words.add(word)

len(input_texts)

input_words

target_words

len(input_words)

input_texts









input_words=sorted(list(input_words))
target_words=sorted(list(target_words))

num_encoder_tokens=len(input_words)
num_decoder_tokens=len(target_words)

print("Length of Encoder Tokens : ",num_encoder_tokens)

print("Length of Decoder Tokens : ",num_decoder_tokens)

input_words

lenght_list=[]
for l in s_lines.eng:
    lenght_list.append(len(l.split(' ')))
np.max(lenght_list)

temp_ilen_list=[]
temp_tlen_list=[]

for x in input_texts:
    temp_ilen_list.append(len(x.split(' ')))
    
for x in target_texts:
    temp_tlen_list.append(len(x.split(' ')))
    
max(temp_ilen_list),max(temp_tlen_list)

max_encoder_word_len=max(temp_ilen_list)
max_decoder_word_len=max(temp_tlen_list)

input_token_index=dict([(word,i) for i,word in enumerate(input_words)])
target_token_index=dict([(word,i) for i,word in enumerate(target_words)])

input_token_index

target_token_index



#Important shaping of inputs :

encoder_input_data=np.zeros(
    (len(input_texts),max_encoder_word_len),
    dtype='float32'
)

decoder_input_data=np.zeros(
(len(target_texts),max_decoder_word_len),
    dtype='float32'
)

decoder_target_data=np.zeros(
(len(target_texts),max_decoder_word_len,num_decoder_tokens),
    dtype='float32'
)

target_token_index

for i,(input_text,target_text) in enumerate(zip(input_texts,target_texts)):
    for t,word in enumerate(input_text.split()):
        encoder_input_data[i,t]=input_token_index[word]
    
    for t,word in enumerate(target_text.split()):
        decoder_input_data[i,t]=target_token_index[word]
        
        if t>0:
                   # decoder_target_data will be ahead by one timestep
            # and will not include the start character.
            
            decoder_target_data[i,t-1,target_token_index[word]]=1

#Model Build  :

latent_dim=128

from tensorflow.keras.layers import Dense,LSTM,Embedding,Input
from tensorflow.keras.models import Model
from tensorflow.keras.utils import plot_model
from tensorflow.keras.callbacks import EarlyStopping

encoder_inputs=Input(shape=(None,))
encoder_embed_layer=Embedding(num_encoder_tokens,latent_dim)(encoder_inputs)
encoder_LSTM=LSTM(latent_dim,return_state=True)
encoder_outputs,state_h,state_c=encoder_LSTM(encoder_embed_layer)

encoder_states=[state_h,state_c]

# Set up the decoder, using `encoder_states` as initial state.

decoder_inputs=Input(shape=(None,))

decoder_embed_layer=Embedding(num_decoder_tokens,latent_dim)
final_decoder_embed_layer=decoder_embed_layer(decoder_inputs)

decoder_LSTM=LSTM(latent_dim,return_sequences=True,return_state=True)

decoder_outputs,_,_=decoder_LSTM(final_decoder_embed_layer,initial_state=encoder_states)

decoder_dense=Dense(num_decoder_tokens,activation='softmax')

decoder_outputs=decoder_dense(decoder_outputs)





#optim=tf.keras.optimizers.RMSprop(lr=0.01)

model=Model([encoder_inputs,decoder_inputs],decoder_outputs)
model.compile(optimizer='adam',loss='categorical_crossentropy',metrics=['accuracy'])
model.summary()

batch_size=128
epochs=100
history=model.fit([encoder_input_data,decoder_input_data],decoder_target_data,
                  batch_size=batch_size,epochs=epochs,validation_split=0.2)



#Sampling and Inference Model Build : 

encoder_model=Model(encoder_inputs,encoder_states)
encoder_model.summary()

decoder_state_input_h = Input(shape=(latent_dim,))
decoder_state_input_c = Input(shape=(latent_dim,))
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]

final_decoder_embed= decoder_embed_layer(decoder_inputs)

decoder_outputs2, state_h2, state_c2 = decoder_LSTM(final_decoder_embed, initial_state=decoder_states_inputs)
decoder_states2 = [state_h2, state_c2]

decoder_outputs2 = decoder_dense(decoder_outputs2)

decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs2] + decoder_states2)



# Reverse-lookup token index to decode sequences back to
# something readable.

reverse_input_word_index = dict(
    (i, word) for word, i in input_token_index.items())
reverse_target_word_index = dict(
    (i, word) for word, i in target_token_index.items())



#Decoding an Sequence Function :
def decode_seq(input_seq):
    states_value=encoder_model.predict(input_seq)
    
    target_seq=np.zeros((1,1))
    
    target_seq[0,0]=target_token_index['<GO>']
    
    stop_condition=False
    decoded__sent=''
    
    while not stop_condition:
        output_tokens,h,c=decoder_model.predict(
        [target_seq]+states_value
        )
        
        sampled_token_index=np.argmax(output_tokens[0,-1,:])
        sampled_word=reverse_target_word_index[sampled_token_index]
        
        decoded_sent=decoded__sent+sampled_word
        
        if sampled_word ==' <STOP>' or len(decoded__sent)>max_decoder_word_len:
            stop_condition=True
        
        target_seq=np.zeros((1,1))
        target_seq[0,0]=sampled_token_index
        
        states_value=[h,c]
        
        
    return decoded__sent



v=encoder_input_data[0:1]
decode_seq(v)

for seq_index in [5,6,7]:
    input_seq = encoder_input_data[seq_index: seq_index + 1]
    decoded_sentence = decode_seq(input_seq)
    print('-')
    print('Input sentence:', s_lines.eng[seq_index: seq_index + 1])
    print('Decoded sentence:', decoded_sentence)

