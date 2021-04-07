import logging
import base64
import contextlib
import psutil
import signal
import time
import tempfile
from zipfile import ZipFile
from pathlib import Path

from contextlib import suppress
from importlib import import_module

from selenium.common.exceptions import  WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from browsermobproxy import Server as BmpServerDaemon
from browsermobproxy import Client as BmpClientProxy

def save_screenshot(web_driver, screenshot_file_name, screen=None):
    if web_driver is None or screenshot_file_name is None:
        raise ValueError

    if screen is None:
        web_driver.save_screenshot(screenshot_file_name)
    else:
        # see https://stackoverflow.com/questions/37480641/how-do-i-view-the-screenshot-available-via-screen

        with open(screenshot_file_name, "wb") as f:
            f.write(base64.decodebytes(screen.encode()))

def closeBmpDaemon(bmp_daemon):
    # see https://github.com/AutomatedTester/browsermob-proxy-py/issues/8#issuecomment-679150656
    if bmp_daemon is not None and bmp_daemon.process is not None:
        childs_process = []
        try:
            cmd_process = psutil.Process(bmp_daemon.process.pid)
            childs_process = cmd_process.children(recursive=True)
            childs_process = [*childs_process, cmd_process]

            bmp_daemon.stop()
        finally:
            for child in childs_process:
                # we can't accidentally kill newly created process
                # we can kill only the process we have cached earlier
                # if process was already finished we will get NoSuchProcess
                # that we're just suppressing
                with suppress(psutil.NoSuchProcess):
                    child.send_signal(signal.SIGTERM)

def _validate_param(d, param_name):
    if d is None:
        raise ValueError(f"Expected '{param_name} param not found")


@contextlib.contextmanager
def BMPDaemon(**kwargs):
    daemon_d = kwargs.get('daemon', None)
    _validate_param(daemon_d, 'daemon')

    daemon_init_d = daemon_d.get('init', None)
    _validate_param(daemon_init_d, 'init')

    daemon_start_d = daemon_d.get('start', None)
    _validate_param(daemon_start_d, 'start')

    bmpDaemon = None

    try:
        bmpDaemon = BmpServerDaemon(**daemon_init_d)
        bmpDaemon.start(**daemon_start_d)
        yield bmpDaemon
    finally:
        closeBmpDaemon(bmpDaemon)


@contextlib.contextmanager
def BrowserDataDir(**kwargs):
    work_dir = kwargs.get('work_dir', None)
    work_file_prefix = kwargs.get('work_file_prefix', None)
    work_file_suffix = kwargs.get('work_file_suffix', None)

    with tempfile.TemporaryDirectory(suffix=work_file_suffix, prefix=work_file_prefix, dir=work_dir) as root:
        file = kwargs.get('template', None)
        _validate_param(file, 'template')

        with ZipFile(file, 'r') as zipObj:
            zipObj.extractall(root)
        yield root




@contextlib.contextmanager
def BMPProxy(**kwargs):
    #This method assumes that BMPDaemon is already up
    browsermob_d = kwargs.get('browsermob', None)
    _validate_param(browsermob_d, 'browsermob')

    bmp_daemon_host = browsermob_d.get('daemon', {}).get('init', {}).get('options', {}).get('host', 'localhost')
    bmp_daemon_port = browsermob_d.get('daemon', {}).get('init', {}).get('options', {}).get('port', 8080)

    bmp_proxy_params = browsermob_d.get('proxy', {}).get('param', {})

    bmp_daemon_url = f"{bmp_daemon_host}:{bmp_daemon_port}"

    bmp_proxy = None
    try:
        bmp_proxy = BmpClientProxy(bmp_daemon_url, bmp_proxy_params)

        yield bmp_proxy
    finally:
        if bmp_proxy is not None:
            bmp_proxy.close()


def closeSeleniumWebDriver(web_driver):
    # see closeBmpDaemon()
    if web_driver is not None:
        if getattr(getattr(web_driver, 'service', {}), 'process', None) is not None:
            childs_process = []
            try:
                cmd_process = psutil.Process(web_driver.service.process.pid)
                childs_process = cmd_process.children(recursive=True)
                childs_process = [*childs_process, cmd_process]

                web_driver.quit()
            finally:
                for child in childs_process:
                    # we can't accidentally kill newly created process
                    # we can kill only the process we have cached earlier
                    # if process was already finished we will get NoSuchProcess
                    # that we're just suppressing
                    with suppress(psutil.NoSuchProcess):
                        child.send_signal(signal.SIGTERM)
        else:
            web_driver.quit()




