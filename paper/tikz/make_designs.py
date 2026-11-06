"""Writes the experiment-design schematics fig_d<k>.tex (E3 is fig_d3.tex, written by hand).

Run from any directory; then compile each with pdflatex and copy to
../figures/fig_design_e<k>.pdf."""
import os
OUT = os.path.dirname(os.path.abspath(__file__))
PRE = r"""\documentclass[tikz,border=3pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{amsmath}
\usepackage{sansmath}
\input{icons.tex}
\input{expdesign.tex}
\begin{document}
\begin{tikzpicture}
"""
POST = r"""
\end{tikzpicture}
\end{document}
"""
F = {}

# ------------------------------------------------------------------ E1
F["d1"] = r"""
\expgrid{4.8}{Configurations}{Two measurements}{Runs}{Measured}{Analysis}
\node[dev, anchor=west] at (\cA+0.1,-1.0) {\devlandref};
\node[stxt, anchor=west, text width=1.8cm] at (\cA+1.25,-1.0) {\textbf{REF service}\\4,096 configs};
\node[stxt, text width=2.9cm] at (\cA+0.12,-1.6) {141 drawn by utilisation of the busiest tier:};
\foreach \t/\c/\y in {{below 85\,\%: 90}/devgreen/-2.5, {85--97\,\%: 30}/devamber/-2.95, {97\,\% and over: 20}/devred/-3.4}{\node[chip=\c, text width=2.2cm] at (\cA+0.15,\y) {\t};}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.85) {+ the optimum; 6 configs spanning $U$ for noise};
% (2) lane A: emulation
\node[dev] (ph) at (\cB+0.35,-1.2) {\devphone};
\node[dev] (lp) at (\cB+1.0,-1.25) {\devlaptop};
\node[dev] (rk) at (\cB+2.1,-1.25) {\devrack};
\draw[flow] (lp.east) -- (rk.west);
\node[stxt, anchor=west, text width=2.3cm] at (\cB+2.8,-1.2) {\textbf{(a) emulation}: SimPy, 6,000 sessions ($\approx$3 min)};
% lane B: analytic model
\node[box, font=\scriptsize\sffamily\sansmath, minimum height=6mm] (an) at (\cB+1.3,-2.5) {Erlang-C,\\M/M/$c$ per tier};
\node[stxt, anchor=west, text width=2.3cm] at (\cB+2.8,-2.5) {\textbf{(b) analytic model}: steady state, ground truth};
% lane C: noise
\foreach \n/\s in {0/1.6,1/2.2,2/3.0,3/4.2}{\node[tst=devfill, minimum size=\s mm] at (\cB+0.35+\n*0.55,-3.85) {};}
\node[stxt, anchor=west, text width=2.3cm] at (\cB+2.8,-3.85) {\textbf{(c) noise}: 4 sizes, 500 to 4,000 sessions; 20 replications; emulator vs sampler};
\draw[devline!40, dashed] (\cB+0.1,-1.95) -- (\cB+5.1,-1.95);
\draw[devline!40, dashed] (\cB+0.1,-3.1) -- (\cB+5.1,-3.1);
% (3)
\node[dev, anchor=north] at (\cC+1.3,-0.7) {\devserver[devpurple]};
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {(a)+(b): 141 emulated experiments\\[3pt](c): 6 configs $\times$ 4 sizes $\times$ 20 = 480 replications\\[3pt]\textbf{621 runs}};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {conversion rate\\p95 page time\\utility $U$\\[3pt]s.d.\ of a test result at each size $n$};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Correlation and mean difference by stratum\\[4pt]model-error s.d.\ net of measurement noise\\[4pt]log variance ratio emulator\,/\,sampler};
"""

