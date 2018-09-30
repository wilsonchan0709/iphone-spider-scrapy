# -*- coding: utf-8 -*-
#date: 22-Sep-2018
"""
This project is to crawl the price of various iPhone models from jd.com
by using the software / programming below:
- Docker
- Python with its packages
- Sublime Text 3

Before running this script, we need to run below command on a separate terminal in order to
hande JavaScript Rendering by splash:
- docker run -p 8050:8050 scrapinghub/splash

In the orginal terminal, run below to start crawling:
- scrapy crawl iPhone_spider -o items.csv

In first part of this script, it is to crawl the unstructured data from various url; in 
second part, the script uses data manipulation and classification to transform the 
unstructured data to structured data such that the structued data can be aggregated to
produce the statistics which serves the purpose of this project. I.e. estimate the price
of all iPhone models in the online store market.
"""
import os
import glob
from scrapy import Spider
from scrapy.http import Request
from scrapy_splash import SplashRequest
from iphone_spider.items import IphoneSpiderItem
import numpy as np
import pandas as pd
import re

lua_script = '''
function main(splash)                     
    splash:go(splash.args.url)        --open the url
    splash:wait(2)                    --wait 2 seconds
    splash:runjs("document.getElementsByClassName('page')[0].scrollIntoView(true)")
    --run JavaScript to scroll down the view
    return splash:html()              --return html code
end
'''
#Splash implements the JavaScript Rendering by above lua script

