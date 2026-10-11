"""Receipts Report - Android (Kivy) version. Uses the same core.py as the Windows app."""
import os, math, zipfile
from datetime import date, datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, Rectangle

import core

ORANGE = (1, 0.624, 0.263, 1)
ORANGE_D = (0.949, 0.541, 0.118, 1)
ORANGE_L = (1, 0.89, 0.76, 1)
ORANGE_XL = (1, 0.957, 0.902, 1)
TEXT = (0.24, 0.17, 0.12, 1)
WHITE = (1, 1, 1, 1)

Window.clearcolor = WHITE

if platform == 'android':
    try:
        from androidstorage4kivy import SharedStorage, Chooser, ShareSheet
    except Exception:          # pragma: no cover
        SharedStorage = Chooser = ShareSheet = None
else:
    SharedStorage = Chooser = ShareSheet = None


# ------------------------------------------------------------------ small helpers
def btn(text, cb, accent=False, h=44, **kw):
    b = Button(text=text, size_hint_y=None, height=dp(h), font_size=sp(14),
               background_normal='', background_color=ORANGE if accent else ORANGE_L,
               color=WHITE if accent else TEXT, **kw)
    b.bind(on_release=lambda *_: cb())
    return b


def lbl(text, **kw):
    kw.setdefault('color', TEXT)
    kw.setdefault('font_size', sp(13))
    l = Label(text=text, size_hint_y=None, height=dp(24), halign='left', valign='middle', **kw)
    l.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
    return l


def tinput(**kw):
    kw.setdefault('multiline', False)
    kw.setdefault('size_hint_y', None)
    kw.setdefault('height', dp(42))
    kw.setdefault('font_size', sp(14))
    return TextInput(background_color=ORANGE_XL, foreground_color=TEXT, padding=(dp(8), dp(10)), **kw)


def message(title, text):
    box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
    l = Label(text=text, color=TEXT, font_size=sp(14), halign='left', valign='top')
    l.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
    box.add_widget(l)
    p = Popup(title=title, content=box, size_hint=(0.92, 0.5))
    box.add_widget(btn('OK', p.dismiss, accent=True))
    p.open()
    return p


def sniff_ext(path):
    """Files picked on Android may come without an extension - detect xlsx vs csv."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.csv', '.txt', '.xlsx', '.xlsm', '.xls'):
        return path
    try:
        new = path + ('.xlsx' if zipfile.is_zipfile(path) else '.csv')
        os.replace(path, new)
        return new
    except OSError:
        return path


class BgLabel(Label):
    """Row of the result lists: wrapped text on a coloured background, height set by the data."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._upd, pos=self._upd)
        self._bg = None

    def _upd(self, *_):
        self.text_size = (self.width - dp(16), None)
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*(self.bgc if hasattr(self, 'bgc') else WHITE))
            Rectangle(pos=self.pos, size=self.size)

    def refresh_view_attrs(self, rv, index, data):
        self.bgc = data.get('bgc', WHITE)
        super().refresh_view_attrs(rv, index, data)


def make_rv():
    rv = RecycleView(scroll_type=['bars', 'content'], bar_width=dp(6))
    lay = RecycleBoxLayout(default_size=(None, None), default_size_hint=(1, None),
                           size_hint_y=None, orientation='vertical', spacing=dp(2))
    lay.bind(minimum_height=lay.setter('height'))
    rv.add_widget(lay)
    rv.viewclass = 'BgLabel'
    return rv


from kivy.factory import Factory
Factory.register('BgLabel', cls=BgLabel)


def row_item(text, bg, bold=False):
    chars = max(20, int((Window.width - dp(24)) / sp(7.2)))
    lines = sum(max(1, math.ceil(len(t) / chars)) for t in text.split('\n'))
    return dict(text=text, bgc=bg, color=TEXT, font_size=sp(13), halign='left', valign='top',
                bold=bold, height=dp(16) * lines + dp(14), size_hint_y=None)


