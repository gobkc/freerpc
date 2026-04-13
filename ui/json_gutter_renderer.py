import json
import re

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk


class JsonGutterRenderer(Gtk.Box):
    def __init__(self, theme="light", show_line_numbers=True):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.show_line_numbers = show_line_numbers
        self._is_rendering = False

        self.themes = {
            "light": {
                "gutter_bg": "#f5f5f5",
                "line_num": "#999999",
                "fold_btn": "black",
                "string": "#e91e63",
                "number": "#2e7d32",
                "placeholder": "#2e7d32",
            },
            "dark": {
                "gutter_bg": "#000000",
                "line_num": "#666666",
                "fold_btn": "#64b5f6",
                "string": "#f48fb1",
                "number": "#a5d6a7",
                "placeholder": "white",
            },
        }

        self.config = self.themes.get(theme, self.themes["light"])

        self.textview = Gtk.TextView()
        self.textview.set_monospace(True)
        self.textview.set_wrap_mode(Gtk.WrapMode.NONE)
        self.textview.set_vexpand(True)
        self.textview.set_hexpand(True)

        self.buffer = self.textview.get_buffer()
        self.gutter = Gtk.DrawingArea()

        gutter_width = 45 if self.show_line_numbers else 25
        self.gutter.set_size_request(gutter_width, -1)
        self.gutter.set_draw_func(self._draw_gutter)

        self.append(self.gutter)
        self.append(self.textview)

        self.fold_regions = []
        self._raw_text = ""

        self._init_tags()

        self.gutter.add_controller(self._click_controller())

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.textview.add_controller(key_ctrl)

        self.buffer.connect("changed", self._on_buffer_changed)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        mask = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.ALT_MASK
        if (state & mask) == mask and keyval in (Gdk.KEY_l, Gdk.KEY_L):
            self.format_all_json_content()
            return True

        if keyval in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab):
            is_shift = (
                bool(state & Gdk.ModifierType.SHIFT_MASK)
                or keyval == Gdk.KEY_ISO_Left_Tab
            )
            self._handle_indent(is_shift)
            return True
        return False

    def format_all_json_content(self):
        self._is_rendering = True

        start_iter, end_iter = self.buffer.get_bounds()
        text = self.buffer.get_text(start_iter, end_iter, False)

        new_text = ""
        last_pos = 0
        i = 0
        while i < len(text):
            if text[i] in "{[":
                stack = []
                found_end = -1
                for j in range(i, len(text)):
                    char = text[j]
                    if char in "{[":
                        stack.append(char)
                    elif char in "}]":
                        if not stack:
                            break
                        opening = stack.pop()
                        if (opening == "{" and char == "}") or (
                            opening == "[" and char == "]"
                        ):
                            if not stack:
                                found_end = j + 1
                                break
                        else:
                            break

                if found_end != -1:
                    snippet = text[i:found_end]
                    try:
                        obj = json.loads(snippet)
                        formatted = json.dumps(obj, indent=2)
                        new_text += text[last_pos:i] + formatted
                        i = found_end
                        last_pos = i
                        continue
                    except:
                        pass
            i += 1
        new_text += text[last_pos:]

        if new_text != text:
            self.buffer.begin_user_action()
            s, e = self.buffer.get_bounds()
            self.buffer.delete(s, e)
            self.buffer.insert(self.buffer.get_start_iter(), new_text)
            self.buffer.end_user_action()

        self._is_rendering = False
        self._on_buffer_changed()

    def _get_iter_at_line(self, line_num):
        res = self.buffer.get_iter_at_line(line_num)
        return res[-1] if isinstance(res, (tuple, list)) else res

    def _handle_indent(self, unindent=False):
        res = self.buffer.get_selection_bounds()
        if not res:
            if not unindent:
                self.buffer.insert_at_cursor("  ")
            return

        start, end = res
        start_line = start.get_line()
        end_line = end.get_line()
        if end.get_line_offset() == 0 and end_line > start_line:
            end_line -= 1

        self._is_rendering = True
        self.buffer.begin_user_action()
        for i in range(end_line, start_line - 1, -1):
            line_start = self._get_iter_at_line(i)
            if unindent:
                check_end = line_start.copy()
                check_end.forward_chars(2)
                text = self.buffer.get_text(line_start, check_end, False)
                if text.startswith("  "):
                    del_end = line_start.copy()
                    del_end.forward_chars(2)
                    self.buffer.delete(line_start, del_end)
                elif text.startswith(" ") or text.startswith("\t"):
                    del_end = line_start.copy()
                    del_end.forward_chars(1)
                    self.buffer.delete(line_start, del_end)
            else:
                self.buffer.insert(line_start, "  ")
        self.buffer.end_user_action()
        self._is_rendering = False
        self._on_buffer_changed()

    def _click_controller(self):
        ctrl = Gtk.GestureClick()
        ctrl.set_button(1)
        ctrl.connect("pressed", self._on_click)
        return ctrl

    def _on_click(self, gesture, n, x, y):
        line = self._line_from_y(y)
        region = self._region_at_line(line)
        if not region:
            return
        region["collapsed"] = not region["collapsed"]
        self._apply_fold()

    def _on_buffer_changed(self, *args):
        if self._is_rendering:
            return

        start_iter, end_iter = self.buffer.get_bounds()
        text = self.buffer.get_text(start_iter, end_iter, False)

        clean_text = ""
        i = 0
        tag_table = self.buffer.get_tag_table()
        placeholder_tag = tag_table.lookup("placeholder")
        while i < len(text):
            it = self.buffer.get_iter_at_offset(i)
            if it.has_tag(placeholder_tag):
                i += 1
                continue
            clean_text += text[i]
            i += 1

        self._raw_text = clean_text
        self._parse_json_regions(clean_text)
        self._highlight()
        self._apply_fold()
        GLib.idle_add(self.gutter.queue_draw)

    def set_text(self, text: str):
        self.buffer.set_text(text)

    def _parse_json_regions(self, text: str):
        old_states = {r["start"]: r.get("collapsed", False) for r in self.fold_regions}
        self.fold_regions.clear()
        stack, in_string, escape = [], False, False

        for i, ch in enumerate(text):
            if ch == "\\" and not escape:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
            escape = False
            if in_string:
                continue

            if ch in "{[":
                stack.append((ch, i))
            elif ch in "}]":
                if not stack:
                    continue
                op, start = stack.pop()
                if (op == "{" and ch == "}") or (op == "[" and ch == "]"):
                    start_line = text[:start].count("\n")
                    end_line = text[:i].count("\n")
                    if start_line == end_line:
                        continue
                    self.fold_regions.append(
                        {
                            "start": start,
                            "end": i,
                            "type": op,
                            "start_line": start_line,
                            "end_line": end_line,
                            "display_line": start_line,
                            "collapsed": old_states.get(start, False),
                        }
                    )

    def _apply_fold(self):
        self._is_rendering = True
        self.buffer.begin_user_action()

        start, end = self.buffer.get_bounds()
        self.buffer.remove_tag_by_name("hidden", start, end)

        it = self.buffer.get_start_iter()
        placeholder_tag = self.buffer.get_tag_table().lookup("placeholder")
        while not it.is_end():
            next_it = it.copy()
            next_it.forward_char()
            if it.has_tag(placeholder_tag):
                self.buffer.delete(it, next_it)
                it = self.buffer.get_start_iter()
                continue
            it.forward_char()

        for r in sorted(self.fold_regions, key=lambda x: x["start"], reverse=True):
            if not r.get("collapsed"):
                continue

            s_iter = self.buffer.get_iter_at_offset(r["start"] + 1)
            e_iter = self.buffer.get_iter_at_offset(r["end"] + 1)

            if s_iter.get_offset() < e_iter.get_offset():
                self.buffer.apply_tag_by_name("hidden", s_iter, e_iter)
                placeholder_text = "…]" if r["type"] == "[" else "…}"
                self.buffer.insert_with_tags_by_name(
                    s_iter, placeholder_text, "placeholder"
                )

        self.buffer.end_user_action()
        self._is_rendering = False
        GLib.idle_add(self.gutter.queue_draw)

    def _draw_gutter(self, area, cr, w, h):
        cr.set_source_rgba(*self._hex_to_rgb(self.config["gutter_bg"]))
        cr.rectangle(0, 0, w, h)
        cr.fill()
        line = self.buffer.get_start_iter()
        while True:
            line_num = line.get_line()
            rect = self.textview.get_iter_location(line)
            _, win_y = self.textview.buffer_to_window_coords(
                Gtk.TextWindowType.TEXT, rect.x, rect.y
            )
            if rect.height > 0:
                if self.show_line_numbers:
                    cr.set_font_size(11)
                    cr.set_source_rgba(*self._hex_to_rgb(self.config["line_num"]))
                    cr.move_to(5, win_y + 12)
                    cr.show_text(str(line_num + 1))
                region = self._region_at_line(line_num)
                if region:
                    icon = "+" if region["collapsed"] else "−"
                    cr.set_font_size(14)
                    cr.set_source_rgba(*self._hex_to_rgb(self.config["fold_btn"]))
                    btn_x = 28 if self.show_line_numbers else 7
                    cr.move_to(btn_x, win_y + 13)
                    cr.show_text(icon)
            if not line.forward_line():
                break

    def _line_from_y(self, y):
        bx, by = self.textview.window_to_buffer_coords(
            Gtk.TextWindowType.TEXT, 0, int(y)
        )
        it_res = self.textview.get_iter_at_location(bx, by)
        it = it_res[-1] if isinstance(it_res, (tuple, list)) else it_res
        return it.get_line()

    def _region_at_line(self, line):
        for r in self.fold_regions:
            if r["display_line"] == line:
                return r
        return None

    def _init_tags(self):
        table = self.buffer.get_tag_table()

        def add(name, color=None, invisible=False, weight=None):
            tag = Gtk.TextTag.new(name)
            if color:
                tag.set_property("foreground", color)
            if invisible:
                tag.set_property("invisible", True)
            if weight:
                tag.set_property("weight", weight)
            table.add(tag)

        add("string", self.config["string"])
        add("number", self.config["number"])
        add("hidden", invisible=True)
        add("placeholder", color=self.config["placeholder"], weight=400)

    def _highlight(self):
        start, end = self.buffer.get_bounds()
        self.buffer.remove_tag_by_name("string", start, end)
        self.buffer.remove_tag_by_name("number", start, end)
        text = self.buffer.get_text(start, end, False)
        for m in re.finditer(r'"[^"]*"', text):
            self.buffer.apply_tag_by_name(
                "string",
                self.buffer.get_iter_at_offset(m.start()),
                self.buffer.get_iter_at_offset(m.end()),
            )
        for m in re.finditer(r"\b\d+\b", text):
            self.buffer.apply_tag_by_name(
                "number",
                self.buffer.get_iter_at_offset(m.start()),
                self.buffer.get_iter_at_offset(m.end()),
            )

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip("#")
        return [int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