# ------------------------------------------------------------------ E2
F["d2"] = r"""
\expgrid{4.5}{Landscapes \& runs}{Policies \& horizon}{Programme}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{REF, 1 inst.}{300 runs}
\landrow{-1.95}{\devlandsvc}{SVC, 30 inst.}{8 runs each}
\landrow{-2.9}{\devlandrug}{RUG, 20 inst.}{8 runs each}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.45) {long runs (loop): REF 100; 10 SVC + 10 RUG inst.\ $\times$ 6};
% (2) chips + horizon
\node[chip=devacc, text width=1.5cm] at (\cB+0.12,-1.0) {Design-thinking loop};
\node[chip=devgreen, text width=1.5cm] at (\cB+0.12,-1.7) {Evidence ledger};
\node[stxt, text width=1.4cm] at (\cB+0.12,-2.15) {400 tests of 2,000 sessions, checkpoint every 25\\[3pt]loop also to 3,200 tests};
% decomposition on a scaled axis (loop, REF, 400 tests): y = (v-84)/16*2.6 - 3.75
\begin{scope}[shift={(\cB+2.25,-4.05)}]
  \draw[devline, -{Stealth[length=3pt]}] (0,0) -- (0,2.95);
  \node[stxt, anchor=south, rotate=90, inner sep=1pt] at (-0.36,1.3) {utility, \% of $U^*$};
  \foreach \v in {84,88,92,96,100}{\pgfmathsetmacro{\yy}{(\v-84)/16*2.6}\draw[devline] (0,\yy) -- (-0.07,\yy) node[stxt, anchor=east, inner sep=1pt] {\v};}
  \foreach \v/\t/\c in {97.4/found/devacc, 93.7/shipped/devgreen!60!black, 99.8/believed/devpurple}{%
    \pgfmathsetmacro{\yy}{(\v-84)/16*2.6}
    \draw[\c, line width=1.1pt] (0.05,\yy) -- (0.45,\yy);}
  \node[stxt, anchor=west, text=devacc] at (0.45,{(97.4-84)/16*2.6}) {found 97.4};
  \node[stxt, anchor=west, text=devgreen!60!black] at (0.45,{(93.7-84)/16*2.6}) {shipped 93.7};
  \node[stxt, anchor=west, text=devpurple] at (0.45,{(99.8-84)/16*2.6+0.06}) {believed 99.8};
  \draw[decorate, decoration={brace, amplitude=2pt, mirror}, devline] (1.8,{(93.7-84)/16*2.6}) -- (1.8,{(97.4-84)/16*2.6}) node[midway, right=2pt, stxt, align=left, inner sep=0pt] {cost of\\choosing};
\end{scope}
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt] at (\cC+0.12,-1.85) {loop};
\foreach \k in {0,...,4}{\node[tst=\ifnum\k<1 devacc!35\else white\fi] at (\cC+1.0+\k*0.29,-1.95) {};}
\node[stxt] at (\cC+0.12,-2.3) {ledger};
\foreach \k in {0,...,4}{\node[tst=\ifnum\k<3 devacc!35\else white\fi] at (\cC+1.0+\k*0.29,-2.4) {};}
\node[stxt, text width=2.4cm] at (\cC+0.12,-2.8) {\tikz\node[tst=devacc!35,minimum size=2mm]{}; new variant\\\tikz\node[tst,minimum size=2mm]{}; re-test\\[3pt]5 tests per round};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {shipped, found, believed\\[3pt]is the favourite / best tested a local optimum? (all 78 variants within two capabilities enumerated)};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Means with 95\,\% $t$-intervals\\[4pt]families: instance as unit\\[4pt]ledger $-$ loop: paired Wilcoxon test};
"""

