import sys

from zope.interface import implementer

from pyramid.compat import reraise

try:
    from chameleon.zpt.template import PageTemplateFile
    PageTemplateFile # prevent pyflakes complaining about a redefinition below
except ImportError: # pragma: no cover
    exc_class, exc, tb = sys.exc_info()
    # Chameleon doesn't work on non-CPython platforms
    class PageTemplateFile(object):
        def __init__(self, *arg, **kw):
            reraise(ImportError, exc, tb)

from pyramid.interfaces import ITemplateRenderer

from pyramid.decorator import reify
from pyramid import renderers

def renderer_factory(info):
    return renderers.template_renderer_factory(info, ZPTTemplateRenderer)

@implementer(ITemplateRenderer)
class ZPTTemplateRenderer(object):
    def __init__(self, path, lookup, macro=None):
        self.path = path
        self.lookup = lookup
        self.macro = macro

    @reify # avoid looking up reload_templates before manager pushed
    def template(self):
        if sys.platform.startswith('java'): # pragma: no cover
            raise RuntimeError(
                'Chameleon templates are not compatible with Jython')
        tf = PageTemplateFile(self.path,
                              auto_reload=self.lookup.auto_reload,
                              debug=self.lookup.debug,
                              translate=self.lookup.translate)
        if self.macro:
            # render only the portion of the template included in a
            # define-macro named the value of self.macro
            macro_renderer = tf.macros[self.macro].include
            tf._render = macro_renderer
        return tf

    def implementation(self):
        return self.template
    
    def __call__(self, value, system):
        try:
            system.update(value)
        except (TypeError, ValueError):
            raise ValueError('renderer was passed non-dictionary as value')
        result = self.template(**system)
        return result

