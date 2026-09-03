import asyncio
from src.cli import run

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")