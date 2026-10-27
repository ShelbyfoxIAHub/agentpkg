from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ["script", "style"]:
            self.skip = True

    def handle_endtag(self, tag):
        if tag.lower() in ["script", "style"]:
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            self.result.append(data)

    def get_text(self):
        return " ".join("".join(self.result).split())

def parse_html(content: bytes | str) -> str:
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")
    parser = HTMLTextExtractor()
    parser.feed(content)
    return parser.get_text()
