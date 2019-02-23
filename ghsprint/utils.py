from datetime import datetime


def str2date(input: str):
    if input:
        return datetime.strptime(input, '%Y-%m-%dT%H:%M:%SZ')
    return None
