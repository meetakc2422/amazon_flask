from flask import render_template,request,Flask
import time
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from mysql.connector.errors import ProgrammingError
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import string
import mysql.connector
from parsel import Selector
from time import sleep
user_name = 'akash'
password = 'akash'
my_app = Flask(__name__)
data_points = ['ID', 'rank1', 'category', 'ProductTitle','brandname','clientid','modelnumber','total_rating','average_rating','ASIN','main_image_link' ,'first_listed_on' ,'sub_title_text' ,'brand_store_link'  ,'number_of_images'   ,'number_of_videos'   ,'standard_delivery_type'   ,'has_variation_mapping'   ,'has_APlus'   ,'feature_bullet_count'   ,'specifications','abt_this_item','sale_price'   ,'mrp','discount','discount_percentage','availability','item_weight','product_dimension','standard_delivery_date','seller_name','no_of_sellers','fastest_delivery']
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="2422",
    database="mydatabase"
)

cursor = mydb.cursor()
cursor.execute("DROP TABLE IF EXISTS result1")
cursor.execute("DROP TABLE IF EXISTS variants_asin")
cursor.execute("DROP TABLE IF EXISTS combined_table")

def cacheclear(driver):
    driver.get('chrome://settings/clearBrowserData')
    actions = ActionChains(driver)
    time.sleep(2)
    actions.send_keys(Keys.TAB * 7 + Keys.DOWN * 3)  # send right combination
    actions.send_keys(Keys.ENTER)
    actions.perform()
    time.sleep(1)

def removeRedundantTables(mydb):
    sql_cursor = mydb.cursor()
    remove_table1 = "DROP TABLE IF EXISTS result1"
    remove_table2 = "DROP TABLE IF EXISTS variants_asin"
    sql_cursor.execute(remove_table1)
    sql_cursor.execute(remove_table2)


def createservicedb(mydb):
    sql_cursor = mydb.cursor()
    table = "CREATE TABLE if not exists ProductService(ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,clientID varchar(255),serviceType varchar(255),workplace varchar(244), serviceRequestDate DATE, status varchar(225))"
    insert2table = "INSERT INTO ProductService(clientID,serviceType,serviceRequestDate,status,workplace) Values('','Service',CURDATE(),'pending','amazon')"
    sql_cursor.execute(table)
    sql_cursor.execute(insert2table)
    mydb.commit()

def insert2db(record):

    cur = mydb.cursor()
    try:
        cur.execute("CREATE TABLE if not exists result1 (ID INT(244),rank1 VARCHAR(100), category LONGTEXT,ProductTitle LONGTEXT,brandname VARCHAR(100),clientid varchar(244),modelnumber VARCHAR(100),total_rating VARCHAR(30),average_rating VARCHAR(4),ASIN LONGTEXT,main_image_link VARCHAR(300),first_listed_on LONGTEXT,sub_title_text LONGTEXT,brand_store_link VARCHAR(300),number_of_images VARCHAR(4),number_of_videos VARCHAR(30),standard_delivery_type VARCHAR(30),has_variation_mapping VARCHAR(30),has_APlus VARCHAR(30),feature_bullet_count VARCHAR(30),specifications VARCHAR(1000),abt_this_item LONGTEXT,sale_price VARCHAR(30),mrp VARCHAR(30),discount VARCHAR(10),discount_percentage VARCHAR(30),availability LONGTEXT,item_weight VARCHAR(30),product_dimension TEXT(300),standard_delivery_date VARCHAR(30),seller_name LONGTEXT,no_of_sellers VARCHAR(30),fastest_delivery VARCHAR(30))")
    except Exception:
        pass
    InsertData = "INSERT INTO result1(ID, rank1, category, ProductTitle,brandname,clientid,modelnumber,total_rating,average_rating,ASIN,main_image_link ,first_listed_on ,sub_title_text ,brand_store_link  ,number_of_images   ,number_of_videos   ,standard_delivery_type   ,has_variation_mapping   ,has_APlus   ,feature_bullet_count   ,specifications   ,abt_this_item   ,sale_price   ,mrp,discount,discount_percentage,availability,item_weight,product_dimension,standard_delivery_date,seller_name,no_of_sellers,fastest_delivery) Values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    cur.execute(InsertData,record)
    mydb.commit()

