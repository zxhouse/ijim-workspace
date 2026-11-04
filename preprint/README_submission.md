# Design Studies – pliki do zgłoszenia

| Pole w systemie | Plik |
|---|---|
| Title page with author details | `Title_page.docx` |
| Manuscript without author details | `Manuscript_anonymised.tex` (źródło; `Manuscript_anonymised.pdf` do podglądu) |
| Highlights | `Highlights.docx` |
| Figure (osobne pliki) | `Figure1.pdf` … `Figure5.pdf` (wektorowe, czcionki osadzone) |
| Declaration of competing interests | pole wyboru „I confirm…” w systemie; to samo oświadczenie jest na stronie tytułowej |

Zgodność z wytycznymi (stan na 3.10.2026):
- typ: Research Paper, limit 5000–8000 słów; tekst główny (od Introduction do Conclusion, bez
  tabel, podpisów, wzorów wystawionych i bibliografii) ma ok. 7900 słów; z tabelami i podpisami ok. 9200
- streszczenie: 248 słów (limit 250)
- słowa kluczowe: 6 (limit 1–7), bez fraz z „and”/„of”
- highlights: 5 punktów, 73–81 znaków (limit 85)
- recenzja podwójnie anonimowa: w manuskrypcie nie ma nazwisk, afiliacji, podziękowań, CRediT
  ani adresu repozytorium (jest na stronie tytułowej)
- deklaracja o AI: wymagany nagłówek i szablon Elsevier, przed bibliografią
- bibliografia: styl APA, 72 pozycje, wszystkie cytowane, z DOI
- pisownia brytyjska (-ise)
- klasa LaTeX: `elsarticle` (opcje `preprint,review,authoryear`), numeracja wierszy

Do potwierdzenia przez autorów przed wysłaniem: adres korespondencyjny, role CRediT, treść deklaracji o AI.

Poprawki techniczne (27.10.2026, na prośbę redakcji):
- `Title_page.docx`: dodane sekcje Abstract (248 słów, identyczne z manuskryptem) i Keywords (5; usunięte „evaluation”, bo formularz EM przyjmuje maks. 5)
- `abstract_for_EM.txt`: ten sam tekst streszczenia do wklejenia w pole Abstract w Editorial Manager
