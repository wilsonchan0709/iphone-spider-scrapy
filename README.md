# iphone-scrapy-spider
Date: 30-Sep-2018

Objective:
- Estimate iPhone selling price in the online market.

Requirements:
- Mac OS, Docker, Sublime Text 3, Python with its packages - re, os, glob, scrapy, scrapy_splash, numpy and pandas.
- Before running this script, we need to run below command on a separate terminal in order to handle JavaScript Rendering by splash:
  - docker run -p 8050:8050 scrapinghub/splash
- In the orginal terminal, run below to start crawling:
  - scrapy crawl iPhone_spider -o items.csv

Spider Script Overview:

In first part, it defines the total number of pages of search result and make the request of each pages by SplashRequest which provides JavaScript Rendering to load all the iPhone from the page. For each item, it crawls the selected information including sku, price, name of item, name of seller and the url of the item (a page provide detail information of the item). However, it also make request on the item url by normal Scrapy Request to crawl additional information including model, color and memory of the iPhone.

From second part, the script produces a csv file upon completion of the spider run, and it executes the statements from the close method. Inside the close method, it uses data manipulation and classification by NumPy and Pandas to transform the unstructured data to structured data such that the structured data can be aggregated to produce the statistical data which serves the purpose of this project. 

Performance Review:

It scraped a total of 489 webpages by Scrapy and Splash Requests. The time used is about 26 minutes; thus, crawling speed per page is about 3 seconds.

Result Review:

There are 3 outputs produced by the script.
1. JD_iPhone.csv - 472 items scraped.
2. iPhone_price.csv - 273 iPhones after data transformation and cleaning.
3. iPhone_price_average.csv - which estimates the pricing of various iPhones on online store market.

However, by sample checking, it is found that there is a inconsistent data that classifies a iPhone 8 as iPhone SE. The reason is that jd.com categorizes this item as iPhone SE. Checking on model against memory can avoid this problem.
