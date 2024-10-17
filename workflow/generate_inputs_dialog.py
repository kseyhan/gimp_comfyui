#  Copyright (c) 2024. Charles Hymes## Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated# documentation files (the “Software”), to deal in the Software without restriction, including without limitation the# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:## The above copyright notice and this permission notice shall be included in all copies or substantial portions of# the Software.## THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE# SOFTWARE.## import pprintfrom utilities.long_term_storage_utils import get_persistent_dirfrom utilities.persister_petite import PersisterPetitefrom workflow.widgets_authoring import WidgetAuthor, METAKEY_FLAG, append_newline_suffix, KEY_SUFFIX_NEWLINEfrom workflow_2_py_generator import *# FYI:#     Gtk.ShadowType python mappings https://lazka.github.io/pgi-docs/Gtk-3.0/mapping.html#     ETCHED_IN#     ETCHED_OUT#     IN#     OUT#     NONEIMPOSSIBLY_LONG_LINE = 9216  # No Tk Grid will ever be this wide, Right?def is_blacklisted(node_class_name: str = "",  # noqa                   node_title: str = "",  # noqa                   index_str: str = "",  # noqa                   input_name: str = ""  # noqa                   ) -> bool:    # noinspection PyUnusedLocal    missive: str = f"""    node_class_name=\"{node_class_name}\"    node_title=\"{node_title}\"    index_str=\"{index_str}\"    input_name=\"{input_name}\""""    # LOGGER_WF2PY.warning(missive)    if (            (                node_title.lower() == "load image" or                node_title.lower() == "base image" or                node_title.lower() == "mask image"            )            and input_name.lower() == "upload"):        LOGGER_WF2PY.warning(f"Blacklisting node_title=\"{node_title}\" input_name=\"{input_name}\"")        return True    return Falsedef log_newline_keys(some_dict: Dict[str, str], logger=LOGGER_WF2PY):    found: bool = False    for key_str in some_dict.keys():        if KEY_SUFFIX_NEWLINE in key_str:            found = True            logger.warning(key_str)        # else:        #     logger.warning(f"No {METAKEY_FLAG} in {key_str}")    if not found:        dict_dump = json.dumps(some_dict, indent=2, sort_keys=True)        raise ValueError(f"No METAKEY_FLAG in any key.\n{dict_dump}")def log_no_newline(some_dict: Dict[str, str], logger=LOGGER_WF2PY):    for key_str in some_dict.keys():        if KEY_SUFFIX_NEWLINE in key_str:            raw = some_dict[key_str]            newline_val = (raw == "True")            if not newline_val:                logger.warning(f"{key_str}={newline_val}")            else:                raise ValueError(f"{key_str}={newline_val}")def count_cells(widget_keys: List[str]) -> int:    result = 0    for widget_name in widget_keys:        if widget_name.startswith("label"):            result += 1            continue        if widget_name.startswith("checkbutton"):            result += 1            continue        result += 3    # pretty = pprint.pformat(widget_keys)    # LOGGER_WF2PY.info(f"count {result} for {pretty}")    return resultclass DialogInputsGenerator(Workflow2PythonGenerator):    DIALOG_PARAMETERS_TEXT = """                            title_in: str,                            role_in: str,                            blurb_in: str,                            gimp_icon_name: str = GimpUi.ICON_DIALOG_INFORMATION"""    DIALOG_INTERNAL_HANDLERS_TXT = """        dialog.add_button(i8_text("_Cancel"), Gtk.ResponseType.CANCEL)        dialog.add_button(i8_text("_Apply"), Gtk.ResponseType.APPLY)        dialog.add_button(i8_text("_OK"), Gtk.ResponseType.OK)        button_cancel: Gtk.Button = dialog.get_widget_for_response(Gtk.ResponseType.CANCEL)        button_apply: Gtk.Button = dialog.get_widget_for_response(Gtk.ResponseType.APPLY)        button_ok: Gtk.Button = dialog.get_widget_for_response(Gtk.ResponseType.OK)        def delete_results(subject: Any):  # noqa            pass        def assign_results(subject: Any):  # noqa            for providers in widget_getters.items():                key_name: str = providers[0]                getter = providers[1]                gotten = getter()  # blob_getters return the full path, then the leaf                if re.fullmatch(r"treeview_.+_image", key_name):                    self.add_image_tuple(gotten)                    dialog_data[key_name] = gotten[1]  # the leaf. We use the full path elsewhere.                else:                    if re.fullmatch(r"treeview_.+_mask", key_name):  # Not yet implemented.                        self.add_mask_tuple(gotten)                        dialog_data[key_name] = gotten[1]  # the leaf. We use the full path elsewhere.                    else:                        dialog_data[key_name] = gotten            persister.update_config(dialog_data)            # persister.log_config()            persister.store_config()            self.put_inputs(dialog_data=dialog_data)"""    DIALOG_SUFFIX_TEXT = """        button_cancel.connect("clicked", delete_results)        button_apply.connect("clicked", assign_results)        button_ok.connect("clicked", assign_results)        progress_bar: GimpUi.ProgressBar = GimpUi.ProgressBar.new()        progress_bar.set_hexpand(True)        progress_bar.set_show_text(True)        dialog_box.add(progress_bar)        progress_bar.show()        geometry = Gdk.Geometry()  # noqa        geometry.min_aspect = 0.5        geometry.max_aspect = 1.0        dialog.set_geometry_hints(None, geometry, Gdk.WindowHints.ASPECT)  # noqa        fill_widget_values()        dialog.show_all()        return dialog"""    IMPORTS_TEXT = """import gigi.require_version('Gimp', '3.0')  # noqa: E402gi.require_version('GimpUi', '3.0')  # noqa: E402gi.require_version("Gtk", "3.0")  # noqa: E402gi.require_version('Gdk', '3.0')  # noqa: E402gi.require_version("Gegl", "0.4")  # noqa: E402from gi.repository import Gdk, Gio, Gimp, GimpUi, Gtk, GLib, GObject, Gegl  # noqafrom typing import Setfrom utilities.cui_resources_utils import *from utilities.heterogeneous import *from utilities.persister_petite import *from utilities.sd_gui_utils import *from workflow.node_accessor import NodesAccessorfrom workflow.workflow_dialog_factory import WorkflowDialogFactory"""    INPUTS_TYPES_MAPPINGS_TAG = "_inputs_types"    SPECIAL_FRAME_LABELS: dict[str, str] = {        "Base Image": "Base Image: (select layer)",        "Load Image": "Load Image: (select layer)",        "Mask Image": "Mask Image: (select layer)"    }    SPECIAL_LABEL_TEXTS: dict[str, str] = {        "image": "Layer",        "Image": "Layer"    }    def __init__(self):        super().__init__()        self._frames_dict: Dict[str, str] = {}        self._generator_instance: WidgetAuthor = WidgetAuthor()    @property    def dialog_header0_text(self) -> str:        text = f"""        widgets_invalid_set: Set[str] = set()        # noinspection PyMethodMayBeStatic        def validate_dialog(invalidated: bool):            nonlocal button_apply            nonlocal button_ok            if invalidated:                LOGGER_SDGUIU.info("Invalidating dialog")                button_apply.set_sensitive(False)                button_ok.set_sensitive(False)            else:                LOGGER_SDGUIU.info("Validating dialog")                button_apply.set_sensitive(True)                button_ok.set_sensitive(True)        def track_invalid_widgets(my_widget: Gtk.Widget, is_invalid: bool):            nonlocal widgets_invalid_set            widget_name: str = my_widget.get_name()            if widget_name is None:                raise ValueError("Widget does not have a name")            if not widget_name.strip():                raise ValueError("Widget name cannot be empty nor whitespace.")            if re.search(r"\\s", widget_name):                raise ValueError("Widget name cannot contain whitespace")            if widget_name in WIDGET_NAME_DEFAULTS:                raise ValueError(f"Widget name cannot be default name \\"{{widget_name}}\\"")            orig_size = len(widgets_invalid_set)            if is_invalid:                if widget_name not in widgets_invalid_set:                    widgets_invalid_set.add(widget_name)                    LOGGER_SDGUIU.info(f"Added {{widget_name}} as INVALID")            else:                # LOGGER_SDGUIU.info(f"Discarding {{widget_name}} from invalid")                widgets_invalid_set.discard(widget_name)            new_size = len(widgets_invalid_set)            delta_size = new_size - orig_size            if delta_size != 0:                validate_dialog(new_size > 0)        dialog = GimpUi.Dialog(use_header_bar=True, title=title_in, role=role_in)        fallback_path = os.path.join(super().asset_dir, "model_dirs.json")        persister: PersisterPetite = PersisterPetite(chassis=dialog,                                                     chassis_name="{self.dialog_identifier}",                                                     fallback_path=fallback_path)        dialog_data: Dict = dict(persister.load_config())        widget_getters: Dict[str, Callable[[], Any]] = {{}}        widget_setters: Dict[str, Callable[[Any], None]] = {{}}        def fill_widget_values():            for consumers in widget_setters.items():                key_name: str = consumers[0]                setter = consumers[1]                try:                    setter(dialog_data[key_name])                except KeyError as k_err:  # noqa                    pass                dialog_box = dialog.get_content_area()        if blurb_in:            label_and_icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)            icon_image = Gtk.Image.new_from_icon_name(gimp_icon_name, Gtk.IconSize.DIALOG)  # noqa            blurb_label: Gtk.Label = Gtk.Label.new(blurb_in)            label_and_icon_box.pack_start(child=icon_image, expand=False, fill=False, padding=0)  # noqa            label_and_icon_box.pack_start(child=blurb_label, expand=False, fill=False, padding=0)  # noqa            label_and_icon_box.show_all()  # noqa            dialog_box.add(label_and_icon_box)"""        return text    @property    def python_class_file_name(self) -> str:        mangled = self.workflow_filename.replace(Workflow2PythonGenerator.WORKFLOW_TAG, "_dialogs")        mangled = re.sub(CRUDE_VERSION_REGEX, r"\g<1>dot\g<2>", mangled)        mangled = mangled.replace(".json", ".py")        return mangled    @property    def dialog_identifier(self) -> str:        mangled = self.workflow_filename.replace(Workflow2PythonGenerator.WORKFLOW_TAG, "_dialog")        mangled = re.sub(CRUDE_VERSION_REGEX, r"\g<1>dot\g<2>", mangled)        mangled = mangled.replace(".json", "")        return mangled.lower()    @property    def frames(self) -> Dict[str, str]:        return self._frames_dict    @property    def input_mappings_json(self):        return self.json_path.replace(Workflow2PythonGenerator.WORKFLOW_TAG,                                      DialogInputsGenerator.INPUTS_TYPES_MAPPINGS_TAG)    @property    def widget_author(self) -> WidgetAuthor:        return self._generator_instance    @property    def installation_data_filename(self):        return f"{self.python_class_name}_dialog_config"    @property    def installation_data_path(self):        idp: str = self.installation_data_filename + ".json"        return os.path.join(get_persistent_dir(), idp)    def constructor_text(self):        text: str = (f"{SP04}def __init__(self, accessor: NodesAccessor):\n"                     f"{SP08}super().__init__(\n"                     f"{SP12}accessor=accessor,\n"                     f"{SP12}api_workflow={self.python_class_name}.WORKFLOW_FILE,\n"                     f"{SP12}dialog_config_chassis_name=\"{self.installation_data_filename}\",\n"                     f"{SP12}wf_data_chassis_name=\"{self.python_class_name}_wf_data\",\n"                     f"{SP08})\n\n"                     )        return text    def dialog_factory_text(self) -> str:        text: str = ""        text += self.dialog_signature()        text += self.dialog_header0_text + "\n"        text += DialogInputsGenerator.DIALOG_INTERNAL_HANDLERS_TXT + "\n"        text += self.frames_text()        text += DialogInputsGenerator.DIALOG_SUFFIX_TEXT + "\n"        return text    # noinspection PyMethodMayBeStatic    def dialog_signature(self) -> str:        # decorator = "%s# noinspection PyMethodMayBeStatic\n" % SP04        complaint = (f"{SP04}# GIMP is preventing subclassing GimpUI.Dialog by preventing access to the constructors."                     " This might be accidental.\n")        signature: str = (f"{complaint}{SP04}def new_workflow_dialog(self,"                          f" {DialogInputsGenerator.DIALOG_PARAMETERS_TEXT}\n"                          f"{SP28}) -> GimpUi.Dialog:")        return signature + "\n"    def frame_declaration_text(self, index_str: str, node_dict: Dict, special_title: str) -> str:        fid: str = identifier_external(index_str=index_str, node_dict=node_dict)        if special_title:            frame_title: str = special_title        else:            frame_title: str = title(node_dict)        self.frames[index_str] = fid        return f"\n{SP08}# New Frame\n{SP08}frame_{fid}: Gtk.Frame = Gtk.Frame.new(label=\"{frame_title}\")  # noqa\n"    def frame_widgets_text(self, index_str: str, node_dict: Dict, frame_id: str) -> str:        field_text = ""        layout_text = ""        grid_id = f"grid_{index_str}"        input_items = node_dict["inputs"].items()        if not input_items:            return ""        node_title: str = node_dict["_meta"]["title"]        # Consider each frame a paragraph, with multiple lines. Each horizontal line has one or more widget sets.        # For example "width, height" will be one line, with four widgets: two pairs of a label and an int entry.        # "positive_prompt" will be one line, with a label and a textview.        # First, derive aggregate data about this frame.        most_cells_on_a_row: int = -1        newline_for_input: Dict[str, bool] = {}        row_base_widths: Dict[int, int] = {}        row_cell_counts: Dict[int, int] = {}        rows_per_frame: int = 0        widget_id_length_longest: int = -1        widgeted_input_item_count: int = 0        width_of_widest_row: int = -1        *_, last_item = input_items  # Funky syntax to get last item in iterable.        last_key = last_item[0]        # Begin 1st pass of all input_items        for input_item in input_items:            key = input_item[0]            value = input_item[1]            metadata_key_newline = append_newline_suffix(key)            w_texts_raw = self.widget_texts(node_class_name=node_dict["class_type"],                                            node_title=node_dict["_meta"]["title"],                                            index_str=index_str,                                            input_name=key,                                            json_value=value)            if not w_texts_raw:                LOGGER_WF2PY.debug(f"{frame_id}::Pass 1::No widgets for node {node_title}:{key}")                continue  # Skip to next input_item            widgeted_input_item_count += 1            # Set newline flag for this input            if metadata_key_newline in w_texts_raw:                nl_value = w_texts_raw[metadata_key_newline]                input_gets_newline: bool = (nl_value == "True")                LOGGER_WF2PY.debug(f"{frame_id}::Pass 1::Metadata newline for input {key}={nl_value}")            else:                input_gets_newline: bool = True                LOGGER_WF2PY.debug(f"{frame_id}::Pass 1::Implicit newline for input {key}")            if key == last_key:                input_gets_newline: bool = True                LOGGER_WF2PY.debug(f"{frame_id}::Pass 1::Last input {key} gets newline.")            newline_for_input[key] = input_gets_newline            # Filter out metadata from w_texts_raw. Dict Comprehension            w_texts = {k: v for (k, v) in w_texts_raw.items() if METAKEY_FLAG not in k}            if not w_texts:                continue  # Skip to next input_item            for declaration in w_texts.values():                field_text += declaration + "\n"                        widget_keys = w_texts.keys()            cells_per_input = count_cells(list(widget_keys))            # Begin widget_field loop            for widget_field in widget_keys:                wfl = len(widget_field)                if wfl > widget_id_length_longest:                    widget_id_length_longest = wfl                w_width: int = 1                # This section can be enhanced to access metadata for width                if not widget_field.startswith("label"):                    w_width = 3                if rows_per_frame in row_base_widths:  # So far, this case has always been false                    row_base_widths[rows_per_frame] += w_width                else:                    row_base_widths[rows_per_frame] = w_width                if row_base_widths[rows_per_frame] > width_of_widest_row:                    width_of_widest_row = row_base_widths[rows_per_frame]            # End widget_field loop            if input_gets_newline:                LOGGER_WF2PY.debug(f"{frame_id}::Pass 1::Newline for {key}")                if rows_per_frame in row_cell_counts:  # So far, this case has always been false                    row_cell_counts[rows_per_frame] += cells_per_input                    LOGGER_WF2PY.debug(f"{frame_id}::Pass 1::{key}:: Incremented row_cell_counts[{rows_per_frame}] to"                                       f" row_cell_counts[{rows_per_frame}]")                else:                    row_cell_counts[rows_per_frame] = cells_per_input                    LOGGER_WF2PY.debug(f"{frame_id}::Pass 1::{key}:: Assigned row_cell_counts[{rows_per_frame}]="                                       f"{cells_per_input}")                if row_cell_counts[rows_per_frame] > most_cells_on_a_row:                    most_cells_on_a_row = row_cell_counts[rows_per_frame]                rows_per_frame += 1            else:                LOGGER_WF2PY.debug(f"{frame_id}::Pass 1::NO Newline for {key}")        row_cell_counts[rows_per_frame] = IMPOSSIBLY_LONG_LINE  # By default, last row is impossibly long.        # End 1st pass of all input_items        # Now generate source code        row: int = 0        column: int = 0  # incremented with width of every widget. If input has newline, resets after widget_field loop        column_biggest: int = 3        # widget_index is inc'ed with every widget in an input. If input has newline, resets after widget_field loop        widget_index: int = 0        # dumped = json.dumps(newline_for_input, indent=2, sort_keys=True)        # LOGGER_WF2PY.debug(f"{frame_id}:: inputs that should generate subsequent newline {dumped}")        # Begin 2nd pass of all input_items        for input_item in input_items:            key = input_item[0]            value = input_item[1]            w_texts_raw = self.widget_texts(node_class_name=node_dict["class_type"],                                            node_title=node_dict["_meta"]["title"],                                            index_str=index_str,                                            input_name=key,                                            json_value=value)            if not w_texts_raw:                LOGGER_WF2PY.debug(f"{frame_id}::Pass 2::No widgets for {node_title}:{key}")                continue  # Skip to next input_item            # Filter out metadata from w_texts_raw. Dict Comprehension            w_texts = {k: v for (k, v) in w_texts_raw.items() if METAKEY_FLAG not in k}            if not w_texts:                continue  # Skip to next input_item            # widget_field loop: Iterate over the widgets of this input            # Begin widgets for single input, aka widget_field loop            for widget_field in w_texts.keys():                padding = " " * (widget_id_length_longest - len(widget_field))                # Begin calculating widget width                width: int = 1                if not widget_field.startswith("label"):  # Labels always have width 1                    width = 3                    if "<Some widget to debug>" == widget_field:                        LOGGER_WF2PY.debug(f"Pass 2::"                                           f"{frame_id}::"                                           f"{widget_field}::"                                           f"widgeted_input_item_count={widgeted_input_item_count}; "                                           f"widget_index={widget_index}; "                                           f"column_biggest={column_biggest}; "                                           f"row={row}")                    if (newline_for_input[key] is True  # Explicit syntax just to call attention to possible truthiness                            or widget_index == (row_cell_counts[row] + 1)  # So far this is never true.                            # Special cases go here. Perhaps metadata might be useful.                            or widget_field.endswith("text_g")                            or widget_field.endswith("text_l")                            or widget_field.startswith("scale_")):                        width = column_biggest - column                        if width < 1:  # column_biggest should always be > column, but special cases can mess that up.                            width = 3                        LOGGER_WF2PY.debug(f"{widget_field}:: Is last")                # Done calculating widget width                comment: str = (f"{SP08}# "                                f"{widget_field}:: "                                f"most_widgets={most_cells_on_a_row}; "                                f"widget_index={widget_index}; "                                f"row={row}; "                                f"newline_for_input[{key}]={newline_for_input[key]}; "                                )                statement = (f"{SP08}"                             f"{grid_id}.attach({widget_field}, {padding}left={column}, top={row}, width={width}"                             f", height=1)  # noqa")                LOGGER_WF2PY.debug(comment)                LOGGER_WF2PY.debug(statement)                if width < 1:                    raise ValueError(f"Width for {widget_field} is < 1")                # The comment is most useful when developing frames for a new workflow.                # layout_text += comment + "\n"                layout_text += statement + "\n"                # Finished using layout values, recalculate them for next iteration                column += width                if column > column_biggest:                    column_biggest = column                widget_index += 1            # End widget_field loop            newline_log_message = f"newline_for_input[{key}]=={newline_for_input[key]}"            if newline_for_input[key] is True:  # ARGH! Beware Python Truthiness!                LOGGER_WF2PY.debug(f"{frame_id}::Pass 2::{newline_log_message}, row="                                   f"{row}. New row {row+1} should start")                row += 1                column = 0                widget_index = 0            else:                LOGGER_WF2PY.debug(f"{frame_id}::Pass 2::{newline_log_message}, continue row {row}")        # End 2nd pass of all input_items        text: str = f"{field_text}{SP08}{grid_id}: Gtk.Grid = Gtk.Grid.new()\n{layout_text}"        text += f"{SP08}{grid_id}.set_column_homogeneous(False)\n"        text += f"{SP08}{grid_id}.set_row_homogeneous(False)\n"        text += f"{SP08}frame_{frame_id}.add(widget={grid_id})  # noqa\n"        return text    def frame_text(self, index_str: str, node_dict: Dict, special_title: str) -> str:        text: str = ""        fid: str = identifier_external(index_str=index_str, node_dict=node_dict)        fwt = self.frame_widgets_text(index_str=index_str, node_dict=node_dict, frame_id=fid)        if fwt:            text += self.frame_declaration_text(index_str, node_dict, special_title=special_title)            text += "%sframe_%s.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)  # noqa\n" % (SP08, fid)            text += "%s" % fwt        return text    def frames_text(self) -> str:        text: str = ""        for item in self.nodes_dictionary.items():            index_str: str = item[0]            node_dict: Dict = item[1]            if title(node_dict) in DialogInputsGenerator.SPECIAL_FRAME_LABELS:                special_title = DialogInputsGenerator.SPECIAL_FRAME_LABELS[title(node_dict)]            else:                special_title = None            text += self.frame_text(index_str=index_str, node_dict=node_dict, special_title=special_title)        text += "%scontent_area: Gtk.Box = dialog.get_content_area()\n" % SP08        for frame_item in self.frames.items():            frame_index: str = frame_item[0]            frame_name: str = frame_item[1]            node_dict: Dict = self.nodes_dictionary[frame_index]            node_class_name: str = node_dict["class_type"]            node_title: str = node_dict["_meta"]["title"]            lengthy: bool = (node_class_name == "CLIPTextEncodeSDXL"                             or node_class_name == "CLIPTextEncodeSDXLRefiner"                             or "prompt" in frame_name.lower()                             or node_title == "Positive Base"                             or node_title == "Negative Base"                             )            if lengthy:                expand: str = "True"                fill: str = "True"            else:                expand: str = "False"                fill: str = "False"            text += (                f"{SP08}content_area.pack_start(child=frame_{frame_name},"                f" expand={expand},"                f" fill={fill},"                f" padding=0)  # noqa\n"            )        # text += "\n"        return text    def widget_texts(self,                     node_class_name: str,                     node_title: str,                     index_str: str,                     input_name: str,                     json_value: Any) -> Dict[str, str]:        """        Most widgets are entries, they get a label and an entry, in that order        The grid's name comes from the index_str        :param node_class_name:        :param node_title:        :param index_str: The node number. Will be used to make field names unique.        :param input_name: The name of the input field. Will be used to name fields and show as labels        :param json_value: A value from json. See https://www.w3schools.com/js/js_json_datatypes.asp        :return: A small Dict. A bool yields a {id, checkbutton declaration}, ints, floats and strs        yield {id, label declaration}{id, entry declaration}        In future releases, this or similar functions will need to create range and combobox widgets.        """        if is_blacklisted(node_title=node_title, input_name=input_name):            return {}        result: Dict[str, str] = {}        widget_declaration: str        value_type: type = type(json_value)        assigned_value = json_value        if re.search(r".*seed.*", input_name.lower()):            assigned_value = 42  # makes match for "case int()"        match assigned_value:            case  "enable" | "disable" | "true" | "false" | "yes" | "no" | bool():                authored: Dict[str, str] = self.widget_author.widget_text_for(                    node_class_name=node_class_name,                    node_index_str=index_str,                    node_title=node_title,                    input_name=input_name,                    json_value=json_value                )                if authored:                    result.update(authored)                else:                    widget_id: str = "checkbutton_%s_%s" % (index_str,  input_name)                    widget_declaration = ("%s%s: Gtk.CheckButton = Gtk.CheckButton.new_with_label(\"%s\")  # noqa\n"  # noqa                                          % (SP08, widget_id, input_name.title()))                    result[widget_id] = widget_declaration            case int():                widget_id: str = "label_%s_%s" % (index_str,  input_name)                label_declaration = "%s%s: Gtk.Label = Gtk.Label.new(\"%s\")" % (SP08, widget_id, input_name.title())                margin_start: int = 8  # Should this sometimes be 2?                label_configuration = (f"{SP08}{widget_id}.set_margin_start({margin_start})\n"                                       f"{SP08}{widget_id}.set_alignment(0.95, 0)"                                       )                result[widget_id] = f"{label_declaration}\n{label_configuration}"                authored: Dict[str, str] = self.widget_author.widget_text_for(                    node_class_name=node_class_name,                    node_index_str=index_str,                    node_title=node_title,                    input_name=input_name,                    newline=False,                    json_value=json_value                )                if authored:                    result.update(authored)                    # log_no_newline(result)                else:                    widget_id: str = "entry_%s_%s" % (index_str,  input_name)                    widget_declaration = "%s%s: Gtk.Entry = Gtk.Entry.new()" % (SP08, widget_id)                    result[widget_id] = widget_declaration            case float():                widget_id: str = "label_%s_%s" % (index_str,  input_name)                label_declaration = "%s%s: Gtk.Label = Gtk.Label.new(\"%s\")" % (SP08, widget_id, input_name.title())                label_configuration = f"{SP08}{widget_id}.set_margin_start(8)"                result[widget_id] = f"{label_declaration}\n{label_configuration}"                authored: Dict[str, str] = self.widget_author.widget_text_for(                    node_class_name=node_class_name,                    node_index_str=index_str,                    node_title=node_title,                    input_name=input_name,                    newline=False,                    json_value=json_value                )                if authored:                    result.update(authored)                    # log_no_newline(result)                else:                    widget_id: str = "entry_%s_%s" % (index_str,  input_name)                    widget_declaration = "%s%s: Gtk.Entry = Gtk.Entry.new()" % (SP08, widget_id)                    result[widget_id] = widget_declaration            case str():                widget_id: str = "label_%s_%s" % (index_str,  input_name)                if input_name in DialogInputsGenerator.SPECIAL_LABEL_TEXTS:                    label_text = DialogInputsGenerator.SPECIAL_LABEL_TEXTS[input_name]                else:                    label_text = input_name.title()                widget_declaration = "%s%s: Gtk.Label = Gtk.Label.new(\"%s\")" % (SP08, widget_id, label_text)                result[widget_id] = widget_declaration                authored: Dict[str, str] = self.widget_author.widget_text_for(                    node_class_name=node_class_name,                    node_index_str=index_str,                    node_title=node_title,                    input_name=input_name,                    json_value=json_value                )                if authored:                    result.update(authored)                else:                    widget_id: str = "entry_%s_%s" % (index_str,  input_name)                    widget_declaration = "%s%s: Gtk.Entry = Gtk.Entry.new()" % (SP08, widget_id)                    widget_declaration += "\n%s%s.set_hexpand(True)" % (SP08, widget_id)                    if "text" in widget_id.lower():                        widget_declaration += "\n%s%s.set_vexpand(True)" % (SP08, widget_id)                    result[widget_id] = widget_declaration            case list():                # message = "Cannot create widget for (currently) unsupported type %s" % value_type.__name__                # LOGGER_WF2PY.warning(message)  # Disable this later                pass            case dict():                message = "Cannot create widget for (currently) unsupported type %s" % value_type.__name__                LOGGER_WF2PY.warning(message)  # Disable this later.            case _:                message = "Cannot create widget for unsupported type %s" % value_type.__name__                LOGGER_WF2PY.warning(message)        return result    def write_inputs_meta_mappings(self):        """This method is not as useful as hoped, because the api workflows don't have data sufficient to infer types        or generate widgets like Gtk.Scale or Gtk.Combobox. Disappointing. """        LOGGER_WF2PY.info("nodes_dictionary from %s has %d nodes."                          % (self.workflow_filename, len(self.nodes_dictionary)))        inputs_template_dict: Dict[str, Dict] = {}        for workflow_items in self.nodes_dictionary.items():            node_index = workflow_items[0]            node_dict = workflow_items[1]            inputs_template_dict[node_index] = {}            inputs_dict = node_dict["inputs"]            meta_key = "default"            default_dict: Dict = {}            # LOGGER_WF2PY.debug("item %02d , mode:%s" % (int(node_index), meta_key))            for input_item in inputs_dict.items():                input_name = input_item[0]                input_datum = input_item[1]                input_type = type(input_datum)  # pretty much all will be strings                input_type_name = input_type.__name__                if isinstance(input_datum, list):                    continue                default_dict[input_name] = input_type_name            if default_dict:                inputs_template_dict[node_index][meta_key] = default_dict            meta_key = "parsed"            parsed_dict: Dict = {}            # LOGGER_WF2PY.debug("item %02d , mode:%s" % (int(node_index), meta_key))            for input_item in inputs_dict.items():                input_name = input_item[0]                input_datum = input_item[1]                try:                    parsed_dict[input_name] = attempt_parse(datum=input_datum)                except (NotImplementedError, TypeError , ValueError) as excpt:  # noqa                    if ALL_NUMERIC_LIST_MSG not in excpt.args:                        LOGGER_WF2PY.exception(excpt)            if parsed_dict:                inputs_template_dict[node_index][meta_key] = parsed_dict            if inputs_template_dict[node_index] == {}:                del inputs_template_dict[node_index]        dict_text = json.dumps(inputs_template_dict, indent=2, sort_keys=True)        with open(self.input_mappings_json, "w") as input_mappings_file:            input_mappings_file.write(dict_text)    def write_source_file(self):        with open(self.python_class_file_path, "w") as class_source_file:            message = f"Writing inputs dialog python source file \"{self.python_class_file_path}\""            LOGGER_WF2PY.info(message)            class_source_file.write(DialogInputsGenerator.IMPORTS_TEXT + "\n\n")            class_source_file.write("\nclass " + self.python_class_name + "(WorkflowDialogFactory):\n\n")            class_source_file.write("    WORKFLOW_FILE = \"%s\"\n\n" % self.workflow_filename)            class_source_file.write(self.constructor_text())            class_source_file.write(self.dialog_factory_text())        self.write_dialog_config()    def write_dialog_config(self):        storage_path = self.installation_data_path.replace(".json", f"_{PersisterPetite.UUID_STR}.json")        dictionary = self._generator_instance.config        try:            LOGGER_WF2PY.info("Writing dialog config to " + storage_path)            with open(storage_path, 'w') as outfile:                sorted_keys = sorted(dictionary.keys(), key=int_or_str)                json.dump({i: dictionary[i] for i in sorted_keys}, outfile, indent=2)        except IOError as thrown:            LOGGER_WF2PY.error("Problem writing " + storage_path)            raise throwndef main() -> int:    generator_instance = DialogInputsGenerator()    generator_instance.write_source_file()    # generator_instance.write_inputs_meta_mappings()    return 0# L:\projects\hymerfania\gimp_scripts\two_nintynine\plug-ins_available\gimp_comfyui\assets\comfyui_default_workflow_api.json# L:\projects\hymerfania\gimp_scripts\two_nintynine\plug-ins_available\gimp_comfyui\assets\img2img_sdxl_0.3_workflow_api.json# L:\projects\hymerfania\gimp_scripts\two_nintynine\plug-ins_available\gimp_comfyui\assets\sytan_sdxl_1.0_workflow_api.jsonif __name__ == '__main__':    sys.exit(main())