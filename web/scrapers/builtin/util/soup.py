import bs4


def get_soup_text(tag: bs4.Tag) -> str:
    """
    Get the text from a soup element and
     - keep the <br> new-lines
     - add new-line at end of text-content within <div>s

    All lines are .strip()ed and empty lines are dropped.

    This actually changes the soup tree!

    :param tag: a soup element
    :return: str
    """
    DELIMITER = "#!-%br-DeLiMiTtEr"
    for br in tag.find_all("br"):
        br.replaceWith(DELIMITER)

    for div in tag.find_all("div"):
        childs = list(div.children)
        if len(childs) == 1 and isinstance(childs[0], bs4.NavigableString):
            childs[0].replaceWith(f"{childs[0]}{DELIMITER}")

    text = tag.text.replace(DELIMITER, "\n").strip()
    return "\n".join(filter(bool, (line.strip() for line in text.splitlines())))



