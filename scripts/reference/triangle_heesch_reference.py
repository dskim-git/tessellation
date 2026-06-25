import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# Fixed Triangle Heesch-style Tessellation Unit Generator
# ------------------------------------------------------------
# 생성 유형:
# 1. CC6C6 : 정삼각형, 60도 회전쌍 + 남은 변 C
# 2. CC4C4 : 직각이등변삼각형, 90도 회전쌍 + 남은 변 C
# 3. CC3C3 : 30-120-30 이등변삼각형, 120도 회전쌍 + 남은 변 C
# 4. CCC   : 정삼각형, 세 변 모두 C
# 5. CGG   : 정삼각형, 위쪽 변 C + 아래 꼭짓점에서 만나는 두 변 G
#
# 이번 CGG 핵심:
#
#        B -------- C
#         \        /
#          \      /
#           \    /
#            \  /
#             A
#
# - top side CB : C
# - left side AB : G side 1
# - right side AC : G side 2
#
# AB를 먼저 그리고,
# AC에는 AB의 프로파일을 뒤집고 부호를 반대로 하여 배치한다.
# 즉:
# offset_AC = -offset_AB[::-1]
#
# 이렇게 해야 왼쪽 스케치가 아니라, 사용자가 제시한 오른쪽 CGG 구조가 된다.
# ============================================================


# ------------------------------------------------------------
# 1. 기본 설정
# ------------------------------------------------------------

