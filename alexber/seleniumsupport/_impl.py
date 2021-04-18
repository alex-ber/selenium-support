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
from selenium.common.exceptions import StaleElementReferenceException

from browsermobproxy import Server as BmpServerDaemon
from browsermobproxy import Client as BmpClientProxy

def save_screenshot(web_driver, screenshot_file_name, screen=None):
    """
    This is regular function API. If you want a context-manager, please use Screenshot.
    If screen is not None, it is saved into screenshot_file_name.
    Otherwise, screenshot it taken using  web_driver and saved into screenshot_file_name.

    :param web_driver: Optional if screen provided, otherwise mandatoty.
    :param screenshot_file_name: file_name where screenshot will be saved.
    :param screen: Optional. If not provided, web_driver is used to take screenshot.
    :return:
    """
    if screenshot_file_name is None:
        raise ValueError

    if screen is None:
        if web_driver is None:
            raise ValueError
        web_driver.save_screenshot(screenshot_file_name)
    else:
        # see https://stackoverflow.com/questions/37480641/how-do-i-view-the-screenshot-available-via-screen

        with open(screenshot_file_name, "wb") as f:
            f.write(base64.decodebytes(screen.encode()))

def closeBmpDaemon(bmp_daemon):
    """
    This method fetches all child (grandchild and all ancestors) process ids that was open in bmp_daemon.start().
    We're calling bmp_daemon.stop() and then we're killing all ancestor's processes.

    If the process was meanwhile terminated, we're ignoring if.

    If the process id was reused, we also do nothing.

    :param bmp_daemon:
    :return:
    """
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
    """
    This is context-manager that responsible for running BMP Daemon.
    It returns BMP Daemon.
    In the exit from the code block inside context-manager, BMP Daemon will be stopped, see closeBmpDaemon().


    :param daemon: dict that has 2 keys 'init' and 'start'.
    :param init: dict that will be passed to __init()__ method of BMP Daemon.
              path: The default value is 'browsermob-proxy'. (On Windows it is browsermob-proxy.bat).
                If this file is not available in OS environment variables, you should provide explicit file
                to the executable file.
              options: (dict)
                 port: The default value is 8080. This is the port when BMP daemon will run.
            start: dict that will be passed to start() method of BMP Daemon.
               options: (dict)
                 log_path: The default value is os.getcwd(). This represent directory (without filename!)
                           where logs of BMP Daemon will be written.
                 log_file: The default value is server.log. This represent filename (only filename,
                           without path to directory!) of the log.
               See https://github.com/AutomatedTester/browsermob-proxy-py/blob/master/browsermobproxy/server.py#L59
               for undocumented values.

    :return:
    """
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
    """
    This context-manager can be used for reuse of user data dir.
    It unzips file template to work_dir.
    It returns directory with extracted content from template.
    In the exit from the code block inside context-manager, the work_dir is removed.

    :param work_dir: base directory for temporary directory. Optional. os.gettempdir() is default value.
    :param work_file_prefix: prefix for temporary directory. Optional.
    :param work_file_suffix: suffix for temporary directory. Optional.
    :param template: file to unzip. Mandatory.
    :return:
    """

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
    """
    This context manager is designed to create BMP Proxy on new port.
    It assumes that BMPDaemon is already up.
    It doesn't require BMPDaemon object, but only some of it's parameters.
    It returns BMP Proxy.
    In the exit from the code block inside context-manager, it closes BMP Proxy.

    :param browsermob: dict with 2 keys 'daemon' and 'proxy'
            daemon: dict
              init: dict that was be passed to __init()__ method of BMP Daemon.
                options: (dict)
                   host: The default value is localhost. This is the host where BMP daemon is running.
                   port: The default value is 8080. This is the port when BMP daemon is running.
            proxy: dict
              param: URL query (for example httpProxy and httpsProxy vars)

    :return:
    """
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
    """
    This method fetches all child (grandchild and all ancestors) process ids that was open in
    Selenium's Web Driver initialization.
    We're calling web_driver.quit() and then we're killing all ancestor's processes.

    If the process was meanwhile terminated, we're ignoring if.

    If the process id was reused, we also do nothing.

    :param web_driver:
    :return:
    """
    # see closeBmpDaemon()
    # see https://github.com/AutomatedTester/browsermob-proxy-py/issues/8#issuecomment-679150656
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
    """
    This context manager is designed to create Selenium's Web Driver.
    It assumes that BMPDaemon is already up.

    It returns web_driver.
    In the exit from the code block inside context-manager, it closes web_driver, see closeSeleniumWebDriver().

    :param browsermobproxy. Optional. If you want to use BMP Proxy with Selenium's Web Driver, you should pass the object.
    :param browser: dict
             path: Optional. The path to the browser's executable file.
                             If this file is not available in OS environment variables, you should provide explicit
                             value.
             web_driver: dict
               name: It is used to determine specific (for the browser) Web Driver. For example, 'chrome' or 'firefox'.
               path: Optional. Path to the executable file of the Web Driver. It is needed for the Python wrapper to
                     invoke it. This is where actual browser control part sits.
                     If this file is not available in OS environment variables, you should provide explicit value.
               log_file: Optional. All logs from the Selenium's Web Driver component will be redirected to this log_file.
               command_executor: Optional. If supplied Remote variant of Selenium's Web Driver will be used.
               experimental_options: Optional. For example, for Google Chrome,
                                     'excludeSwitches': ['enable-logging', 'enable-automation'].
               arguments:  Browser's option's arguments. For example,  for Google Chrome,
                          --headless', '--window-size=1920,1080',
                          '--ignore-certificate-errors', '--disable-useAutomationExtension'.

    :return:
    """
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
def Screenshot(web_driver, action=None, base_dir=None, logger=None):
    """
    It is designed to be used as context-manager. 
    If you want API for simple function call, please use save_screenshot().

    You may want to guard piece of you code with this context-manager.
    It is required that you instantiated web_driver first.
    If in the code block inside context-manager exception will be raised, than some additional action will be taken.

    If logger is not None, warning logger message will be issued to it.

    If we have instance of WebDriverException that has screen on it, it will be used to generate png file of screenshot.
    If screen is None or we don't have instance of WebDriverException, that we will actively make screenshot. Note, that this attempt may fail.


    :param web_driver:
    :param action: Optional. Indicator on what action exception occurs.
    :param base_dir: Optional. Directory where to put screenshot.
    :param logger: Optional. If present, logger.warning will be also issued.
    :return:
    """
    try:
        yield web_driver
    except Exception as e:
        t0_str = time.strftime("%Y-%m-%d_%H_%M_%S")
        if logger is not None:
            logger.warning(f'{action} failed at {t0_str}, see screenshot')
        screen = e.screen if isinstance(e, WebDriverException) else None
        if action is None:
            action = ''
        screenshot_file_name = f'screen_{action}_{t0_str}.png' \
                                if base_dir is None \
                                else \
                                 f'{base_dir}/screen_{action}_{t0_str}.png'

        save_screenshot(web_driver, screenshot_file_name, screen)
        raise e


