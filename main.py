import torch
import numpy as np
import cv2
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
from moviepy.editor import VideoFileClip

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ===============================
# 音声合成
# ===============================
def overlay_audio(input_video_path, source_video_path, output_video_path):
    target_clip = VideoFileClip(input_video_path)
    source_clip = VideoFileClip(source_video_path)

    extracted_audio = source_clip.audio
    target_clip = target_clip.set_audio(extracted_audio)

    target_clip.write_videofile(
        output_video_path,
        codec='libx264',
        audio_codec='aac'
    )

# ===============================
# Utility
# ===============================
def compute_auto_threshold(depth_map, ratio=0.4):
    d_min, d_max = depth_map.min(), depth_map.max()
    normalized = (depth_map - d_min) / (d_max - d_min + 1e-8)
    return np.quantile(normalized, 1 - ratio)

# ===============================
# Depth → RGBA
# ===============================
def depth_mask_and_alpha(image_bgr, processor, model, ratio):
    img = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = img.shape

    inputs = processor(images=img, return_tensors="pt").to(device)
    with torch.no_grad():
        prediction = model(**inputs).predicted_depth
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=(h, w),
            mode="bicubic",
            align_corners=False,
        ).squeeze()

        depth_map = prediction.cpu().numpy()

        # 上半分補正
        y = np.linspace(0, 1, h).reshape(-1, 1)
        scale = np.ones((h, 1), dtype=np.float32)
        upper = y <= 0.5
        scale[upper] = 1 - np.cos(y[upper] / 0.5 * np.pi / 2)
        depth_map *= scale

    auto_thresh = compute_auto_threshold(depth_map, ratio)
    mask = (depth_map >= auto_thresh).astype(np.uint8) * 255

    rgba = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2BGRA)
    rgba[mask == 0, 3] = 0
    return rgba

# ===============================
# フェード処理
# ===============================
def apply_edge_fade(image, side='right', fade_width=100):
    alpha = image[:, :, 3].astype(np.float32)
    if side == 'right':
        fade = np.linspace(1.0, 0.0, fade_width)[None, :]
        alpha[:, -fade_width:] *= fade
    else:
        fade = np.linspace(0.0, 1.0, fade_width)[None, :]
        alpha[:, :fade_width] *= fade
    image[:, :, 3] = alpha.clip(0, 255).astype(np.uint8)

def apply_partial_fade_vertical(
    image, x_start, x_end, side='left',
    fade_width=30, apply_upper=True, apply_lower=True
):
    h = image.shape[0]
    y_mid = h // 2
    alpha = image[:, :, 3].astype(np.float32)
    fade_width = min(fade_width, x_end - x_start)

    if side == 'left':
        fade = np.linspace(0.0, 1.0, fade_width)
        xs = range(x_start, x_start + fade_width)
    else:
        fade = np.linspace(1.0, 0.0, fade_width)
        xs = range(x_end - fade_width, x_end)

    for i, x in enumerate(xs):
        if apply_upper:
            alpha[:y_mid, x] *= fade[i]
        if apply_lower:
            alpha[y_mid:, x] *= fade[i]

    image[:, :, 3] = alpha.clip(0, 255).astype(np.uint8)

# ===============================
# 合成処理
# ===============================
def paste_with_alpha(base, overlay, x, y):
    h, w = overlay.shape[:2]
    roi = base[y:y+h, x:x+w]
    alpha = overlay[:, :, 3:4] / 255.0
    base[y:y+h, x:x+w, :3] = (
        overlay[:, :, :3] * alpha + roi[:, :, :3] * (1 - alpha)
    ).astype(np.uint8)
    base[y:y+h, x:x+w, 3] = 255

def create_bf_image(img_bgr):
    bf = np.zeros_like(img_bgr)
    bf[:, :960] = img_bgr[:, 2880:]
    bf[:, 960:] = img_bgr[:, :2880]
    return bf

def generate_alpha_regions(image_bgr, alpha_fg):
    alpha_bg = 255 - alpha_fg
    bgra = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2BGRA)

    img_L = bgra.copy()
    img_L[:, :2560, 3] = alpha_bg[:, :2560]
    crop_L = img_L[:, 1920:]

    img_R = bgra.copy()
    img_R[:, 1280:, 3] = alpha_bg[:, 1280:]
    crop_R = img_R[:, :1920]

    return crop_L, crop_R

def create_composites_numpy(BF_L, BF_R, BF_B):
    base1 = np.zeros((1920, 3840, 4), np.uint8)
    for img in [BF_R[1], BF_L[1], BF_B[1]]:
        apply_edge_fade(img, 'right')
    paste_with_alpha(base1, BF_R[1][:, :1280], 2560, 0)
    paste_with_alpha(base1, BF_L[1], 1280, 0)
    paste_with_alpha(base1, BF_B[1], 0, 0)
    paste_with_alpha(base1, BF_R[1][:, 1280:], 0, 0)

    base2 = np.zeros((1920, 3840, 4), np.uint8)
    for img in [BF_L[0], BF_R[0], BF_B[0]]:
        apply_edge_fade(img, 'left')
    paste_with_alpha(base2, BF_L[0][:, 640:], 0, 0)
    paste_with_alpha(base2, BF_R[0], 640, 0)
    paste_with_alpha(base2, BF_B[0], 1920, 0)
    paste_with_alpha(base2, BF_L[0][:, :640], 3200, 0)

    return np.vstack([base1, base2])

# ===============================
# main（動画）
# ===============================
def main():
    ratio = 0.45

    cap_back  = cv2.VideoCapture("Back.mp4")
    cap_right = cv2.VideoCapture("Right.mp4")
    cap_left  = cv2.VideoCapture("Left.mp4")

    fps = cap_back.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        "output_depth_composite.mp4",
        fourcc,
        fps,
        (3840, 3840)
    )

    processor = AutoImageProcessor.from_pretrained(
        "depth-anything/Depth-Anything-V2-Small-hf"
    )
    model = AutoModelForDepthEstimation.from_pretrained(
        "depth-anything/Depth-Anything-V2-Small-hf"
    ).to(device).eval()

    frame_id = 0
    while True:
        ret_b, back = cap_back.read()
        ret_r, right = cap_right.read()
        ret_l, left = cap_left.read()
        if not (ret_b and ret_r and ret_l):
            break

        bf_imgs = [create_bf_image(x) for x in [left, right, back]]
        alphas = []

        for img in bf_imgs:
            rgba = depth_mask_and_alpha(img, processor, model, ratio)
            apply_partial_fade_vertical(rgba, 1280, 1330, 'left', 50)
            apply_partial_fade_vertical(rgba, 2510, 2560, 'right', 50)
            alphas.append(rgba)

        crops = [
            generate_alpha_regions(img, a[:, :, 3])
            for img, a in zip(bf_imgs, alphas)
        ]

        result = create_composites_numpy(crops[0], crops[1], crops[2])
        out.write(result[:, :, :3])

        frame_id += 1
        if frame_id % 10 == 0:
            print(f"processed frame {frame_id}")

    out.release()
    cap_back.release()
    cap_right.release()
    cap_left.release()
    print("✔ depth composite video saved")

    # 音声を後から合成
    overlay_audio(
        "output_depth_composite.mp4",
        "Back.mp4",
        "output_depth_with_audio.mp4"
    )
    print("✔ audio overlay complete")

if __name__ == "__main__":
    main()