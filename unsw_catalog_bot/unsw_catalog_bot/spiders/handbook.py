# -*- coding: utf-8 -*-
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import Spider, Request
from unsw_catalog_bot.items import CourseItem 
from urllib import urlencode
from urlparse import urlsplit, urlunsplit
import json
import re

class AwesomeHandbookSpider(CrawlSpider):
    name = 'awesome-handbook'
    allowed_domains = ['unsw.edu.au']

    rules = (
        Rule(
            # every link in the table defined by the xpath
            LinkExtractor(
                allow = 'courses/\d{4}/[A-Z]{4}\d{4}\.html',
                restrict_xpaths = "//div[@class='column content-col']/div[@class='internalContentWrapper']/table[@class='tabluatedInfo']",
            ),
            callback = 'parse_item'
        ),
    )

    def __init__(self, year=None, careers=None, *args, **kwargs):
        super(AwesomeHandbookSpider, self).__init__(*args, **kwargs)
        
        if careers is not None:
            # TODO: Further format checking
            self.careers = json.loads(careers) # careers.split(',')
        else:
            self.careers = 'undergraduate|postgraduate|research'.split('|')
        
        if year is not None:
            # TODO: Further format checking
            self.year = year  
        else:
            # TODO: Set default to current year
            self.year = 'current'

        self.start_urls = ['http://www.handbook.unsw.edu.au/vbook{year}/brCoursesByAtoZ.jsp?StudyLevel={level}&descr={descr}' \
            .format(year=self.year, level=career, descr='All') for career in self.careers]
    
    def parse_item(self, response):
        content = response.xpath("//div[@class='column content-col']/div[@class='internalContentWrapper']")
        summary = content.xpath("div[@class='summary']")
        yield CourseItem(
            code = response.xpath("/html/head/meta[@name='DC.Subject.ProgramCode']/@content").extract()[0],
            name = response.xpath("/html/head/meta[@name='DC.Subject.Description.Short']/@content").extract()[0],
            career = response.xpath("/html/head/meta[@name='DC.Subject.Level']/@content").extract()[0],
            uoc = response.xpath("/html/head/meta[@name='DC.Subject.UOC']/@content").extract()[0],
            gened = response.xpath("/html/head/meta[@name='DC.Subject.GenED']/@content").extract()[0] == 'Y',
            faculty = response.xpath("/html/head/meta[@name='DC.Subject.Faculty']/@content").extract()[0],
            school = summary.xpath("p[strong[text()[contains(.,'School')]]]/a/text()").extract()[0],
            campus = summary.xpath("p[strong[text()[contains(.,'Campus')]]]/text()").re(ur'\xa0([\w\s]+)')[0],
            eftsl = summary.xpath("p[strong[text()[contains(.,'EFTSL')]]]/text()").re(ur'\xa0(\d+\.\d+)\xa0')[0],
            description_markup = content.xpath("h2[text()='Description']/following-sibling::div").extract()[0],
        )
        yield Request(url=summary.xpath(".//a[text()[contains(.,'Timetable')]]/@href")[0].extract())

class NewHandbookSpider(CrawlSpider):
    name = 'new-handbook'
    allowed_domains = ['unsw.edu.au']
    
    def process_javascript_link(value):
        mo = re.search(r"javascript:\s*doBrowse\('(?P<relpath>.*)',\s*'(?P<descr>.*)'\);", value)
        if mo:
            print mo.group('relpath')
            print mo.group('descr')
        return value
    
    rules = (
        Rule(
            LinkExtractor(
                allow = 'javascript',
                restrict_xpaths = "//div[@class='column nav-col']/div[@class='sideNavWrapper']/div[@class='sideNav']/ul",
                process_value = process_javascript_link
            ),
        ),
    )
    
    def __init__(self, year=None, careers=None, *args, **kwargs):
        super(NewHandbookSpider, self).__init__(*args, **kwargs)
        
        if careers is not None:
            # TODO: Further format checking
            self.careers = json.loads(careers) # careers.split(',')
        else:
            self.careers = 'undergraduate|postgraduate|research|nonaward'.split('|')
        
        if year is not None:
            # TODO: Further format checking
            self.year = year  
        else:
            self.year = 'current'
        
        self.start_urls = ['http://www.handbook.unsw.edu.au/{career}/{year}/'.format(career=career, year=self.year) for career in self.careers]


class HandbookSpider(CrawlSpider):
    name = 'handbook'
    allowed_domains = ['unsw.edu.au']
    start_urls = (
        'http://www.handbook.unsw.edu.au',
    )

    def process_value(value):
        print '####### ' + value
        return value

    def process_javascript_link(value):
        print '## Javascript original: {0}'.format(value)
        "javascript: doBrowse('/vbook2013/brProgramsByAtoZ.jsp','A');"
        
        return value

    rules = (
        Rule(
            LinkExtractor(
                # allow = '/(?:undergraduate|postgraduate|research|nonaward)/\d{4}/',
                allow = '/undergraduate/\d{4}/',
                restrict_xpaths = "//div[@class='column two-col']/div[@class='infoBox']/div[@class='infoBoxContent']",
                process_value = process_value
            ),
        ),
        Rule(
            LinkExtractor(
                allow = 'previousEditions\.html',
                restrict_xpaths = "//div[@class='rightButtons']",
                process_value = process_value
            ),
        ),
        Rule(
            LinkExtractor(
                allow = '/\d{4}/',
                restrict_xpaths = "//div[@class='internalContentWrapper']/div[4]/table",
                process_value = process_value
            ),
        ),
        Rule(
            LinkExtractor(
                # allow = '/\d{4}/',
                restrict_xpaths = "//div[@class='column nav-col']/div[@class='sideNavWrapper']/div[@class='sideNav']/ul",
                process_value = process_value
            ),
        ),
    )