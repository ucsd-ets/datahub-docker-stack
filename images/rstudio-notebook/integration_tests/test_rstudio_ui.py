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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from setuptools import Command
import time, logging, copy
import logging
import pytest
import os

from scripts.utils import get_logger
from scripts import fs
LOGGER = get_logger()

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

WAIT_TIME = os.environ.get('WAIT_TIME', 60)   # long break when loading sth;
SLEEP_TIME = 5    # short break between operations
FIND_TIME = 10     # tolerence when driver (we call it browser) find element

MAX_RETRIES = os.environ.get('MAX_RETRIES', 5)
JUPYTER_TOKEN = os.environ.get('JUPYTER_TOKEN')
SERVICE_NAME = os.environ.get('SERVICE_NAME', '127.0.0.1')


# @pytest.mark.skip(reason="Skipping test_rstudio() due to Selenium issue")
def test_rstudio(container):

    c = container.run(
        ports={'8888/tcp':8888},
        command=["jupyter","notebook",'--port=8888',"--ip=0.0.0.0","-NotebookApp.token=''","--NotebookApp.password=''"],
    )

    # initialize the driver options and connect to the notebook
    options = Options()
    # options.headless = True   # deprecated
    options.add_argument('--headless=new')  # more powerful functionality
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
    browser.implicitly_wait(FIND_TIME)  # global setting

    # give it some time for nbconvert to run and to spin up notebook server
    baseurl = 'http://{0}:8888'.format(SERVICE_NAME)
    
    LOGGER.info(f"Rstudio UI test: container status: {c.status}")
    LOGGER.info(f"Rstudio UI test: container log: {c.logs()}")
    LOGGER.debug(f'CHECK WAIT_TIME: {WAIT_TIME}')
    LOGGER.debug(f'CHECK SLEEP_TIME: {SLEEP_TIME}')
    LOGGER.debug(f'CHECK FIND_TIME: {FIND_TIME}')
    
    LOGGER.info(f"MAX_RETRIES: {MAX_RETRIES}; SERVICE_NAME: {SERVICE_NAME}")

    current_retries = 0
    # pack everything inside a try-catch. Screenshot when an error is thrown
    try:
        while True:
            if current_retries == MAX_RETRIES:
                raise Exception('Max retry limit hit, could not connect to jupyter server')
            
            browser.get(baseurl)

            if browser.page_source != '<html><head></head><body></body></html>':
                break

            current_retries += 1
            LOGGER.info('Could not connect to server at {0} yet... Retry count = {1}'.format(baseurl, current_retries))
            LOGGER.info(browser.page_source)
            time.sleep(WAIT_TIME)   # to load jupyter notebook homepage
        LOGGER.info('Connected to jupyter notebook')
        time.sleep(SLEEP_TIME)

        # check only 1 tab
        assert len(browser.window_handles) == 1

        # select the new button + create a python notebook
        LOGGER.info('Checking RStudio')
        new_button = webdriverwait(browser, FIND_TIME).until(
            ec.element_to_be_clickable((by.ID, 'new-dropdown-button'))
        )
        new_button.click()

        rstudio_button = webdriverwait(browser, FIND_TIME).until(
            ec.element_to_be_clickable((by.LINK_TEXT, 'RStudio'))
        )
        rstudio_button.click()

        time.sleep(WAIT_TIME)   # for Rstudio Window/Tab to load

        original_window = browser.current_window_handle
        # check 2 tab
        assert len(browser.window_handles) == 2
        for window_handle in browser.window_handles:
            # just switch to the other
            if window_handle != original_window:
                browser.switch_to.window(window_handle)
                break
        LOGGER.info('Switched to RStudio tab')
        
        LOGGER.info('Loading datascience-rstudio.Rmd')
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
        time.sleep(SLEEP_TIME)
        
        LOGGER.info('Checking knit')
        ActionChains(browser).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys("k").perform()
        LOGGER.info('knit clicked worked')
        
        time.sleep(SLEEP_TIME)
        browser.save_screenshot('artifacts/screenshot.png')
        notebook = browser.window_handles[0]
        browser.switch_to.window(notebook)

        # check for the pdf generated
        exit_code,output = c.exec_run('ls /home/jovyan')
        LOGGER.info(output.decode("utf-8"))
        if 'datascience-rstudio.pdf' not in output.decode("utf-8") :
            LOGGER.info('datascience-rstudio.pdf not generated')
            raise FileNotFoundError('datascience-rstudio.pdf not generated')
        
        # select the quit button
        LOGGER.info('Checking the quit button')
        file = browser.window_handles[0]
        browser.switch_to.window(file)
        quit_btn = webdriverwait(browser, WAIT_TIME).until(
            ec.element_to_be_clickable((by.ID, 'shutdown'))
        )
        quit_btn.click()

        time.sleep(SLEEP_TIME)
        LOGGER.info('Exited the notebook server')
        LOGGER.info('RStudio UI test: all pass!')

    except Exception as e:
        # save screenshot
        ss_name = 'error_ss.png'
        browser.save_screenshot(ss_name)
        local_path = os.path.join(fs.LOGS_PATH, ss_name)
        # copy the screenshot from the container to the local machine
        browser.save_screenshot(local_path)
        # with open(local_path, "wb") as local_file:
        #     data, _ = container.get_archive(ss_name)
        #     for chunk in data:
        #         local_file.write(chunk)
        raise Exception("Button Time out, check error screenshot in logs/")
