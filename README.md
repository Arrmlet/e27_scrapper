# e27 startup information scrapper
#To run the program you need to have installed python 3.5+ and python libraries
#You can install it run the following command

pip install -r requirements.txt
#Also you need to have installed chromium browser
#Now you can start a scrapper
#Go to tutorial folder
cd tutorial/


#To scrape all startups and links to e27 profile you need to run this command:
scrapy crawl urls -o quotes.csv

#!!! NOTE call a csv file quotes, cause this name will using in second part
#In settings.yaml you need to put a email and password for your linkeln profile, In other way, script will'not scrape a employees_range
#To scrape a information about random 250 startups yo need to ran this command
scrapy crawl content -o data_about_startups.csv 
