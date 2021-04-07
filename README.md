## selenium-support

TODO:


### Getting Help


### QuickStart
```bash
python3 -m pip install -U selenium-support
```


### Installing from Github

```bash
python3 -m pip install -U https://github.com/alex-ber/selenium-support/archive/master.zip
```
Optionally installing tests requirements.

```bash
python3 -m pip install -U https://github.com/alex-ber/selenium-support/archive/master.zip#egg=alex-ber-utils[tests]
```

Or explicitly:

```bash
wget https://github.com/alex-ber/selenium-support/archive/master.zip -O master.zip; unzip master.zip; rm master.zip
```
And then installing from source (see below).


### Installing from source
```bash
python3 -m pip install -r req.txt # only installs "required" (relaxed)
```
```bash
python3 -m pip install . # only installs "required"
```
```bash
python3 -m pip install .[tests] # installs dependencies for tests
```

#### Alternatively you install install from requirements file:
```bash
python3 -m pip install -r requirements.txt # only installs "required"
```
```bash
python3 -m pip install -r requirements-tests.txt # installs dependencies for tests
```


### Using Docker
`alexberkovich/selenium_support:latest`  contains all `selenium_support` dependencies.
This Dockerfile is very simple, you can take relevant part for you and put them into your Dockerfile.

##
Alternatively, you can use it as base Docker image for your project and add/upgrade 
another dependencies as you need.

For example:

```Dockerfile
FROM alexberkovich/selenium_support:latest

COPY requirements.txt etc/requirements.txt

RUN set -ex && \
    #latest pip,setuptools,wheel
    pip install --upgrade pip setuptools wheel && \
    pip install selenium_support 
    pip install -r etc/requirements.txt 

CMD ["/bin/sh"]
#CMD tail -f /dev/null
```

where `requirements.txt` is requirements for your project.

##

From the directory with setup.py
```bash
python3 setup.py test #run all tests
```

or

```bash

pytest
```

## Installing new version
See https://docs.python.org/3.1/distutils/uploading.html 

## Installing new version to venv

```bash
python38 -m pip uninstall --yes selenium-support
python38 setup.py clean sdist bdist_wheel
python38 -m pip install --find-links=./dist selenium-support==0.1
```


```bash
python3 setup.py sdist upload
```

## Requirements


selenium-support requires the following modules.

* Python 3.8+
* selenium
* browsermob-proxy
* psutil
