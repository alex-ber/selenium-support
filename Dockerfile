FROM alexberkovich/alpine-anaconda3:0.2.1-slim

COPY requirements.txt etc/requirements.txt
COPY requirements-tests.txt etc/requirements-tests.txt


RUN set -ex && \
    #latest pip,setuptools,wheel
    pip install --upgrade pip==20.3.1 setuptools==51.0.0 wheel==0.36.1 && \
    pip install -r etc/requirements.txt && \
    pip install -r etc/requirements-tests.txt


#CMD ["/bin/sh"]
CMD tail -f /dev/null


#docker rmi -f selenium-support-i
#docker rm -f selenium-support
##docker build --squash . -t selenium-support-i
#docker build . -t selenium-support-i
#docker exec -it $(docker ps -q -n=1) bash
#docker tag utils-i alexberkovich/selenium_support:0.0.1
#docker push alexberkovich/selenium_support:0.0.1
# EOF
