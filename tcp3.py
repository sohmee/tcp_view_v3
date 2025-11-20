import gi
import socket
import psutil
import random
import re 
import subprocess # Required for 'kill' and 'whois' commands

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk

class TcpView(Gtk.Window):

    # --- Helper Methods moved to the top for compatibility ---
    def make_toggle(self, label, callback):
        button = Gtk.ToggleButton(label=label)
        button.set_active(True)
        button.connect("toggled", callback)
        self.filter_box.pack_start(button, False, False, 0)
        self.update_button_style(button)
        return button

    def update_button_style(self, button):
        context = button.get_style_context()
        if button.get_active():
            context.add_class("active-button")
        else:
            context.remove_class("active-button")

    def get_color_for_process(self, name):
        if name not in self.process_colors:
            r = random.randint(100, 255)
            g = random.randint(100, 255)
            b = random.randint(100, 255)
            self.process_colors[name] = f"#{r:02x}{g:02x}{b:02x}"
        return self.process_colors[name]
    # --- End Helper Methods ---

    def __init__(self):
        super().__init__(title="Linux TcpView")
        self.set_default_size(1000, 500)

        self.active_only = True
        self.show_tcp = True
        self.show_udp = True
        self.show_ipv4 = True
        self.show_ipv6 = True
        self.process_colors = {}
        self.filter_string = ""
        self.sort_column_id = 0 
        self.sort_order = Gtk.SortType.ASCENDING

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.box)

        # CSS styling
        self.style_provider = Gtk.CssProvider()
        self.style_provider.load_from_data(b"""
            .active-button {
                background-color: #007BFF;
                color: white;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Filter buttons container
        self.filter_box = Gtk.Box(spacing=6)
        self.box.pack_start(self.filter_box, False, False, 0)

        # Initialize toggle buttons (make_toggle is defined above)
        self.active_toggle = self.make_toggle("Active Only", self.toggle_active)
        self.tcp_toggle = self.make_toggle("TCP", self.toggle_tcp)
        self.udp_toggle = self.make_toggle("UDP", self.toggle_udp)
        self.ipv4_toggle = self.make_toggle("IPv4", self.toggle_ipv4)
        self.ipv6_toggle = self.make_toggle("IPv6", self.toggle_ipv6)

        # Search Entry Field
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.filter_box.pack_end(self.search_entry, False, False, 0) 

        # --- Model Setup (Simplified using only ListStore to avoid Gtk.TreeModelFilter errors) ---
        # 8 columns: [0:Proto, 1:IP Ver, 2:LAddr, 3:RAddr, 4:Status, 5:PID, 6:Process, 7:Color]
        self.liststore = Gtk.ListStore(str, str, str, str, str, str, str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        # --- End Model Setup ---

        # Columns setup
        self.columns = ["Proto", "IP Ver", "Local Address", "Remote Address", "Status", "PID", "Process"]
        for i, title in enumerate(self.columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.connect("clicked", self.on_column_clicked, i) 
            column.set_sort_column_id(i) 
            column.add_attribute(renderer, "cell-background", 7)
            self.treeview.append_column(column)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.add(self.treeview)
        self.box.pack_start(self.scroll, True, True, 0)

        # --- Right Click Menu Setup ---
        self.context_menu = Gtk.Menu()
        
        copy_item = Gtk.MenuItem(label="Copy Connection Details")
        copy_item.connect("activate", self.on_copy_details)
        self.context_menu.append(copy_item)

        kill_item = Gtk.MenuItem(label="Kill Process (SIGKILL)")
        kill_item.connect("activate", self.on_kill_process)
        self.context_menu.append(kill_item)
        
        whois_item = Gtk.MenuItem(label="Whois Remote Address")
        whois_item.connect("activate", self.on_whois_address)
        self.context_menu.append(whois_item)

        self.context_menu.show_all()
        
        # Connect button press event to the treeview for right-click handling
        self.treeview.connect("button-press-event", self.on_treeview_button_press)
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        # --- End Right Click Menu Setup ---

        self.refresh_connections()
        GLib.timeout_add_seconds(5, self.refresh_connections)


    def on_column_clicked(self, column, column_id):
        """Manually handles column clicks for sorting."""
        if self.sort_column_id == column_id:
            self.sort_order = Gtk.SortType.DESCENDING if self.sort_order == Gtk.SortType.ASCENDING else Gtk.SortType.ASCENDING
        else:
            self.sort_column_id = column_id
            self.sort_order = Gtk.SortType.ASCENDING
        
        # Update the visual indicator
        for col in self.treeview.get_columns():
            col.set_sort_indicator(False)
        column.set_sort_indicator(True)
        column.set_sort_order(self.sort_order)
        
        self.refresh_connections() 

    # The toggle functions just call refresh_connections()
    def toggle_active(self, widget):
        self.active_only = widget.get_active()
        self.update_button_style(widget)
        self.refresh_connections() 

    def toggle_tcp(self, widget):
        self.show_tcp = widget.get_active()
        self.update_button_style(widget)
        self.refresh_connections()
    
    def toggle_udp(self, widget):
        self.show_udp = widget.get_active()
        self.update_button_style(widget)
        self.refresh_connections()
    
    def toggle_ipv4(self, widget):
        self.show_ipv4 = widget.get_active()
        self.update_button_style(widget)
        self.refresh_connections()

    def toggle_ipv6(self, widget):
        self.show_ipv6 = widget.get_active()
        self.update_button_style(widget)
        self.refresh_connections()

    def on_search_changed(self, widget):
        self.filter_string = widget.get_text().lower()
        self.refresh_connections()

    def on_treeview_button_press(self, treeview, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3: # Right click
            # Unpack the tuple returned by get_path_at_pos correctly
            path_tuple = treeview.get_path_at_pos(int(event.x), int(event.y))
            
            if path_tuple:
                path, column, x, y = path_tuple
                treeview.set_cursor(path) 
                self.context_menu.popup_at_pointer(event)
                return True 

    def get_selected_row_data(self):
        """Helper function to retrieve data from the selected row."""
        model = self.treeview.get_model()
        tree_selection = self.treeview.get_selection()
        if tree_selection.count_selected_rows() == 1:
            model, treeiter = tree_selection.get_selected()
            if treeiter:
                # Return the full list of display columns (0-6)
                return [model.get_value(treeiter, i) for i in range(7)]
        return None

    def on_copy_details(self, menu_item):
        row_data = self.get_selected_row_data()
        if row_data:
            # Format the data into a readable string
            copy_string = (
                f"Proto: {row_data[0]}, IP Ver: {row_data[1]}, "
                f"Local: {row_data[2]}, Remote: {row_data[3]}, "
                f"Status: {row_data[4]}, PID: {row_data[5]}, "
                f"Process: {row_data[6]}"
            )
            self.clipboard.set_text(copy_string, -1)
            print(f"Copied details for PID {row_data[5]} to clipboard.")

    def on_kill_process(self, menu_item):
        row_data = self.get_selected_row_data()
        if row_data:
            pid_str = row_data[5] # Index 5 is the PID column
            if pid_str and pid_str not in ('N/A', '?'):
                try:
                    # Execute system kill command (requires permissions)
                    subprocess.run(['kill', '-9', pid_str], check=True)
                    print(f"Killed process with PID {pid_str}")
                    # Refresh immediately after killing a process
                    self.refresh_connections()
                except subprocess.CalledProcessError as e:
                    print(f"Failed to kill process {pid_str}: {e}")
                except Exception as e:
                    print(f"An error occurred during kill operation: {e}")
            else:
                print("Cannot kill process: No valid PID found.")

    def on_whois_address(self, menu_item):
        row_data = self.get_selected_row_data()
        if row_data:
            remote_addr_port = row_data[3] # Index 3 is the Remote Address column
            if remote_addr_port:
                # Extract just the IP address from the address:port string
                remote_ip = remote_addr_port.split(':')[0]
                try:
                    # Execute system whois command and print output to console
                    print(f"Running whois on {remote_ip}...")
                    result = subprocess.run(['whois', remote_ip], capture_output=True, text=True, check=True)
                    print("--- Whois Results ---")
                    print(result.stdout)
                    print("---------------------")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to run whois on {remote_ip}: {e.stderr}")
                except FileNotFoundError:
                    print("Error: 'whois' command not found. Please install the whois utility (e.g., 'sudo apt install whois').")
                except Exception as e:
                    print(f"An error occurred during whois operation: {e}")
            else:
                print("No remote address available for whois lookup.")


    def refresh_connections(self):
        """Fetches, filters, sorts, and displays connections in the ListStore."""
        all_connections_data = []
        for conn in psutil.net_connections(kind='inet6') + psutil.net_connections(kind='inet'):
            proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            if not conn.laddr: continue 
            ipver = "IPv6" if ':' in conn.laddr.ip else "IPv4"
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
            
            pid_str = str(conn.pid) if conn.pid else "" 
            proc_name = "N/A"
            if conn.pid:
                try:
                    proc_name = psutil.Process(conn.pid).name()
                except (psutil.NoSuchProcess, Exception):
                    pass
            
            color = self.get_color_for_process(proc_name)
            all_connections_data.append([proto, ipver, laddr, raddr, conn.status, pid_str, proc_name, color])
        
        filtered_connections = []
        for conn in all_connections_data:
            proto, ipver, _, _, status, _, _, _ = conn
            
            # Apply Toggles
            if self.active_only and status != 'ESTABLISHED': continue
            if proto == "TCP" and not self.show_tcp: continue
            if proto == "UDP" and not self.show_udp: continue
            if ipver == "IPv4" and not self.show_ipv4: continue
            if ipver == "IPv6" and not self.show_ipv6: continue
            
            # Apply Search Filter
            if self.filter_string:
                match_found = False
                for i in range(7):
                    if self.filter_string in conn[i].lower():
                        match_found = True
                        break
                if not match_found: continue

            filtered_connections.append(conn)

        # 3. Apply Manual Sort
        reverse_sort = (self.sort_order == Gtk.SortType.DESCENDING)
        try:
            filtered_connections.sort(key=lambda x: x[self.sort_column_id], reverse=reverse_sort)
        except Exception:
            pass

        # 4. Update Gtk.ListStore
        self.liststore.clear()
        for conn in filtered_connections:
            self.liststore.append(conn)
            
        return True

win = TcpView()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
