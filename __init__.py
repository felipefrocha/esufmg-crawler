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
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor


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
    courses = list(map(find_list_courses,group_courses))
    return courses


def crawler_ufmg_descriptions(link: str = ""):
    url = f"https://ufmg.br{link}"
    print(url)
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    pre_filter_courses = soup.find("ol", {"class": 'drop__list'}).find_all("ol",{"class":"drop__list--depth-2"})
    group_courses = [x for i in map(find_group_courses,pre_filter_courses) for x in i]
    courses = list(map(find_course_ementa,group_courses))
    courses_descriptions = [
        (
            "",
            x.contents[0].split("-")[0],
            x.contents[0].split("-")[2], 
            x['href']
        ) 
        for x in courses
    ]
    return courses_descriptions


def crawler_ufmg_description(link:str = ""):
    url = f"https://ufmg.br{link}"
    print(url)
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    try:
        filter_paragraph = soup.find_all("p")
        filter_description = filter_paragraph[0].contents[0] if filter_paragraph else soup
        return filter_description
    except:
        print(f"Not Found Descriptio for {link}")
    return ""

def run_crawler(data:List, routine: Callable):
    print(f'Searching for: {len(data)} datas')
    results = None
    with Pool(processes=multiprocessing.cpu_count()) as pool:
        multiple_results = [pool.apply_async(routine, (i,)) for i in data]
        results = [i for res in multiple_results for i in res.get()]
    print(f'End of Searching')
    return results

def run_crawler1(data:List, routine: Callable):
    print(f'Searching for: {len(data)} datas')
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        start = time.time()
        futures = executor.map(routine, data)
        for result in futures:
            results.append(result)
        end = time.time()
        print("Time Taken: {:.6f}s".format(end-start))
    print(f'End of Searching')
    return results


if __name__ == "__main__":
    periodos = [f'{str(i)}-periodo' for i in range(1, 13)]
    periodos.append("optativas")

    print("##### - List System Eng. Courses - #####")

    system_eng_courses = ListCource()
    system_eng_courses.list = run_crawler(periodos,crawler_eng_sistemas)

    df = pd.DataFrame(data=system_eng_courses.list).set_index("course_id")
    df.to_csv("system_eng.csv")
    
    print("##### - List UFMG Courses - #####")

    links = []
    all_courses = crawler_ufmg_courses()
    
    for course in all_courses:
        for turno in course['turnos']:
            for key, value in turno.items():
                links.append(value)

    print("##### - List Courses Descriptions - #####")

    ufmg_courses = ListCource()
    info_courses = run_crawler(links, crawler_ufmg_descriptions)
    ufmg_courses.list = info_courses
    df = pd.DataFrame(data=ufmg_courses.list).set_index("course_id")
    df.to_csv("ufmg_courses_links.csv")
    links = [x[3] for x in  info_courses]

    print("##### - Getting Courses Info - #####")
    all_courses_descriptions = ListCource()
    n = 10
    chunks = [links[i:i+n] for i in range(0,len(links),n)]
    index = 0
    try:
        for chunk in chunks:
            size = len(chunk)
            start, stop = index * size, (index + 1) * size - 1
            partial_descriptions = ListCource()
            descriptions = run_crawler1(chunk,crawler_ufmg_description)
            intermedium = [(
                info_courses[i+start][0], 
                info_courses[i+start][1], 
                info_courses[i+start][2], 
                descriptions[i]) 
                for i in range(size)]
            partial_descriptions.list = intermedium
            all_courses_descriptions.list = intermedium
            print(f"Writing chunk: {index}")
            df = pd.DataFrame(data=partial_descriptions.list).set_index("course_id")
            df.to_csv("ufmg_courses_complete.csv",mode='a')
            print(f"End Writing")
            index += 1
    except Exception as ex:
        print(f"Fail at Index: {index}; {start},{stop}")
        print(ex)
        exit(1)
    
    print("##### - Saving Courses Info - #####")
    df = pd.DataFrame(data=partial_descriptions.list).set_index("course_id")
    df.to_csv("all_courses_descriptions.csv")
    exit(0)

    

