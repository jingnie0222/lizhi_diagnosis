#!/usr/bin/python3
# -*-codig=utf8-*-

import sys
import requests
import re
from configparser import ConfigParser

regex_vr = '\<div id=\"sogou_vr_(.*?)_'
regex_lizhi = '\<div .* id=\"sogou_vr_kmap_(.*?)_'
regex_tupu = '\<div .* id=\"lz-top-(.*?)\"'
regex_tupu_8_1 = 'id=\"kmap-jzvr-81-container\"'

regex_url = '&lt;url&gt;&lt;!\\[CDATA\\[(.*?)\\]\\]'
regex_pcurl = '&lt;pc_url&gt;&lt;!\\[CDATA\\[(.*?)\\]\\]'

url_vrid_list = ["50022101", "50023601", "50024701", "50024801", "50022201", "50024401", "50026401"]
pcurl_vrid_list = ["50022301", "50022501", "50024201", "50024301", "50024501", "50026601", "50026301"]


def log_error(str):
    sys.stderr.write('%s\n' % str)
    sys.stderr.flush()


def get_page_result(url):
    url = url + "&dbg=on"
    try:
        res = requests.get(url)
        return res.text
    except Exception as err:
        log_error('[get_page_result]: %s' % err)


def extract_first_res(page):
    try:
        #在前端源码中通过data-v="101"标识来提取首条结果，正则必须使用多行模式
        if 'data-v="101"' in page:
            pat_first_res = re.search(r'<div(.*?)id=(.*) data-v="101">(.*?)</div>', page, flags=re.DOTALL)

            if pat_first_res:
                first_res = pat_first_res.group(0)
                return first_res
        else:
            print('[extract_first_res]:没有找到首条结果，没有data-v="101"标记')
            return None

    except Exception as err:
        print('[extract_first_res]:%s' % err)
        return None


def extract_lizhi_icon(first_result):

    #判断结果是否有立知icon
    lizhi_flag = False
    try:
        if first_result:
            if "class=\"icon-known\"" in first_result:
                lizhi_flag = True

        return lizhi_flag

    except Exception as err:
        print('[extract_lizhi_icon]:%s' % err)
        return False


def classify_res(first_result):

    #根据vrid的正则规则判断结果类别
    res_type = ""
    vr_vrid = ""

    try:
        pat_vr = re.search(regex_vr, first_result)
        pat_lizhi = re.search(regex_lizhi, first_result)
        pat_tupu = re.search(regex_tupu, first_result)
        pat_tupu_8_1 = re.search(regex_tupu_8_1, first_result)

        if pat_vr:
            vr_vrid = pat_vr.group(1)
            res_type = "VR"

        if pat_lizhi:
            vr_vrid = pat_lizhi.group(1)
            res_type = "Lizhi"

        if pat_tupu:
            vr_vrid = pat_tupu.group(1)
            res_type = "Tupu"

        #图谱结果中的特例，query=描写冬天冷的词语，vrid=kmap-jzvr-81-container
        if pat_tupu_8_1:
            vr_vrid = "kmap-jzvr-81-container"
            res_type = "Tupu"

        return res_type, vr_vrid

    except Exception as err:
        print('[classify_res]:%s' % err)
        return None, None


def extract_pvtype(first_result):

    #从debug信息中提取kmap内容，进一步提取pvtype
    try:

        if 'kmap xml源码' in first_result:
            pat_resin = re.search(r'kmap xml源码(.*?)/DOCUMENT&gt', first_result, flags=re.DOTALL)
            pat_node = re.search(r'kmap xml源码(.*?)&lt;/doc&gt;', first_result, flags=re.DOTALL)

        pat_kmap_xml = pat_resin if pat_resin else pat_node

        if pat_kmap_xml:
            kmap_debug = pat_kmap_xml.group(1)
            pat_pvtype = re.search(r'pvtype=&quot;(.*?)&quot;', kmap_debug)

            if pat_pvtype:
                pvtype = pat_pvtype.group(1)
                #print(pvtype)
                return pvtype
            else:
                print('[extract_pvtype]:在kmap xml内容中没有提取到pvtype\n')

        else:
            print('[extract_pvtype]:没有提取到kmap xml内容\n')

    except Exception as err:
        print('[extract_pvtype]:%s' % err)
        return None

def extract_url(first_result):
    try:
        pat_url = re.search(regex_url, first_result, flags=re.DOTALL)

        if pat_url:
            return pat_url.group(1)

    except Exception as err:
        print('[extract_url]:%s' % err)
        return None