class IphoneSpider(Spider):
    name = 'iphone'
    allowed_domains = ['search.jd.com',
                       'jd.com',
                       '3.cn']
    base_url = 'http://search.jd.com/search?keyword=iPhone&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&bs=1&cid2=653&cid3=655&ev=exbrand_Apple%5E'
    #the url which returns search result of "iPhone"

    def start_requests(self):
        """use start_request instead of start_urls"""
        yield Request(self.base_url, 
                      callback=self.parse_urls)

    def parse_urls(self, response):
        pageNum = int(response.xpath('//*[@class="fp-text"]/i/text()').extract_first())
        #the total number of pages

        for i in range(pageNum):
            """iterate each page of search result"""
            url = '{}&page={}'.format(self.base_url, 2*i+1)
            #analyze the structure of url
            #first page of search result is https://search.jd.com/Search?keyword={}&enc=utf-8&page1,
            #and second page is https://search.jd.com/Search?keyword={}&enc=utf-8&page3

            yield SplashRequest(url, endpoint='execute',
                                args={'lua_source':lua_script},
                                cache_args=['lua_source'],
                                callback=self.parse)
            #return the splash:html() from lua script to this request

    def parse(self, response):
        """crawl sales information of iPhone from search resul page"""
        for sel in response.xpath('//*[@id="J_goodsList"]/ul/li[@class="gl-item"]'):
            """iterate all items in this page"""
            sku = sel.xpath('.//@data-sku').extract_first()
            price = float(sel.xpath('.//div/div[3]/strong/i/text()').extract_first())
            name = ''.join(sel.xpath('.//div/div[4]/a/em/descendant-or-self::node()/text()').extract())
            seller = sel.xpath('.//div/div[7]/span/a/text()').extract_first()
            sku_url = "http:" + sel.xpath('.//div/div[1]/a/@href').extract_first()

            yield Request(sku_url,
                          callback=self.parse_item,
                          meta = {'sku' : sku,
                                  'price' : price,
                                  'name' : name,
                                  'seller' : seller})
            #make the request of individual page

    def parse_item(self, response):
        """crawl sales information of iPhone from its own page"""
        item = IphoneSpiderItem()

        item['sku'] = response.meta.get('sku')
        item['price'] = response.meta.get('price')
        item['name'] = response.meta.get('name')
        item['seller'] = response.meta.get('seller')
        #pass the data from parse to parse_item

        url = response.url
        model = response.xpath('//*[@id="crumb-wrap"]/div/div[1]/div[9]/text()').extract_first()
        color = response.xpath('//div[@data-type="颜色"]/div[@class="dd"]/div[contains(@class, "selected")]/a/i/text()').extract_first()
        memory = response.xpath('//div[@data-type="版本"]/div[@class="dd"]/div[contains(@class, "selected")]/a/text()').extract_first()
        memory2 = response.xpath('//div[@data-type="内存"]/div[@class="dd"]/div[contains(@class, "selected")]/a/text()').extract_first()
        #memory data can be stored in 版本 or 内存

        if memory2:
            memory = memory2.strip()
        elif memory:
            memory = memory.strip()

        item['model'] = model
        item['color'] = color
        item['memory'] = memory
        item['url'] = url

        return item

    def close(self, reason):
        """execute below actions when the spider completes the crawling"""
        csv_file = max(glob.iglob('*.csv'), key=os.path.getctime)
        os.rename(csv_file, 'JD_iPhone.csv')

        base_dir = os.path.abspath(__file__)
        parent_dir = os.path.dirname(base_dir)
        parent_dir = os.path.dirname(parent_dir)
        final_dir = os.path.dirname(parent_dir)
        #retrieve the path of returned csv file

        df = pd.read_csv(final_dir + '/JD_iPhone.csv')
        df1 = df.copy()


        """classify memory"""
        def memoryConvert(x):
            try:
                memory_list = re.findall(r'(\d+)g', x, re.I)
                for i in memory_list:
                    if i != '4': #ignore 4G which represents LTE
                        return i+'GB'
            except:
                return np.nan

        memory_convert = df1['memory'].apply(memoryConvert)
        df1.loc[:, 'memory'] = memory_convert.values #replace column of dataframe by numpy array
        df2 = df1[df1['memory'].isnull() == False]


        """classify model - part 1, by model variable"""
        def iPhoneConvert(item): #x is a string
            """
            iphone list:
            3G, 3GS, 4, 4S, 5, 5C, 5S , 6, 6plus,
            6s, 6s plus, SE, 7, 7plus, 8, 8plus, X, XS, XS MAX, XR
            """
            plus_model = {'iphone\s*6\s*s\s*plus': 'iPhone 6S Plus',
                          'iphone\s*6\s*plus': 'iPhone 6 Plus',
                          'iphone\s*7\s*plus': 'iPhone 7 Plus',
                          'iphone\s*8\s*plus': 'iPhone 8 Plus'}
            max_model = {'iphone\s*x\s*s\s*max': 'iPhone XS Max'}
            normal_model = {'iphone\s*3\s*g\s*s':'iPhone 3GS',
                            'iphone\s*3\s*g':'iPhone 3G',
                            'iphone\s*4\s*s':'iPhone 4S',
                            'iphone\s*4':'iPhone 4',
                            'iphone\s*5\s*c':'iPhone 5C',
                            'iphone\s*5\s*s':'iPhone 5S',
                            'iphone\s*5':'iPhone 5',
                            'iphone\s*6\s*s':'iPhone 6S',
                            'iphone\s*6':'iPhone 6',
                            'iphone\s*se':'iPhone SE',
                            'iphone\s*7':'iPhone 7',
                            'iphone\s*8':'iPhone 8',
                            'iphone\s*x\s*s':'iPhone XS',
                            'iphone\s*x\s*r':'iPhone XR',
                            'iphone\s*x':'iPhone X'}
            
            if item is np.nan:
                return np.nan
            else:
                ignore_list = re.findall('\d+GB|\d+G',item)
                for ignore in ignore_list:
                    item = item.replace(ignore,'')
                    #ignore 4G LTE and memory       
                if re.search("plus", item, re.I):
                    for key, value in plus_model.items():
                        if re.search(key, item, re.I):
                            return value
                    return np.nan
                elif re.search("max", item, re.I):
                    for key, value in max_model.items():
                        if re.search(key, item, re.I):
                            return value
                    return np.nan
                else:
                    for key, value in normal_model.items():
                        if re.search(key, item, re.I):
                            return value
                    return np.nan

        df3 = df2.copy()
        iphone_convert = df3['model'].apply(iPhoneConvert)
        df3.loc[:, 'model'] = iphone_convert.values #replace by numpy array


        """classify model - part 2, by color variable"""
        df4 = df3.copy()
        color_convert_model = df4['color'].apply(iPhoneConvert)

        for index, row in df4.iterrows():
            if df4.loc[index,'model'] is np.nan:
                df4.loc[index,'model'] = color_convert_model[index]
            

        """data aggregation"""
        df5 = df4.copy()
        df5 = df5[df5['model'].isnull() == False][['model','memory','price','url']]
        df5.to_csv(final_dir + '/iPhone_price.csv')

        table = pd.pivot_table(df5, values="price",
                               index=["model", "memory"],
                               aggfunc=np.mean)

        pd.options.display.float_format = '{:,.0f}'.format
        print(table)
        table.to_csv(final_dir + '/iPhone_price_average.csv')