# ------------------------------------------------------------------ E4
F["d4"] = r"""
\expgrid{4.5}{Landscapes \& runs}{Traffic split \& allocation}{Programme}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{REF, 1 inst.}{150 runs}
\landrow{-1.95}{\devlandsvc}{SVC, 30 inst.}{5 runs each}
\landrow{-2.9}{\devlandrug}{RUG, 20 inst.}{5 runs each}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.45) {per cell of 3 sizes $\times$ 6 allocations};
% (2) equal traffic, three test sizes
\node[stxt, text width=5.0cm] at (\cB+0.12,-0.72) {800,000 sessions per run, cut into tests of three sizes:};
\foreach \row/\k/\lab in {0/16/{1,600 tests of 500}, 1/4/{400 tests of 2,000}, 2/1/{100 tests of 8,000}}{%
  \pgfmathsetmacro{\w}{2.4/\k}
  \foreach \j in {1,...,\k}{\draw[devline, line width=0.35pt, fill=devacc!18] ({\cB+0.15+(\j-1)*\w},{-1.3-\row*0.45}) rectangle ++(\w,-0.3);}
  \node[stxt, anchor=west] at (\cB+2.65,{-1.45-\row*0.45}) {\lab};}
\node[stxt, text width=5.0cm] at (\cB+0.12,-2.75) {each bar: $\tfrac{1}{100}$ of the run's traffic};
\node[stxt, font=\scriptsize\sffamily\bfseries] at (\cB+0.12,-3.15) {new configurations per round of 5 tests:};
\foreach \k in {0,...,4}{\node[tst=\ifnum\k<3 devacc!35\else white\fi] at (\cB+0.3+\k*0.29,-3.75) {};}
\node[stxt, text width=3.3cm] at (\cB+1.75,-3.45) {shown: $k_{\text{new}}=3$\\levels: $\tfrac12$, 1, 2, 3, 4, 5\\($\tfrac12$: one every second round)};
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {design-thinking loop without rotating re-test\\[3pt]re-tests go to the leaders\\[3pt]ship when the traffic is spent};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {shipped $U(\hat x)/U^*$ after 800,000 sessions};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Best allocation per class and size\\[4pt]each allocation vs the best: paired difference, 95\,\% CI\\[4pt]families: instance as unit};
"""

# ------------------------------------------------------------------ E5
F["d5"] = r"""
\expgrid{4.5}{Landscapes \& runs}{Generative ideation}{Programme}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{REF, 1 inst.}{60 runs}
\landrow{-1.95}{\devlandsvc}{SVC, 30 inst.}{3 runs each}
\landrow{-2.9}{\devlandrug}{RUG, 20 inst.}{3 runs each}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.45) {per cell of the 45-cell factorial};
% (2)
\node[dev] (llm) at (\cB+0.65,-1.35) {\devcloud[devpurple!12]};
\node[devlabel, font=\scriptsize\sffamily] at (llm) {LLM};
\node[stxt, anchor=north, align=center] at (\cB+0.65,-1.85) {$V$ ideas\\per round};
\begin{scope}[shift={(\cB+1.55,-0.95)}]
  \foreach \c in {1,2,5,7}{\fill[devpurple!25] ({\c*0.19-0.095},0.13) rectangle ({\c*0.19+0.095},-1.2);}
  \foreach \r/\bits in {0/{0,1,0,0,0,1,0,0,0,0,0,0},1/{0,1,1,0,0,0,0,0,0,0,0,0},2/{0,0,0,0,0,1,0,1,0,0,0,0},3/{0,0,0,0,0,0,0,1,0,0,1,0},4/{0,1,0,0,0,0,0,0,0,0,0,0}}{%
    \foreach \b [count=\c from 0] in \bits{%
      \ifnum\b=1 \node[tst=devacc!70, minimum size=1.8mm] at ({\c*0.19},{-\r*0.26}) {};\else \node[tst, minimum size=1.8mm] at ({\c*0.19},{-\r*0.26}) {};\fi}}
  \node[stxt, anchor=north west] at (-0.12,-1.25) {ideas $\times$ 12 flags; shaded: favoured};
\end{scope}
\node[box, font=\scriptsize\sffamily\sansmath, minimum height=6mm, text width=1.0cm] (scr) at (\cB+4.6,-1.45) {screen\\validity $\rho$};
\draw[flow] (llm.east) -- (\cB+1.43,-1.35);
\draw[flow] (\cB+3.75,-1.45) -- (scr.west);
\node[stxt, text width=5.0cm] at (\cB+0.12,-2.75) {$\rho\in\{0,.25,.5,.75,.9\}$\quad $V\in\{1,5,20\}$\\homogenisation $h\in\{0,.5,.9\}$: share of ideas confined to 4 favoured capabilities\\[2pt]$5\times3\times3=45$ cells};
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {evidence ledger builds the 3 best-screened ideas per round\\[3pt]400 tests of 2,000 sessions};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {shipped $U(\hat x)/U^*$ after 100 and 400 tests};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Balanced ANOVA on $V\in\{5,20\}$: partial $\eta^2$\\[4pt]families: instance-level cell means\\[4pt]$V=1$ cannot fill 3 builds: not interpreted};
"""