# ------------------------------------------------------------------ date picker (day / month / year)
class DatePopup(Popup):
    def __init__(self, current, on_pick, **kw):
        today = date.today()
        cur = current or today
        box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.d = Spinner(text='%02d' % cur.day, values=['%02d' % i for i in range(1, 32)])
        self.m = Spinner(text='%02d' % cur.month, values=['%02d' % i for i in range(1, 13)])
        self.y = Spinner(text=str(cur.year), values=[str(y) for y in range(today.year - 6, today.year + 2)])
        for w in (self.d, self.m, self.y):
            w.background_normal = ''; w.background_color = ORANGE_L; w.color = TEXT
            row.add_widget(w)
        box.add_widget(row)
        self.on_pick = on_pick

        def ok():
            try:
                d = date(int(self.y.text), int(self.m.text), int(self.d.text))
            except ValueError:
                message('Invalid date', 'That day does not exist in the chosen month.'); return
            on_pick(d.strftime('%d-%m-%Y')); self.dismiss()
        brow = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        brow.add_widget(btn('Today', lambda: (on_pick(today.strftime('%d-%m-%Y')), self.dismiss())))
        brow.add_widget(btn('Clear', lambda: (on_pick(''), self.dismiss())))
        brow.add_widget(btn('OK', ok, accent=True))
        box.add_widget(brow)
        super().__init__(title='Pick a date', content=box, size_hint=(0.92, None), height=dp(190), **kw)


