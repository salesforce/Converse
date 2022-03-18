# Copyright (c) 2020, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root
# or https://opensource.org/licenses/BSD-3-Clause


import requests
from thefuzz import process, fuzz
from wrapt_timeout_decorator import timeout
from Converse.utils.utils import resp


@timeout(0.1)
def funcInch2Cm(entities, *argv, **kargs):
    entity_name = "inch"
    inch = float(entities[entity_name])
    cm = 2.54 * inch
    return resp(True, "{} inch equals to {} centimeter".format(inch, cm))


@timeout(2.0)
def funcGetWeather(entities, *argv, **kargs):
    def getWeather(zipcode):
        apiKey = "69b8a3eca4a62e882f77a03275ce31a7"
        url = (
            "http://api.openweathermap.org/data/2.5/weather?zip={},us&appid={}".format(
                zipcode, apiKey
            )
        )
        r = requests.get(url).json()
        loc = r["name"]
        weather = r["weather"][0]["description"]
        return weather, loc

    entity_name = "zip_code"
    zipcode = entities[entity_name]
    if isinstance(zipcode, tuple):
        address = dict(zipcode)
        zipcode = " ".join(address.values())
    try:
        res = getWeather(zipcode)
        return resp(
            True, "Weather condition is {} at {}, {}".format(res[0], res[1], zipcode)
        )
    except Exception:
        return resp(False, msg="Weather condition not availiable at {}".format(zipcode))


@timeout(0.5)
def funcGetTVPlanPrice(entities, *argv, **kargs):
    price = {"hulu live": 200, "hulu tv": 200, "fubo tv": 300, "pluto tv": 500}
    entity_name = "new_tv_plan"
    tvplan = entities[entity_name]
    try:
        return resp(
            True, "the price of {} is {} dollar per year".format(tvplan, price[tvplan])
        )
    except Exception:
        return resp(False, msg="the price of {} is not avaiable".format(tvplan))


@timeout(0.2)
def collect_info(entities, *argv, **kargs):
    en_name = kargs["cur_entity_name"]
    return resp(True, msg="Info collected: " + str(entities[en_name]))


@timeout(0.2)
def check_condition(entities, *argv, **kargs):
    polarity = kargs["polarity"]
    if polarity == 1:
        return resp(True, msg="OK.")
    else:
        return resp(False, msg="All right.")


@timeout(0.2)
def check_condition_helpful(entities, *argv, **kargs):
    polarity = kargs["polarity"]
    if polarity == 1:
        return resp(True, msg="OK.")
    else:
        return resp(True, msg="All right.")


@timeout(0.2)
def verify_ssn(entities, *argv, **kargs):
    return resp(True, msg="OK")


@timeout(0.2)
def covid_protocol(entities, *argv, **kargs):
    return resp(
        True,
        msg="If you have COVID-19 symptoms, immediately "
        "self-isolate and contact your local public health "
        "authority or healthcare provider. Wear a mask, stay"
        " at least 6 feet from others, wash your hands, avoid"
        " crowds, and take other steps to prevent the spread "
        "of COVID-19.",
    )


@timeout(0.2)
def create_appointment(entities, *argv, **kargs):
    return resp(
        True,
        msg="Appointment created.",
    )


@timeout(0.2)
def search_departuring_flight(entities, *argv, **kargs):
    msg = "Let's start with your departing flight. "
    msg += "Here are the cheapest flights departing from {} to {} on {}:\n".format(
        entities["origin"], entities["destination"], entities["start_date"]
    )
    msg += "Oceanic 815, Depart at 4:16am, 800USD\n"
    msg += "Ajira 316, Depart at 15:42pm, 1500USD\n"
    msg += "Qantas 442, Depart at 23:08pm, 2300USD."
    return resp(
        True,
        msg=msg,
    )


@timeout(0.2)
def search_returning_flight(entities, *argv, **kargs):
    msg = "And here are your returning flights:\n"
    msg += "Oceanic 443, Depart at 4:16am, 800USD\n"
    msg += "Ajira 232, Depart at 15:42pm, 1500USD\n"
    msg += "Qantas 424, Depart at 23:08pm, 2300USD."
    return resp(
        True,
        msg=msg,
    )


@timeout(0.2)
def choose_flight_departing(entities, *argv, **kargs):
    msg = ""
    flight = choose_entity(
        entities["flight_choice_departing"], ["Oceanic 815", "Ajira 316", "Qantas 442"]
    )
    if not flight:
        flight = "Oceanic 815"
    msg += "Your departing flight is {}. ".format(flight)
    return resp(
        True,
        msg=msg,
    )


