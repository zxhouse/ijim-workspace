# IJIM – lista kontrolna zgłoszenia (wg Guide for Authors)

Typ artykułu: **Research Article** (design science + evaluation in a validated testbed).

## Pliki do wgrania w Editorial Manager

| Pole w systemie | Plik |
|---|---|
| Title page (z danymi autorów, podziękowaniami, deklaracjami) | `Title_page.docx` |
| Manuscript (anonimowy, źródło LaTeX) | `Manuscript_anonymised.tex` (+ podgląd `Manuscript_anonymised.pdf`) |
| Figures (osobne pliki, numerowane wg kolejności w tekście) | `Figure_1.pdf` … `Figure_14.pdf` (wektorowe, czcionki osadzone; mapa: `figure_map.txt`) |
| Highlights (plik edytowalny, „highlights” w nazwie) | `Highlights.docx` (5 punktów, 70–77 znaków) |
| Graphical abstract (zalecany) | `Graphical_abstract.pdf` (13,1 cm; PNG 1550 px przy 300 dpi) |
| Vitae (≤100 słów na autora, edytowalne) | `Vitae.docx` – **szablon do uzupełnienia** |
| Declaration of interest | generowana w narzędziu deklaracji systemu (opcja „I have nothing to declare”) – tekst jest też na stronie tytułowej |

`Manuscript_with_authors.tex/.pdf` – wersja jawna, do archiwum / na etap po akceptacji; **nie wgrywać jako manuskryptu**.

## Zgodność z wytycznymi

- [x] Podwójnie anonimowa recenzja: w manuskrypcie brak nazwisk, afiliacji, podziękowań, CRediT, linku do repozytorium; autocytowanie preprintu i zbioru danych jako „Anonymous (2026a/b)”; metadane PDF bez autora. Sprawdzone automatycznie (0 trafień nazwisk/afiliacji).
- [x] Abstrakt: 243 słowa (limit 250), bez cytowań, z istotnością statystyczną, skróty objaśnione.
- [x] Słowa kluczowe: 6 (limit 1–7), bez „and/of”.
- [x] Highlights: 5 punktów, ≤85 znaków, osobny plik.
- [x] Numerowane sekcje i podsekcje; odwołania przez numery.
- [x] Wzory jako tekst LaTeX.
- [x] Tabele jako tekst, bez pionowych linii i cieniowania, przypisy pod tabelą, wszystkie cytowane; mieszczą się w marginesach (0 przepełnień w tabelach).
- [x] Rysunki: wszystkie cytowane, numerowane wg kolejności, osobne pliki wektorowe z osadzonymi czcionkami; podpisy z opisem.
- [x] GenAI: sekcja „Declaration of generative AI…” przed bibliografią + adnotacja w **każdym** podpisie rysunku (wymóg polityki Elsevier dla grafik).
- [x] Styl APA 7: autor–rok, lista alfabetyczna, DOI w formie `https://doi.org/…`; preprint oznaczony „[Preprint]. arXiv” z DOI 10.48550/arXiv.2611.03034; oprogramowanie (SimPy) jako [Computer software]; dane jako „[dataset]”.
- [x] Open Data (Option C): kod, skrypty i surowe wyniki w repozytorium, cytowane w tekście i w bibliografii; Research Data Availability Statement na stronie tytułowej i w manuskrypcie.
- [x] CRediT, funding, competing interests – na stronie tytułowej (w wersji anonimowej usunięte).
- [x] Pisownia brytyjska konsekwentnie (-ise, -our); nazwy ról CRediT („Conceptualization”) zgodnie z taksonomią.
- [x] Format: LaTeX (`elsarticle`), jedna kolumna, numeracja wierszy.

## Do zrobienia przez autorów przed wysłaniem

1. **Repozytorium danych z DOI.** Opcja C wymaga „relevant data repository”. GitHub nie nadaje DOI – zalecam zdeponować wydanie repozytorium w **Zenodo** (integracja z GitHubem, 1 klik) lub Mendeley Data i podmienić URL na DOI we wpisie `dataset2026` (`refs.tex` i strona tytułowa). Repozytorium `zxhouse/ijim-workspace` musi być publiczne.
2. **Bibliografia – weryfikacja ręczna** (wytyczne: „every reference must correspond to a real source”; AI może się mylić). Wszystkie pozycje to istniejące prace, ale DOI i strony wpisano bez dostępu do baz – sprawdzić w Scopus/Crossref, szczególnie: Boussioux et al. 2024, Koning et al. 2022 (brak DOI), Dell'Acqua et al. 2023, Girotra et al. 2023, Zheng et al. 2023.
3. **APA 7 – Dwivedi et al. (2021, 2023)**: APA wymaga do 20 nazwisk autorów w bibliografii; obecnie „et al.” – uzupełnić listy autorów z ScienceDirect.
4. **CRediT** – role Eweliny Nycz i Patryka Organiściaka są propozycją; potwierdzić. Kolejność autorów w systemie = kolejność na stronie tytułowej.
5. **Afiliacje** – sprawdzić pełne nazwy i adresy (ew. wydział/katedra E. Nycz); adres PRz przyjęto: al. Powstańców Warszawy 12, 35-959 Rzeszów.
6. **Vitae** – uzupełnić `Vitae.docx`.
7. **Preprint**: tekst cytuje preprint (Kuraś et al., 2026) z innym składem autorów – to dopuszczalne; w systemie zaznaczyć, że prace nie są tym samym manuskryptem (różny cel, metoda i wyniki).
8. Uwaga redakcyjna: Tabela 5 częściowo powiela Rys. 8 (wytyczne: „use tables sparingly”) – zostawiono, bo podaje testy istotności i efekty, których nie ma na rysunku; można ją przenieść do Supplementary material, jeśli redakcja zgłosi.
