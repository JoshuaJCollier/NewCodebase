import pickle
import numpy as np
import pandas as pd
file = open('500um_127um_60mm_extra_slow.pkl', 'rb')
object_file = pickle.load(file)
file.close()

output1 = np.array(object_file['Outputs1'])
output2 = np.array(object_file['Outputs2'])
positions = np.array(object_file['Positions'])

all_outs = np.array([output1, output2, positions]).T

#np.savetxt("500um-source_127um-sepeartion_60mm-distance_LED.csv", all_outs, delimiter=",")

filename = "500um-source_127um-sepeartion_60mm-distance_LED.csv"
headers = ['Output1', 'Output2', 'Positions']
df = pd.DataFrame(all_outs, columns=headers)
df.to_csv(filename, header=True, sep=',')