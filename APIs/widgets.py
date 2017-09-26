from django import forms


class HtmlEditor(forms.Textarea):
    def __init__(self, *args, **kwargs):
        super(HtmlEditor, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'html-editor'

    class Media:
        css = {
            'all': (
                'css/codemirror/codemirror.css',
                'css/codemirror/fullscreen.css',
                'css/codemirror/simplescrollbars.css',
            )
        }
        js = (
            'js/codemirror/codemirror.js',
            'js/codemirror/clike.js',
            'js/codemirror/matchbrackets.js',
            'js/codemirror/active-line.js',
            'js/codemirror/fullscreen.js',
            'js/codemirror/markdown.js',
            'js/codemirror/xml.js',
            'js/codemirror/simplescrollbars.js',
            'js/codemirror/init.js'
        )
