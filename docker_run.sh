#!/bin/bash
docker run -d \
	--volume=/home/chenjiwei/Documents/image-ocr/work/OCR2:/home/apps \
    --publish=8001:8000 \
	ocr1.3
