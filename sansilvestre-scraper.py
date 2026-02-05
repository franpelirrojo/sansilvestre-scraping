import scrapy
import re
import sys
import json
from scrapy.crawler import CrawlerProcess
from dataclasses import dataclass

settings_d = {
    "USER_AGENT": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z Safari/537.36",
    "LOG_LEVEL": "INFO",
    "DOWNLOAD_TIMEOUT" : 5,
    "COOKIES_ENABLED" : False,
    'DOWNLOAD_DELAY': 0,
    'CONCURRENT_ITEMS': 25,
    'CONCURRENT_REQUESTS': 12,
    'AUTOTHROTTLE_ENABLED': False
}

class SanSilvestreSp(scrapy.Spider):
    name = "SanSilvestreSp"

    def __init__(self, params, *args, **kwargs):
        super(SanSilvestreSp, self).__init__(*args, **kwargs)
        self.allowed_domains = params.get("allowed_domains")
        self.start_urls = params.get("start_urls")
        self.selectores = params.get("selectores")

    def parse(self, response):
        carreras_url = response.css(self.selectores["carrera_link"]).getall()
        nombre_carrera = response.css(self.selectores["nombre_carrera"]).getall()
        año_carrera = response.css(self.selectores["año_carrera"]).getall()

        for url, nombre, año in zip(carreras_url, nombre_carrera, año_carrera):
            yield response.follow(url,
                                  callback=self.parse_eventos,
                                  cb_kwargs={"edicion":nombre, "año":año})

    def parse_eventos(self, response, **kwargs):
        item = kwargs.copy()
        if "competicion" in (url := response.url):
            yield response.follow(url,
                                  callback=self.parse_resultados,
                                  cb_kwargs=item)
        else:
            categorias_url = response.css(self.selectores["categoria_link"]).getall()
            categorias = response.css(self.selectores['categoria']).getall()
            for url, categoria in zip(categorias_url, categorias):
                item["categoria"] = categoria.strip()
                yield response.follow(url,
                                      callback=self.parse_resultados,
                                      cb_kwargs=item)

    def parse_resultados(self, response, **kwargs): 
        corredor_links = response.css(self.selectores['tupla_link']).getall()
        campos = response.css(self.selectores['tabla_campos']).getall()
        valores = response.css(self.selectores['tabla_valores']).getall()
        pag = response.css(self.selectores['pagination']).get()

        filas = [valores[i : i + len(campos)] for i in range(0, len(valores), len(campos))]
        for i, fila in  enumerate(filas):
            item = kwargs.copy()
            for campo, valor in zip(campos, fila):
                item[campo] = valor

            if corredor_links:
                yield response.follow(corredor_links[i],callback=self.parse_corredor,cb_kwargs=item)
            else:
                yield item

        if pag: yield response.follow(pag,
                                      callback=self.parse_resultados,
                                      cb_kwargs=kwargs.copy())

    def parse_corredor(self, response, **kwargs):
        club = response.xpath(self.selectores['club']).get()
        campos = response.css(self.selectores['tabla_campos']).getall()
        valores = response.css(self.selectores['tabla_valores']).getall()
        campos = [clean for x in campos if (clean := re.sub(r'\s+', '', x))]
        tupla = [clean for x in valores if (clean := re.sub(r'\s+', '', x))]

        item = kwargs.copy()
        if club: item['club'] = club.replace('\n', '')

        controles = []
        if campos:
            tuplas = [valores[i : i + len(campos)] for i in range(0, len(valores), len(campos))]
            for tupla in tuplas:
                control = {}
                for campo, valor in zip(campos, tupla): 
                    control[campo] = valor
                controles.append(control)
            item['controles'] = controles
        else:
            valores = response.css(self.selectores['virtual_valores']).getall()
            if valores: controles.append({valores[i] for i in range(0, 2)})

        yield item


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
