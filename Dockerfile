FROM python:3.7-alpine as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev alpine-sdk

RUN pip3 install --install-option="--prefix=/install" -r /requirements.txt

# Can clean up a lot of space by deleting rogue .c files etc:
RUN find /install/lib/python3.7 -name '*.c' -delete
RUN find /install/lib/python3.7 -name '*.pxd' -delete
RUN find /install/lib/python3.7 -name '*.pyd' -delete
# Cleaning up __pycache__ gains more space
RUN find /install/lib/python3.7 -name '__pycache__' | xargs rm -r

FROM python:3.7-alpine

COPY --from=builder /install /usr/local
COPY memer/ /memer

CMD ["python3", "/memer/main.py"]
