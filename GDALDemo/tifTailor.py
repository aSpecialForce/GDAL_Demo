# _*_ coding: utf-8 _*_
import operator
from osgeo import gdal, gdal_array, osr
import shapefile
from PIL import Image
from PIL import ImageDraw

 
def Image2Array(i):
    #将一个Python图像库的数组转换为一个gdal_array图片
    a = gdal_array.numpy.fromstring(i.tobytes(), 'b')
    a.shape = i.im.size[1], i.im.size[0]
    return a
 
def World2Pixel(geoMatrix, x, y):
    #使用GDAL库的geomatrix对象((gdal.GetGeoTransform()))计算地理坐标的像素位置
    ulx = geoMatrix[0]
    uly = geoMatrix[3]
    xDist = geoMatrix[1]
    yDist = geoMatrix[5]
    rtnX = geoMatrix[2]
    rtnY = geoMatrix[4]
    pixel = int((x - ulx) / xDist)
    line = int((uly - y) / abs(yDist))
    return (pixel, line)

def WriteTiff(im_data,im_width,im_height,im_bands,im_geotrans,im_proj,no_data,path):
    if 'int8' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32

    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
    else:
        im_bands, (im_height, im_width) = 1,im_data.shape
  
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)
    if(dataset!= None):
        dataset.SetGeoTransform(im_geotrans)
        dataset.SetProjection(im_proj)
        for i in range(im_bands):
            band=dataset.GetRasterBand(i+1)
            band.SetNoDataValue(no_data)
            #band.ComputeStatistics(True)
            band.WriteArray(im_data[i])
        print('保存文件成功:'+path)
    else:
        print('保存文件失败:'+path)
    del dataset

def ClipRasterByVector(rasterfiel,vectorfile,outputfile):
    srcArray = gdal_array.LoadFile(rasterfiel)
    srcRaster = gdal.Open(rasterfiel)
    geoTrans = srcRaster.GetGeoTransform()
    im_bands = srcRaster.RasterCount
    
    # 使用PyShp库打开shp文件
    srcShape = shapefile.Reader(vectorfile)
    shapes =srcShape.shapes()
    mypoints=shapes[0].points
    minX, minY, maxX, maxY = srcShape.bbox
    ulX, ulY = World2Pixel(geoTrans, minX, maxY)
    lrX, lrY = World2Pixel(geoTrans, maxX, minY)
    pxWidth = int(lrX - ulX)
    pxHeight = int(lrY - ulY)
    clip = srcArray[:, ulY:lrY, ulX:lrX]
    # 为图片创建一个新的geomatrix对象以便附加地理参照数据
    geoTrans = list(geoTrans)
    geoTrans[0] = minX
    geoTrans[3] = maxY
    # 边界线
    pixels = []
    for p in srcShape.shape(0).points:
        pixels.append(World2Pixel(geoTrans, p[0], p[1]))
    
    rasterPoly = Image.new("L", (pxWidth, pxHeight), 1)
    # 使用PIL创建一个空白图片用于绘制多边形
    rasterize = ImageDraw.Draw(rasterPoly)
    rasterize.polygon(pixels, 0)
    # 使用PIL图片转换为Numpy掩膜数组
    mask = Image2Array(rasterPoly)
    # 根据掩膜图层对图像进行裁剪
    no_data_value = -9999.0
    clip = gdal_array.numpy.choose(mask, (clip,no_data_value)).astype(gdal_array.numpy.float32)
    print (clip.max())
    
    WriteTiff(clip,pxWidth,pxHeight,im_bands,geoTrans,srcRaster.GetProjection(),no_data_value,outputfile)

if __name__ == '__main__':
    testDir = 'F:\\WORK\\TestCodes\\python\\GDALDemo\\GDALDemo\\test\\'
    rasterFileList=[]
    rasterFileList.append('SNOW_3Day_4km_2019_0321_v1.tif')
    rasterFileList.append('SNOW_3Day_4km_2019_0327_v1.tif')
    rasterFileList.append('SNOW_3Day_4km_2019_0725_v1.tif')
    rasterFileList.append('SNOW_3Day_4km_2019_0728_v1.tif')

    shp = testDir+'xinjiangprovince.shp'

    for rasterFile in rasterFileList:
        ClipRasterByVector(testDir+rasterFile,shp,testDir+'output\\'+rasterFile)