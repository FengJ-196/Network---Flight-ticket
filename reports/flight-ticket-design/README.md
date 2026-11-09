# Flight Ticket Booking: professor presentation

The presentation uses the supplied **blue HUST Beamer template, 16:9**, with its original theme and background assets. The original sample in `../11-05-progress-report/` is preserved.

- `flight-ticket-design.pdf`: presentation for display.
- `flight-ticket-design.tex`: editable slide content, TikZ diagrams and hidden speaker notes.
- `speaker-notes.md`: speaking guidance and per-slide timing, approximately **25:15**.
- `build.ps1`: compile on this laptop using the portable Tectonic compiler or Tectonic on PATH.
- `beamerthemeHUST.sty` and `images/`: copied template dependencies.

Present slides **1–20**, then use **Questions** on slide 20 to jump to the final thank-you slide, **30**. Slides **21–29** are optional reference slides for questions. The talk covers the four required areas: introduction, architecture, functionality and protocol design. Protocol messages, state machines and processing receive most of the time.

| Pages | Placement and purpose |
|---|---|
| 1 | Title |
| 2–3 | Application introduction, requirements and scope |
| 4–6 | Architecture, functionality and search example |
| 7–11 | Transport, message formats, operation inventory and state machines |
| 12–16 | Purchase, email, ticket management and notification sequences |
| 17–19 | Processing, logging and recovery |
| 20 | Validation plan and transition to questions |
| 21–29 | Optional appendix details and sources |
| 30 | Thank you, final slide |

Content follows the current files in `../../Design-Review/` and the original requirements in `../../Docs/`. Real email is the only ticket-delivery channel. Cancellation uses the confirmed simple full-fare refund rules and needs no stored quote. The separate change-flight fee/quote remains proposed. This is a design presentation; implementation and runtime demonstration remain future work.

## Build

From the repository root:

```powershell
.\reports\flight-ticket-design\build.ps1
```

After the required packages have been cached:

```powershell
.\reports\flight-ticket-design\build.ps1 -Offline
```

The compiler is kept in `../.build-tools/tectonic/`. Its package cache is in `../.build-tools/latex-cache/`. No system-wide TeX installation or PATH change is required. The first build needs network access. If sharing only this report folder, install Tectonic on the recipient laptop or use a complete TeX distribution with Beamer, TikZ, Latin Modern and Vietnamese support.

Change `\author`, `\institute` and the date in the LaTeX source if team details or the presentation date change. The generic author identifies the project because no flight-project team roster was supplied.

## Laptop compilation check

Checked on 6 November 2026. No existing `pdflatex`, `xelatex`, `lualatex`, `latexmk` or `tectonic` command was on PATH. The report now builds with the project-local **Tectonic 0.17.0** executable. An offline rebuild with cached packages succeeded. The resulting PDF contains 30 slides in 16:9 format. The build script supplies a local Fontconfig configuration and cache for Windows.
