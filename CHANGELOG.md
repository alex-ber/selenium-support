# Changelog

Useful functions for Selenium umbrella project.

All notable changes to this project will be documented in this file.

\#https://pypi.org/manage/project/selenium-support/releases/

## [Unrelased]


## [0.0.1] - 18/04/2021
### Added
All functions below are listed in `alexber.seleniumsupport` package.  
See https://alex-ber.medium.com/selenium-support-19330843c63a for more details.

* `BMPDaemon` is  context-manager that responsible for starting BMP Daemon. In the exit from the code block 
inside context-manager, BMP Daemon will be stopped, see `closeBmpDaemon()`.

See https://github.com/AutomatedTester/browsermob-proxy-py/blob/master/browsermobproxy/server.py#L59 
for undocumented values.

If you have multiple application that uses BMP Daemon, you have 2 basic choices:

*  Start BMP Daemon outside of scope of these application (maybe as 3 application or as OS Daemon or just manually) 
in some predefined port (the default is 8080) and write your application code that assumes that BMP Daemon is up 
and running.

* Each application will start BMP Daemon on different port.

I want to *emphasize*, technically it is sufficient to have only 1 running BMP Daemon for all application 
(You will create BMP Proxy per application).

Personally, I’ve found the second option easier to manage — namely to have multiple BMP Daemons, one per application. 

This is indeed waste of resources, but the application lifecycle is much easier to manage and you don’t 
have some external dependencies. Note, however, that in such case you should, at least in one application, 
explicitly provide the port number. It is better that they will far away one from another, because BMP Proxy is 
created as next port number.

This context-manager also worries to close BMP Daemon. See `closeBmpDaemon()` below. 

If you use it as regular function, this will not happen. 

* `closeBmpDaemon` If you’re using BMPDaemon as context-manager, it will worry to close the BMP Daemon. 
If you want to do it yourself, you can call `closeBmpDaemon()` function.
See https://github.com/AutomatedTester/browsermob-proxy-py/issues/8#issuecomment-679150656

* `BrowserDataDir` -  this context manager can be used for reuse of user data dir. It unzips file template 
(*path/to/chrome_data_dir.zip* in our case) to work_dir (*logs* in our case).
It returns directory  with extracted content from template.

If you want your browser to work with some predefined user data dir ("profile" in Mozilla Firefox).

For more on Google Chrome see https://stackoverflow.com/a/55636113/1137529, for 
Mozilla Firefox see https://firefox-source-docs.mozilla.org/testing/geckodriver/CrashReports.html.

For example, on Windows you can create shortcut: 
`"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --user-data-dir=C:\tmp\chrome_profile`. 

Click on it to create all internal folders and than pass `C:\tmp\chrome_profile` as `--user-data-dir` to 
Google Chrome option's argument.

* `BMPPRoxy` -  this context manager is designed to create BMP Proxy on new port. It assumes that BMPDaemon is 
already up. 

It doesn't require BMPDaemon object, but only some of it's parameters.

By default it assumes, that BMPDaemon is running on localhost. By default it also assumes that it is 
running on port 8080, you may want to override this value.

This context manager returns BMP Proxy.

In the exit from the code block inside context-manager, it closes BMP Proxy.

* `SeleniumWebDriver` - this context manager is designed to create Web Driver. It assumes that BMPDaemon is already up. 
You may pass BMPPRoxy if you want to use it. It doesn't require BMPDaemon object. It returns Web Driver. 
In the exit from the code block inside context-manager, it close Web Driver, see 
`closeSeleniumWebDriver()` for the details.

*Note:* Web Driver consists of Python wrapper and some executable file (chromedriver.exe, for example). 
The term 'Web Driver' (confusingly) refers to both.

*Note*: There is some complexity on how to create general-purpose context-manager that will work for any Web Driver. 
For example, Google Chrome and Mozilla Firefox has different option's class. 

My implementation is inspired by 
https://github.com/clemfromspace/scrapy-selenium/blob/develop/scrapy_selenium/middlewares.py

* `closeSeleniumWebDriver()` If you're using SeleniumWebDriver as context-manager, it will worry to close Web Driver. 
If you want to do it yourself, you can call closeSeleniumWebDriver() function.

You may wonder why call to web_driver.quit() is not sufficient. 
*Note* (**be aware!**): you shouldn't confuse this call with `web_driver.close()`. 
The last call will close only the tab and not browser itself.

Why web_driver.quit() is not enough?

I have noticed, that sometimes, when exception is raised, but not always, Google Chrome browser and/or 
chromedriver.exe remain residents in memory.

When I've added the same logic to close all ancestor processes that was opened in Web Driver initialization, 
this never happens again.

See `closeBmpDaemon()`

