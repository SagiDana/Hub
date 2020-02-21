import subprocess
import pynvim
import requests
import json


@pynvim.plugin
class Gravity(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.tmp_ctags_path = "/tmp/{}.tags"
        self.server_url = 'http://localhost:1337/{}'
        self.terminal_buf_id = 0

    @pynvim.autocmd('BufEnter', pattern='*.gravity', sync=True)
    def autocmd_bufenter(self):
        """
        This function is primarily for generating and loading ctags to the
        current nvim instance to enable convenient way to use our applications
        """
        try:
            # Asking the server for installed applications
            r = requests.get(self.server_url.format('applications'))
            loaded_applications = r.json()
            for application in loaded_applications:
                ctags_path = self.tmp_ctags_path.format(application)
                self.generate_absolute_python_ctags(loaded_applications[application], ctags_path)
                self.load_ctags(ctags_path)
        except Exception as e:
            self.out("Gravity: exception ({})".format(str(e)))

    @pynvim.function('GravityFunc')
    def function_handler(self, args):
        try:
            # Extract all information we might need.
            nvim_buffer = self.nvim.current.buffer

            # Current possion
            cursor_line = self.nvim.call('line', '.')
            cursor_column = self.nvim.call('col', '.')
            quickfix = self.nvim.call('getqflist')

            # Selection
            selected_start_line = self.nvim.call('getpos',"'<")[1]
            selected_start_column = self.nvim.call('getpos',"'<")[2]
            selected_end_line = self.nvim.call('getpos',"'>")[1]
            selected_end_column = self.nvim.call('getpos',"'>")[2]

            json_to_send = {
                    'nvim_buffer': '\n'.join(nvim_buffer[:]),
                    'cursor_line': cursor_line,
                    'cursor_column': cursor_column
                    }
            r = requests.post(self.server_url.format('execute'), json=json_to_send)
            self.out(str(r.status_code))
        except Exception as e:
            self.out("Gravity: exception ({})".format(str(e)))

    @pynvim.function('GravityLaunchTerminal')
    def spawn_terminal_handler(self, args):
        try:
            command = args[0]

            # split to spawn te terminal
            self.nvim.command("split")
            # create new buffer to put the terminal in.
            self.nvim.command("enew")

            # keep track of the terminal buffer id
            self.terminal_buf_id = self.nvim.call('bufnr','%')

            # launch terminal with on_exit handler
            termopen_args = {'on_exit': 'GravityTerminalOnExit'}
            self.nvim.call('termopen', command, termopen_args)

            # enter insert mode int terminal
            self.nvim.command("normal i")
        except Exception as e:
            self.out("Gravity: exception ({})".format(str(e)))

    @pynvim.function('GravityTerminalOnExit')
    def terminal_on_exit_handler(self, args):
        job_id = args[0]
        code = args[1]
        event = args[2]
        terminal_lines = self.nvim.call('nvim_buf_get_lines', self.terminal_buf_id, 0, -1, False)

        # self.out('\n'.join(terminal_lines))
        self.nvim.command("close")

            
    def out(self, message):
        message = message.replace("\"", "\\\"")
        self.nvim.command(f"echo \"{message}\"")

    def set_quickfix_list(self, quickfix_list):
        """
        [
            {
                'filename':'',
                'lnum': '',
                'text': ''
            }
        ]
        """
        self.nvim.call('setqflist', quickfix_list)

    def modify_buffer(self, buffer_number, lines):
        self.nvim.call('nvim_buf_set_lines', buffer_number, 0, -1, 0, lines)

    def load_ctags(self, ctags_path):
        self.nvim.command(f"set tags+={ctags_path}")

    def generate_absolute_python_ctags(self, project_path, ctags_path):
        p = subprocess.Popen(
                [
                    "ctags",
                    "--python-kinds=-i",
                    "-f",
                    ctags_path,
                    "-R",
                    project_path
                ], 
                cwd="/")
        p.wait()

    def generate_absolute_ctags(self, project_path, ctags_path):
        p = subprocess.Popen(
                [
                    "ctags",
                    "-f",
                    ctags_path,
                    "-R",
                    project_path
                ], 
                cwd="/")
        p.wait()
