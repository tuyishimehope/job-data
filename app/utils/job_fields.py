import re

ROLE_KEYWORDS = {
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "Software Engineer I",
    "Associate Software Engineer",
    "Graduate Software Engineer",
    "New Grad Software Engineer",
    "Python Engineer",
    "Java Engineer",
    "Early Career Software Engineer",
    "Software Developer",
    "Graduate Developer"
}


def extract_experience_years(text: str) -> int | None:
    text = text.lower()

    patterns = [
        r"(\d+)\+?\s*(?:years|yrs)\s+of\s+experience",
        r"(\d+)\+?\s*(?:years|yrs)\s+experience",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return int(match.group(1))

    return None


def detect_visa_sponsorship(text: str) -> bool | None:
    text = text.lower()

    negative_patterns = [
        "no visa sponsorship",
        "without visa sponsorship",
        "unable to sponsor",
        "cannot sponsor",
        "do not sponsor",
        "does not sponsor",
        "not eligible for sponsorship",
        "will not sponsor",
    ]

    for pattern in negative_patterns:
        if pattern in text:
            return False

    positive_patterns = [
        "visa sponsorship available",
        "visa sponsorship is available",
        "we offer visa sponsorship",
        "we provide visa sponsorship",
        "visa sponsorship provided",
        "we are able to offer visa sponsorship",
        "sponsor your visa",
    ]

    for pattern in positive_patterns:
        if pattern in text:
            return True

    return None


def is_software_role(title: str) -> bool:
    title = title.lower()

    return any(
        keyword in title
        for keyword in ROLE_KEYWORDS
    )
