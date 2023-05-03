import json
import os
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup


def import_data():

    # Sur la page Mawaqit de chaque mosquée est stocké en clair dans une balise HTML script toutes les horaires de prière de l'année dans une variable appelée confData
    # L'objectif ici est de récupérer le contenu de cette variable puis de parser le tout vers le format de notre choix (ici CSV)
    # Il faut également gérer les cas d'année bisextile et les différences de iqama notamment pour la prière du vendredi

    url = "https://mawaqit.net/fr/grande-mosquee-de-paris"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    item = soup.find_all("script")
    item = str(item[1])
    item = item.split("var")
    item = item[8].split("\n")[0].split(";")[0].strip().split("confData = ")
    file = open("output.json", "w")
    file.write(item[1])
    file.close()


def transform_data(year: int):
    data_json = json.load(open("output.json"))
    output_info_times_prayers = get_info_day_times_by_calendar_type(
        data_json, year, "iqamaCalendar"
    )
    output_iqama_times_prayers = get_info_day_times_by_calendar_type(
        data_json, year, "calendar"
    )
    df = pd.merge(
        save_to_df(output_info_times_prayers),
        save_to_df(output_iqama_times_prayers),
        on=["day", "name_prayers"],
    )
    df["time_jumua_1"] = data_json["jumua"]
    df["time_jumua_2"] = data_json["jumua2"]

    return df


def get_info_day_times_by_calendar_type(data, year: int, calendar_type: str):
    infos_times = []
    for month, month_values in enumerate(data[calendar_type], 1):
        for day, times in month_values.items():
            try:
                date = datetime(int(year), int(month), int(day))
                if calendar_type == "iqamaCalendar":
                    info_type = "iqama_difference"
                    tmp = [int(iqama.replace("+", "")) for iqama in times]
                    fields = tmp[
                        :
                    ]  # we don't have iqama time for shuruq prayers, by default it's 0
                    fields.insert(1, 0)
                else:
                    fields = times
                    info_type = "times_prayer"

                infos_times.append(
                    {
                        "day": date,
                        "name_prayers": [
                            "Fajr",
                            "Shuruq",
                            "Dhouhr",
                            "Asr",
                            "Maghrib",
                            "Isha",
                        ],
                        info_type: fields,
                    }
                )

            except ValueError:
                print("Ignoring 29 February if it's not a leap year!")

    return infos_times


def save_to_df(items):
    df = pd.DataFrame(items).set_index(["day"]).apply(
        pd.Series.explode).reset_index()
    return df


def save_df_to_csv(df):
    df.to_csv("output.csv", index=False)


def main(year: int):
    import_data()
    df = transform_data(year)
    save_df_to_csv(df)


main(2023)
