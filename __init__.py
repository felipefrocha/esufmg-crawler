import re
import os
import time
import requests
import multiprocessing
import pandas as pd
from typing import Callable, List, Tuple
from multiprocessing import Pool, TimeoutError
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class ListCource():
    def __init__(self):
        self.__courses = {
            "period": [],
            "course_id": [],
            "course_name": [],
            "course_description": []
        }

    @property
    def list(self):
        return self.__courses

    @list.setter
    def list(self, courses: List[Tuple]):
        for course in courses:
            if len(course) == 3:
                period, course_id, course_name = course
                course_description = ""
            elif len(course) == 4:
                period, course_id, course_name,course_description = course
            else:
                raise "Error size array is not correct"

            self.__courses["period"].append(period)
            self.__courses["course_id"].append(course_id)
            self.__courses["course_name"].append(course_name)
            self.__courses["course_description"].append(course_description)

    @list.deleter
    def list(self):
        for key, value in self.__courses.items():
            del value
        del self.__courses


def set_chrome_options() -> None:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options


def crawler_eng_sistemas(periodo: str = "1-periodo"):
    browser = webdriver.Chrome(options=set_chrome_options())

    url = f"https://geesufmg.com/o-curso/grade-curricular/{periodo}"
    print(url)
    # req = requests.get(url)
    # soup = BeautifulSoup(req.content, 'html.parser')
    browser.get(url)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    course_title_regex = re.compile('GradeCurricular_course-title.*')
    course_id_regex = re.compile('GradeCurricular_course-id.*')
    courses_titles = [EachPart.get_text() for EachPart in soup.find_all(
        "div", {"class": course_title_regex})]
    courses_ids = [EachPart.get_text() for EachPart in soup.find_all(
        "div", {"class": course_id_regex})]
    courses = [(periodo, courses_ids[i], courses_titles[i])
               for i in range(len(courses_titles))]
    # soup.select("body > div:first-of-type > div > ul li")
    browser.close()
    return courses


regex_courses = re.compile("\/cursos\/graduacao\/.*")

find_group_courses = lambda x: x.find_all("li", {"class","drop__list-item"}, recursive=False)
find_list_courses = lambda x: {"curso": x.find("a", {"href": "#"}).contents[0],
    "turnos": list(map(
        build_struct,
        x.find_all("li", {"class": "drop__list-item--section"}),  
        x.find_all("a", {"href":regex_courses})))
}
find_course_ementa = lambda x: x.find("a", {"href":regex_courses})

build_struct = lambda x, y: {x.contents[0]:y['href']}

find_list_links = lambda x: list(
    map(
        lambda y: (
            y.find_all("li",{"class":"drop__list-item--section"}), 
            y.find_all("a", {"href":regex_courses})
        )
        , x[1]
    )
)


def crawler_ufmg_courses(periodo: str = "1-periodo"):
    url = f"https://ufmg.br/cursos/graduacao/"
    print(url)
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    pre_filter_courses = soup.find("ol", {"class": 'drop__list'}).find_all("ol",{"class":"drop__list--depth-1"})

    group_courses = [x for i in map(find_group_courses,pre_filter_courses) for x in i]
    print(len(group_courses))
    # print(type(group_courses[0]))
    # print(group_courses[0])
    courses = list(map(find_list_courses,group_courses))
    print(len(courses))
    # print(type(courses[0]))
    # print(courses[0])
    return courses


def crawler_ufmg_descriptions(link: str = ""):
    url = f"https://ufmg.br{link}"
    print(url)
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    pre_filter_courses = soup.find("ol", {"class": 'drop__list'}).find_all("ol",{"class":"drop__list--depth-2"})
    group_courses = [x for i in map(find_group_courses,pre_filter_courses) for x in i]
    print(len(group_courses))
    # print(type(group_courses[0]))
    # print(group_courses[0])
    courses = list(map(find_course_ementa,group_courses))
    print(len(courses))
    # print(type(courses[0]))
    # print(courses[0])
    courses_descriptions = [
        (
            "",
            x.contents[0].split("-")[0],
            x.contents[0].split("-")[2], 
            x['href']
        ) 
        for x in courses
    ]
    print(len(courses_descriptions))
    # print(type(courses_descriptions[0]))
    # print(courses_descriptions[0])
    return courses_descriptions


def crawler_ufmg_description(link: str = ""):
    url = f"https://ufmg.br{link}"
    print(url)
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    filter_description = soup.find("article").find("p").contents[0]
    # print(filter_description)
    return filter_description


def run_crawler(data, routine: Callable):
    print(f'Procurados: {data}')
    results = None
    with Pool(processes=multiprocessing.cpu_count()) as pool:
        multiple_results = [pool.apply_async(routine, (i,)) for i in data]
        results = [i for res in multiple_results for i in res.get(timeout=1000)]
    print(f'Final da procura')
    return results


if __name__ == "__main__":
    periodos = [f'{str(i)}-periodo' for i in range(1, 13)]
    periodos.append("optativas")

    print("##### - List System Eng. Courses - #####")

    eng_sis_courses = ListCource()
    eng_sis_courses.list = run_crawler(periodos,crawler_eng_sistemas)
    links = []
    print("##### - List UFMG Courses - #####")

    all_courses = crawler_ufmg_courses()
    
    for course in all_courses:
        for turno in course['turnos']:
            for key, value in turno.items():
                links.append(value)

    print("##### - List Courses Descriptions - #####")

    ufmg_courses = ListCource()
    info_courses = run_crawler(links, crawler_ufmg_descriptions)
    links = [x[3] for x in  info_courses]

    print("##### - Getting Courses Info - #####")

    descriptions = run_crawler(links, crawler_ufmg_description)
    ufmg_courses.list = [(info_courses[i][0], info_courses[i][1], info_courses[i][2], descriptions[i]) for i in range(len(info_courses))]
    
    print("##### - Building Course Info - #####")
    
    df = pd.DataFrame(data=eng_sis_courses.list).set_index("course_id")
    df.append(pd.DataFrame(data=eng_sis_courses.list).set_index("course_id"))
    # print(df.head)
    
    print("##### - Saving Courses Info - #####")

    df.to_excel("all_courses_ementas")
    print(df.head)

