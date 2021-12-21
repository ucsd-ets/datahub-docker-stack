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

import pytest
import os

LOGGER = logging.getLogger(__name__)
THIS_DIR = os.path.dirname(os.path.realpath(__file__))

WAIT_TIME = 15 or os.environ.get('WAIT_TIME')
MAX_RETRIES = 5 or os.environ.get('MAX_RETRIES')
JUPYTER_TOKEN = os.environ.get('JUPYTER_TOKEN')
SERVICE_NAME = 'jupyter' or os.environ.get('SERVICE_NAME')


def test_rstudio(container):


    c = container.run(
        ports={'8888/tcp':8888},
        command=["jupyter",'--port=8888'],
    )

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOGGER.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    LOGGER.addHandler(ch)

    fh = logging.FileHandler('/opt/datahub/ui-test.log')
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

    browser = Chrome(options=options)

    # give it some time for nbconvert to run and to spin up notebook server
    baseurl = 'http://{0}:8888'.format(SERVICE_NAME)

    if JUPYTER_TOKEN:
        baseurl = '{0}/?token={1}'.format(baseurl, JUPYTER_TOKEN)
    else:
        raise TypeError('Must specify JUPYTER_TOKEN as environment variable')

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

    rstudio = browser.window_handles[-1]
    browser.switch_to.window(rstudio)        

    rmarkdown = webdriverwait(browser, WAIT_TIME).until(
        ec.element_to_be_clickable((by.XPATH, '//*[@id="rstudio_container"]/div[2]/div/div[3]/div/div[2]/div/div/div[4]/div/div[6]/div/div[2]/div/div[3]/div/div[2]/div/div[2]/div/div/div[2]/div/div[3]/div/div/div[3]/div/div[4]/div/div[3]/div/div[2]/div/div/table/tbody/tr[1]/td[3]'))
    )
    rmarkdown.click()
    time.sleep(WAIT_TIME)
    LOGGER.info('datascience-rstudio.Rmd ok')

    # logger.info('Checking knit')
    # knit = webdriverwait(browser, WAIT_TIME).until(
    #     ec.element_to_be_clickable((by.XPATH, '//*[@id="rstudio_container"]/div[2]/div/div[3]/div/div[4]/div/div/div[2]/div/div[6]/div/div[2]/div/div[2]/div/div[3]/div/div[2]/div/div[2]/div/table/tbody/tr/td[1]/table/tbody/tr/td[19]/button/table/tbody/tr/td[2]/div'))
    # )

    # knit.click()
    # logger.info('knit clicked worked')

    time.sleep(WAIT_TIME + 15)

    notebook = browser.window_handles[0]
    browser.switch_to.window(notebook)

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