# ------------------------------------------------------------------ E6
F["d6"] = r"""
\expgrid{4.5}{Landscapes \& runs}{Where bias enters}{Programme}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{REF, 1 inst.}{120 runs}
\landrow{-1.95}{\devlandsvc}{SVC, 30 inst.}{4 runs each}
\landrow{-2.9}{\devlandrug}{RUG, 20 inst.}{4 runs each}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.45) {per cell of 6 bias conditions $\times$ 7 levels};
% (2)
\node[dev] (u) at (\cB+0.4,-1.5) {\devphone};
\node[dev] (tel) at (\cB+1.85,-1.5) {\devserver[devpurple]};
\node[dev] (led) at (\cB+3.25,-1.5) {\devledger};
\node[dev] (dm) at (\cB+4.65,-1.55) {\devperson};
\draw[flow] (u.east) -- (tel.west);
\draw[flow] (tel.east) -- (led.west);
\draw[flow] (led.east) -- (dm.west);
\foreach \n/\t in {u/users, tel/telemetry, led/ledger, dm/decision}{\node[stxt, anchor=north, inner sep=1pt] at (\n.south) {\t};}
\tikzset{badge/.style={circle, draw=devred, fill=devred!15, font=\tiny\sffamily\bfseries, text=devred!70!black, inner sep=0.6pt, minimum size=3.8mm}}
\node[badge] at ([yshift=2mm]u.north) {N};
\node[badge] at ([yshift=2mm]tel.north) {I};
\node[badge] at ([yshift=2mm]dm.north) {H};
\node[stxt, text width=5.0cm] at (\cB+0.12,-2.45) {\textcolor{devred!70!black}{\textbf{N}} novelty: first test of every new variant $+b$\\
\textcolor{devred!70!black}{\textbf{I}} instrumentation: every test of TELEM variants $+b$; also with an audit of 10 tests\\
\textcolor{devred!70!black}{\textbf{H}} favourite: every re-test of the favourite $+b$\\[2pt]
$b/\sigma\in\{0,.25,.5,1,1.5,2,3\}$};
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {evidence ledger, 400 tests\\[3pt]tests of 2,000 sessions; H also at 500 and 8,000};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {change in shipped utility against $b=0$ with the same seeds, points of $U^*$};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Paired difference per level, 95\,\% CI\\[4pt]mean over the three classes\\[4pt]bias in units of $\sigma(n)$ and of utility};
"""

