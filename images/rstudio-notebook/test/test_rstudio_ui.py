#!/usr/bin/python

"""To be used with docker compose
this must be python3.5 code
"""

import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait as webdriverwait
import selenium.webdriver.support.expected_conditions as ec
from selenium.webdriver.common.by import By as by
import time, logging, copy
import logging
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from setuptools import Command

import pytest
import os

LOGGER = logging.getLogger(__name__)
THIS_DIR = os.path.dirname(os.path.realpath(__file__))

WAIT_TIME = 15 or os.environ.get('WAIT_TIME')
MAX_RETRIES = 5 or os.environ.get('MAX_RETRIES')
JUPYTER_TOKEN = os.environ.get('JUPYTER_TOKEN')
SERVICE_NAME = '127.0.0.1' or os.environ.get('SERVICE_NAME')


def test_rstudio(container):

    c = container.run(
        ports={'8888/tcp':8888},
        command=["jupyter","notebook",'--port=8888',"--ip=0.0.0.0","-NotebookApp.token=''","--NotebookApp.password=''"],
    )

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOGGER.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    LOGGER.addHandler(ch)

    fh = logging.FileHandler('artifacts/ui-test.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    LOGGER.addHandler(fh)

    # initialize the driver options and connect to the notebook
    options = Options()
    options.headless = True
    options.add_argument('--window-size=1920x1480')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument("--proxy-server='direct://'")
    options.add_argument('--proxy-bypass-list=*')
    options.add_argument('--start-maximized')
    options.add_argument("disable-infobars")
    options.add_argument('--ignore-ssl')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-popup-blocking")

    browser = Chrome(options=options)

    # give it some time for nbconvert to run and to spin up notebook server
    baseurl = 'http://{0}:8888'.format(SERVICE_NAME)

    # if JUPYTER_TOKEN:
    #     baseurl = '{0}/?token={1}'.format(baseurl, JUPYTER_TOKEN)
    # else:
    #     raise TypeError('Must specify JUPYTER_TOKEN as environment variable')
    
    LOGGER.info(c.status)
    LOGGER.info(c.logs())
    current_retries = 0
    while True:

        if current_retries == MAX_RETRIES:
            raise Exception('Max retry limit hit, could not connect to jupyter server')
        
        browser.get(baseurl)

        if browser.page_source != '<html><head></head><body></body></html>':
            break

        current_retries += 1
        LOGGER.info('Could not connect to server at {0} yet... Retry count = {1}'.format(baseurl, current_retries))
        LOGGER.info(browser.page_source)
        time.sleep(WAIT_TIME)

    LOGGER.info('Connected to jupyter notebook')

    # check only 1 tab
    assert len(browser.window_handles) == 1

    # select the new button + create a python notebook
    LOGGER.info('Checking RStudio')
    new_button = webdriverwait(browser, WAIT_TIME).until(
        ec.element_to_be_clickable((by.ID, 'new-dropdown-button'))
    )
    new_button.click()

    rstudio_button = webdriverwait(browser, WAIT_TIME).until(
        ec.element_to_be_clickable((by.LINK_TEXT, 'RStudio'))
    )
    rstudio_button.click()

    time.sleep(WAIT_TIME + 15)
    LOGGER.info('RStudio ok')
    LOGGER.info('Loading datascience-rstudio.Rmd')

    original_window = browser.current_window_handle
    for window_handle in browser.window_handles:
        if window_handle != original_window:
            browser.switch_to.window(window_handle)
            break
    
    browser.implicitly_wait(WAIT_TIME)
    rstudio_handler = browser.current_window_handle
    ActionChains(browser).key_down(Keys.CONTROL).send_keys("o").perform()
    browser.switch_to.window(browser.window_handles[-1])
    ids = browser.find_elements(by.XPATH,'//*[@id]')
    file_id=None
    for ii in ids:
        try:
            e=ii.get_attribute('id')
            if 'rstudio_dirContents' in e:
                if ii.text.split()[0]== 'datascience-rstudio.Rmd':
                    file_id = e
        except:
            pass
         
    file_promtp=browser.find_element(by.ID,file_id)
    file_promtp.click()
    file_close = browser.find_element(by.XPATH,'//*[@id="rstudio_file_accept_open"]')
    file_close.click()
    LOGGER.info('datascience-rstudio.Rmd ok')
    time.sleep(WAIT_TIME+15)
    
    LOGGER.info('Checking knit')
    
    ActionChains(browser).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys("k").perform()
    LOGGER.info('knit clicked worked')
    
    time.sleep(WAIT_TIME + 15)
    browser.save_screenshot('artifacts/screenshot.png')
    notebook = browser.window_handles[0]
    browser.switch_to.window(notebook)

    # check for the pdf generated
    exit_code,output = c.exec_run('ls /home/jovyan')
    LOGGER.info(output.decode("utf-8"))
    if  'datascience-rstudio.pdf' not  in output.decode("utf-8") :
        LOGGER.info('datascience-rstudio.pdf not generated')
        raise FileNotFoundError
       


    # select the quit button
    LOGGER.info('Checking the quit button')
    file = browser.window_handles[0]
    browser.switch_to.window(file)
    quit_btn = webdriverwait(browser, WAIT_TIME).until(
        ec.element_to_be_clickable((by.ID, 'shutdown'))
    )
    quit_btn.click()

    LOGGER.info('Exited the notebook server')
    LOGGER.info('UI testing all pass!')

    # except Exception as e:

    #     LOGGER.error('failed selenium acceptance testing')
    #     LOGGER.error(e)
    #     raise e