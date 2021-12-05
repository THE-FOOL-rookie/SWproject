import pyaudio
import wave
from tqdm import tqdm
import time
import numpy as np
from scipy import signal
import wave
from pixel_ring import pixel_ring
from gpiozero import LED

power = LED(5)
power.on()
pixel_ring.set_brightness(50)



_VARS = {'distance': np.array([]),
         'distance0.1': np.array([]),
         'distance1': np.array([]),
         'myflag': False,
         'audioData': np.array([]),
         '0.1sData': np.array([])}

# record parameters
CHUNK = 4800
#CHUNK = 4410
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000    #采样率
#RATE = 44100
RECORD_SECONDS = 60
WAVE_OUTPUT_FILENAME = "output.wav"



p = pyaudio.PyAudio()

# record file info
recordFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
recordFile.setnchannels(CHANNELS)
recordFile.setsampwidth(p.get_sample_size(FORMAT))
recordFile.setframerate(RATE)

def recordCallback(in_data, frame_count, time_info, status):
    # global myflag
    recordFile.writeframes(in_data)
    _VARS['0.1sData'] = np.frombuffer(in_data,dtype='int16')
    _VARS['audioData'] = np.append(_VARS['audioData'] ,_VARS['0.1sData'] )
    # print(len(_VARS['audioData']))
    # print(_VARS['0.1sData'])
    # print(_VARS['audioData'])

    # _VARS['distance0.1'] = getdistance(_VARS['audioData'])
    # _VARS['distance'] = np.append(_VARS['distance']  ,_VARS['distance0.1'] )

    # print(distance)
    # if distance[4799] >= 3.0 or distance[4799] <= -3.0 :
    #     print ('1')
    #     myflag = 1
    # else:
    #     print ('0')
    #     myflag = 0

    return (in_data, pyaudio.paContinue)


def getdistance(audioData):
    freq = 18000
    fs = RATE
    c = 343
    t = np.arange(len(audioData))/fs
    signalCos = np.cos(2*np.pi*freq*t)
    signalSin = np.sin(2*np.pi*freq*t)
    b, a = signal.butter(3, 50/(fs/2), 'lowpass')
    signalI = signal.filtfilt(b,a,audioData*signalCos)
    signalQ = signal.filtfilt(b,a,audioData*signalSin)
    signalI = signalI - np.mean(signalI)
    signalQ = signalQ - np.mean(signalQ)
    phase = np.arctan(signalQ/signalI)
    phase = np.unwrap(phase*2)/2
    distance = c*phase/(4*np.pi*freq)
    return distance[-1]









# open record stream
recordStream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=10,  #此处需要设置为ac108的index
                frames_per_buffer=CHUNK,
                stream_callback=recordCallback)



print("recording")



t = 0
time.sleep(1)
while t<RECORD_SECONDS:
    _VARS['distance1'] = getdistance(_VARS['audioData'])
    time.sleep(0.5)
    _VARS['distance'] = np.append(_VARS['distance']  ,_VARS['distance1'] )
    print (_VARS['distance1'])
    # print (len(_VARS['distance']))
 

    if _VARS['distance'][-1] >= 0.1 or _VARS['distance'][-1] <= -0.1 :
        print ('1')
        _VARS['myflag'] = 1
        pixel_ring.think()
        time.sleep(0.5)

    elif _VARS['distance'][-1] < 0.1 and _VARS['distance'][-1] > -0.1 :
        print ('0')
        _VARS['myflag'] = 0
        pixel_ring.off()
        time.sleep(0.5)

    else:
        print ('0')
        _VARS['myflag'] = 0     
        pixel_ring.speak()
        time.sleep(0.5)

    # t = t + 1
    # print(t)
    
print("done recording")




# stop record stream
recordStream.stop_stream()
recordStream.close()
recordFile.close()
# close PyAudio
p.terminate()


