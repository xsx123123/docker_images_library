# Author  : JZHANG
# Date    : 2025-11-1
# Version : 1.0.1v (Optimized)

# 1) 选择轻量基底镜像
FROM mambaorg/micromamba:1.5.10

# 2) 设置工作目录
SHELL ["/bin/bash", "-lc"]
WORKDIR /opt

# 3) 创建环境并安装
RUN micromamba create -y -n samtools_env -c conda-forge -c bioconda samtools=1.22.1 && \
    micromamba clean -a -y

# 4) 添加环境变量
ENV PATH=/opt/conda/envs/samtools_env/bin:$PATH

# 5) 设置默认命令 
CMD ["samtools", "version"]