"""Common matplotlib style for the paper's data figures."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

W_FULL = 6.5   # inches, full text width
W_HALF = 3.2
COL = {"ref": "#37474F", "svc": "#1E88E5", "rug": "#E53935"}
CLS_NAME = {"ref": "Reference instance", "svc": "Service family (30)", "rug": "Rugged family (20)"}
POL_COL = {"random": "#9E9E9E", "abtest": "#FB8C00", "oneshot": "#8E24AA", "loop": "#1E88E5",
           "ledger": "#43A047", "thompson": "#6D4C41"}
POL_NAME = {"random": "Random search", "abtest": "Champion–challenger A/B", "oneshot": "Launch-and-learn",
            "loop": "Design-thinking loop", "ledger": "Evidence ledger", "thompson": "Thompson sampling"}


def setup():
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix", "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
        "lines.linewidth": 1.2, "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
        "axes.grid": True, "grid.color": "#E0E0E0", "grid.linewidth": 0.5,
        "axes.titleweight": "bold", "axes.titlelocation": "left"})