def insertAsin2db(record):
    cur = mydb.cursor()
    try:
        cur.execute("CREATE TABLE variants_asin (asin1 LONGTEXT, variants_asinList LONGTEXT)")
    except Exception:
        pass
    InsertAsins = "INSERT INTO variants_asin(asin1, variants_asinList) VALUES (%s,%s)"
    cur.execute(InsertAsins,record)
    mydb.commit()
def merging_table():
    new_table = "CREATE TABLE if not exists combined_table as SELECT * FROM mydatabase.result1 LEFT JOIN mydatabase.variants_asin on result1.ASIN = variants_asin.asin1"
    mydb.cursor().execute(new_table)
    drop_column = "ALTER TABLE combined_table DROP COLUMN asin1"
    mydb.cursor().execute(drop_column)
    # mydb.commit()
    status_change = "UPDATE ProductService SET status = 1 where ID = (select * from (select max(ID) from ProductService) as maxid)"
    mydb.cursor().execute(status_change)
    mydb.commit()

def main_func(urls,client_id):
        sleep(3)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        options.add_argument("--no-sandbox")
        options.add_argument("--diable-dev-shm-usage")
        ID_script = "SELECT ID FROM ProductService WHERE ID=(SELECT MAX(ID) FROM ProductService);"
        cursor.execute(ID_script)
        records = cursor.fetchone()
        ID = records[0]
        print(ID)
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),chrome_options=options)
        cacheclear(driver)
        for url,c_id in zip(urls,client_id):
            driver.get(url)
            sleep(2)
            S = lambda X:driver.execute_script('return document.body.parentNode.scroll'+X)
            driver.set_window_size(S('Width'),S('Height'))
            sel = Selector(text=driver.page_source)
            rank_list = []
            if sel.xpath('//ul[@class="a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list"]/li/span/span[contains(text(),"Rank")]'):
                Rank1 = sel.xpath('((//ul[@class="a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list"])[2]/li/span/text())[2]').extract_first()
                Rank1 = Rank1.split('(')[0]
                rank_list.append(Rank1)
                if sel.xpath('(//ul[@class="a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list"])[2]/li/span/ul/li') is None:
                    rank_list = rank_list
                else:
                    for j in range(int(float(sel.xpath('count((//ul[@class="a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list"])[2]/li/span/ul/li)').extract_first()))):
                            rank_list.append((driver.find_element(By.XPATH,'(//ul[@class="a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list"])[2]/li/span/ul/li[{a}+1]/span'.format(a=j)).text))

            elif sel.xpath('//tr/th[contains(text()," Sellers Rank")]'):
                if int(float(sel.xpath('count(//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text()," Best Sellers Rank ")]/../td/span/span)').extract_first())) > 1:
                    Rank1 = sel.xpath('(//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text()," Best Sellers Rank ")]/../td/span/span/text())[1]').extract_first()
                    Rank1 = Rank1.split('(')[0]
                    rank_list.append(Rank1)
                    Rank2 = driver.find_element(By.XPATH,'(//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text()," Best Sellers Rank ")]/../td/span/span)[2]').text
                    rank_list.append(Rank2)

                elif int(float(sel.xpath('count(//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text()," Best Sellers Rank ")]/../td/span/span)').extract_first())) > 1:
                    Rank1 = sel.xpath('(//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text()," Best Sellers Rank ")]/../td/span/span/text())[1]').extract_first()
                    Rank1 = Rank1.split('(')[0]
                    rank_list.append(Rank1)
                    for i in range(1, int(float(sel.xpath('count(//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text()," Best Sellers Rank ")]/../td/span/span)').extract_first())) - 1):
                        rank_list.append((driver.find_element(By.XPATH,'//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text()," Best Sellers Rank ")]/../td/span/span[{a}+1]'.format(a=i)).text))

                else:
                    Rank1 = sel.xpath('(//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text()," Best Sellers Rank ")]/../td/span/span/text())[1]').extract_first()
                    Rank1 = Rank1.split('(')[0]
                    rank_list.append(Rank1)
            elif sel.xpath('//th[contains(text(),"Best Sellers")]'):
                if int(float(sel.xpath('count(//th[contains(text(),"Best Sellers")]/../td/span/span)').extract_first()))> 1:
                    print('till 1')
                    Rank1 = sel.xpath('(//th[contains(text(),"Best Sellers")]/../td/span/span/text())[1]').extract_first()
                    Rank1 = Rank1.split('(')[0]
                    rank_list.append(Rank1)
                    for i in range(1,int(float(sel.xpath('count(//th[contains(text(),"Best Sellers")]/../td/span/span)').extract_first()))):

                        rank_list.append(driver.find_element(By.XPATH,'(//th[contains(text(),"Best Sellers")]/../td/span/span/a)[{a}+1]'.format(a=i)).get_attribute('innerHTML'))
                        # rank_list.append(sel.xpath('//th[contains(text(),"Best Sellers")]/../td/span/span)[{a}+1]/text())'.format(a=i)).extract_first())
                        # rank_list.append(Rank1)
                else:
                    Rank1 = sel.xpath('(//th[contains(text(),"Best Sellers")]/../td/span/span/text())[1]').extract_first()
                    Rank1 = Rank1.split('(')[0]
                    rank_list.append(Rank1)
            else:
                Rank1 = 'NA'
                rank_list.append(Rank1)

            # ********* Rating and other details **********************8
            for it in range(len(rank_list)):
                print(rank_list[it])
                if rank_list[it] == 'NA':
                    category_based_rank = 'Not available'
                    category = 'Not Available'
                else:
                    category_based_rank = (rank_list[it]).split(' in ')[0]
                    category = (rank_list[it]).split(' in ')[1]
                print   (rank_list)
                print(category_based_rank)
                print(category)
                total_rating = sel.xpath('//span[@id="acrCustomerReviewText"]/text()').extract_first()
                product_title = sel.xpath('//span[@id="productTitle"]/text()').extract_first()
                if sel.xpath(
                        '//table[@id="productDetails_techSpec_section_1"]/tbody/tr/th[contains(text()," Item model number ")]'):
                    modelNumber = sel.xpath(
                        '//table[@id="productDetails_techSpec_section_1"]/tbody/tr/th[contains(text()," Item model number ")]/../td/text()').extract_first()
                    modelNumber = modelNumber.translate({ord(c): None for c in string.whitespace})
                elif sel.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"Item model")]'):
                    modelNumber = sel.xpath(
                        '//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"Item model")]/../span[2]/text()').extract_first()
                elif sel.xpath('//span[contains(text(),"Item part")]'):
                    modelNumber = sel.xpath('//span[contains(text(),"Item part")]/../span[2]/text()').extract_first()
                else:
                    modelNumber = 'NA'
                if sel.xpath(
                        '//div[@id="productOverview_feature_div"]/div/table/tbody/tr/td/span[contains(text(),"Brand")]/../../td[2]/span/text()'):
                    brand_name = sel.xpath(
                        '//div[@id="productOverview_feature_div"]/div/table/tbody/tr/td/span[contains(text(),"Brand")]/../../td[2]/span/text()').extract_first()
                elif sel.xpath(
                        '//div[@class="a-section a-spacing-small a-spacing-top-small"]/table/tbody/tr/td/span[contains(text(),"Brand")]/../../td[2]/span/text()'):
                    brand_name = sel.xpath(
                        '//div[@class="a-section a-spacing-small a-spacing-top-small"]/table/tbody/tr/td/span[contains(text(),"Brand")]/../../td[2]/span/text()').extract_first()
                else:
                    brand_name = ''
                if sel.xpath('//i[@data-hook="average-star-rating"]/span/text()'):
                    average_rating = (sel.xpath('//i[@data-hook="average-star-rating"]/span/text()').extract_first())
                    average_rating = average_rating.split('o')[0]
                else:
                    average_rating = 'NA'
                if sel.xpath('//th[contains(text(),"ASIN")]'):
                    ASIN = sel.xpath('//th[contains(text(),"ASIN")]/../td/text()').extract_first()
                elif sel.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"ASIN")]'):
                    ASIN = sel.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"ASIN")]/following-sibling::span/text()').extract_first()
                else:
                    ASIN = 'NA'
                main_image_link = sel.xpath('//div[@id="imgTagWrapperId"]/img/@src').extract_first()
                if sel.xpath('//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text(),"Date")]/../td/text()'):
                    first_listed_on = sel.xpath('//table[@id="productDetails_detailBullets_sections1"]/tbody/tr/th[contains(text(),"Date")]/../td/text()').extract_first()
                elif sel.xpath('//span[contains(text(),"Date First")]'):
                    first_listed_on = sel.xpath('//span[contains(text(),"Date First")]/../span[2]/text()').extract_first()
                else:
                    first_listed_on = "NA"
                sub_title_text = sel.xpath('//div[@id="bylineInfo_feature_div"]/div/a/text()').extract_first()
                if sel.xpath('//div[@id="bylineInfo_feature_div"]/div/a/@href'):
                    brand_store_link = 'https://amazon.in' + sel.xpath('//div[@id="bylineInfo_feature_div"]/div/a/@href').extract_first()
                else:
                    brand_store_link = 'NA'

                # *********** Images and Videos *************

                number_of_images = int(float(sel.xpath('count(//li[@class="a-spacing-small item imageThumbnail a-declarative"])').extract_first()))
                if sel.xpath('(//div[@id="deliveryBlockMessage"]/div/div/a/text())[1]'):

                    if sel.xpath('//span[@id="videoCount"]/text()'):
                        number_of_videos = sel.xpath('//span[@id="videoCount"]/text()').extract_first()
                        if number_of_videos == "VIDEO":
                            number_of_videos = '1 video'
                    else:
                        number_of_videos = 0
                else:
                    number_of_videos = 0

                ## variation mapping, aplus and ASIN

                if sel.xpath('//div[@id="twisterContainer"]'):
                    has_variation_mapping = True
                else:
                    has_variation_mapping = False
                if sel.xpath('//div[@id="aplus"]'):
                    has_APlus = True
                else:
                    has_APlus = False
                feature_bullet_count = sel.xpath(
                    'count(//ul[@class="a-unordered-list a-vertical a-spacing-mini"]/li)').extract_first()
                spec_list = sel.xpath('//table[@class="a-normal a-spacing-micro"]/tbody/tr')
                a = ''
                for i in spec_list:
                    spe1 = i.xpath('.//td[1]/span/text()').get()
                    spe2 = i.xpath('.//td[2]/span/text()').get()
                    spe3 = spe1 + ':' + spe2
                    a = a + spe3 + '. '
                specifications = a
                b = ''
                abt = sel.xpath('//ul[@class="a-unordered-list a-vertical a-spacing-mini"]/li')
                for j in abt:
                    tx = j.xpath('.//span/text()').get()
                    tx.strip()
                    b = b + tx + '. '
                abt_this_item = b
                # ************ Price details *********************************
                if sel.xpath('(//span[@class="a-price a-text-price a-size-medium apexPriceToPay"]/span/text())[1]'):
                    sale_price = sel.xpath('(//span[@class="a-price a-text-price a-size-medium apexPriceToPay"]/span/text())[1]').extract_first()
                    Sp = sale_price.replace('\u20B9', '')
                elif sel.xpath('(//span[@class="a-price aok-align-center reinventPricePriceToPayPadding priceToPay"]/span/text())[1]'):
                    sale_price = sel.xpath('(//span[@class="a-price aok-align-center reinventPricePriceToPayPadding priceToPay"]/span/text())[1]').extract_first()
                    Sp = sale_price.replace('\u20B9', '')
                elif sel.xpath('//span[@class="a-price aok-align-center"]/span/text()'):
                    sale_price = sel.xpath('//span[@class="a-price aok-align-center"]/span/text()').extract_first()
                    Sp = sale_price.replace('\u20B9', '')

                else:
                    Sp = 'NA'
                if sel.xpath('(//span[@class="a-price a-text-price"]/span[@class="a-offscreen"]/../../../span[contains(text(),"M.R.P.")]/span/span/text())[1]'):
                    Mrp = sel.xpath('(//span[@class="a-price a-text-price"]/span[@class="a-offscreen"]/../../../span[contains(text(),"M.R.P.")]/span/span/text())[1]').extract_first()
                    mrp = Mrp.replace('\u20B9', '')
                elif sel.xpath('(//span[@class="a-price a-text-price a-size-base"]/span/text())[1]'):
                    Mrp = sel.xpath('(//span[@class="a-price a-text-price a-size-base"]/span/text())[1]').extract_first()
                    mrp = Mrp.replace('\u20B9', '')
                elif sel.xpath('//span[@class="a-price aok-align-center"]/span/text()'):
                    Mrp = sel.xpath('//span[@class="a-price aok-align-center"]/span/text()').extract_first()
                    mrp = Mrp.replace('\u20B9', '')
                else:
                    mrp = "NA"
                if sel.xpath('(//span[@class="a-price a-text-price a-size-base"]/span)[3]/text()'):
                    disc = sel.xpath('(//span[@class="a-price a-text-price a-size-base"]/span)[3]/text()').extract_first()
                    disc = disc.replace('\u20B9', '')
                else:
                    disc = 'NA'
                if sel.xpath('//span[@class="a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage"]/text()'):
                    discount_percentage = sel.xpath(
                        '//span[@class="a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage"]/text()').extract_first()
                    discount_percentage = discount_percentage.replace('-', '')
                elif sel.xpath('//span[@class="a-color-price"]/text()[2]'):
                    discount_percentage = sel.xpath('//span[@class="a-color-price"]/text()[2]').extract_first()
                else:
                    discount_percentage = 'NA'
                ## ***** weight and product dimensions ****
                if sel.xpath('//table[@class="a-keyvalue prodDetTable"]/tbody/tr/th[contains(text(),"Item Weight")]'):
                    item_weight = sel.xpath(
                        '//table[@class="a-keyvalue prodDetTable"]/tbody/tr/th[contains(text(),"Item Weight")]/../td/text()').extract_first()
                    item_weight = item_weight.translate({ord(c): None for c in string.whitespace})
                elif sel.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"Weight")]'):
                    item_weight = sel.xpath(
                        '//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"Weight")]/../span[2]//text()').extract_first()
                    item_weight = item_weight.translate({ord(c): None for c in string.whitespace})
                else:
                    item_weight = 'NA'
                if sel.xpath('(//table[@class="a-keyvalue prodDetTable"]/tbody/tr/th[contains(text(),"Dimensions")])[1]'):
                    dm = sel.xpath(
                        '(//table[@class="a-keyvalue prodDetTable"]/tbody/tr/th[contains(text(),"Dimensions")])[1]/../td/text()').extract_first()
                    dimensions = dm.split(';')[0]
                elif sel.xpath(
                        '(//div[@id="detailBulletsWrapper_feature_div"]/div/ul/li/span/span[contains(text(),"Dimensions")])[1]/../span[2]/text()'):
                    dm = sel.xpath(
                        '(//div[@id="detailBulletsWrapper_feature_div"]/div/ul/li/span/span[contains(text(),"Dimensions")])[1]/../span[2]/text()').extract_first()
                    dimensions = dm.split(';')[0]
                else:
                    dimensions = 'NA'

                # **** Availablity and delivery *********
                if sel.xpath(
                        '//div[@class="a-section a-spacing-none a-padding-none"]/div[@id="availabilityInsideBuyBox_feature_div"]'):
                    availability = sel.xpath(
                        '//div[@class="a-section a-spacing-none a-padding-none"]/div[@id="availabilityInsideBuyBox_feature_div"]/div/div/span/text()').extract_first()
                elif sel.xpath('(//div[@id="buybox"]/div/div/form/div/div/div/span/text())[1]'):
                    availability = sel.xpath('(//div[@id="buybox"]/div/div/form/div/div/div/span/text())[1]').extract_first()
                else:
                    availability = "NA"

                if sel.xpath('//div[@id="deliveryBlockMessage"]/div/div/b/text()'):
                    standard_delivery_date = sel.xpath('//div[@id="deliveryBlockMessage"]/div/div/b/text()').extract_first()
                    standard_delivery_date = standard_delivery_date.translate({ord(c): None for c in string.whitespace})
                else:
                    standard_delivery_date = "NA"
                if sel.xpath('(//div[@id="deliveryBlockMessage"]/div/div/a)[1]/text()'):
                    standard_delivery_type = sel.xpath(
                        '(//div[@id="deliveryBlockMessage"]/div/div/a)[1]/text()').extract_first()
                    standard_delivery_date = standard_delivery_date.translate(
                        {ord(c): None for c in string.whitespace})
                else:
                    standard_delivery_type = 'NA'

                ## fastest delivery
                if sel.xpath('//div[@id="deliveryBlockContainer"]/div/div/div/div/span[contains(text(),"Fastest")]/./b/text()'):
                    fastest_delivery_date = sel.xpath(
                        '//div[@id="deliveryBlockContainer"]/div/div/div/div/span[contains(text(),"Fastest")]/./b/text()').extract_first()
                    fastest_delivery_date = fastest_delivery_date.translate({ord(c): None for c in string.whitespace})
                else:
                    fastest_delivery_date = 'NA'

                # ********* sellers information ********
                if sel.xpath('(//div[@class="a-section olp-link-widget"]/span/a/div/div/span/text())[1]'):
                    no_of_sellers = sel.xpath(
                        '(//div[@class="a-section olp-link-widget"]/span/a/div/div/span/text())[1]').extract_first()
                    no_of_sellers = no_of_sellers[5:-6]
                    # no_of_sellers = ns.split(')')[0]
                elif sel.xpath('//div[@class="a-section a-spacing-mini"]/div/span[contains(text(),"Sold")]'):
                    no_of_sellers = 1
                elif sel.xpath('//div[@id="merchant-info"][contains(text(),"Sold")]'):
                    no_of_sellers = 1

                elif sel.xpath('//span/a[contains(text(),"See All Buying")]'):
                    WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH,'//div[@class="a-button-stack"]/span/span/span/a[contains(text(),"See All")]'))).click()
                    # driver.find_element(By.XPATH,
                    #                     '//div[@class="a-button-stack"]/span/span/span/a[contains(text(),"See All")]').click()
                    sleep(2)
                    wait = WebDriverWait(driver, 20)
                    wait.until(EC.presence_of_element_located((By.XPATH, '(//div[@id="aod-message-component"]/span)[contains(text(),"option")]')))
                    text_part = driver.find_element(By.XPATH, '(//div[@id="aod-message-component"]/span)[contains(text(),"option")]').text
                    sleep(2)
                    no_of_sellers = text_part.split('o')[0]
                    driver.refresh()
                else:
                    no_of_sellers = "NA"
                if sel.xpath('(//div[@id="merchant-info"]/a/span)[1]/text()'):
                    seller_name = sel.xpath('(//div[@id="merchant-info"]/a/span)[1]/text()').extract_first()
                elif sel.xpath('//div[contains(text(),"Sold")]/a/text()'):
                    seller_name = sel.xpath('//div[contains(text(),"Sold")]/a/text()').extract_first()
                else:
                    seller_name = 'NA'
                Client_ID = c_id
                print(ASIN)
                print(seller_name)
                record = (ID,category_based_rank,category, product_title, brand_name, c_id,modelNumber, total_rating, average_rating, ASIN, main_image_link, first_listed_on,sub_title_text, brand_store_link, number_of_images,number_of_videos, standard_delivery_type, has_variation_mapping, has_APlus, feature_bullet_count,specifications, abt_this_item, Sp, mrp, disc, discount_percentage, availability, item_weight, dimensions,standard_delivery_date,seller_name, no_of_sellers, fastest_delivery_date)
                insert2db(record)
        driver.close()

