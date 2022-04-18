import os
import time

import selenium.webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def launch_webdriver():
    options = Options()
    optionsList = [
        "--headless", "--enable-javascript", "start-maximized",
        "--disable-gpu", "--disable-extensions", "--no-sandbox",
        "--disable-browser-side-navigation", "--disable-dev-shm-usage"
    ]

    for option in optionsList:
        options.add_argument(option)

    options.page_load_strategy = 'eager'
    options.add_experimental_option(
        "excludeSwitches", ["ignore-certificate-errors", "enable-automation"])

    driver = selenium.webdriver.Chrome(service=Service(
        ChromeDriverManager().install()),
                                       options=options)

    return driver


def wd_login(xuhao, mima):
    driver = launch_webdriver()

    # pageName用来表示当前页面标题
    # 0表示初始页面，Unified Identity Authentication页面，统一身份认证页面和其它页面
    pageName = 0

    # notification表示是否需要邮件通知打卡失败
    # 0表示不需要，1表示需要
    notification = 0

    for retries in range(20):
        try:
            if retries != 0:
                print('刷新页面')

                driver.refresh()

                title = driver.title
                if title == '融合门户':
                    pageName = 1
                elif title == '学生健康状况申报':
                    pageName = 2
                elif title in ['填报健康信息 - 学生健康状况申报', '表单填写与审批::加载中']:
                    pageName = 3
                else:
                    pageName = 0

                print(f'当前页面标题为：{title}')

            if pageName == 0:
                print('正在转到统一身份认证页面')

                driver.get(
                    f'https://newcas.gzhu.edu.cn/cas/login?service=https%3A%2F%2Fnewmy.gzhu.edu.cn%2Fup%2Fview%3Fm%3Dup'
                )

                try:
                    WebDriverWait(driver, 30).until(
                        ec.visibility_of_element_located(
                            (By.XPATH,
                             "//div[@class='robot-mag-win small-big-small']")))
                except:
                    pass

                print('正在尝试登陆融合门户')

                driver.execute_script(
                    f"document.getElementById('un').value='{xuhao}'")
                driver.execute_script(
                    f"document.getElementById('pd').value='{mima}'")
                driver.execute_script(
                    "document.getElementById('index_login_btn').click()")

            if pageName in [0, 1]:
                try:
                    WebDriverWait(driver, 30).until(
                        ec.visibility_of_element_located(
                            (By.XPATH, '//a[@title="健康打卡"]/img')))
                except:
                    pass

                print('正在转到学生健康状况申报页面')

                driver.get(
                    'https://yqtb.gzhu.edu.cn/infoplus/form/XNYQSB/start')

            if pageName in [0, 1, 2]:
                try:
                    WebDriverWait(driver, 30).until(
                        ec.element_attribute_to_include(
                            (By.XPATH, "//div[@id='div_loader']"),
                            "display: none;"))
                except:
                    pass

                try:
                    WebDriverWait(driver, 30).until(
                        ec.element_to_be_clickable(By.ID,
                                                   "preview_start_button"))
                except:
                    pass

                print('正在转到填报健康信息 - 学生健康状况申报页面')

                driver.execute_script(
                    "document.getElementById('preview_start_button').click()")

            if pageName in [0, 1, 2, 3]:
                try:
                    WebDriverWait(driver, 30).until(
                        ec.element_attribute_to_include(
                            (By.XPATH, "//div[@id='div_loader']"),
                            "display: none;"))
                except:
                    pass

                print('开始填表')

                xpath = "//div[@align='right']/input[@type='checkbox']"
                driver.execute_script(
                    f'document.evaluate("{xpath}", document).iterateNext().click();'
                )

                xpath = "//nobr[contains(text(), '提交')]/.."
                driver.execute_script(
                    f'document.evaluate("{xpath}", document).iterateNext().click();'
                )

                try:
                    WebDriverWait(driver, 10).until(
                        ec.element_to_be_clickable(
                            By.XPATH,
                            "//button[@class='dialog_button default fr']"))
                except:
                    pass

                driver.execute_script(
                    "document.getElementsByClassName('dialog_button default fr')[0].click()"
                )

                # 等待页面滑动
                time.sleep(10)

                formErrorContentList = driver.find_elements(
                    By.XPATH, "//div[@class='line10']")

                for formErrorContent in formErrorContentList:
                    button = driver.find_elements(
                        locate_with(By.XPATH, "//input[@type='radio']").below(
                            formErrorContent))[0]
                    ActionChains(driver).move_to_element(
                        button).click().perform()

                print('尝试提交表单')

                xpath = "//nobr[contains(text(), '提交')]/.."
                driver.execute_script(
                    f'document.evaluate("{xpath}", document).iterateNext().click();'
                )

                time.sleep(30)

                message = driver.execute_script(
                    "return document.getElementsByClassName('form_do_action_error')[0]['textContent']"
                )
                print(message)

                if message == '打卡成功':
                    print('打卡程序运行结束')

                    break

                else:
                    print('重新进行打卡')

        except Exception as e:
            print(e)
            print(f"第{retries+1}次运行失败！\n")

            # retries == 19代表最后一次循环，如果这次循环仍然异常，则
            if retries == 19:
                notification = 1

    driver.quit()

    if notification == 1:
        print('打卡失败，尝试抛出异常，以便github邮件通知打卡失败')

        a = '12'
        a.append(a)


if __name__ == "__main__":
    xuhao = str(os.environ['XUHAO'])
    mima = str(os.environ['MIMA'])

    wd_login(xuhao, mima)
