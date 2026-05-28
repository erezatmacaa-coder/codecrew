from . import llm, config
from .agents import AGENTS
from .tools import get_all_tools, execute_tool
from .tools.file_ops import safe_path
import json, os, time, re


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


class ProjectState:
    def __init__(self, task):
        self.task = task
        self.files = []
        self.plan = ""
        self.status = "basladi"
        self.errors = []

    def add_file(self, path):
        if path not in self.files:
            self.files.append(path)

    def to_string(self):
        lines = [f"Gorev: {self.task}", f"Durum: {self.status}"]
        if self.plan:
            lines.append(f"\nPlan:\n{self.plan}")
        if self.files:
            lines.append(f"\nDosyalar: {', '.join(self.files)}")
        if self.errors:
            lines.append(f"\nHatalar: {'; '.join(self.errors[-3:])}")
        return "\n".join(lines)


class Orchestrator:
    def __init__(self):
        self.history = []
        self.project = None

    def _format_history(self):
        if not self.history:
            return "(Henuz bir sey soylenmedi)"
        lines = []
        for entry in self.history[-10:]:
            msg = entry.message[:120]
            lines.append(f"{entry.emoji} {entry.agent_name}: {msg}")
        return "\n".join(lines)

    def _build_agent_prompt(self, agent, project_state):
        role_prompts = {
            "Proje Lideri": "Onceki adimlari incele. Plan hazirsa devam et. Kod yazmana gerek yok.",
            "Gelistirici": "Kodu yaz. Dosya yoksa olustur. Var olani duzelt.",
            "Code Review": "Kodu oku, hata bulursan soyle. Yoksa onayla.",
            "Test Muhendisi": "Test yaz. En az bir test dosyasi olustur.",
            "Hata Avcisi": "Kodu incele. Potansiyel hatalari raporla. Calistirma (input bekleme riski var).",
            "DevOps": "Gerekli dosyalari (requirements.txt vb.) olustur.",
            "Dokumantasyon": "README varsa oku, yoksa olustur.",
            "Yaratici Fikirler": "Onceki katkilari oku. Iyilestirme onerileri sun.",
        }
        role_instruction = role_prompts.get(agent["role"], "Katkida bulun.")
        return (
            f"Sen {agent['name']}'sin, takimin {agent['role']}'i.\n\n"
            f"Kisiligin: {agent['personality']}\n\n"
            f"Takimin gorevi: {project_state.task}\n\n"
            f"Proje Durumu:\n{project_state.to_string()}\n\n"
            f"Onceki Katkilar:\n{self._format_history()}\n\n"
            f"Gorev Tanimi:\n{role_instruction}\n\n"
            f"Kurallar:\n"
            f"1. SADECE gorevinle ilgili is yap. Gereksiz dosya listeleme.\n"
            f"2. Eger arac kullanacaksan, asla text olarak yazma. Sadece arac cagrisi yap.\n"
            f"3. Eger arac kullanmayacaksan, dusunceni dogrudan yaz.\n"
            f"Ne yapacaksin?"
        )

    def _parse_text_tool_calls(self, text):
        """Parse text-based function calls in various formats"""
        calls = []
        patterns = [
            r'(?:^|\n)\s*/?function=(\w+)>(.*?)(?=\n|$)',
            r'(?:^|\n)\s*\[(\w+)\]\s*({.*?})(?=\n|$)',
            r'`(\w+)`\s*({.*?})',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                name = match.group(1)
                try:
                    args = json.loads(match.group(2))
                    calls.append((name, args))
                except:
                    pass
        return calls

    def _run_agent_once(self, agent):
        prompt = self._build_agent_prompt(agent, self.project)
        messages = [{"role": "user", "content": prompt}]
        tool_uses = []
        project_state = self.project

        try:
            response = llm.chat(messages, tools=get_all_tools())
        except Exception as e:
            return AgentRound(
                agent,
                f"[API hatasi, devam ediyorum...]",
                tool_uses,
            )

        if response.tool_calls and len(response.tool_calls) > 0:
            for tc in response.tool_calls:
                tool_uses.append(tc.function.name)
                try:
                    result = execute_tool(tc)
                    args = json.loads(tc.function.arguments)
                    if "path" in args:
                        real_path = safe_path(args["path"])
                        rel = os.path.relpath(real_path)
                        project_state.add_file(rel)
                except Exception as e:
                    project_state.errors.append(str(e))
            return AgentRound(
                agent,
                f"Araclar kullanildi: {', '.join(tool_uses)}",
                tool_uses,
            )

        content = response.content or ""
        text_calls = self._parse_text_tool_calls(content)
        if text_calls:
            for name, args in text_calls:
                tool_uses.append(name)
                try:
                    from .tools import file_ops, shell
                    if name in ("read_file", "write_file", "edit_file", "list_files"):
                        file_ops.execute(name, args)
                    elif name == "execute_command":
                        shell.execute(args)
                    if "path" in args:
                        real_path = safe_path(args["path"])
                        rel = os.path.relpath(real_path)
                        project_state.add_file(rel)
                except Exception as e:
                    project_state.errors.append(str(e))
            return AgentRound(
                agent,
                f"Araclar kullanildi: {', '.join(tool_uses)}",
                tool_uses,
            )

        return AgentRound(agent, content or "(Sessiz kaldi)", tool_uses)

    def run(self, task, on_message=None):
        self.project = ProjectState(task)
        self.history = []

        for round_idx in range(config.MAX_ROUNDS):
            for agent in sorted(AGENTS, key=lambda a: a["order"]):
                agent_round = self._run_agent_once(agent)
                self.history.append(agent_round)
                self.project.status = f"round {round_idx+1}/{config.MAX_ROUNDS}"

                if on_message:
                    on_message(agent_round)

        self.project.status = "tamamlandi"
        return self._summarize()

    def _summarize(self):
        p = self.project
        lines = [
            f"{'='*50}",
            "📋 PROJE RAPORU",
            f"{'='*50}",
            f"Gorev: {p.task}",
            f"Durum: {p.status}",
            f"Toplam {len(self.history)} katki",
        ]
        if p.files:
            lines.append("\nOlusturulan dosyalar:")
            for f in p.files:
                lines.append(f"  ✓ {f}")
        # check if files actually exist
        existing = [f for f in p.files if os.path.exists(f)]
        if existing:
            lines.append(f"\nDosyalar diskte mevcut: ✓")
        if p.errors:
            lines.append(f"\nKarsilasilan hatalar: {len(p.errors)}")
        return "\n".join(lines)
