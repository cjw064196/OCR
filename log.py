#coding:utf-8
import logging

logger = logging.getLogger('ocr')
hdlr = logging.FileHandler('log/ocr.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.INFO)
logger.addHandler(ch)
