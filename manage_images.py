#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker 镜像批量保存和加载脚本 (v2 - 集成 logging)
Author: 哈基咪 (为你编写)
Date: 2025-11-02

功能:
  save: 查找指定 tag 的所有镜像, 并使用 'docker save | pigz > name.tag.gz' 保存。
  load: 加载当前目录下所有的 '*.tag.gz' 压缩包。
"""

import subprocess
import sys
import argparse
import shutil
import glob
import os
import logging # 1. 导入 logging 模块

def setup_logging(level, log_file=None):
    """配置日志记录器"""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(level)

    # 清除任何可能存在的旧处理器
    if logger.hasHandlers():
        logger.handlers.clear()

    # 控制台处理器 (输出到 stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)

    if log_file:
        # 文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(file_handler)
        logger.info(f"日志将同时保存到: {log_file}")

def check_dependencies(tools):
    """检查所需的命令行工具是否已安装。"""
    missing = []
    for tool in tools:
        if shutil.which(tool) is None:
            missing.append(tool)
    if missing:
        logging.error(f"找不到以下必需的命令: {', '.join(missing)}")
        logging.error("请确保它们已安装并在你的 PATH 中。")
        sys.exit(1)
    logging.debug(f"所有依赖项均已找到: {', '.join(tools)}")
    return True

def find_compressor():
    """查找最佳的压缩工具 (优先使用 pigz)。"""
    if shutil.which("pigz"):
        logging.info("发现 'pigz' (并行 gzip)，将用它进行压缩/解压。")
        return "pigz", "pigz -dc"
    else:
        logging.warning("未发现 'pigz'。将回退到 'gzip' (速度较慢)。")
        return "gzip", "gunzip -c"

def save_images(tag, output_dir, compressor):
    """
    查找指定 tag 的镜像并保存。
    """
    logging.info(f"--- 正在查找 Tag 为 '{tag}' 的镜像 ---")
    
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True, text=True, check=True
        )
        all_images = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        logging.error(f"'docker images' 命令执行失败。")
        if e.stderr:
            logging.error(f"Docker 错误: {e.stderr.strip()}")
        sys.exit(1)

    images_to_save = [img for img in all_images if img.endswith(f":{tag}")]
    
    if not images_to_save:
        logging.warning(f"未找到 Tag 为 '{tag}' 的镜像。")
        return

    logging.info(f"找到了 {len(images_to_save)} 个镜像，准备保存...")

    os.makedirs(output_dir, exist_ok=True)
    for image_name in images_to_save:
        safe_name = image_name.replace("/", "-").replace(":", "_")
        output_filename = os.path.join(output_dir, f"{safe_name}.tag.gz")
        
        command = f"docker save {image_name} | {compressor} > {output_filename}"
        
        logging.info(f"  📦 正在保存: {image_name} -> {output_filename}")
        try:
            # 2. 捕获输出以便在出错时记录 stderr
            subprocess.run(
                command, shell=True, check=True, 
                capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"  保存失败: {image_name}。")
            # 3. 记录来自 docker 或 pigz 的实际错误信息
            if e.stderr:
                logging.error(f"  命令错误: {e.stderr.strip()}")

    logging.info("--- ✅ 保存完成 ---")

def load_images(input_dir, decompressor):
    """
    加载目录中所有的 .tag.gz 镜像。
    """
    search_pattern = os.path.join(input_dir, "*.tag.gz")
    image_files = glob.glob(search_pattern)

    if not image_files:
        logging.warning(f"在 '{input_dir}' 目录中未找到 '*.tag.gz' 文件。")
        return
        
    logging.info(f"找到了 {len(image_files)} 个镜像压缩包，准备加载...")

    for image_file in image_files:
        command = f"{decompressor} {image_file} | docker load"
        
        logging.info(f"  🚚 正在加载: {image_file}")
        try:
            # 2. 捕获输出以便在出错时记录 stderr
            subprocess.run(
                command, shell=True, check=True,
                capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"  加载失败: {image_file}。")
            # 3. 记录来自 docker 或 pigz/gunzip 的实际错误信息
            if e.stderr:
                logging.error(f"  命令错误: {e.stderr.strip()}")

    logging.info("--- ✅ 加载完成 ---")

def main():
    parser = argparse.ArgumentParser(description="Docker 镜像批量保存和加载脚本 (v2 - 集成 logging)")
    subparsers = parser.add_subparsers(dest="command", required=True, help="选择 'save' 或 'load'")

    # --- 'save' 子命令 ---
    save_parser = subparsers.add_parser("save", help="查找指定 tag 的镜像并打包保存")
    save_parser.add_argument("--tag", type=str, required=True, help="要保存的镜像 tag (例如: 1.0.2v)")
    save_parser.add_argument("--out-dir", type=str, default=".", help="保存 .tag.gz 文件的目录 (默认: 当前目录)")

    # --- 'load' 子命令 ---
    load_parser = subparsers.add_parser("load", help="加载目录中所有的 .tag.gz 镜像")
    load_parser.add_argument("--in-dir", type=str, default=".", help="加载 .tag.gz 文件的目录 (默认: 当前目录)")
    
    # 4. 添加全局日志参数
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="将日志保存到指定文件 (例如: manage.log)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="启用 DEBUG 级别的详细日志"
    )

    args = parser.parse_args()

    # 5. 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level, args.log_file)

    logging.debug(f"已启用 DEBUG 模式。收到的参数: {args}")
    
    # 检查 Docker
    check_dependencies(["docker"])
    
    compressor, decompressor = find_compressor()

    if args.command == "save":
        check_dependencies([compressor.split()[0]])
        save_images(args.tag, args.out_dir, compressor)
        
    elif args.command == "load":
        check_dependencies([decompressor.split()[0]])
        load_images(args.in_dir, decompressor)

if __name__ == "__main__":
    main()