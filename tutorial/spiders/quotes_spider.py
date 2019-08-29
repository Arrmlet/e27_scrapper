import os
import scrapy
import random
from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import yaml
import pandas as pd
import random
import re
import json
import requests
from bs4 import BeautifulSoup
#Check is email in comment content (using regular experession)
def is_email_phone(text, tp):
    if tp == 'email':
        lst = re.findall('\S+@\S+', text)
    elif tp == 'phone':
        lst = re.findall("\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}",text)
    else:
        lst = re.findall('\d+', text)
    if len(lst) == 0:
        return ''

    lst = ",".join(lst)
    # return of email
    return lst

#Random 250 links from quotes.csv
def get_250():
    url_base = pd.read_csv('quotes.csv')
    urls = url_base.Url.tolist()
    urls = random.choices(urls, k=250)
    return urls

def yaml_loader(filepath):
    with open(filepath, 'r') as file_descriptor:
        data = yaml.load(file_descriptor)
    return data


class UrlApiSpider(scrapy.Spider):
    name = "urls"

    start_urls = [
        'https://e27.co/startups/',
    ]

    def __init__(self):
        opp = Options()
        #opp.add_argument('--blink-settings=imagesEnabled=false')
        opp.add_argument('--headless')
        opp.add_argument('--no-sandbox')
        opp.add_argument('--ignore-certificate-errors')
        opp.add_argument('--window-size=1920,1080')
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['acceptSslCerts'] = True
        capabilities['acceptInsecureCerts'] = True
        self.driver = webdriver.Chrome('./chromedriver', chrome_options=opp, desired_capabilities=capabilities)

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(3)
        num_of_startups =is_email_phone(self.driver.find_element_by_xpath("//p[@class='bold startup_list_count']").text, 'num')
        api_url = 'https://e27.co/api/startups/'


        start, length = 0, 4000
        while (start < int(num_of_startups)):
            PARAMS = {'tab_name':'recentlyupdated','start':start, 'length':length}
            r = requests.get(url = api_url, params = PARAMS)
            data = r.json()
            data = data['data']['list']
            for info in data:
                name = info['name']
                e27url = 'https://e27.co/startups/{}'.format(info['slug'])
                yield {"Startup":name,"Url":e27url}

            start +=length


class ContentSpider(scrapy.Spider):
    name = "content"
    def __init__(self):
        opp = Options()
        #opp.add_argument('--blink-settings=imagesEnabled=false')
        opp.add_argument('--headless')
        opp.add_argument('--no-sandbox')
        opp.add_argument('--ignore-certificate-errors')
        opp.add_argument('--window-size=1920,1080')
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['acceptSslCerts'] = True
        capabilities['acceptInsecureCerts'] = True
        self.driver = webdriver.Chrome('./chromedriver', chrome_options=opp, desired_capabilities=capabilities)

    start_urls = get_250()

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(3)
        name = self.driver.find_element_by_css_selector('.startup_name').text
        profile_url = str(response.url)
        company_website = self.driver.find_element_by_css_selector('.startup_website').get_attribute("href")
        try:
            location = self.driver.find_element_by_css_selector('.startup_location').text
        except:
            location = ''
        tags = self.driver.find_element_by_css_selector('.startup_market').text
        founding_day = 1
        try:
            founding_month = self.driver.find_element_by_css_selector('.startup_found_month').text
            founding_year = self.driver.find_element_by_css_selector('.startup_found_year').text
            datetime_string = "{0} {1}, {2}".format(founding_day, founding_month, founding_year)
            founding_date = datetime.strptime(datetime_string, '%d %B, %Y')
            founding_date = founding_date.strftime('%Y-%m-%d')
        except:
            founding_date = ''

        try:
            social_urls = self.driver.find_element_by_xpath("//div[@class='col-md-5 socials pdt text-right']")
            social_urls = social_urls.find_elements_by_tag_name('a')
            social_urls_list = []

            for social_url in social_urls:
                social_url_href = social_urls_list.append(social_url.get_attribute("href"))

            social_urls_string = ", ".join(social_urls_list)
        except Exception as e:
            print(e)
            social_urls_string = ''
        try:
            main_description = self.driver.find_element_by_css_selector('.profile-desc-text')
            description = main_description.text
            html_description = main_description.get_attribute('innerHTML')
            soup = BeautifulSoup(html_description, 'lxml')
            try:
                p_tag = soup.select('p')
                raw_p_tag = str(p_tag[0]).split('<br/>')[0]
                cleanr = re.compile('<.*?>')
                short_description = re.sub(cleanr, '', raw_p_tag)

            except:
                short_description = ''
        except:
            description, short_description = '', ''

        try:
            #founder_part = self.driver.find_element_by_xpath("//div[@class='row team team-member-parent']")
            team = self.driver.find_elements_by_xpath("//div[@class='desc']")
            founders = []
            for i in range(0,len(team)):
                statement = team[i].find_element_by_xpath("//span[@class='profile-text block role']").text.lower()
                if 'founder' in statement:
                    founder = team[i].find_element_by_xpath("//span[@class='item-label bold member-name']").text
                    founders.append(founder)
            founders = ''.join(founders)
        except Exception as e:
            founders = ''
        emails = is_email_phone(description, 'email')
        phones = is_email_phone(description, 'phone')

        emp_r = ''
        for lin in social_urls_list:
            reg = re.compile('\d+')
            if 'linkedin.com' in lin:
                self.driver.get(lin)
                try:
                    data_for_login = yaml_loader('settings.yaml')
                    log_email = data_for_login['Info']['LinkedIn_email']
                    log_pass = data_for_login['Info']['LinkedIn_password']
                    log =self.driver.find_element_by_link_text('Sign in')
                    log.click()
                    email =self.driver.find_element_by_id('login-email')
                    email.send_keys(log_email)
                    password =self.driver.find_element_by_id('login-password')
                    password.send_keys(log_pass)
                    password.send_keys(Keys.ENTER)
                except Exception as e:
                    print(e)

                try:
                    employee_range = self.driver.find_element_by_css_selector(
                            '.link-without-visited-state.inline-block.ember-view').text
                    emp_r = reg.findall(employee_range)
                    if len(emp_r) > 1:
                        emp_r= str(emp_r[0]) + str(emp_r[1])
                    else:
                        emp_r = emp_r[0]
                except:
                    pass
        yield {"company_name":name,"company_url":profile_url, "company_website_url":company_website,
                "location":location,"tags":tags, "founding_date":founding_date,
                "founders": founders,"employee_range":emp_r, "urls":social_urls_string,"emails":emails,
                "phones":phones,"description_short":short_description,"description":description}