def extract_pcurl(first_result):
    try:
        pat_pcurl = re.search(regex_pcurl, first_result, flags=re.DOTALL)

        if pat_pcurl:
            return pat_pcurl.group(1)

    except Exception as err:
        print('[extract_url]:%s' % err)
        return None


def check_result(page):
    result = {'res_type':'',
              'vrid':'',
              'pvtype':'',
              'url':'',
              'error':''}
    try:
        first_res = extract_first_res(page)

        if first_res:

           res_type, vrid = classify_res(first_res)

           if "VR" == res_type:
               result['res_type'] = res_type
               result['vrid'] = vrid

           if "Tupu" == res_type or "Lizhi" == res_type:
               pvtype = extract_pvtype(first_res)

               if pvtype:
                   #如果是图谱或者通用立知结果，给出详细信息
                   #下面的逻辑通过读库实现
                   '''
                   if pvtype.startswith('15_300_'):
                       classify_pvtype(pvtype)
                   elif pvtype.startswith('18_'):
                       classify_pvtype('18_*')
                   else:
                       classify_pvtype('Tupu')
                   '''
                   result['res_type'] = res_type
                   result['vrid'] = vrid
                   result['pvtype'] = pvtype

                   if vrid in url_vrid_list:
                       result['url'] = extract_url(first_res)
                   elif vrid in pcurl_vrid_list:
                       result['url'] = extract_pcurl(first_res)

                   #优质问答结果的读库url需要拼接，页面url##$vrid
                   elif vrid.startswith('8002'):
                       result['url'] = extract_url(first_res) + "##" + vrid
                   else:
                       result['error'] = "该结果的vrid无法获取url"


               else:
                   result['res_type'] = res_type
                   result['vrid'] = vrid
                   result['error'] = "没有提取到pvtype"

           if not res_type:
               result['error'] = "首条结果不是VR、图谱或立知结果"


        else:
            result['error'] = "[check_result]:没有提取到首条结果"

        return result

    except Exception as err:
        print('[check_result]:%s' % err)
        return None

def classify_pvtype(pvtype):

    #根据pvype映射结果的具体信息
    try:
        cf = ConfigParser()
        cf.read("pvtype.ini", encoding="utf-8-sig")

        if pvtype in cf.sections():
            for option in cf.options(pvtype):
                pass
                #print("%s: %s" % (option, cf.get(pvtype, option)))

        else:
            print('%s不在已知结果范围内, 请确认' % pvtype)
            return None

    except Exception as err:
        print('[classify_pvtype]:%s' % err)
        return None