def asin_var(urls):
        # s = Service(ChromeDriverManager().install())
        # options = webdriver.ChromeOptions()
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        options.add_argument("--no-sandbox")
        options.add_argument("--diable-dev-shm-usage")
        # options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/68.0.3440.84 Safari/537.36')

        # options.add_experimental_option("excludeSwitches", ['enable-automation']);

        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),chrome_options=options)
        cacheclear(driver)

        for url in urls:

            driver.get(url)


            S = lambda X:driver.execute_script('return document.body.parentNode.scroll'+X)
            driver.set_window_size(S('Width'),S('Height'))
            # driver.find_element_by_tag_name('body').screenshot(url+'.png')

            sel3 = Selector(text=driver.page_source)
            asin_list1 = ''
            if sel3.xpath('//th[contains(text(),"ASIN")]'):
                ASIN = sel3.xpath('//th[contains(text(),"ASIN")]/../td/text()').extract_first()
            elif sel3.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"ASIN")]'):
                ASIN = sel3.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"ASIN")]/following-sibling::span/text()').extract_first()
            else:
                ASIN = 'NA'
            if sel3.xpath('//div[contains(@id,"variation")]/ul'):
                try:

                    a = 'first one'
                    print('first one')
                    # sleep(1200)

                    for i in range(int(float(sel3.xpath('count(//div[@id="twisterContainer"]//ul/li)').extract_first()))):
                        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'(//div[contains(@id,"variation")]/ul/li//span[@class="a-button-inner"])[{i}+1]'.format(i=i))))
                        element = driver.find_element(By.XPATH,'(//div[contains(@id,"variation")]/ul/li//span[@class="a-button-inner"])[{i}+1]'.format(i=i))
                        # element.click()
                        driver.execute_script("arguments[0].click();",element)
                        sleep(2)
                        sel1 = Selector(text=driver.page_source)
                        # if sel1.xpath('//table[@id="productDetails_detailBullets_sections1"]/tbody/tr[1]/td/text()'):
                        if sel1.xpath('//th[contains(text()," ASIN")]'):
                            WebDriverWait(driver,20).until(EC.presence_of_element_located((By.XPATH,'//th[contains(text(),"ASIN")]')))
                            ASIN1 = sel1.xpath('//th[contains(text()," ASIN")]/../td/text()').extract_first()
                            asin_list1 += ASIN1 + ','
                            driver.get(url)
                        elif sel1.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"ASIN")]'):
                            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH,'//span[contains(text(),"ASIN")]/following-sibling::span')))
                            ASIN1 = sel1.xpath('//span[contains(text(),"ASIN")]/following-sibling::span/text()').extract_first()
                            asin_list1 += ASIN1 + ','
                            driver.get(url)

                        else:
                            print('NO asin found')
                        sleep(1)
                except Exception as e:
                    print(e+ASIN)
                    continue
            elif sel3.xpath('//span[contains(@class,"a-button a-button-toggle text-swatch-button-with-slots-selector text-swatch-button-with-slots")]'):
                try:
                    a = 'second one'
                    print('second one')
                    # sleep(1200)
                    for row in range(0,int(float(sel3.xpath('count((//span[@class="a-button a-button-toggle text-swatch-button"] |  //span[@class="a-button a-button-toggle a-button-unavailable text-swatch-button"] | //span[@class="a-button a-button-selected a-button-toggle text-swatch-button"]))').extract_first()))):
                        # element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'(//span[@class="a-button a-button-toggle text-swatch-button"] |  //span[@class="a-button a-button-toggle a-button-unavailable text-swatch-button"] | //span[@class="a-button a-button-selected a-button-toggle text-swatch-button"])[{i}+1]'.format(i=row))))
                        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,'(//span[@class="a-button a-button-toggle text-swatch-button"] |  //span[@class="a-button a-button-toggle a-button-unavailable text-swatch-button"] | //span[@class="a-button a-button-selected a-button-toggle text-swatch-button"] | //span[@class="a-button a-button-selected a-button-toggle text-swatch-button-with-slots-selector text-swatch-button-with-slots"] | //span[@class="a-button a-button-toggle text-swatch-button-with-slots-selector text-swatch-button-with-slots"])[{i}+1]'.format(i=row))))
                        # element = driver.find_element(By.XPATH,'(//span[@class="a-button a-button-toggle text-swatch-button"] |  //span[@class="a-button a-button-toggle a-button-unavailable text-swatch-button"] | //span[@class="a-button a-button-selected a-button-toggle text-swatch-button"])[{i}+1]'.format(i=row))
                        # element.click()
                        driver.execute_script("arguments[0].click();",element)
                        sleep(5)
                        sel1 = Selector(text=driver.page_source)
                        if sel1.xpath('//th[contains(text()," ASIN")]'):
                            WebDriverWait(driver, 20).until(
                                EC.presence_of_element_located((By.XPATH, '//th[contains(text(),"ASIN")]')))
                            ASIN1 = sel1.xpath('//th[contains(text()," ASIN")]/../td/text()').extract_first()
                            asin_list1 += ASIN1 + ','
                            driver.get(url)
                        elif sel1.xpath(
                                '//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"ASIN")]'):
                            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                                (By.XPATH, '//span[contains(text(),"ASIN")]/following-sibling::span')))
                            ASIN1 = sel1.xpath(
                                '//span[contains(text(),"ASIN")]/following-sibling::span/text()').extract_first()
                            asin_list1 += ASIN1 + ','
                            driver.get(url)

                        else:
                            print('no asin found')
                    # asin_list1 = ''
                except Exception as e:
                    print(e+ ASIN)
                    continue
            elif sel3.xpath('//li[@data-asin]'):
                try:
                    a = 'third one'
                    print('third one')
                    # sleep(1200)
                    for row in range(0,int(float(sel3.xpath('count(//li[@data-asin]/span/span/span)').extract_first()))):
                        element = driver.find_element(By.XPATH,'(//li[@data-asin]/span/span/span)[{i}+1]'.format(i=int(row)))
                        driver.execute_script("arguments[0].click();",element)
                        sleep(3)
                        sel1 = Selector(text=driver.page_source)
                        if sel1.xpath('//th[contains(text()," ASIN")]'):
                            WebDriverWait(driver, 20).until(
                                EC.presence_of_element_located((By.XPATH, '//th[contains(text(),"ASIN")]')))
                            ASIN1 = sel1.xpath('//th[contains(text()," ASIN")]/../td/text()').extract_first()
                            asin_list1 += ASIN1 + ','
                            driver.get(url)
                        elif sel1.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(),"ASIN")]'):
                            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                                (By.XPATH, '//span[contains(text(),"ASIN")]/following-sibling::span')))
                            ASIN1 = sel1.xpath(
                                '//span[contains(text(),"ASIN")]/following-sibling::span/text()').extract_first()
                            asin_list1 += ASIN1 + ','
                            driver.get(url)

                        else:
                            print('NO asin found')
                        sleep(1)
                except Exception as e:
                    print(e+ASIN)
                    continue

            else:
                print('NO VARIATION')
                # a =='no entry for this one'
            # if a == 'second one':
            #     sleep(2000)
            # else:
            #     pass
            print(asin_list1)
            print(ASIN)
            asin_list1 = asin_list1[:-1]
            record = (ASIN,asin_list1)
            insertAsin2db(record)

def complete_data():
    cursor.execute('select * from mydatabase.combined_table')
    data = cursor.fetchall()
    print(data)
    return data



def func():
    start = time.time()

    with open('input.csv',newline='') as f:
        ereader = csv.DictReader(f)
        urls = []
        client_id = []
        for row in ereader:
            urls.append(row['Product Links'])
            client_id.append(row['C_ID'])
    createservicedb(mydb)
    main_func(urls,client_id)
    asin_var(urls)
    merging_table()
    removeRedundantTables(mydb)
    return 'Done'

@my_app.route('/',methods=["POST","GET"])

def flask_start():
    if request.method == 'POST':
        u_name = request.form['login']
        p_wrd = request.form['password']
        if u_name == user_name and p_wrd == password:
            # start = time.time()
            func()
            # mydb.close()
            end = time.time()
            return render_template('index.html',headers = data_points,li_data = complete_data(),enumerate=enumerate)
        else:
            return 'check credentials'

        print(end-start)
    else:
        return render_template('login.html' )


my_app.run(debug=True)

