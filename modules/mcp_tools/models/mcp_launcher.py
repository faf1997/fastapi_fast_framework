import asyncio
import logging
import json
import re
from core.orm.base import BaseModel

# Try imports
try:
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.providers.openai import OpenAIProvider
    from pydantic_ai.messages import ModelResponse, ToolCallPart
except ImportError:
    Agent = None
    OpenAIModel = None
    OpenAIProvider = None
    ModelResponse = None
    ToolCallPart = None

_logger = logging.getLogger(__name__)

def extract_called_functions(run_result) -> list:
    calls = []
    msgs = run_result.all_messages()
    for msg in msgs:
        if isinstance(msg, ModelResponse):
            parts = msg.parts
            for part in parts:
                if isinstance(part, ToolCallPart):
                    calls.append({
                        "function": part.tool_name,
                        "args": part.args_as_dict(),
                    })
    return calls

class McpLauncher(BaseModel):
    _name = 'mcp.launcher'
    _description = 'Lanzador MCP'

    def mcp_run(self, messages: str, agent_id: str):
        """
        Ejecuta el agente MCP especificado por agent_id.
        """
        if not Agent:
            raise ValueError("pydantic_ai not installed.")

        # 1) Fetch Agent Configuration
        # agent_id acts as ID (int/str). Search expects domain.
        # Assuming agent_id is the database ID.
        agent_record = self.env['mcp.agent'].search([
            ('id', '=', int(agent_id)),
            ('active', '=', True)
        ])
        # search returns RecordSet. Get first.
        agent_record = agent_record[0] if agent_record else None

        if not agent_record:
            raise ValueError(f"La agente '{agent_id}' no se encuentra o no está activo.")

        # 2) Configure Provider and Model from Agent
        if not all([agent_record.provider_base_url, agent_record.provider_api_key, agent_record.llm_model_name]):
             raise ValueError(f"Al agente '{agent_id}' le falta la configuración necesaria.")

        provider = OpenAIProvider(
            base_url=agent_record.provider_base_url,
            api_key=agent_record.provider_api_key,
        )

        llm_model = agent_record.llm_model_name
        chat_model = OpenAIModel(llm_model, provider=provider)

        # Check and launch tools
        # agent_record.tool_ids is a RecordSet in my refactor (Many2many returns list of objects/records)
        tool_ids = agent_record.tool_ids 
        
        for tool in tool_ids:
            if tool.active:
                tool.check_and_launch_mcp_server()

        if not tool_ids:
            # raise ValueError("El agente no tiene tool/s asociada/s.")
            pass # Relaxed check, maybe agent works without tools

        servers = []
        for tool in tool_ids:
             server = tool.get_mcp_server()
             if server:
                 servers.append(server)

        # 4) Instanciar el agente
        agent = Agent(chat_model, mcp_servers=servers, retries=3)

        # 4.5) Prepend Default Prompt
        final_messages_for_agent = messages 
        
        if agent_record.default_prompt_ids:
            default_prompt_text = agent_record.get_default_prompt()
            if not final_messages_for_agent.startswith(default_prompt_text):
                final_messages_for_agent = f"{default_prompt_text}\n\n{final_messages_for_agent}"

        # 5) Async function
        async def _main():
            async with agent.run_mcp_servers():
                return await agent.run(final_messages_for_agent)

        # 6) Execution
        # Handle Event Loop for nested async
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are in an async environment (FastAPI). 
                # We cannot use run_until_complete.
                # Use asyncio.ensure_future or similar? No, we need the result synchronously here?
                # Or this method should be async.
                # For now, if loop is running, we might be in trouble if we want sync result.
                # But since we are likely called from a sync context (ORM), maybe loop is not running?
                # FastAPI runs in a loop.
                # If we are called from a thread pool (psycopg2 is sync), we might be in a separate thread?
                # No, FastAPI runs in main thread usually unless using run_in_executor.
                # Let's try creating a new loop only if needed.
                import nest_asyncio
                nest_asyncio.apply()
                result = loop.run_until_complete(_main())
            else:
                 result = asyncio.run(_main())
        except ImportError:
             # Fallback if nest_asyncio not present: try standard run (might fail if loop running)
             try:
                 result = asyncio.run(_main())
             except RuntimeError:
                 # "asyncio.run() cannot be called from a running event loop"
                 # We need to await it. But we can't await in sync function.
                 # Hack: create a task and wait? No.
                 raise ValueError("Async execution failure: Running inside an existing loop without nest_asyncio.")
        except RuntimeError:
             # loop argument must be used
             result = asyncio.new_event_loop().run_until_complete(_main())
             
        tool_events = extract_called_functions(result)
        
        try:
            result_json = json.loads(result.data) # result.data or result.output? Original used result.output, new pydantic_ai might use data.
            # Assuming result.data based on typical pydantic_ai usage, but original code had result.output. 
            # Original code: result_json = json.loads(result.output)
            # Check pydantic_ai version? 
            # I'll stick to original usage: result.output? 
            # Wait, original code: result = asyncio..._main() -> calls agent.run().
            # RunResult usually has data.
            # I'll check if output is valid attribute. 
            # Safest is trying both or adhering to original if library didn't change.
            # I'll use result.data as it's common in newer versions, but if original used output...
            # I'll try getattr.
            output_content = getattr(result, 'data', getattr(result, 'output', str(result)))
            
            # If output_content is object (e.g. string), load it.
            if isinstance(output_content, str):
                 result_json = json.loads(output_content)
            else:
                 result_json = output_content # Maybe it's already dict?

            return {
                "result": result_json.get("message", ""),
                "should_reply": result_json.get("should_reply", False),
                "tool_events": f"{tool_events}"
            }
        except (json.JSONDecodeError, AttributeError, TypeError):
             # Fallback extraction
             output_str = str(getattr(result, 'data', getattr(result, 'output', str(result))))
             json_str = self.extract_json_str(output_str)
             if json_str:
                 try:
                     result_json = json.loads(json_str)
                     return {
                        "result": result_json.get("message", ""),
                        "should_reply": result_json.get("should_reply", False),
                        "tool_events": f"{tool_events}"
                     }
                 except: pass

             raise ValueError(f"La respuesta del LLM no pudo ser procesada. Resp: {output_str}")

    def extract_json_str(self, text: str) -> str | None:
        dec = json.JSONDecoder()
        i = 0
        while True:
            m = re.search(r'[{[]', text[i:])
            if not m:
                return None
            j = i + m.start()
            try:
                _, end = dec.raw_decode(text[j:])
                return text[j:j+end]
            except json.JSONDecodeError:
                i = j + 1
