"""Forward the former module command without changing its output."""
from wiiready.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
