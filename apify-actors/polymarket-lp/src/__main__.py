"""Entry point for `python -m src` inside the Actor container."""
import asyncio

from .main import main

if __name__ == "__main__":
    asyncio.run(main())
