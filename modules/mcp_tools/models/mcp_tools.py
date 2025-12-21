import os
import logging
import tempfile
import json
import ast
import socket
import subprocess
import shlex
import time
import re
from pathlib import Path
from core.orm.base import BaseModel
from core.orm.fields import Char, Text, Boolean, Many2many, Selection

_logger = logging.getLogger(__name__)

def file_exists(path: str) -> bool:
    p = Path(os.path.expandvars(path)).expanduser()
    if not p.is_file():
        return False
    return os.access(p, os.R_OK)

def mcp_control(action, pattern, workdir, log):
    if action == "start":
        cmd = f'nohup python3 {shlex.quote(os.path.join(workdir, pattern))} >> {shlex.quote(log)} 2>&1 &'
        subprocess.run(cmd, shell=True, cwd=workdir)
        time.sleep(0.3)
        out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
        pids = [int(x) for x in out.stdout.split()] if out.returncode == 0 else []
        return {"started": True, "pids": pids, "log": log}

    elif action == "find":
        out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
        pids = [int(x) for x in out.stdout.split()] if out.returncode == 0 else []
        return {"pids": pids}

    elif action == "kill":
        res = subprocess.run(["pkill", "-f", pattern])
        return {"killed": res.returncode == 0}

    else:
        raise ValueError("La acción debe ser una de: 'start', 'find', 'kill'")


