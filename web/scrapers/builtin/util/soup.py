import bs4


def get_soup_text(tag: bs4.Tag) -> str:
    """
    Get the text from a soup element but keep the <br> new-lines.
    All lines are .strip()ed and empty lines are dropped.

    This actually changes the soup tree!

    :param tag: a soup element
    :return: str
    """
    DELIMITER = "#!-%br-DeLiMiTtEr"
    for br in tag.find_all("br"):
        br.replaceWith(DELIMITER)

    text = tag.text.replace(DELIMITER, "\n").strip()
    return "\n".join(filter(bool, (line.strip() for line in text.splitlines())))



