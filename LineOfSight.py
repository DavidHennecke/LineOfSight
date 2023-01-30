import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import shape
from shapely import Point, Polygon, to_geojson, validation, MultiPolygon, wkt, distance, LineString
from shapely.ops import unary_union
import fiona
from tqdm import tqdm
import json
import rasterio
from turfpy import measurement
from rasterstats import point_query

print("Calculate Line of Sight:")

def plot(observer, target, LoSPoints):
    #plots the result
    fig, axs = plt.subplots()
    axs.set_aspect('equal', 'datalim')

    xs = LoSPoints[:,0]  
    ys = LoSPoints[:,1]
    axs.plot(xs, ys, "o", color="blue", alpha=1) #Plot targetPoints
    
    xo = observer[:,0]  
    yo = observer[:,1] 
    axs.plot(xo, yo, "o", color="red", alpha=1) #Plot observer
    
    xt = target[:,0]  
    yt = target[:,1]
    axs.plot(xt, yt, "o", color="black", alpha=1) #Plot targetPoints
    
    plt.show()
    
def lineToPoints(line, SegmentDistance):
    points = []
    for i in np.arange(0, line.length, 100):
        val = line.interpolate(i)
        points.append([val.x, val.y])
    return points

def checkLineOfSight (observerGeom, targetGeom, dsmData, transform, hubHeight):
    sight = True
    #get Line of Sight and Points on Line
    segmentSize = transform[0]/2
    LoS = LineString([observerGeom, targetGeom])
    LoSPoints = lineToPoints(LoS, segmentSize)
    #get Heights and Distance
    observerHeight = point_query(observerGeom.wkt,dsmData, affine=transform)
    targetHeight = point_query(targetGeom.wkt,dsmData, affine=transform)
    distanceBetweenObserverTarget = distance(observerGeom, targetGeom)
    
    #interpolation between two points x = distance; y= height
    distances = [0,distanceBetweenObserverTarget]
    heights = [observerHeight[0] + 1.65, targetHeight[0]+hubHeight] #1.65 m average size of a human being
    
    for point in LoSPoints:
        height = np.interp(segmentSize, distances, heights)
        segmentSize = segmentSize + segmentSize
        pointRealHeight = point_query(Point(point).wkt,dsmData, affine=transform)[0]
        
        if pointRealHeight > height:
            sight = False
            return sight, LoSPoints
        else:
            sight = True
    return sight, LoSPoints

def main():
    #load DSM-Raster
    dsmPath = r"Testdaten/SRTM_D_32633.tif"
    dsm = rasterio.open(dsmPath)
    dsmData = dsm.read(1)
    transform = dsm.transform
    
    #load observer
    observersPath = r"Testdaten/observer_32633.shp"
    observers = fiona.open(observersPath)
    observer = observers[0]
    observerGeom = shape(observer["geometry"])
    observerCoords = [(observerGeom.x, observerGeom.y)]
    observerCoords = np.array(observerCoords)
    
    #load targets
    targetsPath = r"Testdaten/stock_LoS_32633.shp"
    targets = fiona.open(targetsPath)
    target = targets[0]
    targetGeom = shape(target["geometry"])
    targetCoords = [(targetGeom.x, targetGeom.y)]
    targetCoords = np.array(targetCoords)
    hubHeight = target['properties']['Height']
    
    sight, LoSPoints = checkLineOfSight (observerGeom, targetGeom, dsmData, transform, hubHeight)
    

    plot(observerCoords, targetCoords, np.array(LoSPoints))
    

if __name__ == "__main__":
    main()