# ------------------------------------------------------------------ E7
F["d7"] = r"""
\expgrid{4.5}{Landscapes \& runs}{Drift and regime shift}{Programme}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{REF, 1 inst.}{100 / 150 runs}
\landrow{-1.95}{\devlandsvc}{SVC, 30 inst.}{3 / 4 runs each}
\landrow{-2.9}{\devlandrug}{RUG, 20 inst.}{3 / 4 runs each}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.45) {per cell: drift (16 cells) / shift (4 cells)};
% (2) chart with labelled, scaled axes (illustrative weight paths)
\node[stxt, text width=5.0cm] at (\cB+0.12,-0.72) {drift amplitude $\in\{0,.05,.1,.2\}$ (shaded band)\\\textcolor{devred!70!black}{shift at test 200: traffic $+30\,\%$, mobile $+15$ pp}};
\begin{scope}[shift={(\cB+0.95,-3.9)}]
  \draw[devline, -{Stealth[length=3pt]}] (0,0) -- (3.5,0) node[stxt, anchor=west] {tests};
  \draw[devline, -{Stealth[length=3pt]}] (0,0) -- (0,2.05);
  \node[stxt, anchor=south, rotate=90, inner sep=1pt] at (-0.45,1.0) {weight $w$};
  \foreach \x/\l in {0/0,1.6/200,3.2/400}{\draw[devline] (\x,0) -- (\x,-0.07) node[stxt, anchor=north, inner sep=1pt] {\l};}
  \foreach \y/\l in {0/0,0.6/0.2,1.2/0.4,1.8/0.6}{\draw[devline] (0,\y) -- (-0.07,\y) node[stxt, anchor=east, inner sep=1pt] {\l};}
  \fill[devacc!12] (0,1.05) rectangle (3.2,1.65);
  \draw[devacc, line width=0.8pt, domain=0:3.2, samples=100] plot (\x,{1.35+0.27*sin(\x*360)});
  \draw[devamber, line width=0.8pt, domain=0:3.2, samples=100] plot (\x,{0.75+0.2*sin(\x*360+120)});
  \node[stxt, text=devacc, anchor=west] at (3.22,1.35) {$w_{\mathrm d}$};
  \node[stxt, text=devamber, anchor=west] at (3.22,0.75) {$w_{\mathrm f}$};
  \draw[devred, line width=0.8pt] (1.6,0) -- (1.6,1.95);
\end{scope}
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {evidence ledger, 400 tests\\[3pt]forgetting: old evidence weighted by $\gamma$ per round\\$\gamma\in\{1,.98,.95,.9\}$};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {tracking: $U_t(\hat x)/U_t^*$ under the current criteria, every 25 tests\\[3pt]T3: gap to best variant $\le 4D$?};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Drift: mean over tests 100--400\\[4pt]shift: each $\gamma$ vs $\gamma=1$, paired, at 25, 50 and 200 tests after};
"""

