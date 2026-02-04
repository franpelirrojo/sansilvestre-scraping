import scrapy
import sys
import json
from scrapy.crawler import CrawlerProcess

settings_d = {
    "USER_AGENT": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z Safari/537.36",
    "LOG_LEVEL": "DEBUG",
    "CONCURRENT_REQUESTS" : 200,
    "CONCURRENT_REQUESTS_PER_DOMAIN" : 200,
    "DOWNLOAD_DELAY" : 2,
    "DOWNLOAD_TIMEOUT" : 5,
    "COOKIES_ENABLED" : False
}

class SanSilvestreSp(scrapy.Spider):
    name = "SanSilvestreSp"

    def __init__(self, params, *args, **kwargs):
        super(SanSilvestreSp, self).__init__(*args, **kwargs)
        self.allowed_domains = params.get("allowed_domains")
        self.start_urls = params.get("start_urls")
        self.carrera_link = params.get("carrera_link")
        self.categoria_link = params.get("categoria_link")
        self.fields = params.get("fields")

    def parse(self, response):
        carreras = response.css(self.carrera_link).getall()
        yield from response.follow_all(carreras, callback=self.parse_eventos)

    def parse_eventos(self, response):
        url = response.url

        if url in "competicion":
            yield response.follow(url, callback=self.parse_resultados)
        else:

            categorias_url = response.css(self.categoria_link).getall()
            categorias = response.css(self.fields['categoria']).getall()
            for url, categoria in zip(categorias_url, categorias):
                yield response.follow(url,
                                      callback=self.parse_resultados,
                                      cb_kwargs={"categoria" : categoria})


    def parse_resultados(self, response, categoria): 
        item = {}
        campos = response.css(self.fields['campos']).getall()
        tupla = response.css(self.fields['tupla']).getall()
        pag = response.css(self.fields['pagination']).get()
        print(len(tupla))
        print(len(campos))
        for i in range(0, len(tupla), len(campos)):
            for k, campo in enumerate(campos): 
                item[campo] = tupla[i+k]
        item['categoría'] = categoria.strip()
        yield item

        if pag is not None:
            yield response.follow(pag, callback=self.parse_resultados, cb_kwargs={"categoria" : categoria})
        
        

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs): #TODO:revisar entrada de esto
        spider = super().from_crawler(crawler, *args, **kwargs)
        if "feeds" in kwargs:
            feeds = kwargs['feeds']
            spider.settings.set(
                "FEEDS", {feeds['output_file'] : {'format': feeds['format'], 'overwrite': feeds['overwrite']}}, priority="spider")
        return spider


def main(argv):
    with open(argv[1], 'r') as fd:
        params = json.load(fd)

    process = CrawlerProcess(settings_d)
    process.crawl(SanSilvestreSp, params=params, feeds=params['feeds'])
    process.start()

if __name__ == "__main__": main(sys.argv)
