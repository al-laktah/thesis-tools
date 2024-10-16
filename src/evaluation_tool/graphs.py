"Different graphs for the evaluation tool"
# Imports
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Duration Graphs
def duration_t_s_box_plot(res):
    "show a box plot of the duration of the evaluation of the models"
    number_of_models = len(res)
    data = []
    labels = []

    for i in range(number_of_models):
        data.append(res[i]["metrics"]["duration_metrics"]["eval_durations_t/s"])
        labels.append(f'{res[i]["model"]["name"]}:{res[i]["model"]["size"]}')

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.boxplot(
        data,
        vert=True,
        tick_labels=labels,
        patch_artist=True,
        showmeans=True,
        meanline=True,
        showfliers=False,
    )
    ax.set_title("Generation Speed (Higher is Better)")
    ax.set_ylabel("Speed (tokens/s)")
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.grid(True, color="gray", linestyle="--", linewidth=0.5, axis="y")

    fig.tight_layout()

    return fig, ax


# Difference Graphs
def multi_histogram(res, metric, titel, leg_loc="upper left"):
    "show a histogram of the difference of the models"
    number_of_models = len(res)
    rows = (
        (number_of_models + 1) // 2
        if number_of_models % 2 != 0
        else number_of_models // 2
    )

    fig, axs = plt.subplots(rows, 2, figsize=(12, 8))
    axs = axs.flatten()  # Flatten the 2D array for easier iteration

    for i, ax in enumerate(axs):
        if i >= number_of_models:
            ax.axis("off")  # Hide unused subplots
            continue

        ax.set_xlabel("Ratio")
        ax.set_ylabel("Density")
        ax.set_xlim(0, 1)
        ax.set_xticks(np.arange(0, 1.1, 0.1))
        ax.set_ylim(0, 10)
        ax.grid(True, color="gray", linestyle="--", linewidth=0.5)

        ratios = res[i]["metrics"]["difference_metrics"][metric]
        _, _, patches = ax.hist(
            ratios, bins=10, range=(0, 1), edgecolor="black", density=True
        )
        ax.set_title(f'{titel}: {res[i]["model"]["name"]}:{res[i]["model"]["size"]}')

        sns.kdeplot(ratios, ax=ax, color="red", label="KDE")
        frequencies, _ = np.histogram(ratios, bins=10, range=(0, 1))

        for patch, frequency in zip(patches, frequencies):
            height = patch.get_height()
            ax.text(
                patch.get_x() + patch.get_width() / 2,
                height,
                f"{frequency}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

        ax.legend(loc=leg_loc)

    fig.tight_layout()
    return fig, axs


# Language Tool Graphs
def multi_bar_graph(res, metric, title):
    "show a bar graph of the language tool metrics"

    def get_count(metric, model_res):
        count = 0
        for alist in model_res["metrics"]["language_tool_metrics"][metric]:
            count += len(alist)
        return count

    label_count_dict = {}

    for model_res in res:
        count = get_count(metric, model_res)
        label_count_dict[
            f"{model_res['model']['name']}:{model_res['model']['size']}"
        ] = count

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.bar(label_count_dict.keys(), label_count_dict.values())
    ax.grid(True, color="gray", linestyle="--", linewidth=0.5, axis="y")

    ax.set_ylabel("Count")
    ax.set_title(title)

    plt.xticks(rotation=45, ha="right")

    fig.tight_layout()

    return fig, ax


def multi_bar_model_graph(model_res, metric, yinc):
    "show a bar graph of the language tool metrics"
    label_count_dict = {}

    lengths = [
        len(lst) for lst in model_res["metrics"]["language_tool_metrics"][metric]
    ]

    fig, ax = plt.subplots(figsize=(20, 5))

    ax.bar(label_count_dict.keys(), label_count_dict.values())
    ax.grid(True, color="gray", linestyle="--", linewidth=0.5, axis="y")

    ax.bar(
        range(1, len(model_res["metrics"]["language_tool_metrics"][metric]) + 1),
        lengths,
        color="skyblue",
    )

    # Set the labels and title
    ax.set_title(metric + ' - ' + model_res["model"]["name"] + ':' + model_res["model"]["size"])

     # Set the ticks
    ax.set_xticks(np.arange(1, len(lengths) + 1, 2))
    ax.set_xticklabels(np.arange(1, len(lengths) + 1, 2), rotation=45, ha="center", fontsize=8)
    ax.set_xlim(0, len(lengths) + 0.5)

    ax.set_yticks(np.arange(0, max(lengths) + 1, yinc))
    ax.set_yticklabels(np.arange(0, max(lengths) + 1, yinc), fontsize=8)
    ax.set_ylim(0, max(lengths) + yinc / 2)

    fig.tight_layout()
    return fig, ax


# Semantic Graphs
def semantic_box_plot(res):
    "show a box plot of the semantic similarity of the models"
    number_of_models = len(res)
    data = []
    labels = []
    fail_counts = []

    for i in range(number_of_models):
        llm_scores = res[i]["metrics"]["semantic_metrics"]["llm_scores"]
        valid_scores = [score for score in llm_scores if score != -1]
        fails = [score for score in llm_scores if score == -1]

        data.append(valid_scores)
        labels.append(f'{res[i]["model"]["name"]}:{res[i]["model"]["size"]}')
        fail_counts.append(len(fails))

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.boxplot(
        data,
        vert=True,
        patch_artist=True,
        showmeans=True,
        meanline=True,
        showfliers=False,
    )

    ax.set_title("Semantic Similarity according to Gemma 2 using prompt 6")
    ax.set_ylabel("Speed (tokens/s)")
    ax.grid(True, color="gray", linestyle="--", linewidth=0.5, axis="y")

    plt.xticks(rotation=45, ha="right")

    # Annotate the number of fails for each model below the x-axis labels
    for i, fail_count in enumerate(fail_counts):
        ax.text(
            i + 1,
            ax.get_ylim()[0] - 0.05 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
            f"Fails: {fail_count}",
            ha="center",
            va="top",
            fontsize=10,
            color="red",
            rotation=45,
        )

    # Adjust the plot to make space for the annotations
    fig.subplots_adjust(bottom=0.3)
    fig.tight_layout()
    return fig, ax


def violin_plot(res):
    "show a violin plot of the semantic similarity of the models"
    data = []
    labels = []

    for model_res in res:
        llm_scores = model_res["metrics"]["semantic_metrics"]["llm_scores"]
        valid_scores = [score for score in llm_scores if score != -1]
        data.extend(valid_scores)
        labels.extend(
            [f'{model_res["model"]["name"]}:{model_res["model"]["size"]}']
            * len(valid_scores)
        )

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.violinplot(x=labels, y=data, ax=ax)
    ax.set_title("Semantic Similarity Scores by Model")
    ax.set_ylabel("Score")
    ax.grid(True, color="gray", linestyle="--", linewidth=0.5, axis="y")
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    return fig, ax