# ------------------------------------------------------------------ E8
F["d8"] = r"""
\expgrid{4.5}{Landscapes \& runs}{Stakeholders and methods}{Programme}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{REF, 1 inst.}{60 runs}
\landrow{-1.95}{\devlandsvc}{SVC, 30 inst.}{3 runs each}
\landrow{-2.9}{\devlandrug}{RUG, 20 inst.}{3 runs each}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.45) {per budget of 200, 400 and 800 tests};
% (2)
\foreach \c/\t/\x in {devacc/{users\\$U_{\mathrm d}$}/0.45, devgreen!60!black/{operations\\$U_{\mathrm f}$}/1.5, devamber/{finance\\$U_{\mathrm v}$}/2.55}{%
  \node[dev, anchor=north] (p) at (\cB+\x,-0.7) {\devperson[\c]};
  \node[stxt, anchor=north, align=center] at (p.south) {\t};}
\node[chip=devgreen, text width=2.45cm] at (\cB+0.12,-2.55) {Pareto archive};
\node[chip=devacc, text width=2.45cm] at (\cB+0.12,-3.15) {3 scalarised loops,\\budget/3 each};
\node[chip=devline, text width=2.45cm] at (\cB+0.12,-3.8) {1 loop, default weights};
\begin{scope}[shift={(\cB+3.15,-3.9)}]
  \draw[devline, -{Stealth[length=3pt]}] (0,0) -- (1.95,0);
  \node[stxt, anchor=north, inner sep=1pt] at (0.85,-0.08) {$U_{\mathrm d}$};
  \draw[devline, -{Stealth[length=3pt]}] (0,0) -- (0,2.3) node[stxt, anchor=south, inner sep=1pt] {$U_{\mathrm v}$};
  \foreach \x/\l in {0/0,1.7/1}{\draw[devline] (\x,0) -- (\x,-0.07) node[stxt, anchor=north, inner sep=1pt] {\l};}
  \foreach \y/\l in {0/0,1.9/1}{\draw[devline] (0,\y) -- (-0.07,\y) node[stxt, anchor=east, inner sep=1pt] {\l};}
  \foreach \x/\y in {0.25/0.4,0.5/0.9,0.75/0.3,1.0/0.7,0.6/1.3,1.25/1.0,0.35/1.05,1.45/0.55}{\fill[devline!45] (\x,\y) circle (1.4pt);}
  \foreach \x/\y in {0.35/1.75,0.85/1.6,1.25/1.4,1.6/0.9}{\fill[devgreen!60!black] (\x,\y) circle (1.8pt);}
  \draw[devgreen!60!black, line width=0.6pt] (0.35,1.75) -- (0.85,1.6) -- (1.25,1.4) -- (1.6,0.9);
  \node[stxt, text=devgreen!50!black, anchor=south west, inner sep=1pt] at (0.9,1.62) {archive};
\end{scope}
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {same tests of 2,000 sessions, same budget for every method\\[3pt]archive keeps all non-dominated variants};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {hypervolume share of the true Pareto front\\[3pt]share locally Pareto-optimal (radius 2)\\[3pt]number delivered};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Archive $-$ scalarised loops, paired by seed\\[4pt]Wilcoxon test, Holm over 9 class $\times$ budget cells};
"""

# ------------------------------------------------------------------ E9
F["d9"] = r"""
\expgrid{4.5}{Scenarios}{Drawn factors}{Programme}{Measured}{Analysis}
\node[dev, anchor=north] at (\cA+0.75,-0.75) {\devdice};
\node[stxt, anchor=north west, text width=1.6cm] at (\cA+1.4,-0.75) {\textbf{120}\\scenarios drawn at random};
\node[dev, anchor=west] at (\cA+0.1,-2.25) {\devlandsvc};
\node[stxt, anchor=west] at (\cA+1.25,-2.25) {or};
\node[dev, anchor=west] at (\cA+1.65,-2.25) {\devlandrug};
\node[stxt, text width=2.9cm] at (\cA+0.12,-2.85) {family, then a random instance of it};
% (2) factor table
\node[stxt, text width=5.0cm] at (\cB+0.12,-0.75) {%
\renewcommand{\arraystretch}{1.15}%
\begin{tabular}{@{}l@{\quad}l@{}}
capabilities & 10, 12 or 14\\
test size $n$ & 400--8,000 sessions\\
budget & 100, 200, 400 or 800 tests\\
validity $\rho$ & 0.2--0.8\\
ideas per round $V$ & 2--15\\
reach of an idea & 1, 2 or 3 capabilities\\
\end{tabular}\\[3pt]1,024 to 16,384 configurations; test size log-uniform};
\node[stxt, text width=5.0cm] at (\cB+0.12,-3.5) {signal-to-noise: s.d.\ of the 50 best utilities $/\,\sigma(n)$, from 0.07 to 2.1};
% (3)
\foreach \t/\c/\y in {{\mbox{Champion--challenger}}/devred/-0.9, Launch-and-learn/devamber/-1.4, Design-thinking loop/devacc/-1.9, Evidence ledger/devgreen/-2.4}{\node[chip=\c, text width=2.3cm] at (\cC+0.08,\y) {\t};}
\node[stxt, text width=2.4cm] at (\cC+0.12,-2.85) {$\times$ 12 runs with common seeds per scenario\\[2pt]\textbf{5,760 runs}};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {ledger's advantage over each policy, points of $U^*$\\[3pt]share of scenarios won};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Regression of the advantage on standardised factors\\[4pt]HC3 robust 95\,\% intervals\\[4pt]scenario as unit};
"""