@contextlib.contextmanager
def SeleniumWebDriver(**kwargs):
    #This method assumes that BMPDaemon is already up
    web_driver_d = kwargs.get('web_driver', None)
    _validate_param(web_driver_d, 'web_driver_d')

    browser_d = kwargs.get('browser', {})

    # #insipired by https://github.com/clemfromspace/scrapy-selenium/blob/develop/scrapy_selenium/middlewares.py
    web_driver_base_path = f"selenium.webdriver.{web_driver_d['name']}"

    web_driver_klass_module = import_module(f"{web_driver_base_path}.webdriver")

    web_driver_options_module = import_module(f"{web_driver_base_path}.options")
    web_driver_options_klass = getattr(web_driver_options_module, 'Options')

    web_driver_options = web_driver_options_klass()

    web_driver_executable_path = web_driver_d['path']

    web_driver_log_file = web_driver_d.get('log_file', None)

    browser_executable_path = browser_d.get('path', None)

    browsermobproxy = kwargs.get('browsermobproxy', None)

    command_executor = web_driver_d.get('command_executor', None)

    if browser_executable_path:
        web_driver_options.binary_location = browser_executable_path

    for argument in web_driver_d.get('arguments', []):
        web_driver_options.add_argument(argument)

    if browsermobproxy:
        web_driver_options.add_argument(f'--proxy-server={browsermobproxy.proxy}')


    for key, value in web_driver_d.get('experimental_options', {}).items():
        web_driver_options.add_experimental_option(key, value)

    # locally installed driver
    if web_driver_executable_path is not None:
        web_driver_klass = getattr(web_driver_klass_module, 'WebDriver')

        web_driver_kwargs = {
            'executable_path': web_driver_executable_path,
            "options": web_driver_options,
            "service_log_path": web_driver_log_file,
        }

    # remote driver
    elif command_executor is not None:
        from selenium import webdriver
        web_driver_klass = webdriver.Remote
        capabilities = web_driver_options.to_capabilities()

        web_driver_kwargs = {
            'command_executor': command_executor,
            'desired_capabilities': capabilities
        }


    web_driver = None

    try:
        web_driver = web_driver_klass(**web_driver_kwargs)

        yield web_driver
    finally:
        closeSeleniumWebDriver(web_driver)


@contextlib.contextmanager
def Screenshot(web_driver, action, base_dir, logger=None):
    try:
        yield web_driver
    except Exception as e:
        t0_str = time.strftime("%Y-%m-%d_%H_%M_%S")
        if logger is not None:
            logger.warning(f'{action} failed at {t0_str}, see screenshot')
        screen = e.screen if isinstance(e, WebDriverException) else None
        save_screenshot(web_driver, f'{base_dir}/screen_{action}_{t0_str}.png', screen)
        raise e


def enable_download(web_driver, downloadsPath):
    # run this command for allowing download in headless mode in specific page
    #See
    #https://stackoverflow.com/questions/45631715/downloading-with-chrome-headless-and-selenium
    #https://bugs.chromium.org/p/chromium/issues/detail?id=696481
    web_driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior',
             'params': {'behavior': 'allow', 'downloadPath': downloadsPath}}

    web_driver.execute("send_command", params)

def set_new_har(bmp_proxy, har_name, title=None, **kwargs):
    # har formating
    #see https://medium.com/@jiurdqe/how-to-get-json-response-body-with-selenium-amd-browsermob-proxy-71f10335c66

    options = {'captureHeaders': True, 'captureContent': True, 'captureBinaryContent': True,
               **kwargs}
    bmp_proxy.new_har(har_name, options=options, title=title)

def wait_page_loaded(wait, title=None):
    if title is not None:
        wait.until(EC.title_contains(title))
    wait.until(EC.visibility_of_all_elements_located((By.XPATH, '/html/body')))

def click_sync(web_driver, web_element):
    # see https://stackoverflow.com/a/58378714/1137529
    web_driver.execute_script("return arguments[0].click();", web_element)


@contextlib.contextmanager
def _glob_gen(p, pattern):
    try:
        gen = p.glob(pattern)
        yield gen
    finally:
        gen.close()


def wait_chrome_file_finished_downloades(file_name, downloadsPath, default_sleep_time=10, retries=40, logger=None):
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info("wait_file_downloades()")

    p = Path(downloadsPath)

    while retries > 0:
        time.sleep(default_sleep_time)
        with _glob_gen(p, f"{file_name}*.crdownload") as gen:
            try:
                filename = next(gen)
            except StopIteration:
                break
            else:
                logger.info(f'{filename.name} is still downloaded')
                retries -= 1

    if retries <= 0:
        raise ValueError("It takes too much time to download the file, aborting...")


#https://stackoverflow.com/questions/34915421/make-selenium-driver-wait-until-elements-style-attribute-has-changed
class wait_for_display(object):
    def __init__(self, locator, display_style='none'):
        self.locator = locator
        self.display_style = display_style

    def __call__(self, driver):
        try:
            element = driver.find_element(*self.locator)
            return element.value_of_css_property("display") == self.display_style
        except StaleElementReferenceException:
            return False