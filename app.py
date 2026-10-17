"""Sports engines dashboard: the parlay builder and the NFL engine's picks.

    streamlit run app.py

Read-only. Both pages read the picks the engines save in results/ (or SPORTS_RESULTS_DIR), never change a pick, a rule
or a team note, and never use a betting line (CLAUDE.md rules 1-6). The engines themselves (cfb/, nfl_cfbmethod/) are
not run or imported here.
"""

from __future__ import annotations

PAGES = [
    # (page file, title, icon, url path); the first one opens by default
    ("parlay_app/page.py", "Parlay builder", ":material/stacks:", "parlays"),
    ("nfl_ui/page.py", "NFL engine", ":material/sports_football:", "nfl"),
]


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Sports Engines", page_icon=":material/sports_football:", layout="wide")
    pages = [
        st.Page(path, title=title, icon=icon, url_path=url, default=n == 0)
        for n, (path, title, icon, url) in enumerate(PAGES)
    ]
    st.navigation(pages, position="top").run()


if __name__ == "__main__":
    main()