# ------------------------------------------------------------------ E10
F["d10"] = r"""
\expgrid{4.5}{Landscapes \& runs}{Three checks}{Programme}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{REF, 1 inst.}{150 runs}
\landrow{-1.95}{\devlandsvc}{SVC, 30 inst.}{5 runs each}
\landrow{-2.9}{\devlandrug}{RUG, 20 inst.}{5 runs each}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.45) {per condition, common seeds};
% (2)
\node[stxt, text width=5.0cm] at (\cB+0.12,-0.72) {\textbf{(a) stronger practice baselines} (A/B)};
\node[chip=devred, text width=1.4cm, minimum height=7mm] at (\cB+0.12,-1.35) {5\,\% rule, not pooled};
\node[chip=devred, text width=1.4cm, minimum height=7mm] at (\cB+1.82,-1.35) {5\,\% rule, pooled};
\node[chip=devred, text width=1.4cm, minimum height=7mm] at (\cB+3.52,-1.35) {higher arm, pooled};
\node[stxt, text width=5.0cm] at (\cB+0.12,-1.9) {\textbf{(b) ship rule}: ship $\arg\max\,(\mu-\kappa s)$\\$\kappa\in\{0,\,0.5,\,1,\,1.5,\,2\}$};
\node[stxt, text width=5.0cm] at (\cB+0.12,-2.6) {\textbf{(c) misspecified ground truth}: $U'=U+\varepsilon$\\$\varepsilon\sim N(0,\tau^2)$, fixed per configuration\\$\tau\in\{0,\,0.044,\,0.088\}$: E1's model error and twice it\\policies: A/B, launch-and-learn, loop, ledger};
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {400 tests of 2,000 sessions\\[3pt]\textbf{8,800 runs}};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {shipped $U(\hat x)/U^*$; in (c) judged by the perturbed truth $U'$};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Ledger $-$ policy, paired by seed\\[4pt]Wilcoxon test\\[4pt]families: instance as unit};
"""

# ------------------------------------------------------------------ E11
F["d11"] = r"""
\expgrid{4.8}{Landscapes \& runs}{Audit conditions}{Programme}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{REF, 1 inst.}{150 runs}
\landrow{-1.95}{\devlandsvc}{SVC, 30 inst.}{5 runs each}
\landrow{-2.9}{\devlandrug}{RUG, 20 inst.}{5 runs each}
\node[stxt, text width=2.9cm] at (\cA+0.12,-3.45) {per condition, common seeds};
% (2) ladder
\node[stxt] at (\cB+0.12,-0.7) {\textbf{(a) ladder}: add one element at a time};
\foreach \i/\t in {0/{A/B, one test per arm}, 1/{+ pool champion's evidence}, 2/{+ retain all variants}, 3/{+ re-test favourite 4$\times$ per build}, 4/{+ re-test three leaders}, 5/{+ rotating re-test (= loop)}, 6/{+ ship on lower bound}, 7/{+ three builds per round (= ledger)}}{%
  \fill[devacc!\the\numexpr 15+\i*8\relax] (\cB+0.15,{-1.1-\i*0.25}) rectangle ++({0.12+\i*0.1},-0.19);
  \node[stxt, anchor=west, inner sep=0pt] at (\cB+1.05,{-1.2-\i*0.25}) {L\i\enspace \t};}
\node[stxt, text width=5.0cm] at (\cB+0.12,-3.15) {\textbf{(b) noise}: $\sigma$ assumed $\times\,0.5,\,1,\,1.3,\,2$, or learned online};
\node[stxt, text width=5.0cm] at (\cB+0.12,-3.72) {\textbf{(c) start}: 5 random configurations, or the production configuration with 10 history tests; ledger with 1, 2 or 3 builds per round};
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {400 tests of 2,000 sessions, checkpoints at 50, 100, 200, 400\\[3pt]\textbf{17,600 runs}};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {shipped $U(\hat x)/U^*$\\[3pt](a) gain of each step over the previous one};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Paired differences by seed, 95\,\% CI\\[4pt]Wilcoxon test\\[4pt]families: instance as unit};
"""

