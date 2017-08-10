# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Request


class CricinfoSpider(scrapy.Spider):
    name = 'cricinfo'
    allowed_domains = ['espncricinfo','www.espncricinfo.com']
    start_urls = ['http://www.espncricinfo.com/ci/content/player/index.html']
    country_url = 'http://www.espncricinfo.com/ci/content/player/caps.html?'
    domain_url = 'http://www.espncricinfo.com'

    def parse(self, response):
        countries = {}

        tab_href = response.xpath('//li[@class="ctrytab"]/a/@href').extract()
        tab_country = response.xpath('//li[@class="ctrytab"]/a/text()').extract()
        for idx,value in enumerate(tab_href):
            countries[value.split('=')[1]] = tab_country[idx]

        print(countries)
        country_selector = response.css('option')
        for item in country_selector:
            id = item.xpath('@value').extract_first()
            value = item.css('::text').extract_first()
            if id:
                countries[id] = value

        for id in countries.keys():
            test_url = self.country_url + 'country=' + id + ';class=2'
            #print('get data for ' + countries[id])
            yield scrapy.Request(test_url, callback=self.parse_country_page)

    def parse_country_page(self, response):
        print(response.url)
        players_selector = response.css('.ciPlayername')
        players = {}
        for item in players_selector:
            url = self.domain_url + item.css('a::attr(href)').extract_first()
            players[item.css('::text').extract_first()] = item.css('a::attr(href)').extract_first()
        #print('number of players :' + str(len(players)))

        for player in players.keys():
            url = self.domain_url + players[player]
            yield scrapy.Request(url, callback=self.parse_player_page)


    def parse_player_page(self, response):
        personal_selector_header = response.xpath('//p[@class="ciPlayerinformationtxt"]')

        details = {}
        for item in personal_selector_header:
            details[item.xpath('.//b/text()').extract_first()] = item.xpath('.//span/text()').extract()

        return details