# ------------------------------------------------------------------ the app
class ReceiptsApp(App):
    title = 'Receipts Report'

    def build(self):
        self.data_dir = self.user_data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.rows, self.result, self.summary, self.title_text = [], [], [], ''
        self.sel_services = set()
        self.rules_text = self._read('summary_rules.txt', core.DEFAULT_RULES)
        self.order, self.shorts = self._load_order()
        saved = [l.strip() for l in self._read('output_columns.txt', '').splitlines() if l.strip() in core.ALL_OUT]
        self.cols = core.clean_cols(saved or core.OUT_COLS)

        root = BoxLayout(orientation='vertical')
        bar = BoxLayout(size_hint_y=None, height=dp(52), padding=dp(5), spacing=dp(4))
        with bar.canvas.before:
            Color(*ORANGE)
            self._bar_bg = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda w, v: setattr(self._bar_bg, 'pos', v), size=lambda w, v: setattr(self._bar_bg, 'size', v))
        for t, cb in (('Import', self.import_files), ('Export', self.do_export), ('Rules', self.edit_rules),
                      ('Order', self.edit_order), ('Columns', self.edit_cols)):
            b = btn(t, cb, h=42); b.size_hint_y = 1
            bar.add_widget(b)
        root.add_widget(bar)

        self.tp = TabbedPanel(do_default_tab=False, tab_width=dp(110))
        self.tab_f = TabbedPanelItem(text='Filters'); self.tab_f.add_widget(self._filters_ui())
        self.tab_r = TabbedPanelItem(text='Receipts')
        self.rv = make_rv(); self.tab_r.add_widget(self.rv)
        self.tab_s = TabbedPanelItem(text='Summary')
        sbox = BoxLayout(orientation='vertical')
        self.sum_title = lbl('', bold=True); self.sum_title.height = dp(44)
        self.srv = make_rv()
        sbox.add_widget(self.sum_title); sbox.add_widget(self.srv)
        self.tab_s.add_widget(sbox)
        for t in (self.tab_f, self.tab_r, self.tab_s):
            self.tp.add_widget(t)
        self.tp.default_tab = self.tab_f
        self.tp.switch_to(self.tab_f)
        root.add_widget(self.tp)

        self.status = lbl('Tap Import to choose a CSV / Excel receipts file.')
        self.status.height = dp(32)
        root.add_widget(self.status)
        return root

    # ---------------------------------------------------------- storage
    def _read(self, name, default):
        try:
            with open(os.path.join(self.data_dir, name), encoding='utf-8') as f:
                return f.read()
        except OSError:
            return default

    def _write(self, name, text):
        try:
            with open(os.path.join(self.data_dir, name), 'w', encoding='utf-8') as f:
                f.write(text)
        except OSError:
            pass

    def _load_order(self):
        txt = self._read('service_order.txt', '')
        o = core.parse_order(txt)
        if o:
            return o, core.parse_shorts(txt)
        return list(core.DEFAULT_ORDER), core.parse_shorts('\n'.join(core.DEFAULT_ORDER))

    # ---------------------------------------------------------- filters tab
    def _filters_ui(self):
        sv = ScrollView()
        g = GridLayout(cols=1, size_hint_y=None, spacing=dp(6), padding=dp(10))
        g.bind(minimum_height=g.setter('height'))
        self.t_from, self.t_to = tinput(hint_text='dd-mm-yyyy'), tinput(hint_text='dd-mm-yyyy')
        g.add_widget(lbl('Date from'))
        g.add_widget(self._date_row(self.t_from))
        g.add_widget(lbl('Date to'))
        g.add_widget(self._date_row(self.t_to))
        self.sp_kendra, self.sp_type, self.sp_staff = [self._spinner() for _ in range(3)]
        for name, w in (('Kendra', self.sp_kendra), ('Type', self.sp_type), ('Staff (Generated By)', self.sp_staff)):
            g.add_widget(lbl(name)); g.add_widget(w)
        self.b_services = btn('Services: all', self.pick_services)
        g.add_widget(lbl('Services')); g.add_widget(self.b_services)
        fr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.t_fmin = tinput(hint_text='Fee min', input_filter='float')
        self.t_fmax = tinput(hint_text='Fee max', input_filter='float')
        fr.add_widget(self.t_fmin); fr.add_widget(self.t_fmax)
        g.add_widget(lbl('Fee range')); g.add_widget(fr)
        self.t_text = tinput(hint_text='search any text')
        g.add_widget(lbl('Search')); g.add_widget(self.t_text)
        self.t_query = tinput(hint_text='Service Name contains DDR and Service Fee >= 100')
        g.add_widget(lbl('Query')); g.add_widget(self.t_query)
        self.c_real, r1 = self._check('Sort by real date (inside each service)')
        self.c_all, r2 = self._check('Summary: all services')
        g.add_widget(r1); g.add_widget(r2)
        g.add_widget(btn('Apply Filters', self.apply, accent=True, h=50))
        g.add_widget(btn('Clear', self.clear))
        sv.add_widget(g)
        return sv

    def _spinner(self):
        return Spinner(text='All', values=['All'], size_hint_y=None, height=dp(42), font_size=sp(14),
                       background_normal='', background_color=ORANGE_XL, color=TEXT)

    def _check(self, text):
        row = BoxLayout(size_hint_y=None, height=dp(40))
        c = CheckBox(size_hint_x=None, width=dp(44), color=ORANGE_D)
        row.add_widget(c); row.add_widget(lbl(text))
        return c, row

    def _date_row(self, ti):
        row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        row.add_widget(ti)
        b = btn('Pick', lambda: DatePopup(core.parse_dt(ti.text).date() if core.parse_dt(ti.text) else None,
                                          lambda s: setattr(ti, 'text', s)).open(), h=42)
        b.size_hint_x = None; b.width = dp(70)
        row.add_widget(b)
        return row

    # ---------------------------------------------------------- services multi-select
    def pick_services(self):
        names = sorted({r['Service Name'] for r in self.rows if r['Service Name']})
        if not names:
            message('No data', 'Import a receipts file first.'); return
        boxes = {}
        box = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))
        sv = ScrollView()
        g = GridLayout(cols=1, size_hint_y=None, spacing=dp(2))
        g.bind(minimum_height=g.setter('height'))
        for n in names:
            row = BoxLayout(size_hint_y=None, height=dp(44))
            c = CheckBox(active=n in self.sel_services, size_hint_x=None, width=dp(44), color=ORANGE_D)
            boxes[n] = c
            l = Label(text=n, color=TEXT, font_size=sp(13), halign='left', valign='middle')
            l.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], s[1])))
            row.add_widget(c); row.add_widget(l); g.add_widget(row)
        sv.add_widget(g); box.add_widget(sv)
        p = Popup(title='Select services (none = all)', content=box, size_hint=(0.96, 0.9))

        def ok():
            self.sel_services = {n for n, c in boxes.items() if c.active}
            self.b_services.text = 'Services: %s' % ('all' if not self.sel_services else '%d selected' % len(self.sel_services))
            p.dismiss()
        def none():
            for c in boxes.values(): c.active = False
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        row.add_widget(btn('Clear', none)); row.add_widget(btn('OK', ok, accent=True))
        box.add_widget(row)
        p.open()

    # ---------------------------------------------------------- import
    def import_files(self):
        if Chooser is not None:
            try:
                Chooser(self._on_chosen).choose_content('*/*', multiple=True)
                return
            except Exception as ex:
                message('Cannot open file picker', str(ex)); return
        # desktop fallback (testing)
        fc = FileChooserListView(path=os.path.expanduser('~'), multiselect=True)
        box = BoxLayout(orientation='vertical'); box.add_widget(fc)
        p = Popup(title='Select receipts file(s)', content=box, size_hint=(0.95, 0.9))
        def ok():
            p.dismiss(); self._load_paths(list(fc.selection))
        box.add_widget(btn('Open', ok, accent=True)); p.open()

    def _on_chosen(self, uris):
        if not uris:
            return
        try:
            paths = [sniff_ext(SharedStorage().copy_from_shared(u)) for u in uris]
        except Exception as ex:
            Clock.schedule_once(lambda dt: message('Import failed', str(ex))); return
        Clock.schedule_once(lambda dt: self._load_paths(paths))

    def _load_paths(self, paths):
        if not paths:
            return
        try:
            self.rows = core.load_files(paths)
        except Exception as ex:
            message('Import failed', str(ex)); return
        uniq = lambda k: sorted({r[k] for r in self.rows if r[k]})
        self.sp_kendra.values = ['All'] + uniq('Saanjh Kendra')
        self.sp_type.values = ['All'] + uniq('Saanjh Kendra Type')
        self.sp_staff.values = ['All'] + uniq('Receipt Generated By')
        self.clear()
        self.status.text = 'Imported %d receipts from %d file(s).' % (len(self.rows), len(paths))

    # ---------------------------------------------------------- filter + show
    def _filters(self):
        def d(s):
            s = s.strip()
            if not s:
                return None
            dt = core.parse_dt(s)
            if not dt:
                raise ValueError('Date must be dd-mm-yyyy: ' + s)
            return dt.date()
        one = lambda sp_: {sp_.text} if sp_.text != 'All' else None
        return dict(date_from=d(self.t_from.text), date_to=d(self.t_to.text), services=set(self.sel_services),
                    kendras=one(self.sp_kendra), types=one(self.sp_type), staffs=one(self.sp_staff),
                    fee_min=self.t_fmin.text.strip() or None, fee_max=self.t_fmax.text.strip() or None,
                    text=self.t_text.text, query=self.t_query.text,
                    real_date_sort=self.c_real.active, order=self.order)

    def apply(self):
        if not self.rows:
            message('No data', 'Please import a CSV or Excel file first.'); return
        try:
            f = self._filters()
            self.result = core.apply_filters(self.rows, f)
        except (core.QueryError, ValueError) as ex:
            message('Filter / query error', str(ex)); return
        self.summary = core.summarize(self.result, self.rules_text, self.c_all.active, self.order, self.shorts)
        self.title_text = core.range_text(self.result, f)
        # receipts list: one card per receipt showing the ticked columns
        cols = self.cols
        data = []
        for i, vals in enumerate(core.out_table(self.result, cols)):
            text = '\n'.join('%s: %s' % (c, v) for c, v in zip(cols, vals) if v != '')
            data.append(row_item(text, ORANGE_XL if i % 2 else WHITE))
        total = sum(r['_fee'] for r in self.result)
        if 'Service Fee' in cols:
            data.append(row_item('TOTAL FEE: %s' % total, ORANGE_L, bold=True))
        self.rv.data = data
        sdata = [row_item('%s\nCount: %s   Fee: %s   Total: %s' % s, ORANGE_XL if i % 2 else WHITE)
                 for i, s in enumerate(self.summary)]
        sdata.append(row_item('TOTAL: %s' % sum(s[3] for s in self.summary), ORANGE_L, bold=True))
        self.srv.data = sdata
        self.sum_title.text = self.title_text
        self.status.text = '%d of %d receipts   |   Total fee: %s' % (len(self.result), len(self.rows), total)
        self.tp.switch_to(self.tab_r)

    def clear(self):
        for t in (self.t_from, self.t_to, self.t_fmin, self.t_fmax, self.t_text, self.t_query):
            t.text = ''
        for s in (self.sp_kendra, self.sp_type, self.sp_staff):
            s.text = 'All'
        self.sel_services = set(); self.b_services.text = 'Services: all'
        self.c_real.active = False
        if self.rows:
            self.apply()

    # ---------------------------------------------------------- export (xlsx, then share)
    def do_export(self):
        if not self.rows or not self.title_text:
            message('Nothing to export', 'Import a file and apply filters first.'); return
        if not self.result:
            message('Nothing to export', 'The current filters return no receipts.'); return
        name = 'Receipts_Report_%s.xlsx' % datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(self.data_dir, name)
        try:
            core.export_excel(path, self.result, self.summary, self.title_text, self.cols)
        except Exception as ex:
            message('Export failed', str(ex)); return
        if SharedStorage is not None:
            try:
                SharedStorage().copy_to_shared(path)
                saved = 'Saved to your phone\'s shared storage (Documents).'
            except Exception:
                saved = 'Saved inside the app.'
            box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
            box.add_widget(Label(text=saved + '\nTap Share to send / open / print it (e.g. WhatsApp, Drive, Google Sheets, a printer app).',
                                 color=TEXT, font_size=sp(14)))
            p = Popup(title='Excel exported', content=box, size_hint=(0.92, 0.45))
            box.add_widget(btn('Share / Open', lambda: ShareSheet().share_file(path), accent=True))
            box.add_widget(btn('Close', p.dismiss))
            p.open()
        else:
            message('Excel exported', path)

    # ---------------------------------------------------------- columns / rules / order
    def edit_cols(self):
        boxes = {}
        box = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))
        sv = ScrollView(); g = GridLayout(cols=1, size_hint_y=None, spacing=dp(2))
        g.bind(minimum_height=g.setter('height'))
        for c in core.ALL_OUT:
            row = BoxLayout(size_hint_y=None, height=dp(44))
            cb = CheckBox(active=c in self.cols, size_hint_x=None, width=dp(44), color=ORANGE_D)
            boxes[c] = cb
            row.add_widget(cb); row.add_widget(Label(text=c, color=TEXT, font_size=sp(14), halign='left'))
            g.add_widget(row)
        sv.add_widget(g); box.add_widget(sv)
        p = Popup(title='Output columns', content=box, size_hint=(0.92, 0.9))

        def setall(names):
            for c, cb in boxes.items(): cb.active = c in names
        def ok():
            sel = [c for c, cb in boxes.items() if cb.active]
            if not sel:
                message('Columns', 'Select at least one column.'); return
            self.cols = core.clean_cols(sel)
            self._write('output_columns.txt', '\n'.join(self.cols))
            p.dismiss()
            if self.rows: self.apply()
        r = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        r.add_widget(btn('All', lambda: setall(core.ALL_OUT)))
        r.add_widget(btn('Default', lambda: setall(core.OUT_COLS)))
        r.add_widget(btn('Save', ok, accent=True))
        box.add_widget(r); p.open()

    def _text_editor(self, title, help_text, initial, on_save, extra=None):
        box = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(6))
        h = Label(text=help_text, color=TEXT, font_size=sp(12), size_hint_y=None, height=dp(70), halign='left', valign='top')
        h.bind(size=lambda w, s: setattr(w, 'text_size', s))
        box.add_widget(h)
        t = TextInput(text=initial, multiline=True, background_color=ORANGE_XL, foreground_color=TEXT, font_size=sp(13))
        box.add_widget(t)
        p = Popup(title=title, content=box, size_hint=(0.96, 0.92))
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        if extra:
            row.add_widget(btn(extra[0], lambda: setattr(t, 'text', extra[1]())))
        row.add_widget(btn('Cancel', p.dismiss))
        row.add_widget(btn('Save', lambda: (on_save(t.text), p.dismiss()), accent=True))
        box.add_widget(row); p.open()

    def edit_rules(self):
        def save(txt):
            self.rules_text = txt.strip(); self._write('summary_rules.txt', self.rules_text)
            if self.rows: self.apply()
        self._text_editor('Summary rules',
                          'One line per summary row:  Label: pattern, pattern\nUse * as wildcard.  DDR: DDR*  merges both DDR services.',
                          self.rules_text, save)

    def edit_order(self):
        def save(txt):
            self.order = core.parse_order(txt); self.shorts = core.parse_shorts(txt, base={})
            self._write('service_order.txt', txt.strip())
            if self.rows: self.apply()
        reset = lambda: core.order_lines(core.DEFAULT_ORDER, core.parse_shorts('\n'.join(core.DEFAULT_ORDER)))
        self._text_editor('Service order + short names',
                          'One service per line:  Service Name | Short Name\nOutput is sorted in this order; same short name = merged in summary.',
                          core.order_lines(self.order, self.shorts), save, extra=('Reset', reset))


if __name__ == '__main__':
    ReceiptsApp().run()