# ------------------------------------------------------------------ E13
F["d13"] = r"""
\expgrid{4.7}{Services}{Blind judge and generator}{Ledger runs}{Measured}{Analysis}
\landrow{-1.0}{\devlandref}{A = REF}{537 rated}
\landrow{-1.95}{\devlandsvc}{B = SVC inst.}{200 rated}
\node[stxt, text width=2.9cm] at (\cA+0.12,-2.55) {A: 300 random + 237 one-capability variants of the 30 best\\[2pt]B: 200 random\\[2pt]5 leaders of each for proposals};
% (2)
\node[dev] (br) at (\cB+0.45,-1.2) {\devreport};
\node[stxt, anchor=north, align=center] at (\cB+0.45,-1.75) {brief +\\configs\\(batches\\of 100)};
\node[dev] (cl) at (\cB+2.1,-1.25) {\devcloud[devpurple!12]};
\node[devlabel, font=\scriptsize\sffamily] at (cl) {Claude};
\node[stxt, anchor=north, align=center] at (\cB+2.1,-1.8) {Opus 5.5\\Haiku 5.5};
\draw[flow] (br.east) -- (cl.west);
\node[stxt, anchor=west, text width=1.55cm] (out) at (\cB+3.55,-0.95) {ratings 0--100};
\node[stxt, anchor=west, text width=1.55cm] (out2) at (\cB+3.55,-1.65) {8 variants per leader};
\coordinate (bus) at (\cB+3.3,-1.25);
\draw[devline, line width=0.8pt] (cl.east) -- (bus);
\draw[flow] (bus) |- (out.west);
\draw[flow] (bus) |- (out2.west);
\draw[devred, line width=0.8pt, dashed] (\cB+0.12,-2.95) -- (\cB+5.08,-2.95);
\node[stxt, text width=5.0cm, text=devred!70!black] at (\cB+0.12,-3.07) {blind: no access to the model, the code or any utility; 16 sessions; inputs and outputs released};
\node[stxt, text width=5.0cm] at (\cB+0.12,-3.95) {true utility $U$ from the testbed is used only to score the outputs};
% (3)
\node[dev, anchor=north] (fl) at (\cC+0.65,-0.7) {\devflag};
\node[dev, anchor=north] (lg) at (\cC+1.9,-0.7) {\devledger};
\draw[flow] (fl.east) -- (lg.west);
\node[stxt, text width=2.4cm] at (\cC+0.12,-1.85) {ledger on A with a screen of the measured validity near the leaders\\[3pt]vs no screen and $\rho=0.5$; $V\in\{5,20\}$\\[3pt]100 runs each, \textbf{800 runs}};
% (4)
\node[dev, anchor=north] at (\cD+1.2,-0.65) {\devreport};
\node[stxt, text width=2.25cm] at (\cD+0.1,-1.75) {validity $\rho$: all, random, near leaders\\[2pt]top-decile precision\\[2pt]overload in top quartile\\[2pt]share of proposals improving\\[2pt]toggles on 4 favourite capabilities};
% (5)
\node[stxt, text width=2.05cm] at (\cE+0.12,-0.8) {Bootstrap 95\,\% CI (2,000 resamples)\\[4pt]proposals vs random 1--2 capability variants\\[4pt]ledger: paired difference vs no screen};
"""

for k, body in F.items():
    with open(os.path.join(OUT, f"fig_{k}.tex"), "w") as f:
        f.write(PRE + body + POST)
print("written", list(F))
