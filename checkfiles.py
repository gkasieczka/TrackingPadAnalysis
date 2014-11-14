import os, sets

dirs = os.listdir('results')

missingruns = []

for d in dirs:
    if not os.path.isdir('results/'+d): continue
    if not 'run' in d: continue
    if not os.path.isfile('results/'+d+'/track_info.root'): missingruns.append(int(d.split('_')[1]))


print 'a total of %d runs missing' %(len(missingruns))
print '=========================='
print sorted(missingruns)


missingmasks= [ 142, 148, 154, 152, 149, 156, 158, 157, 159, 162, 161, 165, 166, 169, 180, 168, 184, 185, 187, 186, 336, 338, 340, 342, 344, 348, 350, 352, 354, 356, 357, 358, 359, 360, 361, 362, 363, 364, 366, 368, 371, 370, 434, 372, 373, 622, 663 ]


runs = sets.Set(missingruns)
mask = sets.Set(missingmasks)

print 'issuperset:', runs.issuperset(mask)
print 'in both:', len(runs.intersection(mask))
print 'in runs but not mask:', runs.difference(mask)
print 'in mask but not runs:', mask.difference(runs)
