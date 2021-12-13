""" Web scraper for target.com website. Written by IvanowDenis """

import json
from urllib.parse import urlencode
import logging

import scrapy

from target_com.items import TargetComItem


class TargetSpider(scrapy.Spider):
    name = 'target'
    allowed_domains = ['target.com']
    start_urls = ['https://www.target.com/p/consumer-cellular-apple-iphone-xr-64gb-black/-/A-81406260']

    def parse(self, response):
        """ Parse html page. Extracting data for urls with json data """
        # Extract json data:
        data = response.xpath('//script[contains(., "__TGT_DATA__")]').re("\{.+\}")
        if data:
            data = data[0].replace("undefined", "null")
            data = json.loads(data)
        else:
            logging.critical(f"Json data wasn't extracted from the webpage {response.url}")
            return None

        # Extract data for first url with a product data:
        redsky_aggregations_pdp = data['__PRELOADED_QUERIES__']["queries"][0][0][1]

        url_query_parameters = {}
        url_query_parameters["has_financing_options"] = redsky_aggregations_pdp['has_financing_options']
        url_query_parameters["has_size_context"] = redsky_aggregations_pdp['has_size_context']
        url_query_parameters["key"] = redsky_aggregations_pdp['apiKey']
        url_query_parameters["latitude"] = redsky_aggregations_pdp['latitude']
        url_query_parameters["longitude"] = redsky_aggregations_pdp['longitude']
        url_query_parameters["pricing_store_id"] = redsky_aggregations_pdp['pricing_store_id']
        url_query_parameters["state"] = redsky_aggregations_pdp['state']
        url_query_parameters["tcin"] = redsky_aggregations_pdp['tcin']
        url_query_parameters["zip"] = redsky_aggregations_pdp['zip']
        url_query_parameters["visitor_id"] = redsky_aggregations_pdp['visitor_id']
        redsky_url = f"https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?{urlencode(url_query_parameters)}"

        # Extract data for second url with a questions/answers data:
        url_qa_parameters = {}
        url_qa_parameters["type"] = "product"
        url_qa_parameters["questionedId"] = redsky_aggregations_pdp["tcin"]
        url_qa_parameters["page"] = 0
        url_qa_parameters["size"] = 10
        url_qa_parameters["sortBy"] = "MOST_ANSWERS"
        url_qa_parameters["key"] = redsky_aggregations_pdp['apiKey']
        url_qa_parameters["errorTag"] = "drax_domain_questions_api_error"
        qa_url = f"https://r2d2.target.com/ggc/Q&A/v1/question-answer?{urlencode(url_qa_parameters)}"

        yield scrapy.Request(redsky_url, callback=self.get_data, cb_kwargs={"qa_url": qa_url})

    def get_data(self, response, qa_url):
        """ Extract product data """
        item = TargetComItem()
        data = response.json()['data']['product']

        item["title"] = data['item']["product_description"]["title"]
        item["price"] = data['price']["current_retail"]
        # For bigger images add to urls parameters: ?fmt=webp&wid=1400&qlt=80
        images = data['item']['enrichment']["images"]["content_labels"]
        item["images"] = [image.get("image_url") for image in images]
        item["description"] = data['item']["product_description"]["downstream_description"]
        item["highlights"] = data['item']["product_description"]["soft_bullets"]["bullets"]
        yield scrapy.Request(qa_url, callback=self.get_answers_questions, cb_kwargs={"item": item})

    def get_answers_questions(self, response, item):
        ''' Extract last answer and last question: '''
        data = response.json()['results'][0]

        item["last_question"] = data["text"]
        item["last_answer"] = data["answers"][0]["text"]
        yield item
