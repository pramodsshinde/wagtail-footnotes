import re

from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from wagtail.core.blocks import RichTextBlock

FIND_FOOTNOTE_TAG = re.compile(r'<footnote id="(.*?)">.*?</footnote>')


class RichTextBlockWithFootnotes(RichTextBlock):
    """
    Rich Text block that renders footnotes in the format
    '<footnote id="long-id">short-id</footnote>' as anchor elements. It also
    adds the Footnote object to the 'page' object for later use. It uses
    'page' because variables added to 'context' do not persist into the
    final template context.
    """

    def render_basic(self, value, context=None):
        html = super().render_basic(value, context)

        if "page" not in context:
            return html

        page = context["page"]
        if not hasattr(page, "footnotes_list"):
            page.footnotes_list = []
        self.footnotes = {footnote.uuid: footnote for footnote in page.footnotes.all()}

        def replace_tag(match):
            try:
                index = self.process_footnote(match.group(1), page)
            except (KeyError, ValidationError):
                return ""
            else:
                return f'<a href="#footnote-{index}" id="footnote-source-{index}"><sup>[{index}]</sup></a>'

        return mark_safe(FIND_FOOTNOTE_TAG.sub(replace_tag, html))

    def process_footnote(self, footnote_id, page):
        footnote = self.footnotes[footnote_id]
        if footnote not in page.footnotes_list:
            page.footnotes_list.append(footnote)
        return page.footnotes_list.index(footnote) + 1
