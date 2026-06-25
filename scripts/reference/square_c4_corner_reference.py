import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# Correct corner-based C4 Heesch-style tile generator
# ------------------------------------------------------------
# 핵심:
# - 정사각형 중심 기준 90도 회전이 아님
# - 꼭짓점 기준 90도 회전
#
# 정사각형 꼭짓점:
# A = (0, 0)
# B = (1, 0)
# C = (1, 1)
# D = (0, 1)
#
# C4 조건:
# - A에서 C4: AB를 A 중심으로 90도 회전하면 AD
# - C에서 C4: CD를 C 중심으로 90도 회전하면 CB
# ============================================================


OUTPUT_DIR = Path("correct_c4_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

N_POINTS = 260
DPI = 300


# ------------------------------------------------------------
# 1. 기본 유틸리티
# ------------------------------------------------------------

def normalize_profile(y, amplitude=0.16):
    y = np.array(y, dtype=float)
    max_abs = np.max(np.abs(y))

    if max_abs < 1e-9:
        return y

    return amplitude * y / max_abs


def endpoint_fade(t):
    return np.sin(math.pi * t)


def edge_from_offset(start, end, offset_values):
    """
    start에서 end까지 가는 선분을 기준으로,
    수직 방향으로 offset_values만큼 변형한 곡선 변을 만듭니다.
    """
    start = np.array(start, dtype=float)
    end = np.array(end, dtype=float)

    offset_values = np.array(offset_values, dtype=float)
    t = np.linspace(0, 1, len(offset_values))

    direction = end - start
    length = np.linalg.norm(direction)

    if length < 1e-9:
        raise ValueError("start and end cannot be the same point.")

    direction_unit = direction / length

    # 진행 방향 기준 왼쪽 법선 벡터
    normal = np.array([-direction_unit[1], direction_unit[0]])

    points = start[None, :] + t[:, None] * direction[None, :]
    points = points + offset_values[:, None] * normal[None, :]

    return points


def rotate_points(points, angle_degrees, center):
    """
    points를 center 기준으로 angle_degrees만큼 회전합니다.
    """
    angle = math.radians(angle_degrees)
    c = math.cos(angle)
    s = math.sin(angle)

    rotation = np.array([
        [c, -s],
        [s, c],
    ])

    center = np.array(center, dtype=float)
    return (points - center) @ rotation.T + center


def reverse_points(points):
    return points[::-1].copy()


def translate_points(points, dx=0.0, dy=0.0):
    return points + np.array([dx, dy])


# ------------------------------------------------------------
# 2. 다양한 변 프로파일
# ------------------------------------------------------------

def profile_cat_ears(t, amplitude=0.17):
    """
    고양이 귀처럼 두 개의 돌출이 있는 변.
    """
    y = (
        1.30 * np.exp(-((t - 0.25) / 0.055) ** 2)
        + 1.20 * np.exp(-((t - 0.75) / 0.055) ** 2)
        - 0.45 * np.exp(-((t - 0.50) / 0.16) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_leaf(t, amplitude=0.16):
    """
    잎사귀처럼 부드럽게 흐르는 변.
    """
    y = (
        1.00 * np.sin(math.pi * t)
        + 0.55 * np.sin(2 * math.pi * t)
        - 0.25 * np.sin(4 * math.pi * t)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_robot_steps(t, amplitude=0.15):
    """
    로봇이나 기계 느낌의 계단형 변.
    """
    y = np.zeros_like(t)

    y[(t >= 0.12) & (t < 0.25)] = 0.75
    y[(t >= 0.25) & (t < 0.37)] = -0.40
    y[(t >= 0.37) & (t < 0.53)] = 1.00
    y[(t >= 0.53) & (t < 0.66)] = -0.65
    y[(t >= 0.66) & (t < 0.82)] = 0.55

    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_fish_tail(t, amplitude=0.18):
    """
    물고기 꼬리처럼 들어갔다 나오는 변.
    """
    y = (
        -1.10 * np.exp(-((t - 0.35) / 0.10) ** 2)
        + 1.25 * np.exp(-((t - 0.62) / 0.10) ** 2)
        - 0.40 * np.exp(-((t - 0.82) / 0.07) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_cloud(t, amplitude=0.16):
    """
    구름처럼 둥근 굴곡이 많은 변.
    """
    y = (
        0.70 * np.exp(-((t - 0.18) / 0.10) ** 2)
        + 1.10 * np.exp(-((t - 0.38) / 0.12) ** 2)
        + 0.80 * np.exp(-((t - 0.62) / 0.10) ** 2)
        + 0.55 * np.exp(-((t - 0.82) / 0.08) ** 2)
        - 0.45 * np.exp(-((t - 0.52) / 0.07) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_monster_arm(t, amplitude=0.18):
    """
    몬스터 팔이나 꼬리처럼 크게 튀어나오는 변.
    """
    y = (
        1.30 * np.exp(-((t - 0.28) / 0.12) ** 2)
        - 1.10 * np.exp(-((t - 0.58) / 0.13) ** 2)
        + 0.60 * np.exp(-((t - 0.82) / 0.08) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


# ------------------------------------------------------------
# 3. 올바른 C4 유닛 생성 함수
# ------------------------------------------------------------

def make_corner_C4_unit(
    bottom_profile,
    top_profile,
    bottom_amplitude=0.16,
    top_amplitude=0.16,
):
    """
    꼭짓점 기준 C4 유닛을 생성합니다.

    정사각형:
    A = (0, 0)
    B = (1, 0)
    C = (1, 1)
    D = (0, 1)

    구성:
    1. 아랫변 AB를 자유롭게 만든다.
    2. AB를 A 중심으로 90도 회전하여 왼쪽변 AD를 만든다.
    3. 윗변 CD를 자유롭게 만든다.
    4. CD를 C 중심으로 90도 회전하여 오른쪽변 CB를 만든다.

    외곽선 진행 방향:
    A -> B -> C -> D -> A
    """

    A = np.array([0.0, 0.0])
    B = np.array([1.0, 0.0])
    C = np.array([1.0, 1.0])
    D = np.array([0.0, 1.0])

    t = np.linspace(0, 1, N_POINTS)

    # 1. 아랫변 AB: A -> B
    bottom_offset = bottom_profile(t, amplitude=bottom_amplitude)
    bottom_AB = edge_from_offset(A, B, bottom_offset)

    # 2. 왼쪽변 AD: AB를 A 기준 90도 회전
    left_AD = rotate_points(bottom_AB, 90, center=A)

    # 3. 윗변 CD: C -> D
    # C -> D 방향에서 양수 offset은 아래쪽, 즉 정사각형 안쪽 방향입니다.
    top_offset = top_profile(t, amplitude=top_amplitude)
    top_CD = edge_from_offset(C, D, top_offset)

    # 4. 오른쪽변 CB: CD를 C 기준 90도 회전
    # top_CD는 C -> D
    # 이것을 C 중심으로 90도 회전하면 C -> B가 됩니다.
    right_CB = rotate_points(top_CD, 90, center=C)

    # 외곽선은 A -> B -> C -> D -> A 순서여야 하므로
    # 오른쪽변은 B -> C 방향이 필요합니다.
    right_BC = reverse_points(right_CB)

    # 왼쪽변도 D -> A 방향이 필요합니다.
    left_DA = reverse_points(left_AD)

    outline = np.vstack([
        bottom_AB,
        right_BC[1:],
        top_CD[1:],
        left_DA[1:],
        bottom_AB[:1],
    ])

    return outline


# ------------------------------------------------------------
# 4. 저장 함수
# ------------------------------------------------------------

def save_unit(outline, name):
    """
    단일 유닛 PNG, SVG 저장
    """
    png_path = OUTPUT_DIR / f"{name}_unit.png"
    svg_path = OUTPUT_DIR / f"{name}_unit.svg"

    fig, ax = plt.subplots(figsize=(5, 5))

    ax.plot(outline[:, 0], outline[:, 1], linewidth=3)

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    margin = 0.35
    ax.set_xlim(-margin, 1 + margin)
    ax.set_ylim(-margin, 1 + margin)

    fig.savefig(png_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)

    return png_path, svg_path


def save_unit_with_guide(outline, name):
    """
    기준 정사각형과 꼭짓점 표시가 있는 교사용 확인 이미지 저장
    """
    png_path = OUTPUT_DIR / f"{name}_guide.png"

    fig, ax = plt.subplots(figsize=(5, 5))

    ax.plot(outline[:, 0], outline[:, 1], linewidth=3)

    # 기준 정사각형
    ax.plot(
        [0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0],
        linestyle="--",
        linewidth=1,
    )

    # 꼭짓점 표시
    vertices = {
        "A(C4)": (0, 0),
        "B": (1, 0),
        "C(C4)": (1, 1),
        "D": (0, 1),
    }

    for label, point in vertices.items():
        x, y = point
        ax.scatter([x], [y], s=25)
        ax.text(x + 0.03, y + 0.03, label, fontsize=10)

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    margin = 0.35
    ax.set_xlim(-margin, 1 + margin)
    ax.set_ylim(-margin, 1 + margin)

    fig.savefig(png_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

    return png_path


# ------------------------------------------------------------
# 5. C4 타일링 미리보기
# ------------------------------------------------------------

def rotation_matrix_about_point(angle_degrees, center):
    """
    homogeneous transform matrix를 만듭니다.
    """
    angle = math.radians(angle_degrees)
    c = math.cos(angle)
    s = math.sin(angle)

    cx, cy = center

    # T(center) @ R @ T(-center)
    matrix = np.array([
        [c, -s, cx - c * cx + s * cy],
        [s,  c, cy - s * cx - c * cy],
        [0,  0, 1],
    ])

    return matrix


def apply_transform(points, matrix):
    """
    점 배열에 homogeneous transform을 적용합니다.
    """
    ones = np.ones((len(points), 1))
    homo = np.hstack([points, ones])
    transformed = homo @ matrix.T
    return transformed[:, :2]


def apply_transform_to_point(point, matrix):
    point = np.array([[point[0], point[1]]], dtype=float)
    return apply_transform(point, matrix)[0]


def matrix_key(matrix, decimals=6):
    """
    같은 위치의 타일을 중복 생성하지 않기 위한 키.
    """
    rounded = np.round(matrix, decimals=decimals)
    return tuple(rounded.flatten())


def save_c4_tessellation_preview(outline, name, depth=3):
    """
    C4 꼭짓점 회전을 이용해 주변 타일을 생성하는 미리보기입니다.

    단순 평행이동으로 반복하면 C4 도안은 맞지 않습니다.
    따라서 A, C 꼭짓점을 기준으로 90도 회전한 이웃 타일들을 생성합니다.
    """

    preview_path = OUTPUT_DIR / f"{name}_c4_preview.png"

    # 기본 타일의 C4 꼭짓점
    local_A = np.array([0.0, 0.0])
    local_C = np.array([1.0, 1.0])

    identity = np.eye(3)

    transforms = [identity]
    queue = [(identity, 0)]
    seen = {matrix_key(identity)}

    while queue:
        current_matrix, current_depth = queue.pop(0)

        if current_depth >= depth:
            continue

        # 현재 타일의 C4 꼭짓점 위치
        world_A = apply_transform_to_point(local_A, current_matrix)
        world_C = apply_transform_to_point(local_C, current_matrix)

        for center in [world_A, world_C]:
            for angle in [90, -90, 180]:
                rotation = rotation_matrix_about_point(angle, center)
                new_matrix = rotation @ current_matrix
                key = matrix_key(new_matrix)

                if key not in seen:
                    seen.add(key)
                    transforms.append(new_matrix)
                    queue.append((new_matrix, current_depth + 1))

    fig, ax = plt.subplots(figsize=(7, 7))

    for matrix in transforms:
        moved = apply_transform(outline, matrix)
        ax.plot(moved[:, 0], moved[:, 1], linewidth=1.5)

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    # 자동 범위 설정
    all_points = []

    for matrix in transforms:
        moved = apply_transform(outline, matrix)
        all_points.append(moved)

    all_points = np.vstack(all_points)

    x_min, y_min = all_points.min(axis=0)
    x_max, y_max = all_points.max(axis=0)

    margin = 0.4
    ax.set_xlim(x_min - margin, x_max + margin)
    ax.set_ylim(y_min - margin, y_max + margin)

    fig.savefig(preview_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

    return preview_path


# ------------------------------------------------------------
# 6. 여러 C4 도안 생성
# ------------------------------------------------------------

def generate_correct_c4_presets():
    presets = [
        {
            "name": "C4_corner_cat_leaf",
            "bottom_profile": profile_cat_ears,
            "top_profile": profile_leaf,
            "bottom_amplitude": 0.17,
            "top_amplitude": 0.15,
        },
        {
            "name": "C4_corner_fish_cloud",
            "bottom_profile": profile_fish_tail,
            "top_profile": profile_cloud,
            "bottom_amplitude": 0.18,
            "top_amplitude": 0.15,
        },
        {
            "name": "C4_corner_robot_monster",
            "bottom_profile": profile_robot_steps,
            "top_profile": profile_monster_arm,
            "bottom_amplitude": 0.15,
            "top_amplitude": 0.17,
        },
        {
            "name": "C4_corner_cloud_cat",
            "bottom_profile": profile_cloud,
            "top_profile": profile_cat_ears,
            "bottom_amplitude": 0.15,
            "top_amplitude": 0.17,
        },
    ]

    results = []

    for preset in presets:
        name = preset["name"]

        outline = make_corner_C4_unit(
            bottom_profile=preset["bottom_profile"],
            top_profile=preset["top_profile"],
            bottom_amplitude=preset["bottom_amplitude"],
            top_amplitude=preset["top_amplitude"],
        )

        unit_png, unit_svg = save_unit(outline, name)
        guide_png = save_unit_with_guide(outline, name)
        preview_png = save_c4_tessellation_preview(outline, name, depth=3)

        results.append({
            "name": name,
            "unit_png": unit_png,
            "unit_svg": unit_svg,
            "guide_png": guide_png,
            "preview_png": preview_png,
        })

    return results


# ------------------------------------------------------------
# 7. 실행부
# ------------------------------------------------------------

if __name__ == "__main__":
    print("Generating corrected corner-based C4 tessellation units...")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")

    results = generate_correct_c4_presets()

    print()
    print("Generated corrected C4 files:")

    for item in results:
        print(f"- {item['name']}")
        print(f"  unit png   : {item['unit_png']}")
        print(f"  unit svg   : {item['unit_svg']}")
        print(f"  guide png  : {item['guide_png']}")
        print(f"  preview png: {item['preview_png']}")

    print()
    print("Done.")
