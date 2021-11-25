import bs4


def get_soup_text(tag: bs4.Tag) -> str:
    DELIMITER = "#!-%br-DeLiMiTtEr"
    for br in tag.find_all("br"):
        br.replaceWith(DELIMITER)

    return tag.text.replace(DELIMITER, "\n").strip()