See https://github.com/AutomatedTester/browsermob-proxy-py/issues/8#issuecomment-679150656

* `Screenshot` is designed to be used as context-manager.

If you want API for simple function call, please use `save_screenshot()`.

You may want to guard piece of you code with this context-manager. It is required that you instantiated `web_driver` 
first.

* `save_screenshot()` is regular function API. If you want a context-manager, please use `Screenshot`.

Maybe, you have some try-finally block and you want when you've caught an exception from `web_driver` to get 
screenshot in order to understand better what went wrong. 

Personally, I prefer to use Screenshot, but in some complex scenario you may want to have better control.

*Note*: you can define `dd['browser_download_folder']` as following
`dd['files']['browser_download_folder'] = str(Path(Path.home(), 'Downloads'))`

See see https://stackoverflow.com/questions/37480641/how-do-i-view-the-screenshot-available-via-screen

* `enable_chrome_download()` is Google Chrome specific function.

In Google Chrome in headless mode download is disabled by default. 
It's a "feature", for security. If you want to enable download you can use this function. 


See https://stackoverflow.com/questions/45631715/downloading-with-chrome-headless-and-selenium for more details.
See also https://bugs.chromium.org/p/chromium/issues/detail?id=696481.


* `set_new_har()` is convenient wrapper to `bmp_proxy.new_har()` with `capture*` parameters. 

It is used to get network transmission. For example, if you want to get response body. 

See https://medium.com/@jiurdqe/how-to-get-json-response-body-with-selenium-amd-browsermob-proxy-71f10335c66 
for more details.

Note:
 
1. You should call `bmp_proxy.wait_for_traffic_to_stop(5, 70)` first (you can change parameters).
Here we're waiting (5 ms) for network traffic to stop (with timeout of 70 ms). It is needed to ensure that BMP Proxy 
has recorded all network traffic (up to this point).

2. You should use `for ent in reversed(d['log']['entries']):`, note reversed builtin (it is absent in the link above).
If you have multiple calls to same URL, you should look on last result, so you should reverse the order of log entries.


This call is equivalent to click on *"Start recording"* on *Network* tab of *Page Inspector*.

* `wait_page_loaded()` is helper function to ensure that some basic elements of the page, such as title are loaded.

Usage example:

```python
from alexber.seleniumsupport import wait_page_loaded
wait = WebDriverWait(web_driver, timeout=70, poll_frequency=1)
wait_page_loaded(wait)
```

* `click_sync()`- sometimes calling click() on WebElement raise some weird exception. 
The best practice will be to use `wait.until(EC.element_to_be_clickable((By.XPATH, 'xpath')))`. 
This is "dirty" solution that make synchronous call (by using JavaScript) on `WebElement.click()` 

(WebElement is typically button). See https://stackoverflow.com/a/58378714/1137529 for more details.

Usage example:
```python

from alexber.seleniumsupport import click_sync
wait = WebDriverWait(web_driver, timeout=70, poll_frequency=1)
click_sync(web_driver,
                 wait.until(EC.element_to_be_clickable(
                    (By.XPATH, 'xpath'))))
```

See see https://stackoverflow.com/a/58378714/1137529 

* `wait_chrome_file_finished_downloades() `is Google Chrome specific function.

It works directly with file system. You should know the file_name beforehand. 
It relies on Google Chrome following internal mechanism:

* When Google Chrome downloads file, it has extension ".crdownload". 
* When downloads is finished it Google Chrome rename the file removing this extension.

This function doesn't rely on Google Chrome's downloads status.

On Windows, we can see wrong state of the filesystem. This is the reason for rerty-with-sleep mechanism.


See 
https://docs.python.org/3/library/os.html#os.scandir

https://msdn.microsoft.com/en-us/library/windows/desktop/aa364418(v=vs.85).aspx

https://msdn.microsoft.com/en-us/library/windows/desktop/aa364428(v=vs.85).aspx

*Note:* if the file is very bigger (more than 200MB) you may need to increase retries number.

*` wait_for_display()` - Sometimes, we want to make Selenium Web driver wait until elements style attribute has changed. 

This is usefull for dynamically loaded material. 

For example, we want to wait for the display style to change to none (or to "inline-block" or some other value). 

See https://stackoverflow.com/questions/34915421/make-selenium-driver-wait-until-elements-style-attribute-has-changed

Usage example:
```python
from alexber.seleniumsupport import wait_for_display
wait = WebDriverWait(web_driver, timeout=70, poll_frequency=1)
wait.until(wait_for_display((By.XPATH, 'xpath')))
```

See https://stackoverflow.com/questions/34915421/make-selenium-driver-wait-until-elements-style-attribute-has-changed

<!--
### Added 
### Changed
### Removed
-->