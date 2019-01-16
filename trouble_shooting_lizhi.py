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


def extract_pvtype(page):

    #从debug信息中提取kmap内容，进一步提取pvtype
    try:
        if 'kmap xml源码' in page:
            pat_kmap_xml = re.search(r'kmap xml源码(.*?)/DOCUMENT&gt', page, flags=re.DOTALL)

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


def check_result(page):
    try:
        first_res = extract_first_res(page)

        if first_res:

           res_type, vrid = classify_res(first_res)

           if "VR" == res_type:
               print('首条结果是%s结果，vrid=%s' % (res_type, vrid))

           if "Tupu" == res_type or "Lizhi" == res_type:
               pvtype = extract_pvtype(page)

               if pvtype:
                   print('首条结果是%s结果, vrid=%s, pvtype=%s' % (res_type, vrid, pvtype))

                   #如果是图谱或者通用立知结果，给出详细信息
                   if pvtype.startswith('15_300_'):
                       classify_pvtype(pvtype)
                   elif pvtype.startswith('18_'):
                       classify_pvtype('18_*')
                   else:
                       classify_pvtype('Tupu')

               else:
                   print('没有提取到pvtype, 首条结果是%s结果, vrid=%s' % (res_type, vrid))

           if not res_type:
               print('首条结果不是VR、图谱或立知结果')

        else:
            print('[check_result]:没有提取到首条结果')

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
                print("%s: %s" % (option, cf.get(pvtype, option)))
        else:
            print('%s不在已知结果范围内, 请确认' % pvtype)
    except Exception as err:
        print('[classify_pvtype]:%s' % err)

