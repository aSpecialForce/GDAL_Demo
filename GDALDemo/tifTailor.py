# _*_ coding: utf-8 _*_
import operator
from osgeo import gdal, gdal_array, osr
import shapefile
from PIL import Image
from PIL import ImageDraw
import datetime
import os
import time
import numpy as np
import requests

#WORK_DIR = './'
WORK_DIR = '/usr/local/model/GisData/ServiceData/ModelBase_Data/RemoteSensing/Snowmelt/'
SOURCE_DIR = WORK_DIR+'source/'
OUTPUT_DIR = WORK_DIR+'cliped/'
CONFIG_DIR = WORK_DIR+'config/'
 
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
    
    WriteTiff(clip,pxWidth,pxHeight,im_bands,geoTrans,srcRaster.GetProjection(),no_data_value,outputfile)

def DelFilesByModifyTime(dstDir,daysBefore):
    strDaysBeforeDate = (datetime.datetime.now() + datetime.timedelta(days = (0-daysBefore))).strftime('%Y%m%d')
    if not os.path.exists(dstDir):
        return
    allFile = os.listdir(dstDir)
    for fileName in allFile:
        try:
            full_path = os.path.join(dstDir, fileName)
            if(os.path.isdir(full_path)):
                DelFilesByModifyTime(full_path,daysBefore)
            elif(os.path.isfile(full_path)):
                mdify_time = os.stat(full_path).st_mtime
                file_modify_time = time.strftime('%Y%m%d', time.localtime(mdify_time))
                if int(file_modify_time) < int(strDaysBeforeDate):
                    os.remove(full_path)
                    print('删除文件'+full_path)
        except Exception as e:
            print(e)

def FindNewestDir(province):
    iMaxLastDay = -30
    bFind = False
    strDataDate = ''
    strYear = ''
    strDataDir = ''
    iLastDay=0
    while (not bFind):
        strDataDate = (datetime.datetime.now()+datetime.timedelta(iLastDay)).strftime('%Y_%m%d')
        strYear = strDataDate[0:4]
        strDataDir = SOURCE_DIR+province + '/'+strYear+'/'+strDataDate+'/'
        if os.path.exists(strDataDir):
            bFind = True 
        else:
            iLastDay = iLastDay - 1
        if iLastDay < iMaxLastDay:
            break
    return bFind,strDataDir,strDataDate

def RequestGet(headers,url,bPrintResult = True):
    print('RequestGet......b...e...g...i...n.......')
    print("url = " + url)
    str_result = ""

    response = requests.get(url=url,headers=headers)

    str_result = response.text
    if bPrintResult:
        print(str_result)

    print('......e...n...d.......')
    return str_result

def ClipTif(province):
    bFind,strDataDir,strLastDirName = FindNewestDir(province)
    strDataFileName = ''
    if bFind:
        allFile = os.listdir(strDataDir)
        if len(allFile) > 0:
            strDataFileName = allFile[0]

    if len(strDataFileName) == 0:
        print("未找到数据,路径为:" + WORK_DIR+province)
        return 
    else:
        print("待处理的数据为：" + strDataDir + strDataFileName)

    shp = CONFIG_DIR + province + '/shp/' + province+".shp"
    outputDirTemp = OUTPUT_DIR + province +'/'+ strLastDirName[0:4] +'/'+ strLastDirName+'/'
    if not os.path.exists(outputDirTemp):
        os.makedirs(outputDirTemp)
    ClipRasterByVector(strDataDir + strDataFileName,shp,outputDirTemp + strDataFileName)
    
    try:
        header={"Accept": "application/json;charset=UTF-8"}
        str_tif_folder = outputDirTemp
        pro_type = 1
        if province == 'xizang':
            pro_type = 2
        tif_url = 'http://10.3.10.116:3012/gsafety/model/snowmeltfloods/snowmelt/tiffofyaoganresolver?tiffOfYaoganPathStr={0}&type={1}'.format(str_tif_folder,pro_type)
        RequestGet(header,tif_url,False)
    except Exception as e:
        print(e)
    DelFilesByModifyTime(OUTPUT_DIR,10)

if __name__ == '__main__':
    ClipTif('xinjiang')
    ClipTif('xizang')