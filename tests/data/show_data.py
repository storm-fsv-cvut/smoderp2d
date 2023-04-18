import pickle
with open('tests\data\destak.save', 'rb') as fd:
# with open('nucice.save', 'rb') as fd:
    data = pickle.load(fd)

for key in data.keys():
    print (key)
    input()
    print (data[key])
    
