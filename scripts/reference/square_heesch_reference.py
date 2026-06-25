import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# Varied Heesch-style tessellation unit generator
# ------------------------------------------------------------
# 목적:
# - 사각형 기반 테셀레이션 유닛 외곽선 후보를 다양하게 생성
# - T, G, C, C4 변환 아이디어 반영
# - Canva, PowerPoint, AI 내부 꾸미기용 도안으로 활용
#
# 기호:
# T  : Translation, 평행이동
# G  : Glide reflection, 미끄럼반사
# C  : 한 변의 중점을 기준으로 하는 180도 중심회전
# C4 : 90도 회전
#
# 주의:
# - 이 코드는 수업용 도안 제작에 적합한 실용 코드입니다.
# - 모든 Heesch 분류를 엄밀하게 자동 구현하는 연구용 코드는 아닙니다.
# - 변형 강도를 너무 크게 하면 자기교차가 생길 수 있습니다.
# ============================================================


# ------------------------------------------------------------
# 1. 기본 설정
# ------------------------------------------------------------

OUTPUT_DIR = Path("varied_heesch_tile_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

N_POINTS = 220
DPI = 300


# ------------------------------------------------------------
# 2. 기본 유틸리티 함수
# ------------------------------------------------------------

def normalize_profile(y, amplitude=0.15):
    """
    프로파일 값을 amplitude 범위로 정규화합니다.
    """
    y = np.array(y, dtype=float)
    max_abs = np.max(np.abs(y))

    if max_abs < 1e-9:
        return y

    return amplitude * y / max_abs


def endpoint_fade(t):
    """
    변의 양 끝점에서 굴곡이 0이 되도록 만드는 완화 함수입니다.
    꼭짓점에서 선이 어긋나는 것을 방지합니다.
    """
    return np.sin(math.pi * t)


def edge_from_offset(start, end, offset_values):
    """
    start에서 end까지 가는 선분을 기준으로,
    수직 방향 offset_values만큼 이동한 곡선을 생성합니다.
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


def reverse_points(points):
    """
    점 배열의 순서를 뒤집습니다.
    """
    return points[::-1].copy()


def translate_points(points, dx=0.0, dy=0.0):
    """
    점 배열을 평행이동합니다.
    """
    return points + np.array([dx, dy])


def rotate_points(points, angle_degrees, center=(0.5, 0.5)):
    """
    점 배열을 center 기준으로 회전합니다.
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


def combine_edges_clockwise(bottom, right, top, left):
    """
    네 변을 시계방향으로 연결합니다.

    bottom: 왼쪽 아래 -> 오른쪽 아래
    right : 오른쪽 아래 -> 오른쪽 위
    top   : 오른쪽 위 -> 왼쪽 위
    left  : 왼쪽 위 -> 왼쪽 아래
    """
    outline = np.vstack([
        bottom,
        right[1:],
        top[1:],
        left[1:],
        bottom[:1],
    ])

    return outline


# ------------------------------------------------------------
# 3. 다양한 변 프로파일
# ------------------------------------------------------------

def profile_wave(t, amplitude=0.15):
    """
    부드러운 물결형.
    기본적인 테셀레이션 도안에 적합합니다.
    """
    y = (
        0.8 * np.sin(math.pi * t)
        - 0.35 * np.sin(2 * math.pi * t)
        + 0.25 * np.sin(3 * math.pi * t)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_big_bump(t, amplitude=0.18):
    """
    가운데가 크게 튀어나온 혹 모양.
    동물의 등, 머리, 배처럼 쓰기 좋습니다.
    """
    y = (
        1.2 * np.exp(-((t - 0.50) / 0.20) ** 2)
        - 0.35 * np.exp(-((t - 0.18) / 0.10) ** 2)
        - 0.25 * np.exp(-((t - 0.82) / 0.10) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_cat_ears(t, amplitude=0.18):
    """
    고양이 귀처럼 두 개의 뾰족한 돌출이 있는 형태.
    """
    y = (
        1.30 * np.exp(-((t - 0.25) / 0.055) ** 2)
        + 1.20 * np.exp(-((t - 0.75) / 0.055) ** 2)
        - 0.45 * np.exp(-((t - 0.50) / 0.16) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_fish_tail(t, amplitude=0.20):
    """
    물고기 꼬리나 리본처럼 들어갔다 나오는 형태.
    """
    y = (
        -1.10 * np.exp(-((t - 0.35) / 0.10) ** 2)
        + 1.25 * np.exp(-((t - 0.62) / 0.10) ** 2)
        - 0.40 * np.exp(-((t - 0.82) / 0.07) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_robot_steps(t, amplitude=0.16):
    """
    로봇이나 기계 느낌의 계단형 변.
    직선적이고 각진 느낌을 줍니다.
    """
    y = np.zeros_like(t)

    y[(t >= 0.12) & (t < 0.25)] = 0.75
    y[(t >= 0.25) & (t < 0.37)] = -0.40
    y[(t >= 0.37) & (t < 0.53)] = 1.00
    y[(t >= 0.53) & (t < 0.66)] = -0.65
    y[(t >= 0.66) & (t < 0.82)] = 0.55

    # 끝점 근처를 부드럽게 줄여 꼭짓점 접합 문제를 줄임
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_teeth(t, amplitude=0.15):
    """
    톱니 또는 지그재그 느낌.
    몬스터, 로봇, 공룡 도안에 적합합니다.
    """
    y = np.zeros_like(t)

    centers = [0.18, 0.32, 0.48, 0.64, 0.80]
    signs = [1, -1, 1, -1, 1]

    for center, sign in zip(centers, signs):
        y += sign * np.maximum(0, 1 - np.abs(t - center) / 0.065)

    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_cloud(t, amplitude=0.17):
    """
    둥근 구름형 굴곡.
    꽃, 잎사귀, 양, 구름 캐릭터 등에 적합합니다.
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


def profile_leaf(t, amplitude=0.17):
    """
    잎사귀처럼 한쪽으로 흐르는 형태.
    자연물 도안에 적합합니다.
    """
    y = (
        1.00 * np.sin(math.pi * t)
        + 0.55 * np.sin(2 * math.pi * t)
        - 0.25 * np.sin(4 * math.pi * t)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_monster_arm(t, amplitude=0.20):
    """
    몬스터 팔이나 꼬리처럼 크게 튀어나왔다가 들어가는 형태.
    """
    y = (
        1.30 * np.exp(-((t - 0.28) / 0.12) ** 2)
        - 1.10 * np.exp(-((t - 0.58) / 0.13) ** 2)
        + 0.60 * np.exp(-((t - 0.82) / 0.08) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_snake(t, amplitude=0.16):
    """
    뱀이나 리본처럼 여러 번 휘어지는 형태.
    """
    y = (
        0.85 * np.sin(2 * math.pi * t)
        - 0.55 * np.sin(4 * math.pi * t)
        + 0.30 * np.sin(6 * math.pi * t)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_mountain(t, amplitude=0.18):
    """
    산봉우리처럼 큰 삼각형 돌출이 있는 형태.
    """
    y = np.zeros_like(t)

    y += 1.2 * np.maximum(0, 1 - np.abs(t - 0.30) / 0.16)
    y += 0.8 * np.maximum(0, 1 - np.abs(t - 0.68) / 0.20)
    y -= 0.45 * np.maximum(0, 1 - np.abs(t - 0.50) / 0.11)

    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def profile_double_socket(t, amplitude=0.19):
    """
    두 개의 홈과 하나의 돌출이 있는 형태.
    퍼즐 조각 느낌이 납니다.
    """
    y = (
        -1.00 * np.exp(-((t - 0.22) / 0.09) ** 2)
        + 1.25 * np.exp(-((t - 0.50) / 0.12) ** 2)
        - 0.90 * np.exp(-((t - 0.78) / 0.09) ** 2)
    )
    y *= endpoint_fade(t)
    return normalize_profile(y, amplitude)


def make_C_profile(profile_func, t, amplitude=0.15):
    """
    C 조건용 프로파일 생성.

    C 조건:
    f(1 - t) = -f(t)

    변의 중점을 기준으로 180도 회전했을 때 맞물리도록
    반대칭 성질을 갖게 만듭니다.
    """
    base = profile_func(t, amplitude=amplitude)
    reversed_base = profile_func(1 - t, amplitude=amplitude)
    y = 0.5 * (base - reversed_base)

    return normalize_profile(y, amplitude)


# 프로파일 목록
PROFILE_LIBRARY = {
    "wave": profile_wave,
    "big_bump": profile_big_bump,
    "cat_ears": profile_cat_ears,
    "fish_tail": profile_fish_tail,
    "robot_steps": profile_robot_steps,
    "teeth": profile_teeth,
    "cloud": profile_cloud,
    "leaf": profile_leaf,
    "monster_arm": profile_monster_arm,
    "snake": profile_snake,
    "mountain": profile_mountain,
    "double_socket": profile_double_socket,
}


# ------------------------------------------------------------
# 4. 변환 규칙별 유닛 생성 함수
# ------------------------------------------------------------

def make_TTTT_unit(bottom_profile, left_profile, amplitude=0.17):
    """
    TTTT형:
    위아래가 평행이동, 좌우가 평행이동 관계인 도안.
    """
    t = np.linspace(0, 1, N_POINTS)

    bottom_offset = bottom_profile(t, amplitude=amplitude)
    left_offset = left_profile(t, amplitude=amplitude)

    bottom = edge_from_offset((0, 0), (1, 0), bottom_offset)
    top_left_to_right = translate_points(bottom, dx=0, dy=1)

    left_bottom_to_top = edge_from_offset((0, 0), (0, 1), left_offset)
    right_bottom_to_top = translate_points(left_bottom_to_top, dx=1, dy=0)

    outline = combine_edges_clockwise(
        bottom=bottom,
        right=right_bottom_to_top,
        top=reverse_points(top_left_to_right),
        left=reverse_points(left_bottom_to_top),
    )

    return outline


def make_TGTG_unit(bottom_profile, left_profile, amplitude=0.17):
    """
    TGTG형:
    위아래는 평행이동 T,
    좌우는 미끄럼반사 G 느낌의 대응.
    """
    t = np.linspace(0, 1, N_POINTS)

    bottom_offset = bottom_profile(t, amplitude=amplitude)
    left_offset = left_profile(t, amplitude=amplitude)

    bottom = edge_from_offset((0, 0), (1, 0), bottom_offset)
    top_left_to_right = translate_points(bottom, dx=0, dy=1)

    left_bottom_to_top = edge_from_offset((0, 0), (0, 1), left_offset)

    # 미끄럼반사: 진행 방향을 뒤집은 프로파일을 오른쪽 변에 사용
    right_bottom_to_top = edge_from_offset((1, 0), (1, 1), left_offset[::-1])

    outline = combine_edges_clockwise(
        bottom=bottom,
        right=right_bottom_to_top,
        top=reverse_points(top_left_to_right),
        left=reverse_points(left_bottom_to_top),
    )

    return outline


def make_G1G2G1G2_unit(bottom_profile, left_profile, amplitude=0.17):
    """
    G1G2G1G2형:
    위아래, 좌우 모두 미끄럼반사형 대응을 넣은 도안.
    """
    t = np.linspace(0, 1, N_POINTS)

    bottom_offset = bottom_profile(t, amplitude=amplitude)
    left_offset = left_profile(t, amplitude=amplitude)

    bottom = edge_from_offset((0, 0), (1, 0), bottom_offset)
    top_left_to_right = edge_from_offset((0, 1), (1, 1), bottom_offset[::-1])

    left_bottom_to_top = edge_from_offset((0, 0), (0, 1), left_offset)
    right_bottom_to_top = edge_from_offset((1, 0), (1, 1), left_offset[::-1])

    outline = combine_edges_clockwise(
        bottom=bottom,
        right=right_bottom_to_top,
        top=reverse_points(top_left_to_right),
        left=reverse_points(left_bottom_to_top),
    )

    return outline


def make_TCTC_unit(bottom_profile, side_profile, amplitude=0.17):
    """
    TCTC형:
    위아래는 평행이동 T,
    좌우는 C 조건을 갖는 중심회전형 변.
    """
    t = np.linspace(0, 1, N_POINTS)

    bottom_offset = bottom_profile(t, amplitude=amplitude)
    side_offset = make_C_profile(side_profile, t, amplitude=amplitude)

    bottom = edge_from_offset((0, 0), (1, 0), bottom_offset)
    top_left_to_right = translate_points(bottom, dx=0, dy=1)

    right = edge_from_offset((1, 0), (1, 1), side_offset)
    left = edge_from_offset((0, 1), (0, 0), side_offset)

    outline = combine_edges_clockwise(
        bottom=bottom,
        right=right,
        top=reverse_points(top_left_to_right),
        left=left,
    )

    return outline


def make_CGCG_unit(horizontal_profile, vertical_profile, amplitude=0.17):
    """
    CGCG형:
    위아래는 C 조건,
    좌우는 G 조건.
    """
    t = np.linspace(0, 1, N_POINTS)

    horizontal_offset = make_C_profile(horizontal_profile, t, amplitude=amplitude)
    vertical_offset = vertical_profile(t, amplitude=amplitude)

    bottom = edge_from_offset((0, 0), (1, 0), horizontal_offset)
    top = edge_from_offset((1, 1), (0, 1), horizontal_offset)

    left_bottom_to_top = edge_from_offset((0, 0), (0, 1), vertical_offset)
    right_bottom_to_top = edge_from_offset((1, 0), (1, 1), vertical_offset[::-1])

    outline = combine_edges_clockwise(
        bottom=bottom,
        right=right_bottom_to_top,
        top=top,
        left=reverse_points(left_bottom_to_top),
    )

    return outline


def make_CCCC_unit(profile_a, profile_b, profile_c, profile_d, amplitude=0.17):
    """
    CCCC형:
    네 변 모두 각각 C 조건을 갖게 만든 도안.
    변별로 다른 프로파일을 넣을 수 있어서 이전보다 훨씬 다양한 모양이 나옵니다.
    """
    t = np.linspace(0, 1, N_POINTS)

    bottom_offset = make_C_profile(profile_a, t, amplitude=amplitude)
    right_offset = make_C_profile(profile_b, t, amplitude=amplitude)
    top_offset = make_C_profile(profile_c, t, amplitude=amplitude)
    left_offset = make_C_profile(profile_d, t, amplitude=amplitude)

    bottom = edge_from_offset((0, 0), (1, 0), bottom_offset)
    right = edge_from_offset((1, 0), (1, 1), right_offset)
    top = edge_from_offset((1, 1), (0, 1), top_offset)
    left = edge_from_offset((0, 1), (0, 0), left_offset)

    outline = combine_edges_clockwise(
        bottom=bottom,
        right=right,
        top=top,
        left=left,
    )

    return outline


def make_C4C4C4C4_unit(profile_func, amplitude=0.17):
    """
    C4C4C4C4형:
    한 변을 만든 뒤 정사각형 중심 기준 90도씩 회전시켜 네 변을 구성.
    """
    t = np.linspace(0, 1, N_POINTS)

    bottom_offset = profile_func(t, amplitude=amplitude)
    bottom = edge_from_offset((0, 0), (1, 0), bottom_offset)

    right = rotate_points(bottom, 90, center=(0.5, 0.5))
    top = rotate_points(bottom, 180, center=(0.5, 0.5))
    left = rotate_points(bottom, 270, center=(0.5, 0.5))

    # 방향 보정
    if np.linalg.norm(right[0] - np.array([1, 0])) > np.linalg.norm(right[-1] - np.array([1, 0])):
        right = reverse_points(right)

    if np.linalg.norm(top[0] - np.array([1, 1])) > np.linalg.norm(top[-1] - np.array([1, 1])):
        top = reverse_points(top)

    if np.linalg.norm(left[0] - np.array([0, 1])) > np.linalg.norm(left[-1] - np.array([0, 1])):
        left = reverse_points(left)

    outline = combine_edges_clockwise(
        bottom=bottom,
        right=right,
        top=top,
        left=left,
    )

    return outline


# ------------------------------------------------------------
# 5. 저장 함수
# ------------------------------------------------------------

def save_unit_outline(outline, name, output_dir=OUTPUT_DIR):
    """
    단일 유닛 외곽선을 PNG, SVG로 저장합니다.
    """
    png_path = output_dir / f"{name}_unit.png"
    svg_path = output_dir / f"{name}_unit.svg"

    fig, ax = plt.subplots(figsize=(5, 5))

    ax.plot(outline[:, 0], outline[:, 1], linewidth=3)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    margin = 0.30
    ax.set_xlim(-margin, 1 + margin)
    ax.set_ylim(-margin, 1 + margin)

    fig.savefig(png_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.05)

    plt.close(fig)

    return png_path, svg_path


def save_unit_with_square_guide(outline, name, output_dir=OUTPUT_DIR):
    """
    기준 정사각형이 보이는 확인용 이미지를 저장합니다.
    실제 학생용 도안보다는 교사용 검토용입니다.
    """
    png_path = output_dir / f"{name}_with_square_guide.png"

    fig, ax = plt.subplots(figsize=(5, 5))

    ax.plot(outline[:, 0], outline[:, 1], linewidth=3)
    ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], linestyle="--", linewidth=1)

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    margin = 0.30
    ax.set_xlim(-margin, 1 + margin)
    ax.set_ylim(-margin, 1 + margin)

    fig.savefig(png_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

    return png_path


def save_translation_preview(outline, name, output_dir=OUTPUT_DIR, rows=4, cols=4):
    """
    단순 평행이동 반복 미리보기입니다.

    TTTT형은 정확히 잘 맞습니다.
    다른 유형은 '외곽선 반복 느낌 확인용'으로 쓰면 됩니다.
    """
    preview_path = output_dir / f"{name}_translation_preview_{cols}x{rows}.png"

    fig, ax = plt.subplots(figsize=(7, 7))

    for i in range(cols):
        for j in range(rows):
            moved = translate_points(outline, dx=i, dy=j)
            ax.plot(moved[:, 0], moved[:, 1], linewidth=1.8)

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_xlim(-0.2, cols + 0.2)
    ax.set_ylim(-0.2, rows + 0.2)

    fig.savefig(preview_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

    return preview_path


def save_contact_sheet(items, filename="contact_sheet.png", output_dir=OUTPUT_DIR):
    """
    생성된 도안들을 한 장에 모아 보여주는 contact sheet를 만듭니다.
    """
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
        ax.set_title(name, fontsize=10)
        ax.set_xlim(-0.30, 1.30)
        ax.set_ylim(-0.30, 1.30)
        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")

    sheet_path = output_dir / filename
    fig.savefig(sheet_path, dpi=DPI, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)

    return sheet_path


# ------------------------------------------------------------
# 6. 다양한 도안 프리셋 생성
# ------------------------------------------------------------

def generate_varied_presets():
    """
    변 조작이 큰 다양한 도안들을 생성합니다.
    """
    P = PROFILE_LIBRARY

    presets = [
        # TTTT 계열
        {
            "name": "TTTT_cat_ears_monster_arm",
            "maker": lambda: make_TTTT_unit(
                P["cat_ears"],
                P["monster_arm"],
                amplitude=0.20,
            ),
        },
        {
            "name": "TTTT_fish_tail_cloud",
            "maker": lambda: make_TTTT_unit(
                P["fish_tail"],
                P["cloud"],
                amplitude=0.19,
            ),
        },
        {
            "name": "TTTT_robot_teeth",
            "maker": lambda: make_TTTT_unit(
                P["robot_steps"],
                P["teeth"],
                amplitude=0.18,
            ),
        },
        {
            "name": "TTTT_double_socket_mountain",
            "maker": lambda: make_TTTT_unit(
                P["double_socket"],
                P["mountain"],
                amplitude=0.20,
            ),
        },

        # TGTG 계열
        {
            "name": "TGTG_cat_dog_strong",
            "maker": lambda: make_TGTG_unit(
                P["cat_ears"],
                P["monster_arm"],
                amplitude=0.20,
            ),
        },
        {
            "name": "TGTG_fish_snake",
            "maker": lambda: make_TGTG_unit(
                P["fish_tail"],
                P["snake"],
                amplitude=0.19,
            ),
        },
        {
            "name": "TGTG_robot_monster",
            "maker": lambda: make_TGTG_unit(
                P["robot_steps"],
                P["teeth"],
                amplitude=0.19,
            ),
        },
        {
            "name": "TGTG_leaf_cloud",
            "maker": lambda: make_TGTG_unit(
                P["leaf"],
                P["cloud"],
                amplitude=0.18,
            ),
        },

        # G1G2G1G2 계열
        {
            "name": "G1G2_robot_teeth",
            "maker": lambda: make_G1G2G1G2_unit(
                P["robot_steps"],
                P["teeth"],
                amplitude=0.18,
            ),
        },
        {
            "name": "G1G2_monster_socket",
            "maker": lambda: make_G1G2G1G2_unit(
                P["monster_arm"],
                P["double_socket"],
                amplitude=0.20,
            ),
        },
        {
            "name": "G1G2_snake_mountain",
            "maker": lambda: make_G1G2G1G2_unit(
                P["snake"],
                P["mountain"],
                amplitude=0.19,
            ),
        },

        # TCTC 계열
        {
            "name": "TCTC_cat_center",
            "maker": lambda: make_TCTC_unit(
                P["cat_ears"],
                P["monster_arm"],
                amplitude=0.19,
            ),
        },
        {
            "name": "TCTC_fish_center",
            "maker": lambda: make_TCTC_unit(
                P["fish_tail"],
                P["snake"],
                amplitude=0.19,
            ),
        },
        {
            "name": "TCTC_robot_center",
            "maker": lambda: make_TCTC_unit(
                P["robot_steps"],
                P["teeth"],
                amplitude=0.18,
            ),
        },

        # CGCG 계열
        {
            "name": "CGCG_cloud_glide",
            "maker": lambda: make_CGCG_unit(
                P["cloud"],
                P["monster_arm"],
                amplitude=0.19,
            ),
        },
        {
            "name": "CGCG_socket_glide",
            "maker": lambda: make_CGCG_unit(
                P["double_socket"],
                P["snake"],
                amplitude=0.19,
            ),
        },

        # CCCC 계열
        {
            "name": "CCCC_mixed_strong",
            "maker": lambda: make_CCCC_unit(
                P["cat_ears"],
                P["fish_tail"],
                P["robot_steps"],
                P["cloud"],
                amplitude=0.18,
            ),
        },
        {
            "name": "CCCC_monster_rotation",
            "maker": lambda: make_CCCC_unit(
                P["monster_arm"],
                P["double_socket"],
                P["teeth"],
                P["snake"],
                amplitude=0.19,
            ),
        },

        # C4 계열
        {
            "name": "C4_cat_ears",
            "maker": lambda: make_C4C4C4C4_unit(
                P["cat_ears"],
                amplitude=0.18,
            ),
        },
        {
            "name": "C4_robot_steps",
            "maker": lambda: make_C4C4C4C4_unit(
                P["robot_steps"],
                amplitude=0.17,
            ),
        },
        {
            "name": "C4_leaf_flower",
            "maker": lambda: make_C4C4C4C4_unit(
                P["leaf"],
                amplitude=0.17,
            ),
        },
        {
            "name": "C4_double_socket",
            "maker": lambda: make_C4C4C4C4_unit(
                P["double_socket"],
                amplitude=0.18,
            ),
        },
    ]

    generated_items = []

    for preset in presets:
        name = preset["name"]
        outline = preset["maker"]()

        unit_png, unit_svg = save_unit_outline(outline, name)
        guide_png = save_unit_with_square_guide(outline, name)
        preview_png = save_translation_preview(outline, name)

        generated_items.append({
            "name": name,
            "outline": outline,
            "unit_png": unit_png,
            "unit_svg": unit_svg,
            "guide_png": guide_png,
            "preview_png": preview_png,
        })

    contact_sheet_path = save_contact_sheet(
        generated_items,
        filename="all_varied_units_contact_sheet.png",
    )

    return generated_items, contact_sheet_path


# ------------------------------------------------------------
# 7. 실행부
# ------------------------------------------------------------

if __name__ == "__main__":
    print("Generating varied Heesch-style tessellation unit outlines...")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")

    items, sheet = generate_varied_presets()

    print()
    print("Generated files:")
    for item in items:
        print(f"- {item['name']}")
        print(f"  unit png      : {item['unit_png']}")
        print(f"  unit svg      : {item['unit_svg']}")
        print(f"  guide png     : {item['guide_png']}")
        print(f"  preview png   : {item['preview_png']}")

    print()
    print(f"Contact sheet: {sheet}")
    print()
    print("Done.")
