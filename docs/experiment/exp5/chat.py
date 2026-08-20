"""CLI REPL untuk AI Manager cabang Finance (eksperimen 5).

Menjalankan AI Manager (primary) yang mendelegasikan pertanyaan data ke
sub-agent spesialis via tool-calling. Menyimpan riwayat percakapan dalam
satu sesi dan mengirim seluruh riwayat ke model setiap turn.

Cara pakai:
    docs/experiment/exp5/.venv/Scripts/python.exe docs/experiment/exp5/chat.py

Perintah:
    /exit   keluar dari REPL
    /reset  hapus riwayat percakapan sesi ini
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from langchain_core.messages import HumanMessage, AIMessage

from primary import build_manager

WELCOME = """AI Manager cabang Finance (AIOS) — eksperimen 5.

AI Manager mendelegasikan pertanyaan data ke sub-agent spesialis
(Finance Staff, Financial Analyst, Budgeting Staff, Treasurer, CFO).

Ketik pesan untuk mengobrol. Ketik /exit untuk keluar, /reset untuk
mengosongkan riwayat.
"""


def main() -> None:
    print(WELCOME)
    manager = build_manager()
    history: list = []

    while True:
        try:
            user_input = input("Kamu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSampai jumpa!")
            break

        if not user_input:
            continue

        if user_input.lower() == "/exit":
            print("Sampai jumpa!")
            break

        if user_input.lower() == "/reset":
            history = []
            print("[riwayat direset]")
            continue

        history.append(HumanMessage(content=user_input))

        try:
            result = manager.invoke({"messages": history})
            reply = result["messages"][-1].content
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {exc}")
            history.pop()
            continue

        print(f"\nAI Manager Finance: {reply}\n")
        history.append(AIMessage(content=reply))


if __name__ == "__main__":
    sys.exit(main())