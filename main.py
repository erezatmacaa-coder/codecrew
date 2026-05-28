import sys
from masa.core import Orchestrator
from masa.agents import AGENTS

COLORS = {
    "🧠": "\033[96m", "💻": "\033[92m", "👁️": "\033[93m", "🧪": "\033[95m",
    "🐛": "\033[91m", "🚀": "\033[94m", "📖": "\033[97m", "💡": "\033[90m",
}
RESET = "\033[0m"
BOLD = "\033[1m"


def print_banner():
    print(f"\n{BOLD}{'='*50}")
    print("    C O D E C R E W")
    print("    Multi-Agent Kod Gelistirme Sistemi")
    print(f"{'='*50}{RESET}\n")


def print_agents_info():
    print(f"{BOLD}Masada kimler var?{RESET}")
    for a in AGENTS:
        print(f"  {a['emoji']} {a['name']} — {a['role']}")
    print()


def print_agent_message(agent_round):
    color = COLORS.get(agent_round.emoji, "\033[97m")
    sep = "-" * 55
    print(f"\n{color}{sep}{RESET}")
    print(f"{color}{BOLD}{agent_round.emoji} {agent_round.agent_name} ({agent_round.role}){RESET}")
    print(f"{color}{sep}{RESET}")
    print(agent_round.message)
    if agent_round.tool_calls:
        print(f"\033[90m[Kullanilan araclar: {', '.join(agent_round.tool_calls[:5])}]\033[0m")


def interactive_mode():
    print_banner()
    print_agents_info()
    orchestrator = Orchestrator()

    while True:
        try:
            task = input(f"\n{BOLD}Gorev tanimla> {RESET}")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not task:
            continue
        if task.lower() in ("exit", "quit"):
            break

        print(f"\n{BOLD} Gorev basliyor: {task}{RESET}")
        import time
        start = time.time()
        summary = orchestrator.run(task, on_message=print_agent_message)
        elapsed = time.time() - start
        print(f"\033[90m[Sure: {elapsed:.1f}s]\033[0m")
        print(summary)


def single_mode(prompt):
    print_banner()
    print(f"{BOLD} Gorev: {prompt}{RESET}\n")
    orchestrator = Orchestrator()
    import time
    start = time.time()
    summary = orchestrator.run(prompt, on_message=print_agent_message)
    elapsed = time.time() - start
    print(f"\n\033[90m[Sure: {elapsed:.1f}s]\033[0m")
    print(summary)


def main():
    if len(sys.argv) > 1:
        single_mode(" ".join(sys.argv[1:]))
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