OUTPUT_DIR = Path("triangle_heesch_fixed_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

N_POINTS = 320
DPI = 300

SQRT3 = math.sqrt(3)


# ------------------------------------------------------------
# 2. 기본 유틸리티
# ------------------------------------------------------------

def normalize_profile(y, amplitude=0.14):
    y = np.array(y, dtype=float)
    max_abs = np.max(np.abs(y))

    if max_abs < 1e-9:
        return y

    return amplitude * y / max_abs


def endpoint_fade(t):
    return np.sin(math.pi * t)


def edge_from_offset(start, end, offset_values):
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
    angle = math.radians(angle_degrees)
    cos_v = math.cos(angle)
    sin_v = math.sin(angle)

    rotation = np.array([
        [cos_v, -sin_v],
        [sin_v,  cos_v],
    ])

    center = np.array(center, dtype=float)

    return (points - center) @ rotation.T + center


def reverse_points(points):
    return points[::-1].copy()


def combine_triangle_edges(edge_1, edge_2, edge_3):
    outline = np.vstack([
        edge_1,
        edge_2[1:],
        edge_3[1:],
        edge_1[:1],
    ])

    return outline


# ------------------------------------------------------------
# 3. 자기교차 검사 함수
# ------------------------------------------------------------

def orientation(p, q, r):
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def on_segment(p, q, r, eps=1e-9):
    return (
        min(p[0], r[0]) - eps <= q[0] <= max(p[0], r[0]) + eps
        and min(p[1], r[1]) - eps <= q[1] <= max(p[1], r[1]) + eps
    )


def segments_intersect(p1, q1, p2, q2, eps=1e-9):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    if o1 * o2 < -eps and o3 * o4 < -eps:
        return True

    if abs(o1) <= eps and on_segment(p1, p2, q1):
        return True
    if abs(o2) <= eps and on_segment(p1, q2, q1):
        return True
    if abs(o3) <= eps and on_segment(p2, p1, q2):
        return True
    if abs(o4) <= eps and on_segment(p2, q1, q2):
        return True

    return False


def outline_has_self_intersection(outline):
    points = np.array(outline, dtype=float)
    segment_count = len(points) - 1

    for i in range(segment_count):
        p1 = points[i]
        q1 = points[i + 1]

        for j in range(i + 1, segment_count):
            if abs(i - j) <= 1:
                continue

            if i == 0 and j == segment_count - 1:
                continue

            p2 = points[j]
            q2 = points[j + 1]

            if segments_intersect(p1, q1, p2, q2):
                return True

    return False


# ------------------------------------------------------------
# 4. 변 프로파일
# ------------------------------------------------------------

def profile_wave(t, amplitude=0.14):
    y = (
        0.8 * np.sin(math.pi * t)
        - 0.35 * np.sin(2 * math.pi * t)
        + 0.25 * np.sin(3 * math.pi * t)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_cat_ears(t, amplitude=0.15):
    y = (
        1.30 * np.exp(-((t - 0.25) / 0.055) ** 2)
        + 1.20 * np.exp(-((t - 0.75) / 0.055) ** 2)
        - 0.45 * np.exp(-((t - 0.50) / 0.16) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_fish_tail(t, amplitude=0.16):
    y = (
        -1.10 * np.exp(-((t - 0.35) / 0.10) ** 2)
        + 1.25 * np.exp(-((t - 0.62) / 0.10) ** 2)
        - 0.40 * np.exp(-((t - 0.82) / 0.07) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_robot_steps(t, amplitude=0.14):
    y = np.zeros_like(t)

    y[(t >= 0.12) & (t < 0.25)] = 0.75
    y[(t >= 0.25) & (t < 0.37)] = -0.40
    y[(t >= 0.37) & (t < 0.53)] = 1.00
    y[(t >= 0.53) & (t < 0.66)] = -0.65
    y[(t >= 0.66) & (t < 0.82)] = 0.55

    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_cloud(t, amplitude=0.15):
    y = (
        0.70 * np.exp(-((t - 0.18) / 0.10) ** 2)
        + 1.10 * np.exp(-((t - 0.38) / 0.12) ** 2)
        + 0.80 * np.exp(-((t - 0.62) / 0.10) ** 2)
        + 0.55 * np.exp(-((t - 0.82) / 0.08) ** 2)
        - 0.45 * np.exp(-((t - 0.52) / 0.07) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_leaf(t, amplitude=0.14):
    y = (
        1.00 * np.sin(math.pi * t)
        + 0.55 * np.sin(2 * math.pi * t)
        - 0.25 * np.sin(4 * math.pi * t)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_monster_arm(t, amplitude=0.16):
    y = (
        1.30 * np.exp(-((t - 0.28) / 0.12) ** 2)
        - 1.10 * np.exp(-((t - 0.58) / 0.13) ** 2)
        + 0.60 * np.exp(-((t - 0.82) / 0.08) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_teeth(t, amplitude=0.14):
    y = np.zeros_like(t)

    centers = [0.18, 0.32, 0.48, 0.64, 0.80]
    signs = [1, -1, 1, -1, 1]

    for center, sign in zip(centers, signs):
        y += sign * np.maximum(0, 1 - np.abs(t - center) / 0.065)

    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_double_socket(t, amplitude=0.16):
    y = (
        -1.00 * np.exp(-((t - 0.22) / 0.09) ** 2)
        + 1.25 * np.exp(-((t - 0.50) / 0.12) ** 2)
        - 0.90 * np.exp(-((t - 0.78) / 0.09) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_snake(t, amplitude=0.14):
    y = (
        0.85 * np.sin(2 * math.pi * t)
        - 0.55 * np.sin(4 * math.pi * t)
        + 0.30 * np.sin(6 * math.pi * t)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


PROFILE_LIBRARY = {
    "wave": profile_wave,
    "cat_ears": profile_cat_ears,
    "fish_tail": profile_fish_tail,
    "robot_steps": profile_robot_steps,
    "cloud": profile_cloud,
    "leaf": profile_leaf,
    "monster_arm": profile_monster_arm,
    "teeth": profile_teeth,
    "double_socket": profile_double_socket,
    "snake": profile_snake,
}


# ------------------------------------------------------------
# 5. C 조건
# ------------------------------------------------------------

def make_C_profile(profile_func, t, amplitude=0.14):
    base = profile_func(t, amplitude=amplitude)
    reversed_base = profile_func(1 - t, amplitude=amplitude)

    y = 0.5 * (base - reversed_base)

    return normalize_profile(y, amplitude)


# ------------------------------------------------------------
# 6. 좌표 생성
# ------------------------------------------------------------

def make_isosceles_vertices(angle_degrees, side_length=1.0):
    A = np.array([0.0, 0.0])
    B = np.array([side_length, 0.0])

    angle = math.radians(angle_degrees)
    C = np.array([
        side_length * math.cos(angle),
        side_length * math.sin(angle),
    ])

    return A, B, C


def make_equilateral_vertices(side_length=1.0):
    return make_isosceles_vertices(60, side_length=side_length)


def make_equilateral_vertices_for_cgg(side_length=1.0):
    """
    CGG 전용 정삼각형 좌표.

          B -------- C
           \        /
            \      /
             \    /
              \  /
               A

    A: 아래 꼭짓점
    B: 왼쪽 위
    C: 오른쪽 위

    AB, AC가 G 쌍이고, BC가 C 변이 된다.
    """
    A = np.array([0.5 * side_length, 0.0])
    B = np.array([0.0, SQRT3 / 2 * side_length])
    C = np.array([1.0 * side_length, SQRT3 / 2 * side_length])

    return A, B, C


# ------------------------------------------------------------
# 7. CCnCn 일반 생성기
# ------------------------------------------------------------

def make_CCnCn_triangle_unit(
    angle_degrees,
    c_rotation_profile,
    c_edge_profile,
    rotation_amplitude=0.15,
    c_amplitude=0.13,
    rotation_offset_sign=None,
    auto_safe=True,
):
    if rotation_offset_sign is None:
        if angle_degrees == 120:
            rotation_offset_sign = -1.0
        else:
            rotation_offset_sign = 1.0

    A, B, C = make_isosceles_vertices(angle_degrees)
    t = np.linspace(0, 1, N_POINTS)

    scale_candidates = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

    last_result = None

    for scale in scale_candidates:
        current_rotation_amplitude = rotation_amplitude * scale
        current_c_amplitude = c_amplitude * scale

        offset_AB = c_rotation_profile(
            t,
            amplitude=current_rotation_amplitude,
        )
        offset_AB = rotation_offset_sign * offset_AB

        edge_AB = edge_from_offset(A, B, offset_AB)
        edge_AC = rotate_points(edge_AB, angle_degrees, center=A)

        offset_BC = make_C_profile(
            c_edge_profile,
            t,
            amplitude=current_c_amplitude,
        )
        edge_BC = edge_from_offset(B, C, offset_BC)

        edge_CA = reverse_points(edge_AC)

        outline = combine_triangle_edges(
            edge_AB,
            edge_BC,
            edge_CA,
        )

        edges = {
            "A": A,
            "B": B,
            "C": C,
            "edge_AB": edge_AB,
            "edge_AC": edge_AC,
            "edge_BC": edge_BC,
            "edge_CA": edge_CA,
            "used_rotation_amplitude": current_rotation_amplitude,
            "used_c_amplitude": current_c_amplitude,
            "rotation_offset_sign": rotation_offset_sign,
            "scale": scale,
        }

        last_result = (outline, edges)

        if not auto_safe:
            return outline, edges

        if not outline_has_self_intersection(outline):
            return outline, edges

    return last_result


def verify_CCnCn(angle_degrees, edges):
    A = edges["A"]
    B = edges["B"]
    C = edges["C"]

    edge_AB = edges["edge_AB"]
    edge_AC = edges["edge_AC"]
    edge_BC = edges["edge_BC"]

    rotated_AB = rotate_points(edge_AB, angle_degrees, center=A)
    rotation_error = np.max(np.linalg.norm(rotated_AB - edge_AC, axis=1))

    midpoint_BC = (B + C) / 2
    rotated_BC = rotate_points(edge_BC, 180, center=midpoint_BC)
    c_error = np.max(np.linalg.norm(rotated_BC - reverse_points(edge_BC), axis=1))

    outline = combine_triangle_edges(edge_AB, edge_BC, reverse_points(edge_AC))
    has_self_intersection = outline_has_self_intersection(outline)

    return rotation_error, c_error, has_self_intersection


# ------------------------------------------------------------
# 8. CCC 정삼각형 생성기
# ------------------------------------------------------------

def make_CCC_equilateral_unit(profile_ab, profile_bc, profile_ca, amplitude=0.14):
    A, B, C = make_equilateral_vertices()
    t = np.linspace(0, 1, N_POINTS)

    offset_AB = make_C_profile(profile_ab, t, amplitude=amplitude)
    offset_BC = make_C_profile(profile_bc, t, amplitude=amplitude)
    offset_CA = make_C_profile(profile_ca, t, amplitude=amplitude)

    edge_AB = edge_from_offset(A, B, offset_AB)
    edge_BC = edge_from_offset(B, C, offset_BC)
    edge_CA = edge_from_offset(C, A, offset_CA)

    outline = combine_triangle_edges(edge_AB, edge_BC, edge_CA)

    edges = {
        "A": A,
        "B": B,
        "C": C,
        "edge_AB": edge_AB,
        "edge_BC": edge_BC,
        "edge_CA": edge_CA,
    }

    return outline, edges


def verify_CCC(edges):
    A = edges["A"]
    B = edges["B"]
    C = edges["C"]

    side_data = [
        (edges["edge_AB"], A, B),
        (edges["edge_BC"], B, C),
        (edges["edge_CA"], C, A),
    ]

    errors = []

    for edge, P, Q in side_data:
        midpoint = (P + Q) / 2
        rotated = rotate_points(edge, 180, center=midpoint)
        error = np.max(np.linalg.norm(rotated - reverse_points(edge), axis=1))
        errors.append(error)

    outline = combine_triangle_edges(
        edges["edge_AB"],
        edges["edge_BC"],
        edges["edge_CA"],
    )

    return errors, outline_has_self_intersection(outline)


# ------------------------------------------------------------
# 9. CGG 정삼각형 생성기
# ------------------------------------------------------------

def make_CGG_equilateral_unit(
    c_profile,
    g_profile,
    c_amplitude=0.13,
    g_amplitude=0.14,
    g_offset_sign=1.0,
    auto_safe=True,
):
    """
    수정된 CGG 유닛.

    구조:

          B -------- C
           \        /
            \      /
             \    /
              \  /
               A

    - AB : G side 1
    - AC : G side 2
    - CB : C side

    핵심:
    - AB를 먼저 그린다.
    - AC는 AB를 회전시켜 만들지 않는다.
    - AC에는 AB의 프로파일을 뒤집고 부호를 반대로 하여 배치한다.
      offset_AC = -offset_AB[::-1]
    - CB는 C 조건이다.
    """

    A, B, C = make_equilateral_vertices_for_cgg()
    t = np.linspace(0, 1, N_POINTS)

    scale_candidates = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
    last_result = None

    for scale in scale_candidates:
        current_g_amplitude = g_amplitude * scale
        current_c_amplitude = c_amplitude * scale

        # 1. AB: G side 1
        offset_AB = g_profile(t, amplitude=current_g_amplitude)
        offset_AB = g_offset_sign * offset_AB
        edge_AB = edge_from_offset(A, B, offset_AB)

        # 2. AC: G side 2
        # AB 프로파일을 뒤집고 부호를 반대로 해서 배치한다.
        # 이것이 오른쪽 스케치의 핵심 구조다.
        offset_AC = -offset_AB[::-1]
        edge_AC = edge_from_offset(A, C, offset_AC)

        # 3. CB: C side
        # 외곽선 진행 방향을 A -> C -> B -> A로 잡기 때문에
        # 위쪽 C 변은 C -> B 방향으로 생성한다.
        offset_CB = make_C_profile(c_profile, t, amplitude=current_c_amplitude)
        edge_CB = edge_from_offset(C, B, offset_CB)

        # 외곽선: A -> C -> B -> A
        edge_BA = reverse_points(edge_AB)

        outline = combine_triangle_edges(
            edge_AC,
            edge_CB,
            edge_BA,
        )

        edges = {
            "A": A,
            "B": B,
            "C": C,
            "edge_AB": edge_AB,
            "edge_AC": edge_AC,
            "edge_CB": edge_CB,
            "edge_BA": edge_BA,
            "offset_AB": offset_AB,
            "offset_AC": offset_AC,
            "offset_CB": offset_CB,
            "g_offset_sign": g_offset_sign,
            "scale": scale,
            "used_g_amplitude": current_g_amplitude,
            "used_c_amplitude": current_c_amplitude,
        }

        last_result = (outline, edges)

        if not auto_safe:
            return outline, edges

        if not outline_has_self_intersection(outline):
            return outline, edges

    return last_result


def verify_CGG(edges):
    """
    CGG 생성 방식 확인.

    확인:
    - AC의 프로파일이 AB의 뒤집힌 프로파일에 부호 반전된 형태인가?
      offset_AC = -offset_AB[::-1]
    - CB는 C 조건을 만족하는가?
    """
    B = edges["B"]
    C = edges["C"]

    offset_AB = edges["offset_AB"]
    offset_AC = edges["offset_AC"]
    edge_CB = edges["edge_CB"]

    g_error = np.max(np.abs((-offset_AB[::-1]) - offset_AC))

    midpoint_CB = (C + B) / 2
    rotated_CB = rotate_points(edge_CB, 180, center=midpoint_CB)
    c_error = np.max(np.linalg.norm(rotated_CB - reverse_points(edge_CB), axis=1))

    outline = combine_triangle_edges(
        edges["edge_AC"],
        edges["edge_CB"],
        edges["edge_BA"],
    )

    return g_error, c_error, outline_has_self_intersection(outline)


# ------------------------------------------------------------
# 10. 저장 함수
# ------------------------------------------------------------

def save_unit_outline(outline, name):
    png_path = OUTPUT_DIR / f"{name}_unit.png"
    svg_path = OUTPUT_DIR / f"{name}_unit.svg"

    fig, ax = plt.subplots(figsize=(5, 5))

    ax.plot(outline[:, 0], outline[:, 1], linewidth=3)

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    margin = 0.35
    x_min, y_min = outline[:, 0].min(), outline[:, 1].min()
    x_max, y_max = outline[:, 0].max(), outline[:, 1].max()

    ax.set_xlim(x_min - margin, x_max + margin)
    ax.set_ylim(y_min - margin, y_max + margin)

    fig.savefig(png_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)

    return png_path, svg_path


def save_unit_with_guide(outline, name, tile_type, edges):
    guide_path = OUTPUT_DIR / f"{name}_guide.png"

    fig, ax = plt.subplots(figsize=(5, 5))

    ax.plot(outline[:, 0], outline[:, 1], linewidth=3)

    A = edges["A"]
    B = edges["B"]
    C = edges["C"]

    guide = np.vstack([A, B, C, A])
    ax.plot(guide[:, 0], guide[:, 1], linestyle="--", linewidth=1)

    labels = {
        "A": A,
        "B": B,
        "C": C,
    }

    if tile_type in ["CC6C6", "CC4C4", "CC3C3"]:
        labels["A(rot)"] = labels.pop("A")

    for label, point in labels.items():
        ax.scatter([point[0]], [point[1]], s=25)
        ax.text(point[0] + 0.03, point[1] + 0.03, label, fontsize=10)

    if tile_type == "CGG":
        midpoint_AB = (A + B) / 2
        midpoint_AC = (A + C) / 2
        midpoint_CB = (C + B) / 2

        ax.text(midpoint_AB[0] - 0.08, midpoint_AB[1], "G side 1", fontsize=9, ha="center")
        ax.text(midpoint_AC[0] + 0.08, midpoint_AC[1], "G side 2", fontsize=9, ha="center")
        ax.text(midpoint_CB[0], midpoint_CB[1] + 0.08, "C side", fontsize=9, ha="center")

    else:
        midpoint_AB = (A + B) / 2
        midpoint_AC = (A + C) / 2
        midpoint_BC = (B + C) / 2

        if tile_type in ["CC6C6", "CC4C4", "CC3C3"]:
            ax.text(midpoint_AB[0], midpoint_AB[1] - 0.08, "rot side 1", fontsize=9, ha="center")
            ax.text(midpoint_AC[0] - 0.08, midpoint_AC[1], "rot side 2", fontsize=9, ha="center")
            ax.text(midpoint_BC[0] + 0.08, midpoint_BC[1], "C side", fontsize=9, ha="center")

        elif tile_type == "CCC":
            ax.text(midpoint_AB[0], midpoint_AB[1] - 0.08, "C", fontsize=9, ha="center")
            ax.text(midpoint_AC[0] - 0.08, midpoint_AC[1], "C", fontsize=9, ha="center")
            ax.text(midpoint_BC[0] + 0.08, midpoint_BC[1], "C", fontsize=9, ha="center")

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    margin = 0.40
    x_min, y_min = outline[:, 0].min(), outline[:, 1].min()
    x_max, y_max = outline[:, 0].max(), outline[:, 1].max()

    ax.set_xlim(x_min - margin, x_max + margin)
    ax.set_ylim(y_min - margin, y_max + margin)

    fig.savefig(guide_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

    return guide_path


# ------------------------------------------------------------
# 11. 변환 미리보기
# ------------------------------------------------------------

def rotation_matrix_about_point(angle_degrees, center):
    angle = math.radians(angle_degrees)
    cos_v = math.cos(angle)
    sin_v = math.sin(angle)

    cx, cy = center

    matrix = np.array([
        [cos_v, -sin_v, cx - cos_v * cx + sin_v * cy],
        [sin_v,  cos_v, cy - sin_v * cx - cos_v * cy],
        [0.0,    0.0,   1.0],
    ])

    return matrix


def apply_transform(points, matrix):
    ones = np.ones((len(points), 1))
    homo = np.hstack([points, ones])
    transformed = homo @ matrix.T

    return transformed[:, :2]


def apply_transform_to_point(point, matrix):
    point_array = np.array([[point[0], point[1]]], dtype=float)
    return apply_transform(point_array, matrix)[0]


def matrix_key(matrix, decimals=6):
    rounded = np.round(matrix, decimals=decimals)
    return tuple(rounded.flatten())


def save_transform_preview(outline, transforms, preview_path):
    fig, ax = plt.subplots(figsize=(7, 7))

    all_points = []

    for matrix in transforms:
        moved = apply_transform(outline, matrix)
        all_points.append(moved)
        ax.plot(moved[:, 0], moved[:, 1], linewidth=1.4)

    all_points = np.vstack(all_points)

    x_min, y_min = all_points.min(axis=0)
    x_max, y_max = all_points.max(axis=0)

    margin = 0.4

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_xlim(x_min - margin, x_max + margin)
    ax.set_ylim(y_min - margin, y_max + margin)

    fig.savefig(preview_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def save_CCnCn_preview(outline, name, edges, angle_degrees, depth=4):
    preview_path = OUTPUT_DIR / f"{name}_preview.png"

    local_A = edges["A"]
    local_B = edges["B"]
    local_C = edges["C"]
    local_BC_midpoint = (local_B + local_C) / 2

    identity = np.eye(3)

    transforms = [identity]
    queue = [(identity, 0)]
    seen = {matrix_key(identity)}

    while queue:
        current_matrix, current_depth = queue.pop(0)

        if current_depth >= depth:
            continue

        world_A = apply_transform_to_point(local_A, current_matrix)
        world_BC_midpoint = apply_transform_to_point(local_BC_midpoint, current_matrix)

        candidate_transforms = [
            rotation_matrix_about_point(angle_degrees, world_A),
            rotation_matrix_about_point(-angle_degrees, world_A),
            rotation_matrix_about_point(180, world_BC_midpoint),
        ]

        for transform in candidate_transforms:
            new_matrix = transform @ current_matrix
            key = matrix_key(new_matrix)

            if key not in seen:
                seen.add(key)
                transforms.append(new_matrix)
                queue.append((new_matrix, current_depth + 1))

    save_transform_preview(outline, transforms, preview_path)

    return preview_path


def save_CCC_preview(outline, name, edges, depth=3):
    preview_path = OUTPUT_DIR / f"{name}_preview.png"

    A = edges["A"]
    B = edges["B"]
    C = edges["C"]

    side_midpoints = [
        (A + B) / 2,
        (B + C) / 2,
        (C + A) / 2,
    ]

    identity = np.eye(3)

    transforms = [identity]
    queue = [(identity, 0)]
    seen = {matrix_key(identity)}

    while queue:
        current_matrix, current_depth = queue.pop(0)

        if current_depth >= depth:
            continue

        for midpoint in side_midpoints:
            world_midpoint = apply_transform_to_point(midpoint, current_matrix)
            rotation = rotation_matrix_about_point(180, world_midpoint)
            new_matrix = rotation @ current_matrix

            key = matrix_key(new_matrix)

            if key not in seen:
                seen.add(key)
                transforms.append(new_matrix)
                queue.append((new_matrix, current_depth + 1))

    save_transform_preview(outline, transforms, preview_path)

    return preview_path


def save_CGG_preview(outline, name, edges, depth=3):
    """
    CGG 미리보기.

    실제 CGG 배치의 핵심은:
    - top C side는 중심회전으로 맞음
    - left/right G side는 프로파일 뒤집기 + 부호 반전 관계

    여기서는 구조 확인용으로:
    - top C side의 180도 회전 이웃
    - A 주변의 60도 방향 배치
    를 함께 보여준다.
    """
    preview_path = OUTPUT_DIR / f"{name}_preview.png"

    A = edges["A"]
    B = edges["B"]
    C = edges["C"]

    top_c_midpoint = (C + B) / 2

    identity = np.eye(3)

    transforms = [identity]
    queue = [(identity, 0)]
    seen = {matrix_key(identity)}

    while queue:
        current_matrix, current_depth = queue.pop(0)

        if current_depth >= depth:
            continue

        world_A = apply_transform_to_point(A, current_matrix)
        world_top_c_midpoint = apply_transform_to_point(top_c_midpoint, current_matrix)

        candidate_transforms = [
            rotation_matrix_about_point(180, world_top_c_midpoint),
            rotation_matrix_about_point(60, world_A),
            rotation_matrix_about_point(-60, world_A),
        ]

        for transform in candidate_transforms:
            new_matrix = transform @ current_matrix
            key = matrix_key(new_matrix)

            if key not in seen:
                seen.add(key)
                transforms.append(new_matrix)
                queue.append((new_matrix, current_depth + 1))

    save_transform_preview(outline, transforms, preview_path)

    return preview_path


# ------------------------------------------------------------
# 12. Contact sheet
# ------------------------------------------------------------

def save_contact_sheet(items, filename="all_triangle_heesch_fixed_contact_sheet.png"):
    n = len(items)
    cols = 4
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))

    if rows == 1:
        axes = np.array([axes])

    axes = axes.flatten()

    for ax in axes:
        ax.axis("off")
        ax.set_aspect("equal", adjustable="box")

    for ax, item in zip(axes, items):
        outline = item["outline"]
        name = item["name"]

        ax.plot(outline[:, 0], outline[:, 1], linewidth=2.2)
        ax.set_title(name, fontsize=9)

        x_min, y_min = outline[:, 0].min(), outline[:, 1].min()
        x_max, y_max = outline[:, 0].max(), outline[:, 1].max()

        margin = 0.25
        ax.set_xlim(x_min - margin, x_max + margin)
        ax.set_ylim(y_min - margin, y_max + margin)

        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")

    sheet_path = OUTPUT_DIR / filename
    fig.savefig(sheet_path, dpi=DPI, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)

    return sheet_path


# ------------------------------------------------------------
# 13. 프리셋 생성
# ------------------------------------------------------------

def generate_all_presets():
    P = PROFILE_LIBRARY

    presets = [
        # ----------------------------------------------------
        # CC6C6: 정삼각형
        # ----------------------------------------------------
        {
            "name": "CC6C6_cat_cloud",
            "type": "CC6C6",
            "angle": 60,
            "maker": lambda: make_CCnCn_triangle_unit(
                angle_degrees=60,
                c_rotation_profile=P["cat_ears"],
                c_edge_profile=P["cloud"],
                rotation_amplitude=0.15,
                c_amplitude=0.13,
                rotation_offset_sign=1.0,
                auto_safe=True,
            ),
        },
        {
            "name": "CC6C6_fish_wave",
            "type": "CC6C6",
            "angle": 60,
            "maker": lambda: make_CCnCn_triangle_unit(
                angle_degrees=60,
                c_rotation_profile=P["fish_tail"],
                c_edge_profile=P["wave"],
                rotation_amplitude=0.16,
                c_amplitude=0.13,
                rotation_offset_sign=1.0,
                auto_safe=True,
            ),
        },

        # ----------------------------------------------------
        # CC4C4: 직각이등변삼각형
        # ----------------------------------------------------
        {
            "name": "CC4C4_robot_cloud",
            "type": "CC4C4",
            "angle": 90,
            "maker": lambda: make_CCnCn_triangle_unit(
                angle_degrees=90,
                c_rotation_profile=P["robot_steps"],
                c_edge_profile=P["cloud"],
                rotation_amplitude=0.14,
                c_amplitude=0.13,
                rotation_offset_sign=1.0,
                auto_safe=True,
            ),
        },
        {
            "name": "CC4C4_leaf_socket",
            "type": "CC4C4",
            "angle": 90,
            "maker": lambda: make_CCnCn_triangle_unit(
                angle_degrees=90,
                c_rotation_profile=P["leaf"],
                c_edge_profile=P["double_socket"],
                rotation_amplitude=0.14,
                c_amplitude=0.13,
                rotation_offset_sign=1.0,
                auto_safe=True,
            ),
        },

        # ----------------------------------------------------
        # CC3C3: 30-120-30 이등변삼각형
        # ----------------------------------------------------
        {
            "name": "CC3C3_monster_wave",
            "type": "CC3C3",
            "angle": 120,
            "maker": lambda: make_CCnCn_triangle_unit(
                angle_degrees=120,
                c_rotation_profile=P["monster_arm"],
                c_edge_profile=P["wave"],
                rotation_amplitude=0.12,
                c_amplitude=0.10,
                rotation_offset_sign=-1.0,
                auto_safe=True,
            ),
        },
        {
            "name": "CC3C3_fish_teeth",
            "type": "CC3C3",
            "angle": 120,
            "maker": lambda: make_CCnCn_triangle_unit(
                angle_degrees=120,
                c_rotation_profile=P["fish_tail"],
                c_edge_profile=P["teeth"],
                rotation_amplitude=0.12,
                c_amplitude=0.10,
                rotation_offset_sign=-1.0,
                auto_safe=True,
            ),
        },

        # ----------------------------------------------------
        # CCC: 정삼각형
        # ----------------------------------------------------
        {
            "name": "CCC_cat_fish_cloud",
            "type": "CCC",
            "angle": None,
            "maker": lambda: make_CCC_equilateral_unit(
                profile_ab=P["cat_ears"],
                profile_bc=P["fish_tail"],
                profile_ca=P["cloud"],
                amplitude=0.14,
            ),
        },
        {
            "name": "CCC_robot_leaf_snake",
            "type": "CCC",
            "angle": None,
            "maker": lambda: make_CCC_equilateral_unit(
                profile_ab=P["robot_steps"],
                profile_bc=P["leaf"],
                profile_ca=P["snake"],
                amplitude=0.14,
            ),
        },

        # ----------------------------------------------------
        # CGG: 정삼각형
        # 오른쪽 스케치 기준:
        # - top side CB: C
        # - left side AB: G side 1
        # - right side AC: G side 2
        # ----------------------------------------------------
        {
            "name": "CGG_cloud_snake",
            "type": "CGG",
            "angle": None,
            "maker": lambda: make_CGG_equilateral_unit(
                c_profile=P["cloud"],
                g_profile=P["snake"],
                c_amplitude=0.12,
                g_amplitude=0.13,
                g_offset_sign=1.0,
                auto_safe=True,
            ),
        },
        {
            "name": "CGG_robot_monster",
            "type": "CGG",
            "angle": None,
            "maker": lambda: make_CGG_equilateral_unit(
                c_profile=P["robot_steps"],
                g_profile=P["monster_arm"],
                c_amplitude=0.11,
                g_amplitude=0.13,
                g_offset_sign=1.0,
                auto_safe=True,
            ),
        },
        {
            "name": "CGG_fish_cloud",
            "type": "CGG",
            "angle": None,
            "maker": lambda: make_CGG_equilateral_unit(
                c_profile=P["fish_tail"],
                g_profile=P["cloud"],
                c_amplitude=0.12,
                g_amplitude=0.13,
                g_offset_sign=1.0,
                auto_safe=True,
            ),
        },
    ]

    items = []

    for preset in presets:
        name = preset["name"]
        tile_type = preset["type"]
        angle = preset["angle"]

        outline, edges = preset["maker"]()

        unit_png, unit_svg = save_unit_outline(outline, name)
        guide_png = save_unit_with_guide(outline, name, tile_type, edges)

        if tile_type in ["CC6C6", "CC4C4", "CC3C3"]:
            preview_png = save_CCnCn_preview(
                outline=outline,
                name=name,
                edges=edges,
                angle_degrees=angle,
                depth=4,
            )

            rotation_error, c_error, has_self_intersection = verify_CCnCn(angle, edges)

            check_info = {
                "rotation_error": rotation_error,
                "c_error": c_error,
                "has_self_intersection": has_self_intersection,
                "scale": edges.get("scale", 1.0),
                "used_rotation_amplitude": edges.get("used_rotation_amplitude", None),
                "used_c_amplitude": edges.get("used_c_amplitude", None),
                "rotation_offset_sign": edges.get("rotation_offset_sign", None),
            }

        elif tile_type == "CCC":
            preview_png = save_CCC_preview(
                outline=outline,
                name=name,
                edges=edges,
                depth=3,
            )

            c_errors, has_self_intersection = verify_CCC(edges)

            check_info = {
                "c_errors": c_errors,
                "has_self_intersection": has_self_intersection,
            }

        elif tile_type == "CGG":
            preview_png = save_CGG_preview(
                outline=outline,
                name=name,
                edges=edges,
                depth=3,
            )

            g_error, c_error, has_self_intersection = verify_CGG(edges)

            check_info = {
                "g_error": g_error,
                "c_error": c_error,
                "has_self_intersection": has_self_intersection,
                "scale": edges.get("scale", 1.0),
                "used_g_amplitude": edges.get("used_g_amplitude", None),
                "used_c_amplitude": edges.get("used_c_amplitude", None),
                "note": "CGG: top side CB is C; AB and AC are G pair with offset_AC = -offset_AB[::-1].",
            }

        else:
            raise ValueError(f"Unknown tile type: {tile_type}")

        items.append({
            "name": name,
            "type": tile_type,
            "outline": outline,
            "unit_png": unit_png,
            "unit_svg": unit_svg,
            "guide_png": guide_png,
            "preview_png": preview_png,
            "check_info": check_info,
        })

    contact_sheet = save_contact_sheet(items)

    return items, contact_sheet


# ------------------------------------------------------------
# 14. 실행부
# ------------------------------------------------------------

if __name__ == "__main__":
    print("Generating fixed triangle Heesch-style tessellation units...")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")

    items, contact_sheet = generate_all_presets()

    print()
    print("Generated files:")

    for item in items:
        print(f"- {item['name']} [{item['type']}]")
        print(f"  unit png   : {item['unit_png']}")
        print(f"  unit svg   : {item['unit_svg']}")
        print(f"  guide png  : {item['guide_png']}")
        print(f"  preview png: {item['preview_png']}")

        check_info = item["check_info"]

        if item["type"] in ["CC6C6", "CC4C4", "CC3C3"]:
            print(f"  rotation error       : {check_info['rotation_error']:.10f}")
            print(f"  C error              : {check_info['c_error']:.10f}")
            print(f"  self intersection    : {check_info['has_self_intersection']}")
            print(f"  used scale           : {check_info['scale']}")
            print(f"  rotation offset sign : {check_info['rotation_offset_sign']}")
            print(f"  used rot amplitude   : {check_info['used_rotation_amplitude']}")
            print(f"  used C amplitude     : {check_info['used_c_amplitude']}")

        elif item["type"] == "CCC":
            c_errors = check_info["c_errors"]
            print(
                "  C errors             : "
                + ", ".join(f"{error:.10f}" for error in c_errors)
            )
            print(f"  self intersection    : {check_info['has_self_intersection']}")

        elif item["type"] == "CGG":
            print(f"  G flip error         : {check_info['g_error']:.10f}")
            print(f"  C error              : {check_info['c_error']:.10f}")
            print(f"  self intersection    : {check_info['has_self_intersection']}")
            print(f"  used scale           : {check_info['scale']}")
            print(f"  used G amplitude     : {check_info['used_g_amplitude']}")
            print(f"  used C amplitude     : {check_info['used_c_amplitude']}")
            print(f"  note                 : {check_info['note']}")

        print()

    print(f"Contact sheet: {contact_sheet}")
    print()
    print("Done.")
