import re
import unicodedata


TEAM_ALIAS = {
    # USA
    "USA": "United States",
    "U.S.": "United States",
    "US": "United States",
    "United States of America": "United States",

    # Korea
    "Korea Republic": "South Korea",
    "Republic of Korea": "South Korea",

    # Ivory Coast
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Côte d Ivoire": "Ivory Coast",

    # Cape Verde
    "Cabo Verde": "Cape Verde",

    # Czech
    "Czech Republic": "Czechia",

    # Congo
    "DR Congo": "Democratic Republic of Congo",
    "Congo DR": "Democratic Republic of Congo",
    "Congo-Kinshasa": "Democratic Republic of Congo",

    # Turkey
    "Türkiye": "Turkey",

    # Curacao
    "Curacao": "Curaçao",
}


def clean_team_name(name: str) -> str:
    if not isinstance(name, str):
        return name

    name = unicodedata.normalize("NFKC", name)
    name = name.replace("\u00a0", " ")
    name = re.sub(r"\s+", " ", name)
    name = name.strip()

    return name


def canonical_team_name(name: str) -> str:
    name = clean_team_name(name)
    return TEAM_ALIAS.get(name, name)

