from . import llm, config
from .agents import AGENTS
from .tools import get_all_tools, execute_tool
import json


class AgentRound:
    def __init__(self, agent, message, tool_calls=None):
        self.agent_name = agent["name"]
        self.emoji = agent["emoji"]
        self.role = agent["role"]
        self.message = message
        self.tool_calls = tool_calls or []

    def to_dict(self):
        return {
            "name": self.agent_name,
            "emoji": self.emoji,
            "role": self.role,
            "message": self.message,
        }


class Orchestrator:
    def __init__(self):
        self.history = []
        self.task = ""

    def _format_history(self):
        if not self.history:
            return "(Henüz bir şey söylenmedi)"
        lines = []
        for entry in self.history:
            lines.append(f"{entry.emoji} {entry.agent_name} ({entry.role}): {entry.message}")
        return "\n".join(lines)

    def _build_agent_prompt(self, agent):
        return (
            f"Sen {agent['name']}'sin, takımın {agent['role']}'i.\n\n"
            f"Kişiliğin: {agent['personality']}\n\n"
            f"Takımın görevi: {self.task}\n\n"
            f"Şu ana kadar söylenenler:\n{self._format_history()}\n\n"
            f"Şimdi sıra sende. Kişiliğine uygun şekilde katkıda bulun.\n"
            f"Gerekirse dosya oluşturmak, kod yazmak veya komut çalıştırmak "
            f"için araçlarını kullanabilirsin.\n"
            f"Kısa ve öz ol. Her seferinde tek bir iş yap.\n"
            f"Ne yapmak istersin?"
        )

    def _run_agent_once(self, agent):
        prompt = self._build_agent_prompt(agent)
        messages = [{"role": "user", "content": prompt}]
        tool_uses = []

        for _ in range(config.MAX_AGENT_INTERNAL):
            try:
                response = llm.chat(messages, tools=get_all_tools())
            except Exception as e:
                msg = f"[Tool çağrısı başarısız: {e}]"
                return AgentRound(agent, msg, tool_uses)

            if response.tool_calls:
                assistant_msg = {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in response.tool_calls
                    ],
                }
                messages.append(assistant_msg)

                for tc in response.tool_calls:
                    tool_uses.append(tc.function.name)
                    try:
                        result = execute_tool(tc)
                    except Exception as e:
                        result = f"[Araç hatası: {e}]"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": str(result),
                    })
            else:
                msg = response.content or "(Sessiz kaldı)"
                return AgentRound(agent, msg, tool_uses)

        return AgentRound(agent, "Çok fazla düşündüm, pas geçiyorum.", tool_uses)

    def run(self, task, on_message=None):
        self.task = task
        self.history = []

        for round_idx in range(config.MAX_ROUNDS):
            for agent in sorted(AGENTS, key=lambda a: a["order"]):
                agent_round = self._run_agent_once(agent)
                self.history.append(agent_round)

                if on_message:
                    on_message(agent_round)

        return self._summarize()

    def _summarize(self):
        summary = f"\n{'='*50}\n"
        summary += "📋 GÖREV TAMAMLANDI\n"
        summary += f"{'='*50}\n"
        summary += f"Görev: {self.task}\n"
        summary += f"Toplam {len(self.history)} katkı yapıldı.\n"

        used_files = set()
        for entry in self.history:
            for line in entry.message.lower().split("\n"):
                if "oluşturuldu" in line or "yazıldı" in line:
                    for msg in entry.message.split("\n"):
                        if msg.strip():
                            used_files.add(msg.strip())

        if used_files:
            summary += f"\nOluşturulan dosyalar:\n"
            for f in list(used_files)[:10]:
                summary += f"  • {f}\n"

        return summary