class McpTools(BaseModel):
    _name = 'mcp.tools'
    _description = 'MCP Tools'
    _table = 'mcp_tools' # Explicitly setting table name to match original if needed, or default

    WORKDIR = "/home/odoo/src/mcp_temp"
    MCP_LOG = "/home/odoo/src/mcp_server.log"

    name = Char(string='Name', required=True)
    description = Text(string='Description')
    active = Boolean(string='Activado', default=False)
    
    # Many2many arguments adapted to new core: comodel_name, relation, col1, col2, string
    agent_ids = Many2many(
        comodel_name='mcp.agent',
        relation='mcp_agent_tools_rel',
        column1='tool_id',
        column2='agent_id',
        string='Used by Agents'
    )
    
    python_code = Text(string="Código Python")

    port = Char(string="Puerto", required=True)
    host = Char(string="Host", required=True, default="127.0.0.1")
    
    temp_file = Char(string="Eliminar archivo temporal")

    transport = Selection(
        selection=[
            ('sse', 'SSE'),
            # ('http', 'HTTP'),
        ],
        string="Transporte",
        required=True,
        default="sse"
    )

    def ensure_one(self):
        if len(self) != 1:
            raise ValueError("Expected singleton: %s" % self)

    def find_double_brace_values(self, s: str) -> list[str]:
        return [m.strip() for m in re.findall(r"\{\{\s*(.+?)\s*\}\}", s, flags=re.DOTALL)]

    def check_and_launch_mcp_server(self):
        """
        Validamos que el servidor esté funcionando y lo ejecutamos en caso de que no esté funcionando.
        """
        for rec in self:
            status, message = rec.tcp_port_libre(rec.port, rec.host)
            if status and rec.active: # puerto libre y estado activo
                rec.action_stop_mcp() # elimina el archivo temporal y pone active en False
                _logger.error(f"Servidor MCP detenido en {rec.host}:{rec.port}")
                rec.action_launch_mcp() # ejecutamos el servidor
                _logger.info(f"Servidor MCP reiniciado en {rec.host}:{rec.port}")
            elif not status and not rec.active: # puerto ocupado y estado inactivo
                rec.action_stop_mcp() # elimina el archivo temporal y pone active en False
                _logger.error(f"Servidor MCP detenido en {rec.host}:{rec.port}")

    def get_max_port(self):
        with self.env.cr.connection.cursor() as cur:
            cur.execute("""
                SELECT MAX((trim(port))::int)
                FROM mcp_tools
                WHERE port IS NOT NULL
                  AND trim(port) ~ '^[0-9]+$'
            """)
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else False

    def get_next_port(self, default=8000):
        max_port = self.get_max_port()
        if not max_port:
            return default
        return max_port + 1 if max_port >= default else default

    def replace_variables(self, text, variables):
        def replacer(match):
            var_name = match.group(1)
            return str(variables[var_name]) if var_name in variables else match.group(0)
        return re.sub(r'\{\{(\w+)\}\}', replacer, text)

    # Note: MCPServerHTTP needs to be imported if available, or mocked.
    # Assuming pydantic_ai is available in the env or we need to handle it.
    # Leaving it commented if import not verified, or add try/except.
    # For now, keeping as is but check dependencies.
    def get_mcp_server(self):
        self.ensure_one()
        try:
            from pydantic_ai.mcp import MCPServerHTTP
        except ImportError:
            _logger.warning("pydantic_ai not found. verify requirement.")
            return None

        if not self.agent_ids:
            raise ValueError("No hay agentes asignados al servidor, ingresa al agente y asigna la MCP Tool")
        
        url = f"http://{self.host}:{self.port}/{self.transport}"
        return MCPServerHTTP(url=url)


    def action_stop_mcp(self):
        self.ensure_one()
        if self.active:
            file_absolute_path = f"{self.WORKDIR}/{self.temp_file}"

            if len(mcp_control("find", pattern=self.temp_file, workdir=self.WORKDIR, log=self.MCP_LOG)["pids"]) > 0:
                    mcp_control("kill", pattern=self.temp_file, workdir=self.WORKDIR, log=self.MCP_LOG)

            exist = file_exists(file_absolute_path)
            if exist:
                self.delete_temp_file(file_absolute_path)
            
            # Since we cannot update self directly like self.temp_file = False in this ORM generally without 'write'
            # But in the old Odoo code, self.field = x works if it's an iterator (ActiveRecord pattern).
            # The new core BaseModel.__getattr__ reads from DB. Setting attributes on 'self' instance 
            # won't persist unless 'write' is called or we implement __setattr__.
            # The new core BaseModel does NOT appear to implement __setattr__ for write.
            # So I must use self.write().
            self.write({'temp_file': False, 'active': False})


    def action_launch_mcp(self):
        self.ensure_one()
        
        # Stop first if running
        self.action_stop_mcp()
        
        status, message = self.tcp_port_libre(self.port, self.host)
        if not status:
            try:
                current_port = int(self.port)
                old_port = current_port - 1
            except ValueError:
                current_port = 8000
                old_port = 7999
            
            status_2, message_2 = self.tcp_port_libre(old_port, self.host)
            new_port_val = old_port if status_2 else str(self.get_next_port())
            
            # update port
            self.write({'port': str(new_port_val)})
            # We need to re-read or use the new value. 
            # self.port might still be old if caching exists (not implemented in this simple core).
            # But let's assume we need to use the variable.
        
        # Re-read to be sure (or just use values)
        # Using values is safer.
        rec = self.read(['port', 'host', 'transport', 'python_code', 'name'])[0]
        
        if rec['python_code']:
            try:
                data = {
                    "port": rec['port'],
                    "host": rec['host'],
                    "transport": rec['transport'],
                }
                
                # Verify Code
                self.validate_syntax(rec['python_code'])
                self._check_name_format(rec['name'])

                file_name = self.save_str_to_temp(
                    self.replace_variables(rec['python_code'], data), 
                    suffix=rec['name'], 
                    directory=self.WORKDIR
                ).split('/')[-1]
                
                # self.temp_file = file_name
                
                mcp_control("start", pattern=file_name, workdir=self.WORKDIR, log=self.MCP_LOG)
                
                is_active = len(mcp_control("find", pattern=file_name, workdir=self.WORKDIR, log=self.MCP_LOG)["pids"]) > 0
                
                self.write({'temp_file': file_name, 'active': is_active})
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise ValueError(f"Error al iniciar el script:\n\n{e}")

    def tcp_port_libre(self, port, host="127.0.0.1", timeout=0.5) -> tuple:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                s.bind((host, int(port)))
                return (True, "Puerto libre")
            except PermissionError as e:
                _logger.error(f">>>\n\n{e}\n\n")
                return (False, "Puertos <1024 requieren root")
            except Exception as e: # OSError and others
                _logger.error(f">>>\n\n{e}\n\n")
                return (False, "EADDRINUSE u otros -> ocupado/no disponible")

    def _check_name_format(self, name):
        if name:
            if not name.endswith('.py'):
                raise ValueError('El nombre del script debe terminar con .py')
            if name.count('.') != 1:
                raise ValueError('El nombre del script debe contener solo un punto (para la extensión .py)')

    def save_str_to_temp(self, content: str, suffix=".py", directory="/home/odoo/src/mcp_temp") -> str:
        os.makedirs(directory, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8",
            dir=directory, suffix=suffix,
            delete=False
        ) as tmp:
            tmp.write(content)
            path = tmp.name
        return path

    def delete_temp_file(self, path: str) -> bool:
        _logger.error(f"path: {path}")
        if path and os.path.isfile(path):
            os.remove(path)
            return True
        return False

    def validate_syntax(self, code: str) -> str | None:
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            raise ValueError(f"SyntaxError: {e.msg} on line {e.lineno}, column {e.offset}")

    def strip_equal_fences(self, text: str, collapse_blank_lines: bool = False) -> str:
        DELIM_LINE = re.compile(r'^[ \t]*===\s*.+?\s*===\s*$', re.MULTILINE)
        s = DELIM_LINE.sub('', text)
        if collapse_blank_lines:
            s = re.sub(r'[ \t]+\r?$', '', s, flags=re.MULTILINE)
            s = re.sub(r'\n{3,}', '\n\n', s).strip('\n')
        return s

    def create(self, vals):
        # Handle default values
        if 'port' not in vals:
            vals['port'] = str(self.get_next_port())
        if 'host' not in vals:
            vals['host'] = "127.0.0.1"
        if 'transport' not in vals:
            vals['transport'] = "sse"
        if 'active' not in vals:
            vals['active'] = False
            
        # Validate constraints
        if 'name' in vals:
             # Check unique name
             existing = self.search([('name', '=', vals['name'])])
             if existing:
                 raise ValueError("El nombre del script debe ser único.")
             self._check_name_format(vals['name'])
             
        if 'port' in vals:
             # Check unique port
             existing = self.search([('port', '=', vals['port'])])
             if existing:
                 raise ValueError("El puerto del script debe ser único.")
             if not vals['port'].isdigit():
                 raise ValueError("Port must contain only digits.")

        if 'python_code' in vals and vals['python_code']:
            self.validate_syntax(vals['python_code'])

        return super().create(vals)

    def write(self, vals):
        # Validate constraints if fields are being written
        for rec in self:
            if 'name' in vals:
                if vals['name'] != rec.name:
                     existing = self.search([('name', '=', vals['name']), ('id', '!=', rec.id)])
                     if existing:
                         raise ValueError("El nombre del script debe ser único.")
                self._check_name_format(vals['name'])
            
            if 'port' in vals:
                start_port = vals['port']
                if start_port != rec.port:
                     existing = self.search([('port', '=', vals['port']), ('id', '!=', rec.id)])
                     if existing:
                         raise ValueError("El puerto del script debe ser único.")
                if not str(vals['port']).isdigit():
                     raise ValueError("Port must contain only digits.")

            if 'python_code' in vals and vals['python_code']:
                 self.validate_syntax(vals['python_code'])

        return super().write(vals)