def choose_entity(
    query,
    entities,
):
    """
    choose entity from an entity pool based on cur_turn_states.asr_out and
    cur_turn_states.extracted_info,
    return got_entity:bool and entity:Entity
    """

    def ordinal(info):
        order = None
        # TODO: this is too hacky, may need a better way in the future
        ordinal_dict = {
            "latter": -1,
            "former": 0,
            "middle": 1,
            "last": -1,
            "first": 0,
            "second": 1,
            "third": 2,
        }
        for key in ordinal_dict:
            if key in info:
                order = ordinal_dict[key]
        return order

    entity = None
    order = ordinal(query.split())
    if order is not None:
        entity = entities[order]
    else:
        entity = process.extract(query, entities, limit=1, scorer=fuzz.ratio,)[
            0
        ][0]

    return entity


@timeout(0.2)
def choose_flight_returning(entities, *argv, **kargs):
    flight = choose_entity(
        entities["flight_choice_returning"],
        ["Oceanic 443", "Ajira 232", "Qantas 424"],
    )
    if not flight:
        flight = "Oceanic 443"
    msg = "Alright, your returning flight is {}. ".format(flight)
    return resp(
        True,
        msg=msg,
    )


@timeout(0.2)
def check_application_status_by_number(entities, *argv, **kargs):
    entity_name = "application_number"
    application_num = entities[entity_name]
    status = {"1234456": "Pending Review"}
    try:
        return resp(
            True,
            'OK, your application {}, is currently "{}."'.format(
                application_num, status[application_num]
            ),
        )
    except Exception:
        return resp(
            False,
            msg="Application {} is not available in the system.".format(
                application_num
            ),
        )


@timeout(0.2)
def check_application_status_by_auth(entities, *argv, **kargs):
    entity_name = "auth_code"
    auth_code = entities[entity_name]
    status = {"1974": "Pending Review"}
    try:
        return resp(
            True,
            'OK, your application 1234456, is currently "{}"'.format(status[auth_code]),
        )
    except Exception:
        return resp(False, msg="The authentication is not valid")


@timeout(0.2)
def verify_name_for_checking_application(entities, *argv, **kargs):
    if entities["name"].lower() == "john locke":
        return resp(True, msg="OK")
    else:
        return resp(False, msg="Sorry, I cannot find you name.")


@timeout(0.2)
def verify_security_question(entities, *argv, **kargs):
    if entities["security_question"].lower() == "toyota camry":
        return resp(True, msg="OK")
    else:
        return resp(False, msg="Sorry, the answer of the security question is wrong.")


@timeout(0.1)
def movies_being_shown(entities, *argv, **kargs):
    message = """Here are the movies in theater now:
      - The Shawshank Redemption (1994)
      - The Godfather (1972)
      - The Godfather: Part II (1974)
      - The Dark Knight (2008)
      - 12 Angry Men (1957)
      - Schindler's List (1993)
      - The Lord of the Rings: The Return of the King (2003)
      - Pulp Fiction (1994)
      - The Good, the Bad and the Ugly (1966)
      - The Lord of the Rings: The Fellowship of the Ring (2001)
    """
    return resp(
        True,
        msg=message,
    )


@timeout(0.5)
def finish_booking_movie_tickets(entities, *argv, **kargs):
    # Skip storing entity information to database
    return resp(
        True,
        msg="Successfully booked tickets",
    )


@timeout(0.5)
def get_name_and_welcome(entities, *argv, **kargs):
    first_name = entities["name"].split()[0]
    return resp(True, msg="Hi, " + first_name)


@timeout(0.5)
def verify_credit_card(entities, *argv, **kargs):
    return resp(True, msg="Card number verified")


@timeout(0.5)
def verify_zip_code(entities, *argv, **kargs):
    return resp(True, msg="Zip code verified")


@timeout(0.5)
def inform_the_credit_card_issue(entities, *argv, **kargs):
    # Assume the message is retrieved from backend (like a database)
    # according to the identity info in entities
    return resp(
        True,
        msg="It seems that your credit card has been suspended"
        " because your balance has not been paid for 3 months."
        " We will re-activate your credit card as soon as we "
        "receive the payment in full.",
    )


@timeout(0.5)
def get_remaining_balance(entities, *argv, **kargs):
    # Assume the balance info is retrieved from backend (like a
    # database) according to the identity info in entities
    return resp(True, msg="Your balance due is $250.13.")


@timeout(0.5)
def finish_order_tshirts(entities, *argv, **kargs):
    color = entities["color"]
    size = entities["size"]
    front_text = entities["front_text"]
    back_text = entities["back_text"]
    message = (
        "A "
        + color
        + " "
        + size
        + " T-shirt with "
        + front_text
        + " on the front side and "
        + back_text
        + " on the back side. Your order is submitted. Thank you!"
    )
    return resp(True, msg=message)
