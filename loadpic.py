import urllib.request
#fileout = './user_pic/test.bmp'
#image_url = "http://img2015.zdface.com/20180223/162ba002713d02c19d87292eedd3fe8d.gif"
#image_url = "https://timgsa.baidu.com/timg?image&quality=80&size=b9999_10000&sec=1531370305403&di=9a2604f365a62c98bde583b50edd292f&imgtype=0&src=http%3A%2F%2Fh.hiphotos.baidu.com%2Fzhidao%2Fpic%2Fitem%2F4a36acaf2edda3cc9b2102f903e93901203f9226.jpg"
#urllib.request.urlretrieve(image_url, fileout)
def urls(url):
    saveurl = url.split('egs')[1]
    return saveurl
def loadimage(url,p_id):
    fileout = './user_pic/{}.bmp'.format(p_id)
    urllib.request.urlretrieve(url, fileout)