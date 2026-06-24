#!/usr/bin/env python3
import json
import os
import cv2
import numpy as np


PKG_DIR = os.path.dirname(os.path.abspath(__file__))

PNG_PATH = os.path.join(
    PKG_DIR,
    "models",
    "qr_whiteboard",
    "materials",
    "textures",
    "qr_board.png",
)

JSON_PATH = os.path.join(
    PKG_DIR,
    "models",
    "qr_whiteboard",
    "materials",
    "textures",
    "qr_board.json",
)

OUT_MODEL = os.path.join(
    PKG_DIR,
    "models",
    "qr_whiteboard",
    "model.sdf",
)

OUT_QR_WHITEBOARD = os.path.join(
    PKG_DIR,
    "models",
    "qr_whiteboard",
    "qr_whiteboard.sdf",
)


def sdf_header():
    return """<?xml version="1.0"?>
<sdf version="1.9">
  <model name="qr_whiteboard">
    <static>true</static>
    <link name="board">

      <collision name="board_collision">
        <geometry>
          <box>
            <size>0.06 2.25 2.0</size>
          </box>
        </geometry>
      </collision>

      <visual name="board_body">
        <geometry>
          <box>
            <size>0.06 2.25 2.0</size>
          </box>
        </geometry>
        <material>
          <ambient>1 1 1 1</ambient>
          <diffuse>1 1 1 1</diffuse>
          <specular>0.05 0.05 0.05 1</specular>
        </material>
      </visual>
"""


def sdf_footer():
    return """
    </link>
  </model>
</sdf>
"""


def black_box_visual(name, x, y, z, sy, sz):
    return f"""
      <visual name="{name}">
        <pose>{x:.5f} {y:.5f} {z:.5f} 0 0 0</pose>
        <geometry>
          <box>
            <size>0.004 {sy:.5f} {sz:.5f}</size>
          </box>
        </geometry>
        <material>
          <ambient>0 0 0 1</ambient>
          <diffuse>0 0 0 1</diffuse>
          <specular>0 0 0 1</specular>
        </material>
      </visual>
"""


def pixel_to_board(px, py, tex_w, tex_h, board_w, board_h):
    # 图像左上角 -> 白板本地坐标
    # 白板宽度方向对应 local y
    # 白板高度方向对应 local z
    y = board_w / 2.0 - (px / tex_w) * board_w
    z = board_h / 2.0 - (py / tex_h) * board_h
    return y, z


def main():
    img = cv2.imread(PNG_PATH, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Cannot read image: {PNG_PATH}")

    with open(JSON_PATH, "r") as f:
        meta = json.load(f)

    board_w, board_h = meta["board_size_m"]
    tex_w, tex_h = meta["texture_size_px"]

    parts = [sdf_header()]

    visual_count = 0

    # 每 10 像素合成一个 Gazebo 方块。
    # 400px QR -> 40x40 网格，足够看清二维码图案，而且不会生成太多 visual。
    cell_px = 10

    for code in meta["codes"]:
        label = code["label"]
        x0, y0, w, h = code["pixel_rect"]

        crop = img[y0:y0 + h, x0:x0 + w]

        grid_w = w // cell_px
        grid_h = h // cell_px

        for gy in range(grid_h):
            run_start = None

            for gx in range(grid_w):
                cell = crop[
                    gy * cell_px:(gy + 1) * cell_px,
                    gx * cell_px:(gx + 1) * cell_px,
                ]

                is_black = np.mean(cell) < 128

                if is_black and run_start is None:
                    run_start = gx

                if (not is_black or gx == grid_w - 1) and run_start is not None:
                    run_end = gx if not is_black else gx + 1

                    px_center = x0 + ((run_start + run_end) / 2.0) * cell_px
                    py_center = y0 + (gy + 0.5) * cell_px

                    y_board, z_board = pixel_to_board(
                        px_center, py_center, tex_w, tex_h, board_w, board_h
                    )

                    run_width_px = (run_end - run_start) * cell_px
                    sy = run_width_px / tex_w * board_w
                    sz = cell_px / tex_h * board_h

                    # 负 X 面：给无人机看的二维码面
                    parts.append(
                        black_box_visual(
                            f"{label}_black_{visual_count}",
                            -0.034,
                            y_board,
                            z_board,
                            sy,
                            sz,
                        )
                    )
                    visual_count += 1

                    run_start = None

    parts.append(sdf_footer())

    sdf = "".join(parts)

    with open(OUT_MODEL, "w") as f:
        f.write(sdf)

    with open(OUT_QR_WHITEBOARD, "w") as f:
        f.write(sdf)

    print(f"Generated: {OUT_MODEL}")
    print(f"Generated: {OUT_QR_WHITEBOARD}")
    print(f"Black visual boxes: {visual_count}")


if __name__ == "__main__":
    main()