if __name__ == '__main__':

    url_vr_1 = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546930885316&s_t=1546932617545&tabMode=1&s_from=result_up&htprequery=%E4%B9%A9%E6%80%8E%E4%B9%88%E8%AF%BB&keyword=%E4%B9%A9%E6%80%8E%E4%B9%88%E8%AF%BB&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=e60923fa-2fe5-4181-88e9-ce64c40a7dfe&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546932617546&wm=3206'

    url_tupu = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546932618128&s_t=1546935465810&tabMode=1&s_from=result_up&htprequery=%E4%B9%A9%E6%80%8E%E4%B9%88%E8%AF%BB&keyword=%E9%A9%AC%E6%9D%A5%E8%A5%BF%E4%BA%9A%E5%AE%98%E6%96%B9%E8%AF%AD%E8%A8%80&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=582b578c-ec33-4d74-a90d-2707b9cd0f1f&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546935465812&wm=3206'

    url_lizhi = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547092644734&s_t=1547092653580&tabMode=1&s_from=result_up&htprequery=%E4%B8%AD%E5%A4%AE%E7%A9%BA%E8%B0%83%E4%BB%80%E4%B9%88%E6%84%8F%E6%80%9D&keyword=%E7%A1%AB%E9%85%B8%E9%95%81%E7%9A%84%E4%BD%9C%E7%94%A8&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=47a63917-27a2-4542-9545-d02c14d3635f&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547092653582&wm=3206'

    url_lizhi_yiliao = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546935494995&s_t=1546942015467&tabMode=1&s_from=result_up&htprequery=%E9%A9%AC%E6%9D%A5%E8%A5%BF%E4%BA%9A%E5%AE%98%E6%96%B9%E8%AF%AD%E8%A8%80&keyword=%E8%A2%AB%E8%9A%82%E8%9A%81%E5%92%AC%E4%BA%86%E6%80%8E%E4%B9%88%E5%8A%9E&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=2ac8598c-a1d3-40cc-aacf-6897c19617f8&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546942015468&wm=3206'

    url_vr_2 = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546942201053&s_t=1546948617196&tabMode=1&s_from=result_up&htprequery=%E8%A2%AB%E8%9A%82%E8%9A%81%E5%92%AC%E4%BA%86%E6%80%8E%E4%B9%88%E5%8A%9E&keyword=%E7%BB%BF%E8%8C%B6%E5%A9%8A%E6%98%AF%E4%BB%80%E4%B9%88%E6%84%8F%E6%80%9D&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=a734b863-2e90-46d7-9704-4ad2003be5f6&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546948617199&wm=3206'

    url_youzhi = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546948618405&s_t=1546948771482&tabMode=1&s_from=result_up&htprequery=%E7%BB%BF%E8%8C%B6%E5%A9%8A%E6%98%AF%E4%BB%80%E4%B9%88%E6%84%8F%E6%80%9D&keyword=%E5%B9%B3%E5%A4%B4%E5%93%A5%E6%98%AF%E4%BB%80%E4%B9%88%E5%8A%A8%E7%89%A9&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=30d105f9-ef2f-4d59-9947-238fe3ed2e21&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546948771484&wm=3206'

    url_tupu_nolz = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546948772756&s_t=1546948935737&tabMode=1&s_from=result_up&htprequery=%E5%B9%B3%E5%A4%B4%E5%93%A5%E6%98%AF%E4%BB%80%E4%B9%88%E5%8A%A8%E7%89%A9&keyword=%E7%94%9F%E5%BD%93%E4%BD%9C%E4%BA%BA%E6%9D%B0+%E6%AD%BB%E4%BA%A6%E4%B8%BA%E9%AC%BC%E9%9B%84%E6%98%AF%E8%B0%81%E5%86%99%E7%9A%84+&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=76dc9817-3d06-4faf-8e0c-1c507d81319c&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1546948935739&wm=3206'

    url_google = 'https://www.google.com/search?q=trending+%E4%B8%AD%E6%96%87&rlz=1C1GCEU_zh-CNCN829CN829&oq=Trending&aqs=chrome.1.69i57j0l5.1216j0j8&sourceid=chrome&ie=UTF-8'

    url_8_1 = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1546950883916&s_t=1547091390345&tabMode=1&s_from=result_up&htprequery=%E5%B9%B3%E5%A4%B4%E5%93%A5%E6%98%AF%E4%BB%80%E4%B9%88%E5%8A%A8%E7%89%A9&keyword=%E6%8F%8F%E5%86%99%E5%86%AC%E5%A4%A9%E5%86%B7%E7%9A%84%E8%AF%8D%E8%AF%AD&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=8486b873-2c24-4f5e-9ce8-c4092cfb2d0a&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547091390347&wm=3206'

    url_norm = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547121795290&s_t=1547122340433&tabMode=1&s_from=result_up&htprequery=%E7%94%9F%E5%BD%93%E4%BD%9C%E4%BA%BA%E6%9D%B0+%E6%AD%BB%E4%BA%A6%E4%B8%BA%E9%AC%BC%E9%9B%84%E6%98%AF%E8%B0%81%E5%86%99%E7%9A%84&keyword=%E7%99%BE%E5%BA%A6%E7%BB%8F%E9%AA%8C&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=ad217218-c845-4a84-b63c-da32cf7f5154&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547122340434&wm=3206'

    url_youzhi2 = 'https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547188805691&s_t=1547192091410&tabMode=1&s_from=result_up&htprequery=%E7%BB%BF%E8%8C%B6%E5%A9%8A%E6%98%AF%E4%BB%80%E4%B9%88%E6%84%8F%E6%80%9D&keyword=%E4%BA%AC%E4%B8%9C%E7%99%BD%E6%9D%A1%E6%80%8E%E4%B9%88%E5%BC%80%E9%80%9A&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=d138d81f-04a7-42bb-a23b-35ec5188cd8f&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547192091411&wm=3206'

    url_3xx = "https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547522193463&s_t=1547522225461&tabMode=1&s_from=result_up&htprequery=%E7%99%BE%E5%BA%A6%E7%BB%8F%E9%AA%8C&keyword=%E7%99%BE%E5%BA%A6%E7%BB%8F%E9%AA%8C%E4%B8%80%E5%A4%A9%E8%83%BD%E8%B5%9A200&pg=webSearchList&sugct=0&sugri=8&sourceid=sugg&sugoq=%E7%99%BE%E5%BA%A6%E7%BB%8F%E9%AA%8C&sugn=10&suguuid=46e667dc-0e0b-408e-8f29-8cfc2483fb97&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547522225463&wm=3206"

    url_shiwange = "https://wap.sogou.com/web/searchList.jsp?uID=Kk6oNl1Hu3zHTKMJ&v=5&dp=1&w=1278&t=1547539189697&s_t=1547541667639&tabMode=1&s_from=result_up&htprequery=%E4%B8%9C%E4%BA%AC%E4%BA%BA%E5%8F%A3&keyword=%E5%8D%81%E4%B8%87%E4%B8%AA%E4%B8%BA%E4%BB%80%E4%B9%88&pg=webSearchList&s=%E6%90%9C%E7%B4%A2&suguuid=e762abf5-4171-47e9-af5b-6a29e2fa0aa4&sugsuv=AAFesoLIJAAAAAqZOz4PmgoAkwA%3D&sugtime=1547541667641&sugclass=%25E5%258A%25A8%25E6%25BC%25AB&wm=3206"

    source_page = get_page_result(url_lizhi)
    check_result(source_page)

    first_res = extract_first_res(source_page)
    #print(first_res)
    #lizhi = extract_lizhi_icon(source_page)
    #print(lizhi)
    #res_type, vrid = classify_res(first_res)
    #print('type=%s, vrid=%s' % (res_type, vrid))
    #extract_pvtype(source_page)

