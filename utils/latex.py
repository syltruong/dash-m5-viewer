import re
import urllib

def convert_markdown(text : str) -> str:
    """
    Return Markdown text with external image links for latex equations

    Parameters
    ----------
    text : str
        Markdown text with inline latex

    Returns
    -------
    str
        Markdown text with external image links
    """

    def _toimage(x):
        if x[1] and x[-2] == r'$':
            x = x[2:-2]
            return '\n' + r'![](https://math.now.sh?from={})'.format(urllib.parse.quote_plus(x)) + '\n'
            img = "<img src='https://math.now.sh?from={}' style='display: block; margin: 0.5em auto;'>\n"
            return img.format(urllib.parse.quote_plus(x))
        else:
            x = x[1:-1]
            return r'![](https://math.now.sh?from={})'.format(urllib.parse.quote_plus(x))
    
    return re.sub(r'\${2}([^$]+)\${2}|\$(.+?)\$', lambda x: _toimage(x.group()), text)

def read_text_from_file(path : str) -> str:
    """
    Return Markdown text with external image links for latex equations

    Parameters
    ----------
    text : str
        Markdown text with inline latex

    Returns
    -------
    str
        Markdown text with external image links
    """

    with open(path, 'r') as f:
        ret = f.read()
    
    return ret