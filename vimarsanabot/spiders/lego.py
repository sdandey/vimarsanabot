# -*- coding: utf-8 -*-
import scrapy


class LegoSpider(scrapy.Spider):
    name = 'lego'
    allowed_domains = ['http://brickset.com/sets/year-2016',
                       'brickset.com']
    start_urls = ['http://brickset.com/sets/year-2016']

    def parse(self, response):
        print(response.url)
        SET_SELECTOR = '.set'
        for brickset in response.css(SET_SELECTOR):
            NAME_SELECTOR = 'h1 a ::text'
            name = brickset.css('h1 a ::text').extract()[1]
            # rating = brickset.css('.rating').xpath('@title').extract_first()
            rating = brickset.css('.rating::attr(title)').extract_first()
            reviews = brickset.css('.rating a ::text').extract_first()
            pieces = brickset.xpath('.//dl[dt/text() = "Pieces"]/dd/a/text()').extract_first()
            miniflags = brickset.xpath('.//dl[dt/text() = "Minifigs"]/dd[2]/a/text()').extract_first()
            image = brickset.css('img ::attr(src)').extract_first()

            # print(name + ',' + LegoSpider.check_none(self,rating) + ',' +
            #       LegoSpider.check_none(self,reviews))
            # print(rating)

            # print(name + ' ' + rating + ' ' + reviews )

            yield {
                'name': name,
                'rating': LegoSpider.check_none(self, rating),
                'reviews': LegoSpider.check_none(self, reviews),
                'pieces': pieces,
                'image': image,
                'miniflags': miniflags
            }

        next_page = response.css('.next a ::attr(href)').extract_first()
        if next_page is not None:
            yield response.follow(
                next_page,
                callback=self.parse
            )

    def check_none(self, var):
        if var is None:
            return ''
        return str(var)
