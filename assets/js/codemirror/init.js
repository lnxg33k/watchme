(function(){
    var $ = django.jQuery;
    $(document).ready(function(){
        $('textarea.html-editor').each(function(idx, el){
            CodeMirror.fromTextArea(el, {
                lineNumbers: true,
                mode: 'text/x-csharp',
                matchBrackets: true,
                styleActiveLine: true,
                indentUnit: 4,
                scrollbarStyle: "simple",
                lineWrapping: true,
                readOnly: true,
                extraKeys: {
                    "F11": function(cm) {
                      cm.setOption("fullScreen", !cm.getOption("fullScreen"));
                    },
                    "Esc": function(cm) {
                      if (cm.getOption("fullScreen")) cm.setOption("fullScreen", false);
                    }
                }
            });
        });
    });
})();