if __name__ == '__main__':

    url_vr_1 = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546930885316&s_t=1546932617545&tabMode=1&s_from=result_up&htprequery=%E4%B9%A9%E6%80%8E%E4%B9%88%E8%AF%BB&keyword=%E4%B9%A9%E6%80%8E%E4%B9%88%E8%AF%BB&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=e60923fa-2fe5-4181-88e9-ce64c40a7dfe&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546932617546&wm=3206'

    url_tupu = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546932618128&s_t=1546935465810&tabMode=1&s_from=result_up&htprequery=%E4%B9%A9%E6%80%8E%E4%B9%88%E8%AF%BB&keyword=%E9%A9%AC%E6%9D%A5%E8%A5%BF%E4%BA%9A%E5%AE%98%E6%96%B9%E8%AF%AD%E8%A8%80&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=582b578c-ec33-4d74-a90d-2707b9cd0f1f&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546935465812&wm=3206'

    url_lizhi = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547092644734&s_t=1547092653580&tabMode=1&s_from=result_up&htprequery=%E4%B8%AD%E5%A4%AE%E7%A9%BA%E8%B0%83%E4%BB%80%E4%B9%88%E6%84%8F%E6%80%9D&keyword=%E7%A1%AB%E9%85%B8%E9%95%81%E7%9A%84%E4%BD%9C%E7%94%A8&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=47a63917-27a2-4542-9545-d02c14d3635f&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547092653582&wm=3206'

    url_lizhi_yiliao = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546935494995&s_t=1546942015467&tabMode=1&s_from=result_up&htprequery=%E9%A9%AC%E6%9D%A5%E8%A5%BF%E4%BA%9A%E5%AE%98%E6%96%B9%E8%AF%AD%E8%A8%80&keyword=%E8%A2%AB%E8%9A%82%E8%9A%81%E5%92%AC%E4%BA%86%E6%80%8E%E4%B9%88%E5%8A%9E&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=2ac8598c-a1d3-40cc-aacf-6897c19617f8&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546942015468&wm=3206'

    url_vr_2 = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546942201053&s_t=1546948617196&tabMode=1&s_from=result_up&htprequery=%E8%A2%AB%E8%9A%82%E8%9A%81%E5%92%AC%E4%BA%86%E6%80%8E%E4%B9%88%E5%8A%9E&keyword=%E7%BB%BF%E8%8C%B6%E5%A9%8A%E6%98%AF%E4%BB%80%E4%B9%88%E6%84%8F%E6%80%9D&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=a734b863-2e90-46d7-9704-4ad2003be5f6&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546948617199&wm=3206'

    url_youzhi = 'http://tc.wap.sogou/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546948618405&s_t=1546948771482&tabMode=1&s_from=result_up&htprequery=%E7%BB%BF%E8%8C%B6%E5%A9%8A%E6%98%AF%E4%BB%80%E4%B9%88%E6%84%8F%E6%80%9D&keyword=%E5%B9%B3%E5%A4%B4%E5%93%A5%E6%98%AF%E4%BB%80%E4%B9%88%E5%8A%A8%E7%89%A9&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=30d105f9-ef2f-4d59-9947-238fe3ed2e21&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546948771484&wm=3206'

    url_tupu_nolz = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546948772756&s_t=1546948935737&tabMode=1&s_from=result_up&htprequery=%E5%B9%B3%E5%A4%B4%E5%93%A5%E6%98%AF%E4%BB%80%E4%B9%88%E5%8A%A8%E7%89%A9&keyword=%E7%94%9F%E5%BD%93%E4%BD%9C%E4%BA%BA%E6%9D%B0+%E6%AD%BB%E4%BA%A6%E4%B8%BA%E9%AC%BC%E9%9B%84%E6%98%AF%E8%B0%81%E5%86%99%E7%9A%84+&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=76dc9817-3d06-4faf-8e0c-1c507d81319c&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546948935739&wm=3206'

    url_google = 'https://www.google.com/search?q=trending+%E4%B8%AD%E6%96%87&rlz=1C1GCEU_zh-CNCN829CN829&oq=Trending&aqs=chrome.1.69i57j0l5.1216j0j8&sourceid=chrome&ie=UTF-8'

    url_8_1 = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546950883916&s_t=1547091390345&tabMode=1&s_from=result_up&htprequery=%E5%B9%B3%E5%A4%B4%E5%93%A5%E6%98%AF%E4%BB%80%E4%B9%88%E5%8A%A8%E7%89%A9&keyword=%E6%8F%8F%E5%86%99%E5%86%AC%E5%A4%A9%E5%86%B7%E7%9A%84%E8%AF%8D%E8%AF%AD&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=8486b873-2c24-4f5e-9ce8-c4092cfb2d0a&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547091390347&wm=3206'

    url_norm = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547121795290&s_t=1547122340433&tabMode=1&s_from=result_up&htprequery=%E7%94%9F%E5%BD%93%E4%BD%9C%E4%BA%BA%E6%9D%B0+%E6%AD%BB%E4%BA%A6%E4%B8%BA%E9%AC%BC%E9%9B%84%E6%98%AF%E8%B0%81%E5%86%99%E7%9A%84&keyword=%E7%99%BE%E5%BA%A6%E7%BB%8F%E9%AA%8C&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=ad217218-c845-4a84-b63c-da32cf7f5154&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547122340434&wm=3206'

    url_youzhi2 = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547188805691&s_t=1547192091410&tabMode=1&s_from=result_up&htprequery=%E7%BB%BF%E8%8C%B6%E5%A9%8A%E6%98%AF%E4%BB%80%E4%B9%88%E6%84%8F%E6%80%9D&keyword=%E4%BA%AC%E4%B8%9C%E7%99%BD%E6%9D%A1%E6%80%8E%E4%B9%88%E5%BC%80%E9%80%9A&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=d138d81f-04a7-42bb-a23b-35ec5188cd8f&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547192091411&wm=3206'

    url_3xx = "https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547522193463&s_t=1547522225461&tabMode=1&s_from=result_up&htprequery=%E7%99%BE%E5%BA%A6%E7%BB%8F%E9%AA%8C&keyword=%E7%99%BE%E5%BA%A6%E7%BB%8F%E9%AA%8C%E4%B8%80%E5%A4%A9%E8%83%BD%E8%B5%9A200&pg=webSearchList&sugct=0&sugri=8&sourceid=sugg&sugoq=%E7%99%BE%E5%BA%A6%E7%BB%8F%E9%AA%8C&sugn=10&suguuid=46e667dc-0e0b-408e-8f29-8cfc2483fb97&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547522225463&wm=3206"

    url_shiwange = "https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547539189697&s_t=1547541667639&tabMode=1&s_from=result_up&htprequery=%E4%B8%9C%E4%BA%AC%E4%BA%BA%E5%8F%A3&keyword=%E5%8D%81%E4%B8%87%E4%B8%AA%E4%B8%BA%E4%BB%80%E4%B9%88&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=e762abf5-4171-47e9-af5b-6a29e2fa0aa4&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547541667641&sugclass=%25E5%258A%25A8%25E6%25BC%25AB&wm=3206"

    url_bianselong = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1548061133724&s_t=1548062199541&tabMode=1&s_from=result_up&htprequery=%E5%8D%81%E4%B8%87%E4%B8%AA%E4%B8%BA%E4%BB%80%E4%B9%88&keyword=%E5%8F%98%E8%89%B2%E9%BE%99%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E5%8F%98%E8%89%B2&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=1cd0c0b5-a2b4-4947-9d61-c5f719e80350&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1548062199543&wm=3206'

    url_short_1 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551931673357&s_t=1551946299029&s_from=result_up&tabMode=1&htprequery=%E8%82%AF%E6%B3%A2%E7%90%B3%E5%93%AA%E5%9B%BD%E4%BA%BA&keyword=%E5%85%83%E7%B4%A0%E5%91%A8%E6%9C%9F%E8%A1%A851%E5%8F%B7%E5%85%83%E7%B4%A0&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=950263f5-63cf-4782-87a4-9eea17bcd213&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551946299032&wm=3206"

    url_short_13 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551946300295&s_t=1551948759512&s_from=result_up&tabMode=1&htprequery=%E5%85%83%E7%B4%A0%E5%91%A8%E6%9C%9F%E8%A1%A851%E5%8F%B7%E5%85%83%E7%B4%A0&keyword=%E8%82%AF%E6%B3%A2%E7%90%B3%E5%93%AA%E5%9B%BD%E4%BA%BA&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=ebded988-a481-4f2f-af5e-ea828df44382&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551948759515&wm=3206"

    url_short_14 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551948760873&s_t=1551948849921&s_from=result_up&tabMode=1&htprequery=%E8%82%AF%E6%B3%A2%E7%90%B3%E5%93%AA%E5%9B%BD%E4%BA%BA&keyword=%E5%B7%9E%E8%A5%BF%E6%B6%A7%E6%BB%81%E4%BD%9C%E8%80%85&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=1a402e8f-8539-4c11-ad35-215842b56680&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551948849926&wm=3206"

    url_short_7 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551948851338&s_t=1551948945737&s_from=result_up&tabMode=1&htprequery=%E5%B7%9E%E8%A5%BF%E6%B6%A7%E6%BB%81%E4%BD%9C%E8%80%85&keyword=%E4%B8%89%E4%BA%BA%E4%B8%80%E6%97%A5%E6%89%93%E4%B8%80%E5%AD%97&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=c74b7361-ed0d-4e21-88f4-fef427d990d9&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551948945739&wm=3206&dbg=on"

    url_baike_2 = "https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1551948953340&s_t=1551949012526&tabMode=1&s_from=result_up&htprequery=%E4%B8%89%E4%BA%BA%E4%B8%80%E6%97%A5%E6%89%93%E4%B8%80%E5%AD%97&keyword=%E6%B2%B9%E9%A6%8D%E7%9A%84%E6%84%8F%E6%80%9D&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=3e3fa715-b15f-42cc-867f-83e8cba51e44&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551949012527&wm=3206"

    url_quanwei_10 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551949013773&s_t=1551949102471&s_from=result_up&tabMode=1&htprequery=%E6%B2%B9%E9%A6%8D%E7%9A%84%E6%84%8F%E6%80%9D&keyword=%E5%BE%AE%E4%BF%A1%E8%A7%A3%E5%B0%81&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=c31c83e0-9225-4aef-9058-8f514a21dd2b&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551949102473&wm=3206"

    url_long_3 = "https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1551949189941&s_t=1551949200275&tabMode=1&s_from=result_up&htprequery=%E7%89%A9%E6%B5%81%E5%85%AC%E5%8F%B8%E8%B5%9A%E9%92%B1%E5%90%97&keyword=%E8%8F%A0%E8%90%9D%E6%80%8E%E4%B9%88%E5%90%83&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=962359e4-578b-424a-b9b0-5eedf98bb747&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551949200277&wm=3206"

    url_list_5 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551949201701&s_t=1551949492413&s_from=result_up&tabMode=1&htprequery=%E8%8F%A0%E8%90%9D%E6%80%8E%E4%B9%88%E5%90%83&keyword=app%E8%B5%9A%E9%92%B1%E6%98%AF%E7%9C%9F%E7%9A%84%E5%90%97&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=a2271b21-f945-4c44-8856-73d1c9fd32e4&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551949492415&wm=3206"

    url_tiquan_8 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551949493856&s_t=1551949610774&s_from=result_up&tabMode=1&htprequery=app%E8%B5%9A%E9%92%B1%E6%98%AF%E7%9C%9F%E7%9A%84%E5%90%97&keyword=%E6%9C%80%E5%BF%AB%E7%9A%84%E8%B5%9A%E9%92%B1%E9%97%A8%E8%B7%AF&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=38d8c908-f1d1-4cb8-b576-9d680ed277ad&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551949610776&wm=3206"

    url_tiquan_9 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551949612157&s_t=1551949689857&s_from=result_up&tabMode=1&htprequery=%E6%9C%80%E5%BF%AB%E7%9A%84%E8%B5%9A%E9%92%B1%E9%97%A8%E8%B7%AF&keyword=kdj%E6%8C%87%E6%A0%87%E4%BD%BF%E7%94%A8%E6%8A%80%E5%B7%A7&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=246712c4-97c1-40e3-83fb-9e1624ee3d46&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551949689859&wm=3206&dbg=on"

    url_tiquan_11 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551949819607&s_t=1551949828825&s_from=result_up&tabMode=1&htprequery=mt4%E5%B9%B3%E5%8F%B0%E5%90%88%E6%B3%95%E5%90%97&keyword=%E5%BC%80%E6%B0%B4%E6%9E%9C%E5%BA%97%E8%B5%9A%E9%92%B1%E5%90%97&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=4f510ecd-e93d-4eea-bde0-b0d2e87302c8&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551949828827&wm=3206&dbg=on"

    url_yiliao_22 = "https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1551949837032&s_t=1551949901143&tabMode=1&s_from=result_up&htprequery=%E5%BC%80%E6%B0%B4%E6%9E%9C%E5%BA%97%E8%B5%9A%E9%92%B1%E5%90%97&keyword=%E6%80%80%E5%AD%95%E6%9C%80%E5%BF%AB%E5%87%A0%E5%A4%A9%E6%9C%89%E6%84%9F%E8%A7%89&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=108de38e-33ca-46bf-a1a8-d65e1f8aa329&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551949901145&wm=3206"

    url_yiliao_20 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551949990615&s_t=1551950102472&s_from=result_up&tabMode=1&htprequery=%E8%AF%95%E7%AE%A1%E5%A9%B4%E5%84%BF%E6%88%90%E5%8A%9F%E7%8E%87%E6%9C%89%E5%A4%9A%E9%AB%98&keyword=%E6%8E%89%E5%A4%B4%E5%8F%91%E5%8E%BB%E5%8C%BB%E9%99%A2%E6%8C%82%E5%93%AA%E4%B8%AA%E7%A7%91&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=e8192b51-76cb-4384-9dfd-91531283677f&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551950102474&wm=3206"

    url_yiliao_19 = "https://wap.sogou.com/web/searchList.jsp?uID=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&v=5&dp=1&w=1283&t=1551950377324&s_t=1551950385308&s_from=result_up&tabMode=1&htprequery=%E5%AD%95%E5%A6%87%E5%BF%85%E5%90%83%E7%9A%8412%E7%A7%8D%E6%B0%B4%E6%9E%9C&keyword=%E9%A2%88%E6%A4%8E%E7%97%8510%E7%A7%8D%E9%94%BB%E7%82%BC%E6%96%B9%E6%B3%95&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=c11455b2-7bd2-4595-ac8d-899fccf4dfd3&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1551950385310&wm=3206&dbg=on"

    source_page = get_page_result(url_vr_1)
    res_dict = check_result(source_page)
    for key in res_dict:
        print('key:%s  value:%s' % (key, res_dict[key]))

    #first_res = extract_first_res(source_page)
    #print(first_res)
    #extract_url(first_res)
    #extract_pcurl(first_res)
    #lizhi = extract_lizhi_icon(source_page)
    #print(lizhi)
    #res_type, vrid = classify_res(first_res)
    #print('type=%s, vrid=%s' % (res_type, vrid))
    #extract_pvtype(source_page)
    #print(classify_pvtype(source_page))
    #print(source_page)