def enable_chrome_download(web_driver, downloadsPath):
    """
    In Google Chrome in headless mode download is disabled by default. It's a "feature", for security.
    If you want to enable download you can use this function.

    :param web_driver:
    :param downloadsPath: - where to save downloaded files.
    :return:
    """
    # run this command for allowing download in headless mode in specific page
    #See
    #https://stackoverflow.com/questions/45631715/downloading-with-chrome-headless-and-selenium
    #https://bugs.chromium.org/p/chromium/issues/detail?id=696481
    web_driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior',
             'params': {'behavior': 'allow', 'downloadPath': downloadsPath}}

    web_driver.execute("send_command", params)

def set_new_har(bmp_proxy, har_name, title=None, **kwargs):
    """
    Convenient wrapper to bmp_proxy.new_har() with capture* parameters.
    For example, if you want to get response body.

    :param bmp_proxy:
    :param har_name: name of the har file
    :param title: Optional.
    :param kwargs: Optional. Additional options to pass or override.
    :return:
    """
    # har formating
    #see https://medium.com/@jiurdqe/how-to-get-json-response-body-with-selenium-amd-browsermob-proxy-71f10335c66

    options = {'captureHeaders': True, 'captureContent': True, 'captureBinaryContent': True,
               **kwargs}
    bmp_proxy.new_har(har_name, options=options, title=title)

def wait_page_loaded(wait, title=None):
    """
    This is helper function to ensure that some basic elements of the page, such as title are loaded.

    :param wait: how much to wait. WebDriverWait is expecting.
    :param title: what should be in the page's title.
    :return:
    """
    if title is not None:
        wait.until(EC.title_contains(title))
    wait.until(EC.visibility_of_all_elements_located((By.XPATH, '/html/body')))

def click_sync(web_driver, web_element):
    """
    Sometimes calling click() on WebElement raise some weird exception.
    The best practice will be to use wait.until(EC.element_to_be_clickable("xpath")).
    This is "dirty" solution that make synchronous call (by using JavaScript) on WebElement.click()
    (WebElement is typically button).

    :param web_driver:
    :param web_element: to make click upon
    :return:
    """
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
    """
    This is Google Chrome specific function.
    It works directly with file system. You should know the file_name beforehand.
    It relies on Google Chrome following internal mechanism: when Google Chrome downloads file, it has extension
    ".crdownload". When downloads is finished it Google Chrome rename the file removing this extension.

    Note: if the file is very bigger (more than 200MB) you may need to increase retries number.


    :param file_name: to check
    :param downloadsPath: the download's folder of the browser. Typically, /home/<YOUR_USERNAME>/Downloads
    :param default_sleep_time: how many second to sleep before consulting file system.
    :param retries: how may retries to make to see that file was downloaded.
    :param logger:
    :return:
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info("wait_file_downloades()")

    p = Path(downloadsPath)

    while retries > 0:
        #https://docs.python.org/3/library/os.html#os.scandir
        #https://msdn.microsoft.com/en-us/library/windows/desktop/aa364418(v=vs.85).aspx
        #https://msdn.microsoft.com/en-us/library/windows/desktop/aa364428(v=vs.85).aspx
        #In rare cases or on a heavily loaded system, file attribute information on
        #NTFS file systems may not be current at the time this function is called.
        #We want to give a filesystem time to sync with Python's System Call
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
    """
    Sometimes, we want to make Selenium Web driver wait until elements style attribute has changed.
    This is usefull for dynamically loaded material.
    For example, we want to wait for the display style to change to none (or to "inline-block" or some other value)
    """
    def __init__(self, locator, display_style='none'):
        self.locator = locator
        self.display_style = display_style

    def __call__(self, driver):
        try:
            element = driver.find_element(*self.locator)
            return element.value_of_css_property("display") == self.display_style
        except StaleElementReferenceException:
            return False