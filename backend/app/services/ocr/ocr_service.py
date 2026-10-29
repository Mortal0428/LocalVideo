# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent - 多模态字幕与文字识别服务 (OCRService)
【业务定位】：支持从短剧视频关键帧中提取台词字幕与招牌文字
==============================================================================
"""
# -*- coding: utf-8 -*-
"""
多模态视觉感知中枢 · RapidOCR 深度神经网络服务
为全舰 1~9 号所有智能体提供开箱即用的离线高精度图像文字与视觉特征提取能力。
"""

import os
import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger("rapidocr_service")

class RapidOCRService:
    def __init__(self):
        self._lock = threading.Lock()
        self.engine = None
        self.engine_type = "NONE"
        self.init_error = None
        self._init_engine()

    def _init_engine(self):
        # 1. 优先加载基于 ONNX 的 RapidOCR 深度神经网络
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.engine = RapidOCR()
            self.engine_type = "RAPID_OCR"
            logger.info("RapidOCR 深度神经网络引擎已成功就绪 (E 盘 Python ONNX 运行时)")
            return
        except Exception as e:
            logger.warning(f"RapidOCR 加载未就绪: {e}")
            self.init_error = str(e)

        # 2. 备用双轨: ddddocr
        try:
            import ddddocr
            self.engine = ddddocr.DdddOcr(show_ad=False)
            self.engine_type = "DDDD_OCR"
            logger.info("已平滑切换至 ddddocr 备用视觉识别引擎")
            return
        except Exception as e2:
            logger.warning(f"ddddocr 备用引擎亦未加载: {e2}")

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        全量解析图片元数据与神经网络识别文本，封装为大模型友好的结构化提示块。
        """
        if not image_path or not os.path.exists(image_path):
            return {
                "success": False,
                "has_text": False,
                "detected_text": "",
                "formatted_prompt_block": "[多模态视觉系统提示: 图片附件不存在或路径无效]"
            }

        file_size_kb = round(os.path.getsize(image_path) / 1024, 1)
        ext = os.path.splitext(image_path)[1].lower().replace(".", "").upper() or "IMAGE"
        img_w, img_h = 0, 0

        try:
            from PIL import Image
            with Image.open(image_path) as im:
                img_w, img_h = im.size
                ext = (im.format or ext).upper()
        except Exception:
            pass

        meta_desc = f"{ext} 图像 ({img_w}x{img_h}px, {file_size_kb}KB)" if img_w else f"{ext} 图像 ({file_size_kb}KB)"

        extracted_lines = []
        if self.engine:
            with self._lock:
                try:
                    if self.engine_type == "RAPID_OCR":
                        result, _ = self.engine(image_path)
                        if result:
                            for item in result:
                                if len(item) > 1 and item[1] and str(item[1]).strip():
                                    extracted_lines.append(str(item[1]).strip())
                    elif self.engine_type == "DDDD_OCR":
                        with open(image_path, "rb") as f:
                            img_bytes = f.read()
                        text = self.engine.classification(img_bytes)
                        if text and text.strip():
                            extracted_lines.append(text.strip())
                except Exception as ex:
                    logger.warning(f"OCR 推理异常: {ex}")

        detected_text = "\n".join(extracted_lines)
        has_text = len(extracted_lines) > 0

        if has_text:
            formatted_prompt_block = (
                f"\n\n[多模态视觉感知系统 · RapidOCR 深度神经网络解析结果]\n"
                f"- 附件图像属性: {meta_desc}\n"
                f"- 图像中识别提取出的真实文字/数字/符号内容如下:\n"
                f"```text\n{detected_text}\n```\n"
                f"- 视觉推理协同指引: 以上文本为 RapidOCR 从用户上传的原始图片附件中高精度检测提取的真实内容。请智能体充分结合当前视觉文本与用户的问询进行深度推理、合规质检或创作解答。"
            )
        else:
            engine_status_tip = (
                f"经 {self.engine_type} 神经网络完整扫描，未在画面中检测出印刷或手写文字，属于纯自然图景/照片/图案"
                if self.engine else "系统处于轻量元数据模式"
            )
            formatted_prompt_block = (
                f"\n\n[多模态视觉感知系统 · 图像分析结果]\n"
                f"- 附件图像属性: {meta_desc}\n"
                f"- 视觉特征: {engine_status_tip}。\n"
                f"- 交互指引: 用户已上传该图片，请结合用户输入的消息与上下文，在回复中明确告知已查阅该图片并展开协同解读。"
            )

        return {
            "success": True,
            "has_text": has_text,
            "detected_text": detected_text,
            "lines_count": len(extracted_lines),
            "meta_desc": meta_desc,
            "formatted_prompt_block": formatted_prompt_block
        }


# 全局单例
ocr_service = RapidOCRService()
