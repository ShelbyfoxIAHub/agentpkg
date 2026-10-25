"""HTML text extractor using standard library html.parser."""

from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ["script", "style", "head"]:
            self.skip = True

    def handle_endtag(self, tag):
        if tag.lower() in ["script", "style", "head"]:
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.result.append(text)

    def get_text(self) -> str:
        return " ".join(self.result)


def parse_html_bytes(data: bytes) -> str:
    """Extract clean text from HTML bytes."""
    html_content = data.decode("utf-8", errors="ignore")
    parser = HTMLTextExtractor()
    parser.feed(html_content)
    return parser.get_text()


def parse_html(file_path) -> str:
    """Extract clean text from HTML file."""
    with open(file_path, "rb") as f:
        return parse_html_bytes(f.read())
