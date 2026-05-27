import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from masa.core import Orchestrator
from masa.agents import AGENTS

COLORS = {
    "🧠": "\033[96m",   # Alp - cyan
    "💻": "\033[92m",   # Cem - green
    "👁️": "\033[93m",   # Rusty - yellow
    "🧪": "\033[95m",   # Testo - magenta
    "🐛": "\033[91m",   # Bug - red
    "🚀": "\033[94m",   # Devina - blue
    "📖": "\033[97m",   # Doc - white
    "💡": "\033[90m",   # Ideator - gray
}
RESET = "\033[0m"
BOLD = "\033[1m"


def print_banner():
    print(f"""
{BOLD}{'='*50}
    C O D E C R E W
    Multi-Agent Kod Gelistirme Sistemi
{'='*50}{RESET}
""")


def print_agent_message(agent_round):
    color = COLORS.get(agent_round.emoji, "\033[97m")
    sep = "-" * 55

    print(f"\n{color}{sep}{RESET}")
    print(f"{color}{BOLD}{agent_round.emoji} {agent_round.agent_name} ({agent_round.role}){RESET}")
    print(f"{color}{sep}{RESET}")
    print(agent_round.message)

    if agent_round.tool_calls:
        tools = ", ".join(agent_round.tool_calls)
        print(f"\033[90m[Kullanılan araçlar: {tools}]\033[0m")


def print_agents_info():
    print(f"\n{BOLD}Masada kimler var?{RESET}")
    for a in AGENTS:
        print(f"  {a['emoji']} {a['name']} — {a['role']}")
    print()


def interactive_mode():
    print_banner()
    print_agents_info()

    orchestrator = Orchestrator()

    while True:
        try:
            task = input(f"\n{BOLD}Görev tanımla{'>' if sys.stdin.isatty() else ''} {RESET}")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not task:
            continue
        if task.lower() in ("exit", "quit"):
            break

        print(f"\n{BOLD}🎯 Görev başlıyor: {task}{RESET}")
        import time
        start = time.time()
        summary = orchestrator.run(task, on_message=print_agent_message)
        elapsed = time.time() - start
        print(f"\033[90m[Süre: {elapsed:.1f}s]\033[0m")
        print(summary)


def single_mode(prompt):
    print_banner()
    print(f"{BOLD}🎯 Görev: {prompt}{RESET}\n")
    orchestrator = Orchestrator()
    import time
    start = time.time()
    summary = orchestrator.run(prompt, on_message=print_agent_message)
    elapsed = time.time() - start
    print(f"\n\033[90m[Süre: {elapsed:.1f}s]\033[0m")
    print(summary)


def main():
    if len(sys.argv) > 1:
        single_mode(" ".join(sys.argv[1:]))
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
