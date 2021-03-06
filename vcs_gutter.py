import sublime
import sublime_plugin
try:
    from .view_collection import ViewCollection
except ValueError:
    from view_collection import ViewCollection

ST3 = int(sublime.version()) >= 3000

_show_in_minimap = False

def plugin_loaded():
    """
    Ugly hack for icons in ST3
    kudos:
    github.com/facelessuser/BracketHighlighter/blob/BH2ST3/bh_core.py#L1380
    """
    from os import makedirs
    from os.path import exists, join

    icon_path = join(sublime.packages_path(), "Theme - Default")
    if not exists(icon_path):
        makedirs(icon_path)

    settings = sublime.load_settings('VcsGutter.sublime-settings')
    global _show_in_minimap
    _show_in_minimap = settings.get('show_in_minimap', False)

class VcsGutterCommand(sublime_plugin.WindowCommand):
    region_names = ['deleted_top', 'deleted_bottom',
                    'deleted_dual', 'inserted', 'changed']

    def run(self):
        self.view = self.window.active_view()
        if not self.view:
            # View is not ready yet, try again later.
            sublime.set_timeout(self.run, 1)
            return
        self.clear_all()
        inserted, modified, deleted = ViewCollection.diff(self.view)
        self.lines_removed(deleted)
        self.bind_icons('inserted', inserted)
        self.bind_icons('changed', modified)

    def clear_all(self):
        for region_name in self.region_names:
            self.view.erase_regions('vcs_gutter_%s' % region_name)

    def lines_to_regions(self, lines):
        regions = []
        for line in lines:
            position = self.view.text_point(line - 1, 0)
            region = sublime.Region(position, position+1)
            regions.append(region)
        return regions

    def lines_removed(self, lines):
        top_lines = lines
        bottom_lines = [line - 1 for line in lines if line > 1]
        dual_lines = []
        for line in top_lines:
            if line in bottom_lines:
                dual_lines.append(line)
        for line in dual_lines:
            bottom_lines.remove(line)
            top_lines.remove(line)

        self.bind_icons('deleted_top', top_lines)
        self.bind_icons('deleted_bottom', bottom_lines)
        self.bind_icons('deleted_dual', dual_lines)

    def icon_path(self, icon_name):
        if int(sublime.version()) < 3014:
            path = '..'
            extn = ''
        else:
            path = 'Packages'
            extn = '.png'
        return path + '/VCS Gutter/icons/' + icon_name + extn

    def bind_icons(self, event, lines):
        regions = self.lines_to_regions(lines)
        event_scope = event
        if event.startswith('deleted'):
            event_scope = 'deleted'
        scope = 'markup.%s.vcs_gutter' % event_scope
        icon = self.icon_path(event)
        if ST3 and _show_in_minimap:
            flags = sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
        else:
            flags = sublime.HIDDEN
        self.view.add_regions('vcs_gutter_%s' % event, regions, scope, icon, flags)
