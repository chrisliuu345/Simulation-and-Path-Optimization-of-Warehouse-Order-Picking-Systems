"""Generate a clean warehouse layout plan diagram for the report."""
from __future__ import annotations

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(PROJECT, "results", "warehouse_layout.png")

N_AISLES = 10
POS_PER_AISLE = 20
AISLE_SPACING = 2.5
POS_SPACING = 1.0

fig, ax = plt.subplots(1, 1, figsize=(11, 7))

# Give plenty of margin on all sides
margin_left = 2.5
margin_right = 5.5
margin_bottom = 3.0
margin_top = 3.0

ax.set_xlim(-margin_left, (N_AISLES - 1) * AISLE_SPACING + margin_right)
ax.set_ylim(-margin_bottom, POS_PER_AISLE * POS_SPACING + margin_top)
ax.set_aspect("equal")

left_x = 0
right_x = (N_AISLES - 1) * AISLE_SPACING
front_y = 0
back_y = POS_PER_AISLE * POS_SPACING
io_x = right_x / 2
io_y = -1.5

# --- Cross aisles (horizontal lanes) ---
cross_color = "#D5D8DC"
ax.add_patch(mpatches.Rectangle(
    (left_x - 0.8, front_y - 0.7), right_x - left_x + 1.6, 1.4,
    facecolor=cross_color, edgecolor="#AAAAAA", linewidth=0.5, linestyle="--", zorder=0))
ax.add_patch(mpatches.Rectangle(
    (left_x - 0.8, back_y - 0.7), right_x - left_x + 1.6, 1.4,
    facecolor=cross_color, edgecolor="#AAAAAA", linewidth=0.5, linestyle="--", zorder=0))

# --- Aisle labels at top ---
for i in range(N_AISLES):
    x = i * AISLE_SPACING
    ax.text(x, back_y + 0.2, f"A{i+1}", ha="center", va="bottom",
            fontsize=6.5, color="#555555", style="italic")

# --- Draw positions ---
for i in range(N_AISLES):
    x = i * AISLE_SPACING
    for p in range(POS_PER_AISLE):
        y = (p + 0.5) * POS_SPACING
        score = p * 2.0 + i * 0.5
        if score < POS_PER_AISLE / 2:
            color, edge, size = "#E74C3C", "#C0392B", 28
        elif score < POS_PER_AISLE * 1.2:
            color, edge, size = "#F39C12", "#E67E22", 24
        else:
            color, edge, size = "#3498DB", "#2980B9", 24
        ax.scatter(x, y, c=color, s=size, edgecolors=edge, linewidth=0.3, zorder=2)

# --- I/O point ---
ax.scatter(io_x, io_y, c="#2ECC71", s=180, marker="s", edgecolors="#27AE60",
           linewidth=2, zorder=3)
ax.annotate("I/O\n出入库点", xy=(io_x, io_y), xytext=(io_x, io_y - 2.2),
            fontsize=9, fontweight="bold", color="#1E8449", ha="center",
            arrowprops=dict(arrowstyle="->", color="#1E8449", lw=1.5, connectionstyle="arc3,rad=0"))

# --- Dimension lines ---
# Vertical dimension (right side)
dim_x = right_x + 1.2
ax.annotate("", xy=(dim_x, front_y - 0.7), xytext=(dim_x, back_y + 0.7),
            arrowprops=dict(arrowstyle="<->", color="#777777", lw=0.8))
ax.text(dim_x + 0.8, (front_y + back_y) / 2, "20个货位\n(20 m)",
        ha="center", va="center", fontsize=8, color="#555555")

# Horizontal dimension (below)
dim_y = -0.8
ax.annotate("", xy=(left_x, dim_y), xytext=(right_x, dim_y),
            arrowprops=dict(arrowstyle="<->", color="#777777", lw=0.8))
ax.text((left_x + right_x) / 2, dim_y - 0.6, f"10条通道 ({right_x:.1f} m)",
        ha="center", va="top", fontsize=8, color="#555555")

# --- Cross aisle labels ---
ax.text(right_x / 2, -1.3, "前端横通道", ha="center", fontsize=7.5, color="#888888")
ax.text(right_x / 2, back_y + 0.6, "后端横通道", ha="center", fontsize=7.5, color="#888888")

# --- S-Shape path demo ---
path_aisles = [0, 2, 3, 5, 7, 9]
px, py = [io_x], [io_y]
for idx, ai in enumerate(path_aisles):
    x = ai * AISLE_SPACING
    if idx == 0:
        px.append(x); py.append(front_y)
    else:
        prev_x = path_aisles[idx - 1] * AISLE_SPACING
        if idx % 2 == 1:
            px.extend([prev_x, x]); py.extend([back_y, back_y])
        else:
            px.extend([prev_x, x]); py.extend([front_y, front_y])
    if idx % 2 == 0:
        px.extend([x, x]); py.extend([front_y, back_y])
    else:
        px.extend([x, x]); py.extend([back_y, front_y])
# Return
last_x = path_aisles[-1] * AISLE_SPACING
return_y = back_y if (len(path_aisles) - 1) % 2 == 0 else front_y
px.extend([last_x, io_x]); py.extend([return_y, return_y])
px.append(io_x); py.append(io_y)

ax.plot(px, py, color="#E74C3C", linewidth=2.5, linestyle="--", zorder=4, alpha=0.85)

# Path label
label_x = path_aisles[3] * AISLE_SPACING
label_y = (front_y + back_y) / 2
ax.annotate("S-Shape\n路径示例",
            xy=(label_x, label_y), xytext=(label_x + 3.8, label_y + 2),
            fontsize=8, color="#C0392B", fontstyle="italic", ha="center",
            arrowprops=dict(arrowstyle="->", color="#E74C3C", lw=1.2, alpha=0.7,
                          connectionstyle="arc3,rad=-0.3"))

# --- Legend (placed below the warehouse, outside) ---
legend_elements = [
    mpatches.Patch(facecolor="#E74C3C", edgecolor="#C0392B", label="A类 (高频, 占20%)"),
    mpatches.Patch(facecolor="#F39C12", edgecolor="#E67E22", label="B类 (中频, 占30%)"),
    mpatches.Patch(facecolor="#3498DB", edgecolor="#2980B9", label="C类 (低频, 占50%)"),
    plt.Line2D([0], [0], marker="s", color="w", markerfacecolor="#2ECC71",
               markeredgecolor="#27AE60", markersize=8, label="I/O 出入库点"),
    plt.Line2D([0], [0], color="#E74C3C", linestyle="--", linewidth=2,
               label="S-Shape 拣选路径"),
]
legend = ax.legend(handles=legend_elements, loc="lower center",
                   bbox_to_anchor=(0.5, -0.12), ncol=5, fontsize=8,
                   framealpha=0.95, edgecolor="#CCCCCC",
                   columnspacing=1.0, handletextpad=0.5)

# --- Clean up axes ---
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

fig.suptitle("仓库布局平面示意图", fontsize=14, fontweight="bold", y=0.97)

plt.tight_layout(rect=[0, 0.05, 1, 0.95])
fig.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor="white", pad_inches=0.3)
plt.close(fig)
print(f"Saved: {OUTPUT}")
