"""Graphing functions for the evaluation tool."""
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def overlap_histogram(data_list, title, xlabel, ylabel):
    """Histogram of multiple data sets on the same plot."""
    _, axs = plt.subplots(1, 1, figsize=(12, 8))

    for data_dict in data_list:
        axs.hist(
            data_dict["data"],
            bins=100,
            range=(0, 1),
            edgecolor="black",
            density=True,
            cumulative=False,
            alpha=0.5,
            label=data_dict["label"],
        )

    axs.set_title(title)
    axs.set_xlabel(xlabel)
    axs.set_ylabel(ylabel)

    axs.xaxis.set_major_locator(MaxNLocator(nbins=20))
    axs.set_xlim(0, 1)

    # Add legend
    axs.legend()

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Show the plots
    plt.show()
