from RoboticArmControl.LayerModule import Layer
from RoboticArmControl.Elements import Position
from RoboticArmControl.BrickModule import Brick
import numpy as np
from RoboticArmControl.dataOb import DB


#Layer Test
layer = Layer()

for i in range(10):
    tmp = Brick()
    tmp.pos.setPos(np.array([float(i), 0.0, 0.0]))
    layer.addBrick(tmp)


#DB Test
db=DB("data.txt")
db.getData()

print("Source")
for d in db.srcBricks:
    print(d.pos.pos)

print("Destination")
for d in db.dstBricks:
    print(d.pos.pos)

for layer in db.layerList:
    print(layer.calCenter())
