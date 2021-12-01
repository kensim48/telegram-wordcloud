from collections import Counter
import os
import json
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from tqdm import tqdm
from wordcloud import WordCloud, ImageColorGenerator

# Handle resource import for PyInstaller
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Recursively search for words in text messages
def text_to_words(answer, messages_long, ignored_words):
    try:
        messages = messages_long["text"]
    except TypeError:
        messages = messages_long
    if type(messages) == str:
        message = messages.lower()
        res = re.sub(
            "[" + r"""!"#$%&()*+,-./:;<=>?@[\]^_`{|}~""" + "]", "", message
        ).split()
        answer += [x for x in res if x not in ignored_words]
    else:
        for message in messages:
            text_to_words(answer, message, ignored_words)


if __name__ == "__main__":
    # Parsing arguments
    if len(sys.argv) < 2:
        print(
            "Please enter the name of the json file, or drag the json file into the .exe"
        )
        sys.exit(1)
    elif len(sys.argv) == 2:
        telegram_json = sys.argv[1]
        save_filename = "wordcloud.png"
        ignored_words = set()
    elif len(sys.argv) == 3:
        telegram_json = sys.argv[1]
        save_filename = sys.argv[2]
        ignored_words = set()
    elif len(sys.argv) > 3:
        telegram_json = sys.argv[1]
        save_filename = sys.argv[2]
        ignored_words = sys.argv[3]
        with open(ignored_words, encoding="utf-8") as data_file:
            ignored_words = set(data_file.read().splitlines())
    with open(telegram_json, encoding="utf-8") as data_file:
        data = json.load(data_file)

    # Tries to get user's name
    if "first_name" in data["personal_information"]:
        if "last_name" in data["personal_information"]:
            user_name = (
                data["personal_information"]["first_name"]
                + " "
                + data["personal_information"]["last_name"]
            )
        else:
            user_name = data["personal_information"]["first_name"]
    elif "last_name" in data["personal_information"]:
        user_name = data["personal_information"]["last_name"]
    else:
        exit("Incorrect settings selected when exporting JSON")

    print("📝Reorganizing messages from {}...".format(user_name))
    # Grabs list of all messages, format is a list of lists, where inner list belongs to a single recipient
    list_of_messages = [x["messages"] for x in data["chats"]["list"] if "name" in x]

    # Joins all lists of list into a single long list
    all_messages = [inner for outer in list_of_messages for inner in outer]

    # Some messages don't have a "from" field, so we need to filter those out
    all_text_messages = [x for x in all_messages if "from" in x.keys()]

    # Only grab messages from the person we're interested in
    all_named_messages = [x for x in all_text_messages if user_name == x["from"]]

    print("⏲️Seperating messages into words...")
    # Seperate all messages into individual words
    answer = []
    for message in tqdm(all_named_messages):
        text_to_words(answer, message, ignored_words)
    counted = dict(Counter(answer))

    print("☁️Creating word cloud image...")
    counted = {str(key): value for key, value in counted.items()}

    # Create word cloud
    wordcloud = WordCloud(
        font_path=resource_path("arial.ttf"), width=1024, height=1024
    ).generate_from_frequencies(counted)

    # Rearrange word cloud into image
    mask = np.array(Image.open(resource_path("telegram_logo.png")))
    wordcloud_spa = WordCloud(
        font_path=resource_path("arial.ttf"),
        mask=mask,
        background_color="white",
        max_words=1000,
    ).generate_from_frequencies(counted)

    # Create coloring from image
    image_colors = ImageColorGenerator(mask)
    plt.figure(figsize=[7, 7])
    plt.imshow(wordcloud_spa.recolor(color_func=image_colors), interpolation="bilinear")
    plt.axis("off")

    # Saving word cloud
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    saved_filename = os.path.join(application_path, save_filename)
    print("💾Saving word cloud to {}...".format(saved_filename))
    plt.savefig(saved_filename, bbox_inches="tight", pad_inches=0)
    if getattr(sys, "frozen", False):
        k = input("Press enter to exit")
